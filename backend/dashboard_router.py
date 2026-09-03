from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db
import models
from auth.dependencies import require_worker
from datetime import datetime, timedelta, timezone

router = APIRouter()

@router.get("/worker/me")
def get_worker_dashboard_me(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_worker)
):
    worker_id = current_user.worker.id

    # Fetch worker
    worker = db.query(models.Worker).filter(models.Worker.id == worker_id).first()
    if not worker:
        raise HTTPException(status_code=404, detail="Worker not found")

    # Fetch earnings (mocked computation based on Member 2's goal)
    # Ideally, we would sum the models.Earning records here.
    now = datetime.utcnow()
    one_week_ago = now - timedelta(days=7)
    
    from app.ml.predictor import predict_risk, is_model_available

    earnings = db.query(models.Earning).filter(
        models.Earning.worker_id == worker_id
    ).all()
    
    weekly_income = sum([float(e.amount) for e in earnings if e.period_end >= one_week_ago]) if earnings else 0.0
    
    # Run Inference
    stability_score = 0
    risk_level = "UNKNOWN"
    if is_model_available() and earnings:
        earnings_records = [{"date": e.period_end, "amount": float(e.amount), "is_missing_data": e.is_missing_data} for e in earnings]
        try:
            score, tier, details = predict_risk(earnings_records)
            stability_score = score
            risk_level = tier.value
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"ML Prediction failed: {str(e)}")


    # Calculate real income history
    income_history = []
    # Group earnings by day of week for the past 7 days
    day_map = {0: "Mon", 1: "Tue", 2: "Wed", 3: "Thu", 4: "Fri", 5: "Sat", 6: "Sun"}
    
    # Initialize past 7 days with 0
    history_dict = {}
    for i in range(7):
        d = now - timedelta(days=i)
        history_dict[d.strftime('%Y-%m-%d')] = 0.0

    for e in earnings:
        if e.period_end >= one_week_ago:
            date_str = e.period_end.strftime('%Y-%m-%d')
            if date_str in history_dict:
                history_dict[date_str] += float(e.amount)

    for date_str, amount in reversed(history_dict.items()):
        dt = datetime.strptime(date_str, '%Y-%m-%d')
        income_history.append({"day": day_map[dt.weekday()], "income": amount})

    two_weeks_ago = one_week_ago - timedelta(days=7)
    previous_weekly_income = sum([float(e.amount) for e in earnings if two_weeks_ago <= e.period_end < one_week_ago])
    
    income_change = 0.0
    if previous_weekly_income > 0:
        income_change = ((weekly_income - previous_weekly_income) / previous_weekly_income) * 100

    emergency_pot = db.query(models.EmergencyPot).filter(
        models.EmergencyPot.worker_id == worker_id
    ).first()
    
    emergency_fund = emergency_pot.balance if emergency_pot else 0.0
    emergency_target = round(weekly_income * 0.10, 2)

    return {
        "name": current_user.email.split('@')[0],
        "role": worker.occupation,
        "stabilityScore": stability_score,
        "riskLevel": risk_level,
        "weeklyIncome": weekly_income,
        "incomeChange": round(income_change, 1),
        "emergencyFund": emergency_fund,
        "emergencyTarget": emergency_target,
        "incomeHistory": income_history
    }
