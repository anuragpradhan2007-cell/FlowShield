from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from database import get_db
import models

# Import our custom JWT helper which is slightly different in this codebase
from auth.security import create_access_token
from jose import jwt
from config import settings

from services.sdk_token_service import SDKTokenService
from auth.partner_auth import PartnerAuthService

router = APIRouter()

def verify_jwt_token(token: str):
    """Helper to decode JWT"""
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        return payload
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

# ============ PARTNER ENDPOINTS ============

@router.post("/partner/register")
async def register_partner(
    name: str,
    email: str,
    password: str,
    db: Session = Depends(get_db)
):
    """Register a new partner"""
    partner_auth = PartnerAuthService(db)
    return partner_auth.register_partner(name, email, password)


@router.post("/partner/login")
async def login_partner(
    email: str,
    password: str,
    db: Session = Depends(get_db)
):
    """Login as partner"""
    partner_auth = PartnerAuthService(db)
    return partner_auth.login_partner(email, password)


@router.get("/partner/me")
async def get_partner_profile(
    request: Request,
    db: Session = Depends(get_db)
):
    """Get authenticated partner profile"""
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")
    
    token = auth_header.replace("Bearer ", "")
    payload = verify_jwt_token(token)
    
    if payload.get("role") != "partner":
        raise HTTPException(status_code=403, detail="Not a partner")
    
    partner = db.query(models.Partner).filter(models.Partner.id == payload["partner_id"]).first()
    
    if not partner:
        raise HTTPException(status_code=404, detail="Partner not found")
    
    return {
        "id": str(partner.id),
        "name": partner.name,
        "email": partner.email,
        "api_key": partner.api_key,
        "commission_rate": partner.commission_rate,
        "total_earnings": float(partner.total_earnings),
        "total_workers": partner.total_workers,
        "status": partner.status
    }


# ============ WORKER SDK TOKEN ENDPOINTS ============

@router.post("/token/generate")
async def generate_sdk_token(
    worker_id: str,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Generate SDK token for authenticated worker
    Worker can use this token to access partner services
    """
    
    # Get partner API key from header
    api_key = request.headers.get("X-Partner-API-Key")
    if not api_key:
        raise HTTPException(status_code=401, detail="Missing Partner API key")
    
    # Verify partner
    partner_auth = PartnerAuthService(db)
    try:
        partner_info = partner_auth.verify_api_key(api_key)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid Partner API key")
    
    # Generate SDK token
    token_service = SDKTokenService(db)
    try:
        token_response = token_service.generate_sdk_token(
            worker_id=worker_id,
            partner_id=partner_info["partner_id"],
            expires_in_hours=24
        )
        return token_response
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/token/verify")
async def verify_sdk_token(
    token: str,
    request: Request,
    db: Session = Depends(get_db)
):
    """Verify SDK token (called by frontend before opening SDK modal)"""
    
    # Get partner API key
    api_key = request.headers.get("X-Partner-API-Key")
    if not api_key:
        raise HTTPException(status_code=401, detail="Missing Partner API key")
    
    # Verify token
    token_service = SDKTokenService(db)
    try:
        payload = token_service.verify_sdk_token(token, api_key)
        return {
            "valid": True,
            "worker_id": payload["worker_id"],
            "partner_id": payload["partner_id"],
            "expires_at": payload["expires_at"]
        }
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))


# ============ FRONTEND BRIDGE ENDPOINT ============

@router.post("/worker/get-token")
async def get_sdk_token_for_worker(
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Worker-facing endpoint: Get SDK token for the embedded SDK
    
    This endpoint:
    1. Verifies worker is authenticated (via JWT in request)
    2. Retrieves the default/primary partner (or accepts partner_id)
    3. Generates an SDK token
    4. Returns token to frontend
    
    Frontend then uses this token to initialize the embedded SDK modal
    """
    
    # Extract worker from JWT
    auth_header = request.headers.get("Authorization", "")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Unauthorized")
        
    token = auth_header.replace("Bearer ", "")
    payload = verify_jwt_token(token)
    
    worker_id = payload.get("worker_id")
    if not worker_id:
        # Depending on how auth payload is constructed, try to fetch worker_id from sub
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Unauthorized (no worker ID)")
        worker = db.query(models.Worker).filter(models.Worker.user_id == user_id).first()
        if not worker:
            raise HTTPException(status_code=400, detail="Worker profile not found")
        worker_id = worker.id
    
    # Get partner (for demo, use the first active partner)
    partner = db.query(models.Partner).filter(models.Partner.status == "active").first()
    
    if not partner:
        raise HTTPException(status_code=404, detail="No active partner found")
    
    # Generate SDK token
    token_service = SDKTokenService(db)
    try:
        token_response = token_service.generate_sdk_token(
            worker_id=worker_id,
            partner_id=str(partner.id),
            expires_in_hours=24
        )
        return token_response
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
