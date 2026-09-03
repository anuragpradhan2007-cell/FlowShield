from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db
import models
from auth.dependencies import require_worker
from app.ml.predictor import predict_risk

router = APIRouter()

@router.get("/{worker_id}/risk")
def get_worker_risk(
    worker_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_worker)
):
    # Enforce cross-worker security
    if current_user.worker.id != worker_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Forbidden: Cannot access another worker's data"
        )
    
    # Query DB for earnings
    # The predictor expects earnings_records with "date", "amount", "is_missing_data"
    earnings = db.query(models.Earning).filter(models.Earning.worker_id == worker_id).all()
    
    # Calculate exact features expected by trained model
    earnings_records = []
    for e in earnings:
        earnings_records.append({
            "date": e.period_end,
            "amount": float(e.amount),
            "is_missing_data": e.is_missing_data
        })
    
    # Run inference
    try:
        stability_score, risk_tier, details = predict_risk(earnings_records)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
    return {
        "stability_score": stability_score,
        "risk_level": risk_tier.value,
        "details": details
    }
