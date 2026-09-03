from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db
import schemas
import models
from auth.dependencies import require_worker
import uuid

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
