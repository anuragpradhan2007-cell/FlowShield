from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db
import models
from auth.dependencies import require_worker
from datetime import datetime, timedelta
from app.ml.predictor import predict_risk, is_model_available
from sqlalchemy.exc import IntegrityError
from decimal import Decimal

router = APIRouter()

def calculate_worker_contribution(db: Session, worker_id: str, period_start: datetime):
    earnings = db.query(models.Earning).filter(
        models.Earning.worker_id == worker_id,
        models.Earning.period_end >= period_start
    ).all()
    
    if not earnings:
        return Decimal("0.00")
        
    total_earnings = sum([Decimal(str(e.amount)) for e in earnings])
    return total_earnings * Decimal("0.10")

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
    try:
        pot = db.query(models.EmergencyPot).filter(
            models.EmergencyPot.worker_id == worker_id
        ).with_for_update().first()
        
        if pot is None:
            pot = models.EmergencyPot(
                worker_id=worker_id,
                balance=Decimal("0.00"),
                total_contributed=Decimal("0.00"),
                total_used=Decimal("0.00"),
                period_contributed=Decimal("0.00"),
                period_start=datetime.utcnow() - timedelta(days=7)
            )
            db.add(pot)
            db.flush()
    except IntegrityError:
        db.rollback()
        pot = db.query(models.EmergencyPot).filter(
            models.EmergencyPot.worker_id == worker_id
        ).with_for_update().first()

    period_boundary = datetime.utcnow() - timedelta(days=7)
    if pot.period_start < period_boundary:
        pot.period_contributed = Decimal("0.00")
        pot.period_start = period_boundary

    contribution = calculate_worker_contribution(db, worker_id, pot.period_start)

    if contribution <= 0:
        return {"message": "No recent earnings to contribute from"}

    total_target = contribution.quantize(Decimal("0.01"))
    new_contribution = total_target - Decimal(str(pot.period_contributed))
    
    if new_contribution < Decimal("0.00"):
        new_contribution = Decimal("0.00")

    pot.balance = Decimal(str(pot.balance)) + new_contribution
    pot.total_contributed = Decimal(str(pot.total_contributed)) + new_contribution
    pot.period_contributed = Decimal(str(pot.period_contributed)) + new_contribution

    db.commit()
    db.refresh(pot)

    return {
        "contribution": new_contribution,
        "emergency_pot_balance": pot.balance,
        "message": "Emergency Pot automatically updated from real earnings."
    }

@router.post("/emergency-pot/release")
def release_emergency_funds(
    requested_amount: Decimal,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_worker)
):
    if requested_amount.as_tuple().exponent < -2:
        raise HTTPException(status_code=400, detail="Requested amount exceeds two decimal precision")

    worker_id = current_user.worker.id
    
    pot = db.query(models.EmergencyPot).filter(
        models.EmergencyPot.worker_id == worker_id
    ).with_for_update().first()

    if pot is None or Decimal(str(pot.balance)) <= 0:
        raise HTTPException(status_code=400, detail="Insufficient Emergency Pot funds")

    risk_data = get_real_risk(db, worker_id)
    if risk_data is None:
        raise HTTPException(status_code=500, detail="Risk prediction unavailable")

    risk_tier = risk_data["risk_tier"]
    
    if risk_tier != "Critical":
        return {
            "emergency_support": False,
            "release_amount": Decimal("0.00"),
            "reason": "Worker is not in Critical risk."
        }
        
    release_amount = min(Decimal(str(pot.balance)), requested_amount)
    if release_amount <= 0:
        raise HTTPException(status_code=400, detail="Requested amount must be greater than zero")

    pot.balance = Decimal(str(pot.balance)) - release_amount
    pot.total_used = Decimal(str(pot.total_used)) + release_amount

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
