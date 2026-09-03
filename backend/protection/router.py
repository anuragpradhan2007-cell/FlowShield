from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db
import models
from auth.dependencies import require_worker
from datetime import datetime, timedelta
from app.ml.predictor import predict_risk, is_model_available

router = APIRouter()

def calculate_worker_contribution(db: Session, worker_id: str):
    now = datetime.utcnow()
    one_week_ago = now - timedelta(days=7)
    
    earnings = db.query(models.Earning).filter(
        models.Earning.worker_id == worker_id,
        models.Earning.period_end >= one_week_ago
    ).all()
    
    if not earnings:
        return 0.0
        
    total_earnings = sum([float(e.amount) for e in earnings])
    return total_earnings * 0.10

def get_real_risk(db: Session, worker_id: str):
    earnings = db.query(models.Earning).filter(
        models.Earning.worker_id == worker_id
    ).all()
    
    if is_model_available() and earnings:
        earnings_records = [{"date": e.period_end, "amount": float(e.amount), "is_missing_data": e.is_missing_data} for e in earnings]
        try:
            score, tier, details = predict_risk(earnings_records)
            return {"stability_score": score, "risk_tier": tier.value}
        except Exception as e:
            return None
    return None

@router.post("/emergency-pot/auto-contribute")
def auto_contribute(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_worker)
):
    worker_id = current_user.worker.id
    contribution = calculate_worker_contribution(db, worker_id)

    if contribution <= 0:
        return {"message": "No recent earnings to contribute from"}

    pot = db.query(models.EmergencyPot).filter(
        models.EmergencyPot.worker_id == worker_id
    ).first()

    if pot is None:
        pot = models.EmergencyPot(
            worker_id=worker_id,
            balance=0.0,
            total_contributed=0.0,
            total_used=0.0
        )
        db.add(pot)

    total_target = round(contribution, 2)
    new_contribution = total_target - pot.total_contributed
    
    if new_contribution < 0:
        new_contribution = 0.0

    new_contribution = round(new_contribution, 2)
    
    pot.balance += new_contribution
    pot.total_contributed += new_contribution

    db.commit()
    db.refresh(pot)

    return {
        "contribution": new_contribution,
        "emergency_pot_balance": pot.balance,
        "message": "Emergency Pot automatically updated from real earnings."
    }

@router.post("/emergency-pot/release")
def release_emergency_funds(
    requested_amount: float,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_worker)
):
    worker_id = current_user.worker.id
    
    pot = db.query(models.EmergencyPot).filter(
        models.EmergencyPot.worker_id == worker_id
    ).first()

    if pot is None or pot.balance <= 0:
        raise HTTPException(status_code=400, detail="Insufficient Emergency Pot funds")

    risk_data = get_real_risk(db, worker_id)
    if risk_data is None:
        raise HTTPException(status_code=500, detail="Risk prediction unavailable")

    risk_tier = risk_data["risk_tier"]
    
    # Financial Protection Rule: Only Critical Risk gets release
    if risk_tier != "Critical":
        return {
            "emergency_support": False,
            "release_amount": 0,
            "reason": "Worker is not in Critical risk."
        }
        
    release_amount = min(pot.balance, requested_amount)
    if release_amount <= 0:
        raise HTTPException(status_code=400, detail="Requested amount must be greater than zero")

    pot.balance -= release_amount
    pot.total_used += release_amount

    notification = models.Notification(
        worker_id=worker_id,
        type="EMERGENCY_SUPPORT",
        message=f"Emergency support of {release_amount} has been approved."
    )
    db.add(notification)
    db.commit()
    db.refresh(pot)

    return {
        "emergency_support": True,
        "release_amount": release_amount,
        "remaining_balance": pot.balance,
        "total_used": pot.total_used,
        "reason": "Critical financial risk detected. Emergency funds released."
    }

@router.get("/credit-eligibility")
def get_credit_eligibility(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_worker)
):
    worker_id = current_user.worker.id
    risk_data = get_real_risk(db, worker_id)
    
    if risk_data is None:
        raise HTTPException(status_code=500, detail="Risk prediction unavailable")

    stability_score = risk_data["stability_score"]
    risk_tier = risk_data["risk_tier"]

    if stability_score >= 70:
        eligible = True
        credit_limit = 5000
        reason = "Worker has a stable financial profile."
    elif stability_score >= 40:
        eligible = True
        credit_limit = 2500
        reason = "Worker is at risk but may qualify for limited credit."
    else:
        eligible = False
        credit_limit = 0
        reason = "Worker has critical financial risk."

    assessment = models.CreditAssessment(
        worker_id=worker_id,
        stability_score=stability_score,
        risk_level=risk_tier,
        eligible=eligible,
        credit_limit=credit_limit,
        reason=reason
    )

    db.add(assessment)
    db.commit()
    db.refresh(assessment)

    return {
        "stability_score": stability_score,
        "risk_tier": risk_tier,
        "eligible": eligible,
        "credit_limit": credit_limit,
        "reason": reason
    }
