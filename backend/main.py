from fastapi import FastAPI, Depends, Header, HTTPException
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

# Mock server-side session store mapping session tokens to worker IDs
MOCK_SESSION_STORE = {
    "mock-session-123": "worker-1"
}

@app.post("/api/v1/mock-host/get-sdk-token")
def mock_host_get_sdk_token(
    request: MockHostTokenRequest, 
    host_session_token: str = Header(..., alias="X-Host-Session-Token"),
    db: Session = Depends(get_db)
):
    # This endpoint acts as the Mock Host's backend server.
    # It authenticates the user via a trusted server-side session token
    # and derives the worker_id securely.
    if host_session_token not in MOCK_SESSION_STORE:
        raise HTTPException(status_code=401, detail="Invalid host session token")
        
    secure_worker_id = MOCK_SESSION_STORE[host_session_token]

    # It injects the secure partner_api_key server-side so it's not exposed in the browser bundle.
    internal_request = schemas.SDKTokenRequest(
        partner_api_key="mock-partner-key-123",
        host_worker_id=secure_worker_id,
        occupation=request.occupation
    )
    return generate_sdk_token(internal_request, db)
