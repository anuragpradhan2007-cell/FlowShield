import uuid
from datetime import date, timedelta
import pytest

from app.schemas.risk_score import (
    RiskTier,
    MetricDetail,
    MetricsBreakdown,
    DailyIncomeRecord,
    WorkerDataInput,
)
from app.services.scoring import (
    calculate_composite_stability_score,
    classify_risk_tier,
    detect_anomaly_flags,
    evaluate_worker_risk,
    TIER_STABLE_THRESHOLD,
    TIER_AT_RISK_THRESHOLD,
)


def make_mock_breakdown(
    c_score: float = 100.0,
    f_score: float = 100.0,
    t_score: float = 100.0,
    s_score: float = 100.0,
    e_score: float = 100.0,
) -> MetricsBreakdown:
    return MetricsBreakdown(
        income_consistency=MetricDetail(
            name="Income Consistency",
            weight=0.30,
            normalized_score=c_score,
            tooltip="Consistency tooltip",
        ),
        work_frequency=MetricDetail(
            name="Work Frequency",
            weight=0.25,
            normalized_score=f_score,
            tooltip="Frequency tooltip",
        ),
        recent_income_trend=MetricDetail(
            name="Recent Income Trend",
            weight=0.20,
            normalized_score=t_score,
            tooltip="Trend tooltip",
        ),
        savings_buffer=MetricDetail(
            name="Savings Buffer",
            weight=0.15,
            normalized_score=s_score,
            tooltip="Savings tooltip",
        ),
        external_risk_factors=MetricDetail(
            name="External Risk Factors",
            weight=0.10,
            normalized_score=e_score,
            tooltip="External tooltip",
        ),
    )


# -------------------------------------------------------------------------
# 1. Composite Formula & Weights Verification
# -------------------------------------------------------------------------

def test_composite_stability_score_all_maximum():
    """All 100s produce an exact 100.0 stability score"""
    breakdown = make_mock_breakdown(100.0, 100.0, 100.0, 100.0, 100.0)
    score = calculate_composite_stability_score(breakdown)
    assert score == 100.0


def test_composite_stability_score_all_minimum():
    """All zeros produce an exact 0.0 stability score"""
    breakdown = make_mock_breakdown(0.0, 0.0, 0.0, 0.0, 0.0)
    score = calculate_composite_stability_score(breakdown)
    assert score == 0.0


def test_composite_stability_score_exact_weighting():
    """
    Consistency (30%): 80 -> 24.0
    Frequency (25%): 60 -> 15.0
    Trend (20%): 50 -> 10.0
    Savings (15%): 40 -> 6.0
    External (10%): 20 -> 2.0
    Total = 24.0 + 15.0 + 10.0 + 6.0 + 2.0 = 57.0
    """
    breakdown = make_mock_breakdown(80.0, 60.0, 50.0, 40.0, 20.0)
    score = calculate_composite_stability_score(breakdown)
    assert score == 57.0


# -------------------------------------------------------------------------
# 2. Risk Tier Classification Boundaries
# -------------------------------------------------------------------------

def test_classify_risk_tier_stable():
    assert classify_risk_tier(100.0) == RiskTier.STABLE
    assert classify_risk_tier(85.0) == RiskTier.STABLE
    assert classify_risk_tier(70.0) == RiskTier.STABLE


def test_classify_risk_tier_at_risk():
    assert classify_risk_tier(69.99) == RiskTier.AT_RISK
    assert classify_risk_tier(55.0) == RiskTier.AT_RISK
    assert classify_risk_tier(40.0) == RiskTier.AT_RISK


def test_classify_risk_tier_critical():
    assert classify_risk_tier(39.99) == RiskTier.CRITICAL
    assert classify_risk_tier(20.0) == RiskTier.CRITICAL
    assert classify_risk_tier(0.0) == RiskTier.CRITICAL


# -------------------------------------------------------------------------
# 3. Anomaly Flags for Downstream Protection Engine (Member 4)
# -------------------------------------------------------------------------

def test_anomaly_flags_triggering():
    # Volatile and depleted worker
    breakdown = make_mock_breakdown(
        c_score=25.0,  # < 40 -> HIGH_INCOME_VOLATILITY
        f_score=30.0,  # < 40 -> PROLONGED_INACTIVITY
        t_score=35.0,  # < 50 -> SHARP_INCOME_DECLINE
        s_score=10.0,  # < 30 -> DEPLETED_SAVINGS_BUFFER
        e_score=20.0,  # <= 30 -> SEVERE_EXTERNAL_DISRUPTION
    )
    score = calculate_composite_stability_score(breakdown)
    tier = classify_risk_tier(score)
    flags = detect_anomaly_flags(breakdown, score, tier)

    assert tier == RiskTier.CRITICAL
    assert "CRITICAL_STABILITY_ALERT" in flags
    assert "HIGH_INCOME_VOLATILITY" in flags
    assert "PROLONGED_INACTIVITY" in flags
    assert "SHARP_INCOME_DECLINE" in flags
    assert "DEPLETED_SAVINGS_BUFFER" in flags
    assert "SEVERE_EXTERNAL_DISRUPTION" in flags


# -------------------------------------------------------------------------
# 4. Master Evaluation Pipeline Test
# -------------------------------------------------------------------------

def test_evaluate_worker_risk_pipeline():
    worker_id = uuid.uuid4()
    start_date = date(2026, 1, 1)

    # Steady daily earnings of $140
    records = [
        DailyIncomeRecord(date=str(start_date + timedelta(days=i)), amount=140.0)
        for i in range(30)
    ]

    worker_input = WorkerDataInput(
        worker_id=worker_id,
        income_history=records,
        current_savings=2000.0,
        weekly_expenses=400.0,
        weather_condition="CLEAR",
        expected_capacity_days=24,
    )

    score, tier, breakdown, flags = evaluate_worker_risk(worker_input)

    assert 0.0 <= score <= 100.0
    assert tier == RiskTier.STABLE
    assert score >= 70.0
    assert len(flags) == 0

    # Verify explainability notes are populated for Member 5
    notes = breakdown.explainability_notes
    assert notes is not None
    assert notes["composite_stability_score"] == score
    assert notes["assigned_risk_tier"] == "Stable"
    assert "score_formula" in notes
    assert "tier_explanation" in notes
