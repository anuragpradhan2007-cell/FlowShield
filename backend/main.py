import sys
import os
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'risk_engine'))

from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from database import engine, Base
from auth import router as auth_router
from users import router as users_router
from workers import router as workers_router
import dashboard_router
import risk_router
from protection import router as protection_router
from pydantic import BaseModel
from sqlalchemy.orm import Session
from database import get_db
import schemas
from auth.router import generate_sdk_token
from auth.dependencies import require_worker
import models
from app.ml.predictor import _load_model, is_model_available

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Load the ML model exactly once on startup
    _load_model()
    yield
    # Clean up if needed

Base.metadata.create_all(bind=engine)

app = FastAPI(title="FlowShield Auth Module", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(users_router.router, prefix="/api/v1", tags=["users"])
app.include_router(workers_router.router, prefix="/api/v1/workers", tags=["workers"])
app.include_router(dashboard_router.router, prefix="/api/v1/dashboard", tags=["dashboard"])
app.include_router(risk_router.router, prefix="/api/v1/workers", tags=["risk"])
app.include_router(protection_router.router, prefix="/api/v1/protection", tags=["protection"])

@app.get("/api/v1/health")
def health_check():
    return {"status": "ok", "model_loaded": is_model_available()}

class MockHostTokenRequest(BaseModel):
    occupation: str

@app.post("/api/v1/mock-host/get-sdk-token")
def mock_host_get_sdk_token(
    request: MockHostTokenRequest, 
    current_user: models.User = Depends(require_worker),
    db: Session = Depends(get_db)
):
    # This endpoint acts as the Mock Host's backend server.
    # It authenticates the user via the existing trusted authentication
    # and derives the worker_id securely.
    if not current_user.worker:
        raise HTTPException(status_code=400, detail="Authenticated user is not a worker")
        
    secure_worker_id = current_user.worker.id

    # It injects the secure partner_api_key server-side so it's not exposed in the browser bundle.
    internal_request = schemas.SDKTokenRequest(
        partner_api_key="mock-partner-key-123",
        host_worker_id=secure_worker_id,
        occupation=request.occupation
    )
    return generate_sdk_token(internal_request, db)
