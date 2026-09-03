"""
Worker Stability & Risk Scoring Engine - Composite Scoring & Classification (Member 3)

Calculates the weighted composite Stability Score, maps to standardized Risk Tiers,
and generates anomaly triggers for Member 4 (Protection Engine) and Member 5 (Frontend).
"""

from typing import List, Tuple
from app.schemas.risk_score import (
    RiskTier,
    MetricsBreakdown,
    WorkerDataInput,
)
from app.services.metrics import (
    extract_worker_metrics,
    WEIGHT_INCOME_CONSISTENCY,
    WEIGHT_WORK_FREQUENCY,
    WEIGHT_RECENT_TREND,
    WEIGHT_SAVINGS_BUFFER,
    WEIGHT_EXTERNAL_RISK,
)

# Standardized Tier Boundaries
TIER_STABLE_THRESHOLD = 70.0
TIER_AT_RISK_THRESHOLD = 40.0


def calculate_composite_stability_score(breakdown: MetricsBreakdown) -> float:
    """
    Computes the composite Stability Score using the standardized weighted formula:
    Stability Score = (0.30 * Consistency) + (0.25 * Frequency) + 
                      (0.20 * Trend) + (0.15 * Savings) + (0.10 * External)
    
    Guarantees the output is strictly bounded between 0.0 and 100.0.
    """
    c_score = breakdown.income_consistency.normalized_score if breakdown.income_consistency else 0.0
    f_score = breakdown.work_frequency.normalized_score if breakdown.work_frequency else 0.0
    t_score = breakdown.recent_income_trend.normalized_score if breakdown.recent_income_trend else 0.0
    s_score = breakdown.savings_buffer.normalized_score if breakdown.savings_buffer else 0.0
    e_score = breakdown.external_risk_factors.normalized_score if breakdown.external_risk_factors else 0.0

    raw_composite = (
        (WEIGHT_INCOME_CONSISTENCY * c_score) +
        (WEIGHT_WORK_FREQUENCY * f_score) +
        (WEIGHT_RECENT_TREND * t_score) +
        (WEIGHT_SAVINGS_BUFFER * s_score) +
        (WEIGHT_EXTERNAL_RISK * e_score)
    )

    # Strictly bound between 0.0 and 100.0 and round to 2 decimal places
    bounded_score = max(0.0, min(100.0, float(raw_composite)))
    return round(bounded_score, 2)


def classify_risk_tier(score: float) -> RiskTier:
    """
    Maps a bounded stability score float (0.0 to 100.0) to standardized Enum tiers:
      - 70.0 to 100.0 -> 'Stable'
      - 40.0 to 69.99 -> 'At Risk'
      - 0.0 to 39.99  -> 'Critical'
    """
    if score >= TIER_STABLE_THRESHOLD:
        return RiskTier.STABLE
    elif score >= TIER_AT_RISK_THRESHOLD:
        return RiskTier.AT_RISK
    else:
        return RiskTier.CRITICAL


def detect_anomaly_flags(
    breakdown: MetricsBreakdown,
    stability_score: float,
    risk_tier: RiskTier,
) -> List[str]:
    """
    Generates deterministic anomaly flags for downstream engines (Member 4 Protection Engine).
    Identifies specific failure modes and vulnerability indicators.
    """
    flags: List[str] = []

    # Overall score triggers
    if risk_tier == RiskTier.CRITICAL:
        flags.append("CRITICAL_STABILITY_ALERT")

    # Sub-metric triggers
    if breakdown.income_consistency and breakdown.income_consistency.normalized_score < 40.0:
        flags.append("HIGH_INCOME_VOLATILITY")

    if breakdown.work_frequency and breakdown.work_frequency.normalized_score < 40.0:
        flags.append("PROLONGED_INACTIVITY")

    if breakdown.recent_income_trend and breakdown.recent_income_trend.normalized_score < 50.0:
        flags.append("SHARP_INCOME_DECLINE")

    if breakdown.savings_buffer and breakdown.savings_buffer.normalized_score < 30.0:
        flags.append("DEPLETED_SAVINGS_BUFFER")

    if breakdown.external_risk_factors and breakdown.external_risk_factors.normalized_score <= 30.0:
        flags.append("SEVERE_EXTERNAL_DISRUPTION")

    # Threshold comparison & Pot vulnerability triggers
    if breakdown.pot_summary:
        pot = breakdown.pot_summary
        def_streak = pot.get("current_deficit_streak", 0)

        if def_streak >= 14:
            flags.append("PERSISTENT_DEFICIT_NO_CONTRIBUTION")
        elif def_streak >= 7:
            flags.append("PROLONGED_EARNINGS_DEFICIT")

    return flags


def evaluate_worker_risk(
    input_data: WorkerDataInput,
) -> Tuple[float, RiskTier, MetricsBreakdown, List[str]]:
    """
    Master end-to-end evaluation pipeline for a worker:
    1. Extracts and calculates all 5 feature metrics with variance tracking.
    2. Evaluates daily earnings against threshold, computes surplus/pot contributions,
       and updates status if surplus or deficit persists over time.
    3. Calculates the bounded composite Stability Score.
    4. Classifies the worker into a standardized RiskTier.
    5. Detects downstream anomaly trigger flags for Member 4.
    6. Injects composite summary into explainability notes for Member 5 frontend tooltips.
    """
    # 1. Feature extraction & Pot simulation
    breakdown = extract_worker_metrics(input_data)

    # 2. Composite score calculation
    stability_score = calculate_composite_stability_score(breakdown)

    # 3. Risk tier classification
    risk_tier = classify_risk_tier(stability_score)

    # Long-term status update if deficit has persisted for 14+ days
    if breakdown.pot_summary:
        pot = breakdown.pot_summary
        if pot.get("current_deficit_streak", 0) >= 14 and risk_tier == RiskTier.STABLE:
            risk_tier = RiskTier.AT_RISK

    # 4. Anomaly flags for Member 4
    anomaly_flags = detect_anomaly_flags(breakdown, stability_score, risk_tier)

    # 5. Enrich explainability notes for Member 5 frontend
    if breakdown.explainability_notes is None:
        breakdown.explainability_notes = {}

    pot_info = breakdown.pot_summary or {}
    breakdown.explainability_notes.update({
        "composite_stability_score": stability_score,
        "assigned_risk_tier": risk_tier.value,
        "pot_evaluated_status": pot_info.get("updated_status"),
        "pot_status_reason": pot_info.get("status_reason"),
        "total_pot_accumulated": pot_info.get("current_pot_balance", 0.0),
        "total_surplus_generated": pot_info.get("total_surplus_generated", 0.0),
        "status_cycle_history": pot_info.get("status_cycle_history", []),
        "anomaly_flags_triggered": anomaly_flags,
        "score_formula": (
            f"Stability Score = (0.30 * {breakdown.income_consistency.normalized_score:.1f}) + "
            f"(0.25 * {breakdown.work_frequency.normalized_score:.1f}) + "
            f"(0.20 * {breakdown.recent_income_trend.normalized_score:.1f}) + "
            f"(0.15 * {breakdown.savings_buffer.normalized_score:.1f}) + "
            f"(0.10 * {breakdown.external_risk_factors.normalized_score:.1f}) = {stability_score:.2f}"
        ),
        "tier_explanation": (
            f"Worker classified as '{risk_tier.value}' because the stability score of "
            f"{stability_score:.1f} falls in the range "
            f"{'[70.0, 100.0]' if risk_tier == RiskTier.STABLE else ('[40.0, 69.9]' if risk_tier == RiskTier.AT_RISK else '[0.0, 39.9]') }."
        ),
    })

    return stability_score, risk_tier, breakdown, anomaly_flags


def evaluate_worker_risk_ml(
    input_data: WorkerDataInput,
) -> Tuple[float, RiskTier, MetricsBreakdown, List[str]]:
    """
    ML-Driven end-to-end evaluation pipeline for a worker:
    1. Extracts feature metrics for downstream frontend tooltips and telemetry.
    2. Runs the trained GradientBoostingClassifier to predict risk tier and stability score.
    3. Detects downstream anomaly trigger flags for Member 4.
    4. Populates detailed ML explainability notes (probabilities, learned feature weights).
    """
    from app.ml.predictor import predict_risk, is_model_available

    # Fallback to formula if ML model is unavailable
    if not is_model_available():
        return evaluate_worker_risk(input_data)

    # 1. Standard feature metrics for Member 5 frontend tooltips
    breakdown = extract_worker_metrics(input_data)

    # 2. Format records for ML predictor
    records = []
    for r in input_data.income_history:
        amt = float(r.amount)
        is_missing = getattr(r, "is_missing_data", False)
        is_missing = bool(is_missing) or (amt == 0.0)
        records.append({
            "date": r.date,
            "amount": amt,
            "is_missing_data": is_missing,
        })

    # 3. ML Model prediction
    stability_score, risk_tier, ml_details = predict_risk(records)

    # 4. Anomaly flags for Member 4
    anomaly_flags = detect_anomaly_flags(breakdown, stability_score, risk_tier)

    # 5. Enrich explainability notes with ML metrics
    if breakdown.explainability_notes is None:
        breakdown.explainability_notes = {}

    probabilities = ml_details.get("class_probabilities", {})
    breakdown.explainability_notes.update({
        "scoring_mode": "Machine Learning (GradientBoostingClassifier)",
        "composite_stability_score": stability_score,
        "assigned_risk_tier": risk_tier.value,
        "anomaly_flags_triggered": anomaly_flags,
        "ml_details": ml_details,
        "score_formula": (
            f"ML Classifier Confidence: [Stable: {probabilities.get('Stable', 0.0):.1%}, "
            f"At Risk: {probabilities.get('At Risk', 0.0):.1%}, "
            f"Critical: {probabilities.get('Critical', 0.0):.1%}] "
            f"-> Stability Score = {stability_score:.2f}"
        ),
        "tier_explanation": (
            f"Worker classified as '{risk_tier.value}' by trained ML model with "
            f"{probabilities.get(risk_tier.value, 0.0):.1%} prediction confidence."
        ),
    })

    return stability_score, risk_tier, breakdown, anomaly_flags
