"""
Worker Stability & Risk Scoring Engine - Feature Metrics Engine (Member 3)

Computes the 5 core feature metrics with exact feature weights, standard deviations,
and intermediate statistical breakdowns using Pandas and NumPy.
"""

from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
import pandas as pd

from app.schemas.risk_score import (
    MetricDetail,
    MetricsBreakdown,
    DailyIncomeRecord,
    WorkerDataInput,
)

# Core Feature Weights specified by System Contract
WEIGHT_INCOME_CONSISTENCY = 0.30
WEIGHT_WORK_FREQUENCY = 0.25
WEIGHT_RECENT_TREND = 0.20
WEIGHT_SAVINGS_BUFFER = 0.15
WEIGHT_EXTERNAL_RISK = 0.10


def parse_income_dataframe(income_history: List[DailyIncomeRecord]) -> pd.DataFrame:
    """
    Parses structured income history prepared by Member 2 into a sorted Pandas DataFrame.
    """
    if not income_history:
        return pd.DataFrame(columns=["date", "amount", "hours_worked", "trips_completed"])

    records = []
    for item in income_history:
        record_date = (
            datetime.strptime(item.date, "%Y-%m-%d").date()
            if isinstance(item.date, str)
            else item.date
        )
        records.append({
            "date": record_date,
            "amount": float(item.amount),
            "hours_worked": float(item.hours_worked) if item.hours_worked is not None else 0.0,
            "trips_completed": int(item.trips_completed) if item.trips_completed is not None else 0,
        })

    df = pd.DataFrame(records)
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date").reset_index(drop=True)
    return df


def calculate_income_consistency(
    df: pd.DataFrame,
    weight: float = WEIGHT_INCOME_CONSISTENCY,
) -> MetricDetail:
    """
    Metric 1: Income Consistency (Weight: 30%)
    Goal: Measure how predictable earnings are day-over-day and week-over-week.
    Calculation: Coefficient of variation (CV = Standard Deviation / Mean).
    Normalized to 0-100 scale where lower variance yields higher score.
    """
    if df.empty or len(df) < 2:
        # Edge case: single or zero observations
        amount = float(df["amount"].iloc[0]) if len(df) == 1 else 0.0
        score = 50.0 if amount > 0 else 0.0
        return MetricDetail(
            name="Income Consistency",
            weight=weight,
            raw_value=0.0,
            normalized_score=score,
            mean=amount,
            standard_deviation=0.0,
            intermediate_calculations={
                "mean": amount,
                "standard_deviation": 0.0,
                "coefficient_of_variation": 0.0,
                "sample_size": len(df),
                "note": "Insufficient historical data points (<2) for variance analysis",
            },
            description="Measures earnings predictability via coefficient of variation.",
            tooltip=f"Earnings consistency estimated at {score:.1f}% based on limited history.",
        )

    amounts = df["amount"].to_numpy()
    mean_income = float(np.mean(amounts))
    std_income = float(np.std(amounts, ddof=1))  # Sample standard deviation

    if mean_income <= 0.0:
        cv = 0.0
        normalized_score = 0.0
    else:
        cv = float(std_income / mean_income)
        # Normalization: CV=0 -> 100 (perfect stability); CV >= 1.0 -> 0.0 (extreme volatility)
        normalized_score = max(0.0, min(100.0, 100.0 * (1.0 - cv)))

    normalized_score = round(normalized_score, 2)
    mean_income = round(mean_income, 2)
    std_income = round(std_income, 2)
    cv = round(cv, 4)

    tooltip = (
        f"Earnings consistency is {normalized_score:.1f}%. "
        f"Mean daily income: ${mean_income:.2f} (+/- ${std_income:.2f}, CV: {cv})."
    )

    return MetricDetail(
        name="Income Consistency",
        weight=weight,
        raw_value=cv,
        normalized_score=normalized_score,
        mean=mean_income,
        standard_deviation=std_income,
        intermediate_calculations={
            "mean": mean_income,
            "standard_deviation": std_income,
            "coefficient_of_variation": cv,
            "sample_size": int(len(amounts)),
            "min_income": float(np.min(amounts)),
            "max_income": float(np.max(amounts)),
        },
        description="Predictability of earnings via standard deviation divided by mean.",
        tooltip=tooltip,
    )


def calculate_work_frequency(
    df: pd.DataFrame,
    expected_capacity_days: int = 24,
    window_days: int = 30,
    weight: float = WEIGHT_WORK_FREQUENCY,
) -> MetricDetail:
    """
    Metric 2: Work Frequency (Weight: 25%)
    Goal: Measure how often the user actively earns.
    Calculation: Count active work days over a set time window (past 30 days) vs expected capacity.
    """
    if df.empty:
        return MetricDetail(
            name="Work Frequency",
            weight=weight,
            raw_value=0.0,
            normalized_score=0.0,
            mean=0.0,
            standard_deviation=0.0,
            intermediate_calculations={
                "active_days": 0,
                "window_days": window_days,
                "expected_capacity_days": expected_capacity_days,
                "active_ratio": 0.0,
            },
            description="Active days worked vs monthly capacity.",
            tooltip="No active work days recorded in the past 30 days.",
        )

    # Filter to window
    max_date = df["date"].max()
    window_start = max_date - pd.Timedelta(days=window_days)
    window_df = df[df["date"] >= window_start]

    # Active day = positive earnings
    active_days_count = int((window_df["amount"] > 0).sum())
    active_ratio = float(active_days_count / max(1, expected_capacity_days))
    normalized_score = round(min(100.0, max(0.0, active_ratio * 100.0)), 2)

    tooltip = (
        f"Worked {active_days_count} of {expected_capacity_days} target days "
        f"({normalized_score:.1f}% capacity utilization)."
    )

    return MetricDetail(
        name="Work Frequency",
        weight=weight,
        raw_value=float(active_days_count),
        normalized_score=normalized_score,
        mean=round(float(window_df["amount"].mean()), 2) if not window_df.empty else 0.0,
        standard_deviation=round(float(window_df["amount"].std()), 2) if len(window_df) > 1 else 0.0,
        intermediate_calculations={
            "active_days": active_days_count,
            "window_days": window_days,
            "expected_capacity_days": expected_capacity_days,
            "active_ratio": round(active_ratio, 4),
            "actual_records_in_window": len(window_df),
        },
        description="Active earning days compared to target monthly capacity.",
        tooltip=tooltip,
    )


def calculate_recent_income_trend(
    df: pd.DataFrame,
    recent_window_days: int = 14,
    baseline_window_days: int = 60,
    weight: float = WEIGHT_RECENT_TREND,
) -> MetricDetail:
    """
    Metric 3: Recent Income Trend (Weight: 20%)
    Goal: Detect sudden drops or positive trajectory.
    Calculation: Compare rolling average of the past 7-14 days against the baseline average of past 60 days.
    """
    if df.empty:
        return MetricDetail(
            name="Recent Income Trend",
            weight=weight,
            raw_value=0.0,
            normalized_score=0.0,
            mean=0.0,
            standard_deviation=0.0,
            intermediate_calculations={
                "recent_avg": 0.0,
                "baseline_avg": 0.0,
                "trend_ratio": 0.0,
            },
            description="Recent 14-day rolling average vs 60-day baseline average.",
            tooltip="No earnings history available to calculate income trend.",
        )

    max_date = df["date"].max()

    recent_start = max_date - pd.Timedelta(days=recent_window_days)
    baseline_start = max_date - pd.Timedelta(days=baseline_window_days)

    recent_df = df[df["date"] >= recent_start]
    baseline_df = df[df["date"] >= baseline_start]

    recent_avg = float(recent_df["amount"].mean()) if not recent_df.empty else 0.0
    baseline_avg = float(baseline_df["amount"].mean()) if not baseline_df.empty else 0.0

    recent_std = float(recent_df["amount"].std()) if len(recent_df) > 1 else 0.0
    baseline_std = float(baseline_df["amount"].std()) if len(baseline_df) > 1 else 0.0

    if baseline_avg <= 0.0:
        trend_ratio = 1.0 if recent_avg > 0.0 else 0.0
        normalized_score = 100.0 if recent_avg > 0.0 else 0.0
    else:
        trend_ratio = float(recent_avg / baseline_avg)
        # Cap at 100 for stable or growing; drop scales down proportionally
        normalized_score = min(100.0, max(0.0, trend_ratio * 100.0))

    normalized_score = round(normalized_score, 2)
    recent_avg = round(recent_avg, 2)
    baseline_avg = round(baseline_avg, 2)
    trend_ratio = round(trend_ratio, 4)

    pct_diff = round((trend_ratio - 1.0) * 100.0, 1)
    if pct_diff < 0:
        tooltip = f"Recent income dropped by {abs(pct_diff):.1f}% compared to 60-day baseline (${recent_avg}/day vs ${baseline_avg}/day)."
    else:
        tooltip = f"Recent income is stable/up {pct_diff:+.1f}% vs 60-day baseline (${recent_avg}/day vs ${baseline_avg}/day)."

    return MetricDetail(
        name="Recent Income Trend",
        weight=weight,
        raw_value=trend_ratio,
        normalized_score=normalized_score,
        mean=recent_avg,
        standard_deviation=round(recent_std, 2),
        intermediate_calculations={
            "recent_window_days": recent_window_days,
            "baseline_window_days": baseline_window_days,
            "recent_avg": recent_avg,
            "baseline_avg": baseline_avg,
            "recent_std": round(recent_std, 2),
            "baseline_std": round(baseline_std, 2),
            "trend_ratio": trend_ratio,
            "percentage_change": pct_diff,
        },
        description="Rolling average of past 14 days vs baseline past 60 days.",
        tooltip=tooltip,
    )


def calculate_pot_and_surplus_metrics(
    df: pd.DataFrame,
    threshold: float = 100.0,
    contribution_rate: float = 0.20,
    initial_pot_balance: float = 0.0,
    streak_window: int = 7,
) -> Dict[str, Any]:
    """
    Compares daily earnings against the target benchmark threshold:
    - If daily earning > threshold (surplus):
        surplus = earning - threshold
        pot_contribution = surplus * contribution_rate (contributed to emergency pot)
    - If daily earning <= threshold:
        surplus = 0.0
        pot_contribution = 0.0 (do nothing)

    Long-term status persistence & variation:
    - If surplus continues for a prolonged period (>= streak_window days):
        Updates status toward 'Stable' (Active Pot Contributor).
    - If deficit continues for a prolonged period (>= streak_window days):
        Updates status toward 'At Risk'.
    - If deficit persists over 14+ days or prolonged drop:
        Updates status toward 'Critical'.
    - Cycles dynamically between status tiers as worker earnings fluctuate over time.
    """
    if df.empty:
        return {
            "earning_threshold": threshold,
            "contribution_rate": contribution_rate,
            "total_surplus_generated": 0.0,
            "total_pot_contributions": 0.0,
            "current_pot_balance": round(float(initial_pot_balance), 2),
            "days_evaluated": 0,
            "days_with_surplus": 0,
            "days_with_deficit": 0,
            "current_surplus_streak": 0,
            "current_deficit_streak": 0,
            "max_surplus_streak": 0,
            "max_deficit_streak": 0,
            "updated_status": "Critical",
            "status_reason": "No income records available. Status set to Critical.",
            "status_cycle_history": [],
            "daily_records_summary": [],
        }

    amounts = df["amount"].to_numpy()
    dates = df["date"].tolist()

    total_surplus = 0.0
    total_contributions = 0.0
    accumulated_pot = float(initial_pot_balance)
    days_surplus = 0
    days_deficit = 0

    surplus_streak = 0
    deficit_streak = 0
    max_surplus_streak = 0
    max_deficit_streak = 0

    status = "Stable" if amounts[0] >= threshold else "At Risk"
    cycle_history = []
    daily_summaries = []

    for i, amt in enumerate(amounts):
        day_date = dates[i].strftime("%Y-%m-%d") if hasattr(dates[i], "strftime") else str(dates[i])[:10]
        if amt > threshold:
            surplus = round(float(amt - threshold), 2)
            contrib = round(float(surplus * contribution_rate), 2)
            action = f"Contribute ${contrib:.2f} to Pot"
            days_surplus += 1
            surplus_streak += 1
            deficit_streak = 0
        else:
            surplus = 0.0
            contrib = 0.0
            action = "Do nothing (At or below threshold)"
            days_deficit += 1
            deficit_streak += 1
            surplus_streak = 0

        total_surplus += surplus
        total_contributions += contrib
        accumulated_pot += contrib

        max_surplus_streak = max(max_surplus_streak, surplus_streak)
        max_deficit_streak = max(max_deficit_streak, deficit_streak)

        # Dynamic Status Update & Cycling
        old_status = status
        if surplus_streak >= streak_window:
            status = "Stable"
        elif deficit_streak >= (streak_window * 2):  # 14+ days of sustained deficit
            status = "Critical"
        elif deficit_streak >= streak_window:        # 7-13 days of sustained deficit
            status = "At Risk"

        if status != old_status:
            cycle_history.append({
                "day_index": i + 1,
                "date": day_date,
                "from_status": old_status,
                "to_status": status,
                "trigger": (
                    f"Surplus sustained for {surplus_streak} days"
                    if surplus_streak >= streak_window
                    else f"Deficit sustained for {deficit_streak} days"
                ),
                "pot_balance": round(accumulated_pot, 2),
            })

        daily_summaries.append({
            "day": i + 1,
            "date": day_date,
            "earning": round(float(amt), 2),
            "threshold": threshold,
            "surplus": surplus,
            "pot_contribution": contrib,
            "action": action,
            "accumulated_pot": round(accumulated_pot, 2),
            "status": status,
        })

    # Summary diagnosis
    if deficit_streak >= (streak_window * 2):
        status_reason = f"Deficit has persisted for {deficit_streak} consecutive days below ${threshold:.2f} threshold with $0 pot contributions. Status downgraded to Critical."
    elif deficit_streak >= streak_window:
        status_reason = f"Deficit has persisted for {deficit_streak} consecutive days below ${threshold:.2f} threshold. Status set to At Risk."
    elif surplus_streak >= streak_window:
        status_reason = f"Surplus sustained for {surplus_streak} consecutive days above ${threshold:.2f} threshold (${total_contributions:.2f} contributed to pot). Status elevated to Stable."
    else:
        status_reason = f"Earnings cycle active. Current status: {status} (Surplus streak: {surplus_streak}d, Deficit streak: {deficit_streak}d, Pot balance: ${accumulated_pot:.2f})."

    return {
        "earning_threshold": threshold,
        "contribution_rate": contribution_rate,
        "total_surplus_generated": round(total_surplus, 2),
        "total_pot_contributions": round(total_contributions, 2),
        "current_pot_balance": round(accumulated_pot, 2),
        "days_evaluated": len(amounts),
        "days_with_surplus": days_surplus,
        "days_with_deficit": days_deficit,
        "current_surplus_streak": surplus_streak,
        "current_deficit_streak": deficit_streak,
        "max_surplus_streak": max_surplus_streak,
        "max_deficit_streak": max_deficit_streak,
        "updated_status": status,
        "status_reason": status_reason,
        "status_cycle_history": cycle_history,
        "daily_records_summary": daily_summaries,
    }


def calculate_savings_buffer(
    current_savings: float,
    df: pd.DataFrame,
    weekly_expenses: Optional[float] = None,
    community_pot_balance: float = 0.0,
    target_weeks: float = 4.0,
    weight: float = WEIGHT_SAVINGS_BUFFER,
) -> MetricDetail:
    """
    Metric 4: Savings Buffer (Weight: 15%)
    Goal: Gauge liquidity cushion including personal emergency savings and community pot balance.
    Calculation: Compare total accessible reserves against average weekly expenses.
    Target: 4 weeks of reserves = 100.0 score.
    """
    # Determine weekly burn rate
    if weekly_expenses is not None and weekly_expenses > 0:
        effective_weekly_burn = float(weekly_expenses)
    elif not df.empty and df["amount"].mean() > 0:
        # Estimate: 70% of weekly average income represents regular living expenses
        daily_mean = float(df["amount"].mean())
        effective_weekly_burn = max(50.0, daily_mean * 7.0 * 0.70)
    else:
        effective_weekly_burn = 350.0  # Safe default assumption ($50/day * 7)

    total_accessible_reserves = float(current_savings) + float(community_pot_balance)

    if effective_weekly_burn <= 0:
        weeks_of_buffer = target_weeks
        normalized_score = 100.0
    else:
        weeks_of_buffer = float(total_accessible_reserves / effective_weekly_burn)
        normalized_score = min(100.0, max(0.0, (weeks_of_buffer / target_weeks) * 100.0))

    normalized_score = round(normalized_score, 2)
    weeks_of_buffer = round(weeks_of_buffer, 2)
    effective_weekly_burn = round(effective_weekly_burn, 2)
    current_savings = round(float(current_savings), 2)
    community_pot_balance = round(float(community_pot_balance), 2)

    tooltip = (
        f"Emergency reserve covers {weeks_of_buffer:.1f} weeks of expenses "
        f"(${total_accessible_reserves:.2f} total reserves [${current_savings:.2f} personal + ${community_pot_balance:.2f} pot] "
        f"vs ${effective_weekly_burn:.2f}/week expenses)."
    )

    return MetricDetail(
        name="Savings Buffer",
        weight=weight,
        raw_value=weeks_of_buffer,
        normalized_score=normalized_score,
        mean=None,
        standard_deviation=None,
        intermediate_calculations={
            "current_savings": current_savings,
            "community_pot_balance": community_pot_balance,
            "total_accessible_reserves": round(total_accessible_reserves, 2),
            "effective_weekly_burn": effective_weekly_burn,
            "weeks_of_buffer": weeks_of_buffer,
            "target_weeks": target_weeks,
            "is_expense_estimated": (weekly_expenses is None),
        },
        description="Liquidity cushion measuring weeks of living expenses covered by personal reserves and community pot.",
        tooltip=tooltip,
    )


def calculate_external_risk(
    condition: str = "CLEAR",
    custom_score: Optional[float] = None,
    weight: float = WEIGHT_EXTERNAL_RISK,
) -> MetricDetail:
    """
    Metric 5: External Risk Factors (Weight: 10%)
    Goal: Account for third-party disruptions like adverse weather.
    Calculation: Weather condition severity mapping (Clear = 100, Moderate = 70, Severe = 20)
    or custom external feed score.
    """
    if custom_score is not None:
        normalized_score = round(min(100.0, max(0.0, float(custom_score))), 2)
        condition_used = "CUSTOM_OVERRIDE"
    else:
        condition_norm = condition.strip().upper()
        if condition_norm in ["CLEAR", "SUNNY", "FAVORABLE", "NORMAL"]:
            normalized_score = 100.0
            condition_used = "CLEAR"
        elif condition_norm in ["MODERATE_RAIN", "WINDY", "FOG", "RAIN", "MODERATE"]:
            normalized_score = 70.0
            condition_used = "MODERATE_DISRUPTION"
        elif condition_norm in ["SEVERE_ALERT", "STORM", "HEAVY_FLOOD", "EXTREME", "WARNING", "SEVERE"]:
            normalized_score = 20.0
            condition_used = "SEVERE_WEATHER_ALERT"
        else:
            normalized_score = 100.0
            condition_used = "NORMAL"

    tooltip = f"External risk factor is {normalized_score:.1f}% based on condition: {condition_used}."

    return MetricDetail(
        name="External Risk Factors",
        weight=weight,
        raw_value=normalized_score,
        normalized_score=normalized_score,
        mean=None,
        standard_deviation=None,
        intermediate_calculations={
            "condition_input": condition,
            "condition_resolved": condition_used,
            "raw_score": normalized_score,
            "custom_override_used": custom_score is not None,
        },
        description="External environmental disruptions like adverse weather alerts.",
        tooltip=tooltip,
    )


def extract_worker_metrics(input_data: WorkerDataInput) -> MetricsBreakdown:
    """
    Master pipeline executing all 5 feature calculations for a worker profile.
    Produces an explainability breakdown ready for JSONB logging and Member 5 display.
    """
    df = parse_income_dataframe(input_data.income_history)

    # Calculate threshold, surplus, and community pot metrics
    pot_summary = calculate_pot_and_surplus_metrics(
        df=df,
        threshold=input_data.earning_threshold,
        contribution_rate=input_data.pot_contribution_rate,
        initial_pot_balance=input_data.community_pot_balance,
        streak_window=7,
    )

    m1 = calculate_income_consistency(df, weight=WEIGHT_INCOME_CONSISTENCY)
    m2 = calculate_work_frequency(
        df,
        expected_capacity_days=input_data.expected_capacity_days,
        window_days=30,
        weight=WEIGHT_WORK_FREQUENCY,
    )
    m3 = calculate_recent_income_trend(
        df,
        recent_window_days=14,
        baseline_window_days=60,
        weight=WEIGHT_RECENT_TREND,
    )
    m4 = calculate_savings_buffer(
        current_savings=input_data.current_savings,
        df=df,
        weekly_expenses=input_data.weekly_expenses,
        community_pot_balance=input_data.community_pot_balance,
        target_weeks=4.0,
        weight=WEIGHT_SAVINGS_BUFFER,
    )
    m5 = calculate_external_risk(
        condition=input_data.weather_condition,
        custom_score=input_data.external_risk_override,
        weight=WEIGHT_EXTERNAL_RISK,
    )

    # Positive pot badges
    pot_badges = []
    if pot_summary.get("current_surplus_streak", 0) >= 7:
        pot_badges.append("SUSTAINED_POT_CONTRIBUTOR")
    if pot_summary.get("current_pot_balance", 0.0) > 0 or input_data.community_pot_balance > 0:
        pot_badges.append("POT_PROTECTION_ACTIVE")
    pot_summary["pot_badges"] = pot_badges

    raw_summary = {
        "worker_id": str(input_data.worker_id),
        "total_records_ingested": len(df),
        "current_savings": input_data.current_savings,
        "weekly_expenses": input_data.weekly_expenses,
        "weather_condition": input_data.weather_condition,
        "earning_threshold": input_data.earning_threshold,
        "pot_contribution_rate": input_data.pot_contribution_rate,
        "accumulated_pot_balance": pot_summary["current_pot_balance"],
    }

    # Frontend explainability callouts
    explainability_notes = {
        "summary": "5-Factor stability evaluation completed.",
        "primary_strengths": [
            m.name for m in [m1, m2, m3, m4, m5] if m.normalized_score >= 70.0
        ],
        "vulnerability_areas": [
            m.name for m in [m1, m2, m3, m4, m5] if m.normalized_score < 40.0
        ],
        "pot_status": pot_summary.get("updated_status"),
        "pot_status_reason": pot_summary.get("status_reason"),
        "status_cycle_transitions_count": len(pot_summary.get("status_cycle_history", [])),
        "total_pot_contributions": pot_summary.get("total_pot_contributions", 0.0),
        "current_deficit_streak_days": pot_summary.get("current_deficit_streak", 0),
        "current_surplus_streak_days": pot_summary.get("current_surplus_streak", 0),
        "positive_indicators": pot_badges,
    }

    return MetricsBreakdown(
        income_consistency=m1,
        work_frequency=m2,
        recent_income_trend=m3,
        savings_buffer=m4,
        external_risk_factors=m5,
        pot_summary=pot_summary,
        raw_inputs_summary=raw_summary,
        explainability_notes=explainability_notes,
    )
