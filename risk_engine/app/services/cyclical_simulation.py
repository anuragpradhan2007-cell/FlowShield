"""
Cyclical Worker Simulation & Pot Contribution Engine

Implements dynamic economic life-cycles for gig workers:
1. Threshold Comparison: Evaluates daily earnings against a target threshold.
   - If earnings > threshold: Generates surplus, contributes to the protection pot.
   - If earnings <= threshold: Does nothing (0 contribution).
2. Long-term persistence: If surplus or deficit continues for a prolonged period,
   the status updates accordingly.
3. Status Variation & Cycling: Simulates realistic multi-phase economic cycles
   where a worker transitions and cycles between Stable <-> At Risk <-> Critical.
"""

import uuid
from datetime import date, timedelta
from typing import Any, Dict, List, Tuple

from app.schemas.risk_score import DailyIncomeRecord, WorkerDataInput, RiskTier
from app.services.scoring import evaluate_worker_risk


def generate_cyclical_worker_dataset(
    worker_id: uuid.UUID = None,
    threshold: float = 100.0,
    pot_rate: float = 0.20,
    start_date: date = None,
) -> Tuple[WorkerDataInput, List[Dict[str, Any]]]:
    """
    Constructs a 120-day synthetic worker dataset that explicitly cycles through 4 phases:
    - Phase 1 (Days 1-30):   SURPLUS PHASE  -> Earnings $130-$170 > $100 -> Contributes to pot -> STABLE
    - Phase 2 (Days 31-60):  LEAN PERIOD    -> Earnings $50-$80 < $100   -> 0 pot contrib -> AT RISK
    - Phase 3 (Days 61-90):  CRISIS SLUMP   -> Earnings $0-$30 << $100   -> Deep deficit -> CRITICAL
    - Phase 4 (Days 91-120): RECOVERY PHASE -> Earnings $130-$180 > $100 -> Resumes pot contrib -> Cycles back to STABLE
    """
    if worker_id is None:
        worker_id = uuid.uuid4()
    if start_date is None:
        start_date = date(2026, 1, 1)

    records: List[DailyIncomeRecord] = []
    phase_milestones = []

    current_pot = 0.0

    # -------------------------------------------------------------------------
    # Phase 1: Days 1 to 30 — Sustained Surplus (Thriving & Pot Accumulation)
    # -------------------------------------------------------------------------
    phase_milestones.append({
        "phase": 1,
        "name": "Surplus & Growth Phase",
        "day_range": "Days 1 - 30",
        "expected_status": "Stable",
        "description": f"Earnings $130-$170 consistently exceed ${threshold:.2f} threshold, contributing {int(pot_rate*100)}% of surplus to pot.",
    })
    for day_idx in range(30):
        current_dt = start_date + timedelta(days=day_idx)
        # Steady strong earnings
        amount = round(140.0 + (15.0 if day_idx % 2 == 0 else -10.0), 2)
        surplus = max(0.0, round(amount - threshold, 2))
        contrib = round(surplus * pot_rate, 2)
        current_pot += contrib

        records.append(
            DailyIncomeRecord(
                date=str(current_dt),
                amount=amount,
                hours_worked=8.0,
                trips_completed=10,
                threshold=threshold,
                surplus=surplus,
                pot_contribution=contrib,
            )
        )

    # -------------------------------------------------------------------------
    # Phase 2: Days 31 to 60 — Lean Period (Earnings Dip Below Threshold)
    # -------------------------------------------------------------------------
    phase_milestones.append({
        "phase": 2,
        "name": "Lean Period / Deficit Phase",
        "day_range": "Days 31 - 60",
        "expected_status": "At Risk",
        "description": f"Earnings drop to $50-$80 (< ${threshold:.2f}). No surplus -> $0 contributed to pot. Status downgrades to At Risk.",
    })
    for day_idx in range(30, 60):
        current_dt = start_date + timedelta(days=day_idx)
        # Lean earnings below threshold
        amount = round(65.0 + (10.0 if day_idx % 2 == 0 else -15.0), 2)
        records.append(
            DailyIncomeRecord(
                date=str(current_dt),
                amount=amount,
                hours_worked=5.0,
                trips_completed=4,
                threshold=threshold,
                surplus=0.0,
                pot_contribution=0.0,  # Do nothing
            )
        )

    # -------------------------------------------------------------------------
    # Phase 3: Days 61 to 90 — Severe Disruption / Crisis Slump
    # -------------------------------------------------------------------------
    phase_milestones.append({
        "phase": 3,
        "name": "Crisis / Inactivity Phase",
        "day_range": "Days 61 - 90",
        "expected_status": "Critical",
        "description": f"Severe disruption ($0-$25/day earnings). Deficit sustained for 14+ consecutive days. Status updates to Critical.",
    })
    for day_idx in range(60, 90):
        current_dt = start_date + timedelta(days=day_idx)
        # Deep crisis: mostly $0 with rare tiny day
        amount = 20.0 if day_idx % 5 == 0 else 0.0
        records.append(
            DailyIncomeRecord(
                date=str(current_dt),
                amount=amount,
                hours_worked=1.0 if amount > 0 else 0.0,
                trips_completed=1 if amount > 0 else 0,
                threshold=threshold,
                surplus=0.0,
                pot_contribution=0.0,  # Do nothing
                is_missing_data=(amount == 0.0),
            )
        )

    # -------------------------------------------------------------------------
    # Phase 4: Days 91 to 120 — Economic Rebound & Pot Contribution Resumption
    # -------------------------------------------------------------------------
    phase_milestones.append({
        "phase": 4,
        "name": "Recovery & Rebound Phase",
        "day_range": "Days 91 - 120",
        "expected_status": "Stable",
        "description": f"Worker finds new platforms, earnings rebound to $145-$175 > ${threshold:.2f}. Resumes pot contributions -> Status cycles back to Stable.",
    })
    for day_idx in range(90, 120):
        current_dt = start_date + timedelta(days=day_idx)
        # Strong rebound
        amount = round(155.0 + (10.0 if day_idx % 2 == 0 else -15.0), 2)
        surplus = max(0.0, round(amount - threshold, 2))
        contrib = round(surplus * pot_rate, 2)
        current_pot += contrib

        records.append(
            DailyIncomeRecord(
                date=str(current_dt),
                amount=amount,
                hours_worked=8.5,
                trips_completed=11,
                threshold=threshold,
                surplus=surplus,
                pot_contribution=contrib,
            )
        )

    worker_input = WorkerDataInput(
        worker_id=worker_id,
        income_history=records,
        current_savings=500.0,
        weekly_expenses=400.0,
        weather_condition="CLEAR",
        expected_capacity_days=24,
        earning_threshold=threshold,
        pot_contribution_rate=pot_rate,
        community_pot_balance=0.0,
    )

    return worker_input, phase_milestones


def run_cyclical_lifecycle_evaluation(
    threshold: float = 100.0,
    pot_rate: float = 0.20,
) -> Dict[str, Any]:
    """
    Simulates the full 120-day timeline in 30-day snapshot windows to observe
    how the worker's status varies and cycles through all tiers:
    Stable -> At Risk -> Critical -> Stable.
    """
    worker_id = uuid.uuid4()
    worker_input, milestones = generate_cyclical_worker_dataset(
        worker_id=worker_id,
        threshold=threshold,
        pot_rate=pot_rate,
    )

    all_records = worker_input.income_history
    window_evaluations = []

    # Evaluate snapshots at Day 30, Day 60, Day 90, Day 120
    snapshots = [
        (30, "End of Phase 1 (Sustained Surplus)", "CLEAR"),
        (60, "End of Phase 2 (Persistent Deficit)", "MODERATE_RAIN"),
        (90, "End of Phase 3 (Severe Slump)", "SEVERE_ALERT"),
        (120, "End of Phase 4 (Full Recovery)", "CLEAR"),
    ]

    running_pot = 0.0

    for day_count, label, weather in snapshots:
        sub_records = all_records[:day_count]

        # Calculate pot accumulated up to this point
        pot_so_far = sum(r.pot_contribution or 0.0 for r in sub_records)

        snapshot_input = WorkerDataInput(
            worker_id=worker_id,
            income_history=sub_records,
            current_savings=500.0,
            weekly_expenses=400.0,
            weather_condition=weather,
            expected_capacity_days=24,
            earning_threshold=threshold,
            pot_contribution_rate=pot_rate,
            community_pot_balance=pot_so_far,
        )

        score, tier, breakdown, flags = evaluate_worker_risk(snapshot_input)
        pot_summary = breakdown.pot_summary or {}

        window_evaluations.append({
            "day": day_count,
            "label": label,
            "weather": weather,
            "stability_score": score,
            "assigned_tier": tier.value,
            "pot_updated_status": pot_summary.get("updated_status"),
            "current_deficit_streak": pot_summary.get("current_deficit_streak", 0),
            "current_surplus_streak": pot_summary.get("current_surplus_streak", 0),
            "accumulated_pot": pot_summary.get("current_pot_balance", 0.0),
            "total_surplus": pot_summary.get("total_surplus_generated", 0.0),
            "anomaly_flags": flags,
        })

    return {
        "worker_id": str(worker_id),
        "threshold": threshold,
        "pot_contribution_rate": pot_rate,
        "milestones": milestones,
        "snapshot_evaluations": window_evaluations,
    }
