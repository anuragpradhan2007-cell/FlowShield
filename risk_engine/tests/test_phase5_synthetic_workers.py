"""
Phase 5: Unit Testing with Synthetic Edge-Case Worker Profiles
Validates behavior for:
- Worker A (Ideal): Steady earnings, high frequency, solid savings buffer -> Stable (>= 70.0)
- Worker B (Volatile/At Risk): Sporadic earnings, high variance, recent 50% drop -> At Risk (40.0 - 69.9)
- Worker C (Critical): Zero activity over past 10+ days, depleted savings -> Critical (< 40.0)

Confirms score bounds (0-100) and downstream event triggering for Member 4 Protection Engine.
"""

import uuid
from datetime import date, timedelta
import pytest
from fastapi.testclient import TestClient

from app.database import Base, engine
from app.main import app
from app.schemas.risk_score import (
    RiskTier,
    DailyIncomeRecord,
    WorkerDataInput,
)
from app.services.scoring import evaluate_worker_risk

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_test_database():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


# =========================================================================
# Synthetic Dataset Generators for Workers A, B, and C
# =========================================================================

def build_worker_a_dataset() -> WorkerDataInput:
    """
    Worker A (Ideal):
    - Steady weekly earnings ($150/day with tiny ±$5 variance).
    - High work frequency (worked 28 out of past 30 days).
    - Positive/flat recent trend (past 14 days equal to 60-day baseline).
    - Solid savings buffer ($2,500 reserve vs $500/week expenses = 5 weeks cushion).
    - Clear weather conditions.
    """
    worker_id = uuid.uuid4()
    start_date = date(2026, 1, 1)
    records = []
    for i in range(60):
        # Steady earnings: $150/day with minor $5 variance
        amount = 150.0 + (5.0 if i % 2 == 0 else -5.0)
        records.append(
            DailyIncomeRecord(
                date=str(start_date + timedelta(days=i)),
                amount=amount,
                hours_worked=8.0,
                trips_completed=12,
            )
        )

    return WorkerDataInput(
        worker_id=worker_id,
        income_history=records,
        current_savings=2500.0,
        weekly_expenses=500.0,
        weather_condition="CLEAR",
        expected_capacity_days=24,
    )


def build_worker_b_dataset() -> WorkerDataInput:
    """
    Worker B (Volatile / At Risk):
    - Sporadic earnings and high variance.
    - Recent 50%+ drop in income: earned $180/day for 46 days, then dropped to $50/day (or $0) for last 14 days.
    - Low savings buffer ($300 reserve vs $450/week expenses = < 1 week cushion).
    - Adverse weather alert ("SEVERE_ALERT").
    """
    worker_id = uuid.uuid4()
    start_date = date(2026, 1, 1)
    records = []

    # Baseline 46 days: high and volatile ($180 ± $60)
    for i in range(46):
        amt = 180.0 + (60.0 if i % 2 == 0 else -60.0)
        records.append(DailyIncomeRecord(date=str(start_date + timedelta(days=i)), amount=amt))

    # Recent 14 days: sharp 50%+ drop (alternating between $50 and $0)
    for i in range(46, 60):
        amt = 50.0 if i % 2 == 0 else 0.0
        records.append(DailyIncomeRecord(date=str(start_date + timedelta(days=i)), amount=amt))

    return WorkerDataInput(
        worker_id=worker_id,
        income_history=records,
        current_savings=300.0,
        weekly_expenses=450.0,
        weather_condition="SEVERE_ALERT",
        expected_capacity_days=24,
    )


def build_worker_c_dataset() -> WorkerDataInput:
    """
    Worker C (Critical):
    - Zero activity over past 10-15 days.
    - Minimal earnings in earlier period ($50/day for 10 days, then 0 for 50 days).
    - Completely depleted emergency savings ($0).
    - Severe external disruption.
    """
    worker_id = uuid.uuid4()
    start_date = date(2026, 1, 1)
    records = []

    for i in range(60):
        # Only worked 5 days at the very beginning of the 60-day window
        amt = 50.0 if i < 5 else 0.0
        records.append(DailyIncomeRecord(date=str(start_date + timedelta(days=i)), amount=amt))

    return WorkerDataInput(
        worker_id=worker_id,
        income_history=records,
        current_savings=0.0,
        weekly_expenses=400.0,
        weather_condition="SEVERE_ALERT",
        expected_capacity_days=24,
    )


# =========================================================================
# Phase 5 Validation Tests
# =========================================================================

def test_worker_a_ideal_profile_stability():
    """Verify Worker A achieves Stable tier (>= 70.0) with zero anomaly flags"""
    worker_a = build_worker_a_dataset()
    score, tier, breakdown, flags = evaluate_worker_risk(worker_a)

    # 1. Bounded score validation
    assert 0.0 <= score <= 100.0
    assert score >= 70.0, f"Worker A score should be >= 70.0, got {score}"

    # 2. Tier assignment
    assert tier == RiskTier.STABLE

    # 3. Downstream Member 4 trigger check
    assert len(flags) == 0, f"Worker A should have no anomaly flags, got: {flags}"

    # 4. Feature sub-scores
    assert breakdown.income_consistency.normalized_score >= 80.0
    assert breakdown.work_frequency.normalized_score >= 90.0
    assert breakdown.savings_buffer.normalized_score == 100.0


def test_worker_b_volatile_profile_triggers_at_risk():
    """Verify Worker B falls into 'At Risk' tier (40.0 - 69.9) and flags drop"""
    worker_b = build_worker_b_dataset()
    score, tier, breakdown, flags = evaluate_worker_risk(worker_b)

    # 1. Bounded score validation
    assert 0.0 <= score <= 100.0
    assert 40.0 <= score < 70.0, f"Worker B score should be 40.0-69.9, got {score}"

    # 2. Tier assignment
    assert tier == RiskTier.AT_RISK

    # 3. Downstream Member 4 triggers
    assert "SHARP_INCOME_DECLINE" in flags, "Worker B must trigger SHARP_INCOME_DECLINE"
    assert "DEPLETED_SAVINGS_BUFFER" in flags, "Worker B must trigger DEPLETED_SAVINGS_BUFFER"


def test_worker_c_critical_profile_triggers_critical():
    """Verify Worker C falls into 'Critical' tier (< 40.0) and triggers alerts"""
    worker_c = build_worker_c_dataset()
    score, tier, breakdown, flags = evaluate_worker_risk(worker_c)

    # 1. Bounded score validation
    assert 0.0 <= score <= 100.0
    assert score < 40.0, f"Worker C score should be < 40.0, got {score}"

    # 2. Tier assignment
    assert tier == RiskTier.CRITICAL

    # 3. Downstream Member 4 triggers
    assert "CRITICAL_STABILITY_ALERT" in flags
    assert "PROLONGED_INACTIVITY" in flags
    assert "DEPLETED_SAVINGS_BUFFER" in flags


# =========================================================================
# Phase 5 API Integration & Contract Verification for Workers A, B, C
# =========================================================================

def test_api_pipeline_for_all_worker_personas():
    """
    Sends all 3 worker profiles through the live FastAPI endpoints
    and verifies strict contracts and database persistence.
    """
    for persona_name, worker_input, expected_tier in [
        ("Worker A", build_worker_a_dataset(), "Stable"),
        ("Worker B", build_worker_b_dataset(), "At Risk"),
        ("Worker C", build_worker_c_dataset(), "Critical"),
    ]:
        w_id = str(worker_input.worker_id)
        payload = worker_input.model_dump()
        payload["worker_id"] = w_id
        for record in payload["income_history"]:
            record["date"] = str(record["date"])

        # 1. POST /workers/{id}/calculate
        calc_resp = client.post(f"/workers/{w_id}/calculate", json=payload)
        assert calc_resp.status_code == 201, f"{persona_name} calculation failed: {calc_resp.text}"
        data = calc_resp.json()

        assert data["risk_tier"] == expected_tier
        assert 0.0 <= data["stability_score"] <= 100.0

        # 2. GET /workers/{id}/risk (Member 4 lookup)
        risk_resp = client.get(f"/workers/{w_id}/risk")
        assert risk_resp.status_code == 200
        risk_data = risk_resp.json()

        assert risk_data["risk_tier"] == expected_tier
        if expected_tier == "Critical":
            assert "CRITICAL_STABILITY_ALERT" in risk_data["anomaly_flags"]
        elif expected_tier == "At Risk":
            assert len(risk_data["anomaly_flags"]) > 0
        elif expected_tier == "Stable":
            assert len(risk_data["anomaly_flags"]) == 0
