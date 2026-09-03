from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db
import models
from auth.dependencies import require_worker
from datetime import datetime, timedelta, timezone

router = APIRouter()

@router.get("/worker/{worker_id}")
def get_worker_dashboard(
    worker_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_worker)
):
    # Authorization
    if current_user.worker.id != worker_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Forbidden: Cannot access another worker's dashboard"
        )

    # Fetch worker
    worker = db.query(models.Worker).filter(models.Worker.id == worker_id).first()
    if not worker:
        raise HTTPException(status_code=404, detail="Worker not found")

    # Fetch earnings (mocked computation based on Member 2's goal)
    # Ideally, we would sum the models.Earning records here.
    now = datetime.now(timezone.utc)
    one_week_ago = now - timedelta(days=7)
    
    earnings = db.query(models.Earning).filter(
        models.Earning.worker_id == worker_id,
        models.Earning.period_end >= one_week_ago
    ).all()
    
    weekly_income = sum([e.amount for e in earnings]) if earnings else 4200.0
    
    # Format the data exactly as the frontend expects
    return {
        "name": "Delivery Partner", # Default mock name if no profile name
        "role": worker.occupation,
        "stabilityScore": 78, # Hardcoded for now (Member 3 AI Engine task)
        "weeklyIncome": weekly_income,
        "incomeChange": 12.5,
        "emergencyFund": 1500,
        "emergencyTarget": 5000,
        "incomeHistory": [
            {"day": "Mon", "income": 500},
            {"day": "Tue", "income": 650},
            {"day": "Wed", "income": 400},
            {"day": "Thu", "income": 800},
            {"day": "Fri", "income": 750},
            {"day": "Sat", "income": 900},
            {"day": "Sun", "income": 200},
        ]
    }
