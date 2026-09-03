"""
Unit Tests for Earning Threshold Comparison, Pot Contributions & Status Cycling

Validates:
1. Daily earning vs threshold comparison (surplus contributes to pot; deficit does nothing).
2. Long-term condition persistence updating status (Stable -> At Risk -> Critical).
3. Dynamic lifecycle simulation showing status varying and cycling back to Stable.
"""

import uuid
from datetime import date, timedelta
import pytest
import pandas as pd

from app.schemas.risk_score import DailyIncomeRecord, WorkerDataInput, RiskTier
from app.services.metrics import calculate_pot_and_surplus_metrics, extract_worker_metrics
from app.services.scoring import evaluate_worker_risk
from app.services.cyclical_simulation import (
    generate_cyclical_worker_dataset,
    run_cyclical_lifecycle_evaluation,
)


def test_threshold_comparison_surplus_and_deficit():
    """
    Test daily earning threshold comparison:
    - Days above threshold contribute to the pot.
    - Days at or below threshold do nothing (0 contribution).
    """
    threshold = 100.0
    rate = 0.20

    records = [
        {"date": date(2026, 1, 1), "amount": 150.0},  # Surplus = 50, Contrib = 10
        {"date": date(2026, 1, 2), "amount": 100.0},  # Exactly at threshold -> Surplus = 0, Contrib = 0 (Do nothing)
        {"date": date(2026, 1, 3), "amount": 80.0},   # Deficit -> Surplus = 0, Contrib = 0 (Do nothing)
        {"date": date(2026, 1, 4), "amount": 200.0},  # Surplus = 100, Contrib = 20
        {"date": date(2026, 1, 5), "amount": 0.0},    # Complete zero -> Contrib = 0 (Do nothing)
    ]
    df = pd.DataFrame(records)

    pot_metrics = calculate_pot_and_surplus_metrics(
        df=df,
        threshold=threshold,
        contribution_rate=rate,
        initial_pot_balance=0.0,
        streak_window=3,
    )

    assert pot_metrics["days_evaluated"] == 5
    assert pot_metrics["days_with_surplus"] == 2
    assert pot_metrics["days_with_deficit"] == 3
    assert pot_metrics["total_surplus_generated"] == 150.0  # 50 + 100
    assert pot_metrics["total_pot_contributions"] == 30.0   # 10 + 20
    assert pot_metrics["current_pot_balance"] == 30.0

    # Verify per-day actions
    summaries = pot_metrics["daily_records_summary"]
    assert summaries[0]["action"] == "Contribute $10.00 to Pot"
    assert summaries[1]["action"] == "Do nothing (At or below threshold)"
    assert summaries[2]["action"] == "Do nothing (At or below threshold)"
    assert summaries[3]["action"] == "Contribute $20.00 to Pot"
    assert summaries[4]["action"] == "Do nothing (At or below threshold)"


def test_long_term_deficit_updates_status_to_critical():
    """
    If deficit continues for 14+ consecutive days, verify status updates to Critical
    and triggers PERSISTENT_DEFICIT_NO_CONTRIBUTION.
    """
    threshold = 100.0
    start = date(2026, 1, 1)

    # 15 consecutive days below threshold
    records = [
        DailyIncomeRecord(date=str(start + timedelta(days=i)), amount=40.0)
        for i in range(15)
    ]

    worker_input = WorkerDataInput(
        worker_id=uuid.uuid4(),
        income_history=records,
        current_savings=100.0,
        weekly_expenses=400.0,
        earning_threshold=threshold,
    )

    score, tier, breakdown, flags = evaluate_worker_risk(worker_input)

    pot_summary = breakdown.pot_summary
    assert pot_summary["current_deficit_streak"] == 15
    assert pot_summary["total_pot_contributions"] == 0.0  # Did nothing for all 15 days
    assert pot_summary["updated_status"] == "Critical"
    assert "PERSISTENT_DEFICIT_NO_CONTRIBUTION" in flags


def test_long_term_surplus_updates_status_to_stable():
    """
    If surplus continues for a prolonged period, verify status updates to Stable
    and records positive contributor badges.
    """
    threshold = 100.0
    start = date(2026, 1, 1)

    # 14 consecutive days with earnings of $150
    records = [
        DailyIncomeRecord(date=str(start + timedelta(days=i)), amount=150.0)
        for i in range(14)
    ]

    worker_input = WorkerDataInput(
        worker_id=uuid.uuid4(),
        income_history=records,
        current_savings=1500.0,
        weekly_expenses=400.0,
        earning_threshold=threshold,
        pot_contribution_rate=0.20,
    )

    score, tier, breakdown, flags = evaluate_worker_risk(worker_input)

    pot_summary = breakdown.pot_summary
    assert pot_summary["current_surplus_streak"] == 14
    assert pot_summary["total_surplus_generated"] == 14 * 50.0  # $700 surplus
    assert pot_summary["total_pot_contributions"] == 14 * 10.0  # $140 pot contribution
    assert pot_summary["updated_status"] == "Stable"
    assert "SUSTAINED_POT_CONTRIBUTOR" in pot_summary["pot_badges"]
    assert "POT_PROTECTION_ACTIVE" in pot_summary["pot_badges"]
    assert tier == RiskTier.STABLE


def test_status_varying_and_cycling_across_phases():
    """
    Simulates a worker moving through 4 realistic phases:
    Phase 1 (Surplus) -> Phase 2 (Lean) -> Phase 3 (Crisis) -> Phase 4 (Recovery).
    Confirms status varying and cycling between Stable -> At Risk -> Critical -> Stable.
    """
    sim_results = run_cyclical_lifecycle_evaluation(threshold=100.0, pot_rate=0.20)
    snapshots = sim_results["snapshot_evaluations"]

    assert len(snapshots) == 4

    # Phase 1: End of Day 30 -> Sustained surplus, contributing to pot -> Stable
    snap_1 = snapshots[0]
    assert snap_1["day"] == 30
    assert snap_1["assigned_tier"] == "Stable"
    assert snap_1["accumulated_pot"] > 0.0

    # Phase 2: End of Day 60 -> Earnings below threshold for 30 days -> At Risk
    snap_2 = snapshots[1]
    assert snap_2["day"] == 60
    assert snap_2["assigned_tier"] == "At Risk"
    assert snap_2["current_deficit_streak"] >= 14

    # Phase 3: End of Day 90 -> Severe slump and zero income -> Critical
    snap_3 = snapshots[2]
    assert snap_3["day"] == 90
    assert snap_3["assigned_tier"] == "Critical"
    assert "CRITICAL_STABILITY_ALERT" in snap_3["anomaly_flags"]

    # Phase 4: End of Day 120 -> Rebound, surplus resumed, pot grows -> Cycles back to Stable!
    snap_4 = snapshots[3]
    assert snap_4["day"] == 120
    assert snap_4["assigned_tier"] == "Stable"
    assert snap_4["current_surplus_streak"] >= 14
    assert snap_4["accumulated_pot"] > snap_1["accumulated_pot"]
