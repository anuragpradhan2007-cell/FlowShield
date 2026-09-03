from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db
import schemas
import models
from auth.security import get_password_hash, verify_password, create_access_token

router = APIRouter()

@router.post("/register", response_model=schemas.UserProfileResponse)
def register(user_in: schemas.UserCreate, db: Session = Depends(get_db)):
    existing_user = db.query(models.User).filter(models.User.email == user_in.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered"
        )
    
    # Create user
    db_user = models.User(
        email=user_in.email,
        password_hash=get_password_hash(user_in.password),
        role="WORKER"
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    # Create associated worker profile
    db_worker = models.Worker(
        user_id=db_user.id,
        occupation=user_in.occupation
    )
    db.add(db_worker)
    db.commit()
    db.refresh(db_worker)

    return db_user

@router.post("/login", response_model=schemas.Token)
def login(user_in: schemas.UserLogin, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == user_in.email).first()
    if not user or not verify_password(user_in.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    worker = user.worker
    worker_id = worker.id if worker else None

    # Payload required by phase 3 & 8
    access_token = create_access_token(
        data={
            "sub": user.id,
            "role": user.role,
            "ai_consent_version": user.consent_version,
            "worker_id": worker_id
        }
    )
    
    return {"access_token": access_token, "token_type": "bearer"}
