from fastapi import FastAPI
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
    host_worker_id: str
    occupation: str

@app.post("/api/v1/mock-host/get-sdk-token")
def mock_host_get_sdk_token(request: MockHostTokenRequest, db: Session = Depends(get_db)):
    # This endpoint acts as the Mock Host's backend server.
    # It injects the secure partner_api_key server-side so it's not exposed in the browser bundle.
    internal_request = schemas.SDKTokenRequest(
        partner_api_key="mock-partner-key-123",
        host_worker_id=request.host_worker_id,
        occupation=request.occupation
    )
    return generate_sdk_token(internal_request, db)
