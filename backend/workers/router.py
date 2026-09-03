from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db
import schemas
import models
from auth.dependencies import require_worker
import uuid
from pydantic import BaseModel
from datetime import datetime

class EarningCreate(BaseModel):
    amount: float
    period_start: datetime
    period_end: datetime
    is_missing_data: bool = False
    currency: str = "USD"

router = APIRouter()

@router.get("/{worker_id}", response_model=schemas.WorkerResponse)
def read_worker(
    worker_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_worker)
):
    # Retrieve worker from database
    worker = db.query(models.Worker).filter(models.Worker.id == worker_id).first()
    
    if not worker:
        raise HTTPException(status_code=404, detail="Worker not found")
        
    # Authorization logic (Phase 5)
    # A worker can only access their own profile.
    if current_user.worker.id != worker.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Forbidden: Cannot access another worker's profile"
        )
        
    return worker

@router.post("/{worker_id}/earnings")
def create_worker_earning(
    worker_id: str,
    earning: EarningCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_worker)
):
    if current_user.worker.id != worker_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Forbidden: Cannot add data for another worker"
        )
    
    new_earning = models.Earning(
        worker_id=worker_id,
        amount=earning.amount,
        period_start=earning.period_start,
        period_end=earning.period_end,
        is_missing_data=earning.is_missing_data,
        currency=earning.currency
    )
    db.add(new_earning)
    db.commit()
    db.refresh(new_earning)
    
    return new_earning
