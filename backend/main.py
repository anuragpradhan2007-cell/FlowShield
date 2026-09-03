from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from database import engine, Base
from auth import router as auth_router
from users import router as users_router
from workers import router as workers_router
import dashboard_router
from pydantic import BaseModel
from sqlalchemy.orm import Session
from database import get_db
import schemas
from auth.router import generate_sdk_token
from auth.dependencies import require_worker
import models

Base.metadata.create_all(bind=engine)

app = FastAPI(title="FlowShield Auth Module")

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

@app.get("/api/v1/health")
def health_check():
    return {"status": "ok"}

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
