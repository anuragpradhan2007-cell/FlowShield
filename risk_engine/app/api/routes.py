import logging
import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.database import get_db
from app.models.risk_score import RiskScore
from app.schemas.risk_score import (
    RiskScoreCreate,
    RiskScoreResponse,
    WorkerRiskSummaryResponse,
    WorkerDataInput,
)
from app.services.scoring import (
    evaluate_worker_risk,
    evaluate_worker_risk_ml,
    detect_anomaly_flags,
)

# Configure structured audit logger for Member 3
logger = logging.getLogger("worker_risk_engine.scoring")
logger.setLevel(logging.INFO)
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] [EXPLAINABILITY] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)

router = APIRouter(prefix="/workers", tags=["Risk Scores"])


@router.post(
    "/{worker_id}/calculate",
    response_model=RiskScoreResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Compute, explain, and store stability score from Member 2 data",
    description=(
        "Ingests structured worker income and transaction history prepared by Member 2. "
        "Supports ML classification (GradientBoosting) or legacy formula scoring. "
        "Bounds the composite score (0-100), assigns a standardized Risk Tier, and persists "
        "the record to the database."
    ),
)
def calculate_and_store_risk_score(
    worker_id: uuid.UUID,
    payload: WorkerDataInput,
    method: str = "ml",
    db: Session = Depends(get_db),
) -> RiskScoreResponse:
    # Ensure URL worker_id matches payload worker_id
    if payload.worker_id != worker_id:
        payload = payload.model_copy(update={"worker_id": worker_id})

    # Execute scoring engine (ML model or formula)
    if method.lower() == "ml":
        stability_score, risk_tier, breakdown, anomaly_flags = evaluate_worker_risk_ml(payload)
    else:
        stability_score, risk_tier, breakdown, anomaly_flags = evaluate_worker_risk(payload)

    # Convert breakdown to dict for JSON/JSONB persistence
    metrics_data = breakdown.model_dump()

    # Create and persist database record
    db_record = RiskScore(
        id=uuid.uuid4(),
        worker_id=worker_id,
        stability_score=stability_score,
        risk_tier=risk_tier,
        metrics_breakdown=metrics_data,
    )
    db.add(db_record)
    db.commit()
    db.refresh(db_record)

    # Detailed Explainability Audit Logging
    c_std = breakdown.income_consistency.standard_deviation if breakdown.income_consistency else 0.0
    c_mean = breakdown.income_consistency.mean if breakdown.income_consistency else 0.0
    logger.info(
        "Worker: %s | Score: %.2f | Tier: %s | Mode: %s | Income Mean: $%.2f | StdDev: $%.2f | Flags: %s",
        worker_id,
        stability_score,
        risk_tier.value,
        method.upper(),
        c_mean,
        c_std,
        anomaly_flags,
    )

    return RiskScoreResponse.model_validate(db_record)


@router.post(
    "/{worker_id}/calculate-ml",
    response_model=RiskScoreResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Compute stability score using trained ML Classifier (GradientBoosting)",
    description=(
        "Explicitly evaluates worker data using the trained GradientBoostingClassifier model. "
        "Calculates class probabilities, learned feature importances, and maps probabilities "
        "to a continuous 0-100 stability score."
    ),
)
def calculate_and_store_risk_score_ml(
    worker_id: uuid.UUID,
    payload: WorkerDataInput,
    db: Session = Depends(get_db),
) -> RiskScoreResponse:
    return calculate_and_store_risk_score(worker_id=worker_id, payload=payload, method="ml", db=db)


@router.post(
    "/scores",
    response_model=RiskScoreResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Directly record a pre-computed risk score",
    description="Stores a pre-computed stability score, risk tier, and explainability breakdown with strict Pydantic contract validation.",
)
def create_risk_score(
    payload: RiskScoreCreate,
    db: Session = Depends(get_db),
) -> RiskScoreResponse:
    metrics_data = (
        payload.metrics_breakdown.model_dump()
        if hasattr(payload.metrics_breakdown, "model_dump")
        else payload.metrics_breakdown
    )

    db_record = RiskScore(
        id=payload.id or uuid.uuid4(),
        worker_id=payload.worker_id,
        stability_score=payload.stability_score,
        risk_tier=payload.risk_tier,
        metrics_breakdown=metrics_data,
    )
    db.add(db_record)
    db.commit()
    db.refresh(db_record)

    logger.info(
        "Direct score logged: Worker: %s | Score: %.2f | Tier: %s",
        payload.worker_id,
        payload.stability_score,
        payload.risk_tier.value,
    )

    return RiskScoreResponse.model_validate(db_record)


@router.get(
    "/{worker_id}/stability-score",
    response_model=RiskScoreResponse,
    summary="Fetch latest stability score and explainability breakdown",
    description=(
        "Returns the most recent stability score, risk tier, and intermediate metric details "
        "for a given worker. Includes formula logs and tooltips for Member 5 frontend display."
    ),
)
def get_latest_stability_score(
    worker_id: uuid.UUID,
    db: Session = Depends(get_db),
) -> RiskScoreResponse:
    record = (
        db.query(RiskScore)
        .filter(RiskScore.worker_id == worker_id)
        .order_by(desc(RiskScore.created_at))
        .first()
    )
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No risk score records found for worker ID: {worker_id}",
        )
    return RiskScoreResponse.model_validate(record)


@router.get(
    "/{worker_id}/risk",
    response_model=WorkerRiskSummaryResponse,
    summary="Quick risk status lookup for Member 4 (Protection Engine)",
    description=(
        "Provides a low-latency lookup of current risk tier, stability score, and anomaly flags "
        "to trigger protection policies without parsing full telemetry."
    ),
)
def get_worker_risk_status(
    worker_id: uuid.UUID,
    db: Session = Depends(get_db),
) -> WorkerRiskSummaryResponse:
    record = (
        db.query(RiskScore)
        .filter(RiskScore.worker_id == worker_id)
        .order_by(desc(RiskScore.created_at))
        .first()
    )
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No risk score records found for worker ID: {worker_id}",
        )

    # Extract stored anomaly flags or evaluate deterministically
    breakdown_data = record.metrics_breakdown or {}
    anomaly_flags = []

    notes = breakdown_data.get("explainability_notes") if isinstance(breakdown_data, dict) else {}
    if isinstance(notes, dict) and "anomaly_flags_triggered" in notes:
        anomaly_flags = notes["anomaly_flags_triggered"]
    else:
        # Fallback evaluation
        if record.stability_score < 40.0:
            anomaly_flags.append("CRITICAL_STABILITY_ALERT")
        if isinstance(breakdown_data, dict):
            trend = breakdown_data.get("recent_income_trend") or {}
            if isinstance(trend, dict) and trend.get("normalized_score", 100) < 50.0:
                anomaly_flags.append("SHARP_INCOME_DECLINE")
            savings = breakdown_data.get("savings_buffer") or {}
            if isinstance(savings, dict) and savings.get("normalized_score", 100) < 30.0:
                anomaly_flags.append("DEPLETED_SAVINGS_BUFFER")
            cons = breakdown_data.get("income_consistency") or {}
            if isinstance(cons, dict) and cons.get("normalized_score", 100) < 40.0:
                anomaly_flags.append("HIGH_INCOME_VOLATILITY")

    return WorkerRiskSummaryResponse(
        worker_id=record.worker_id,
        stability_score=record.stability_score,
        risk_tier=record.risk_tier,
        anomaly_flags=anomaly_flags,
        last_calculated_at=record.created_at,
    )


@router.get(
    "/{worker_id}/history",
    response_model=List[RiskScoreResponse],
    summary="Fetch worker risk score historical trajectory",
    description="Returns chronological audit history of risk score evaluations for this worker.",
)
def get_worker_score_history(
    worker_id: uuid.UUID,
    limit: int = 10,
    db: Session = Depends(get_db),
) -> List[RiskScoreResponse]:
    records = (
        db.query(RiskScore)
        .filter(RiskScore.worker_id == worker_id)
        .order_by(desc(RiskScore.created_at))
        .limit(limit)
        .all()
    )
    return [RiskScoreResponse.model_validate(r) for r in records]
