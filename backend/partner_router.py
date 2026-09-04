from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from database import get_db
from services.partner_auth_service import PartnerAuthService
from services.sdk_token_service import SDKTokenService
from auth.security import verify_jwt_token
from pydantic import BaseModel
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

# ============ REQUEST/RESPONSE MODELS ============

class PartnerRegisterRequest(BaseModel):
    name: str
    email: str
    password: str
    commission_rate: float = 10.0

class PartnerLoginRequest(BaseModel):
    email: str
    password: str

class RotateAPIKeyRequest(BaseModel):
    old_api_key: str

# ============ PARTNER MANAGEMENT ENDPOINTS ============

@router.post("/register")
async def register_partner(
    request: PartnerRegisterRequest,
    db: Session = Depends(get_db)
):
    """
    Register a new partner
    
    Returns API key that must be saved securely
    """
    auth_service = PartnerAuthService(db)
    
    try:
        result = auth_service.register_partner(
            name=request.name,
            email=request.email,
            password=request.password,
            commission_rate=request.commission_rate
        )
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Partner registration failed: {e}")
        raise HTTPException(status_code=500, detail="Registration failed")


@router.post("/login")
async def login_partner(
    request: PartnerLoginRequest,
    db: Session = Depends(get_db)
):
    """
    Partner login
    
    Returns JWT token for authenticated requests
    """
    auth_service = PartnerAuthService(db)
    
    try:
        result = auth_service.login_partner(
            email=request.email,
            password=request.password
        )
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Partner login failed: {e}")
        raise HTTPException(status_code=500, detail="Login failed")


@router.get("/me")
async def get_partner_profile(
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Get authenticated partner's profile
    
    Requires: Authorization header with Bearer JWT token
    """
    
    # Extract JWT from header
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid authorization header")
    
    token = auth_header[7:]
    
    try:
        payload = verify_jwt_token(token)
        if payload.get("role") != "partner":
            raise HTTPException(status_code=403, detail="Not a partner account")
        
        partner_id = payload.get("partner_id")
    except Exception as e:
        logger.error(f"Token verification failed: {e}")
        raise HTTPException(status_code=401, detail="Invalid token")
    
    auth_service = PartnerAuthService(db)
    
    try:
        profile = auth_service.get_partner_profile(partner_id)
        return profile
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get partner profile: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve profile")


@router.post("/rotate-api-key")
async def rotate_api_key(
    request_body: RotateAPIKeyRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Rotate partner API key for security
    
    Old key becomes invalid immediately
    """
    
    # Extract JWT
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing authorization")
    
    token = auth_header[7:]
    
    try:
        payload = verify_jwt_token(token)
        if payload.get("role") != "partner":
            raise HTTPException(status_code=403, detail="Not a partner")
        
        partner_id = payload.get("partner_id")
    except Exception as e:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    auth_service = PartnerAuthService(db)
    
    try:
        result = auth_service.rotate_api_key(partner_id, request_body.old_api_key)
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"API key rotation failed: {e}")
        raise HTTPException(status_code=500, detail="Rotation failed")


# ============ SDK TOKEN ENDPOINTS ============

@router.post("/sdk/generate-token")
async def generate_sdk_token(
    worker_id: str,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Generate SDK token for a worker
    
    Requires: X-Partner-API-Key header with valid partner API key
    
    Returns: Signed SDK token that worker can use to open embedded SDK
    """
    
    # Get partner API key from header
    api_key = request.headers.get("X-Partner-API-Key")
    if not api_key:
        raise HTTPException(status_code=401, detail="Missing X-Partner-API-Key header")
    
    # Verify partner API key
    auth_service = PartnerAuthService(db)
    try:
        partner_info = auth_service.verify_api_key(api_key)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"API key verification failed: {e}")
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    # Generate SDK token
    sdk_service = SDKTokenService(db)
    try:
        token_response = sdk_service.generate_sdk_token(
            worker_id=worker_id,
            partner_id=partner_info["partner_id"],
            expires_in_hours=24
        )
        return token_response
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"SDK token generation failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate token")


@router.post("/sdk/verify-token")
async def verify_sdk_token(
    token: str,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Verify SDK token validity
    
    Requires: X-Partner-API-Key header
    
    Returns: Token payload if valid, 401 if invalid/expired
    """
    
    # Get partner API key
    api_key = request.headers.get("X-Partner-API-Key")
    if not api_key:
        raise HTTPException(status_code=401, detail="Missing X-Partner-API-Key header")
    
    # Verify token
    sdk_service = SDKTokenService(db)
    try:
        payload = sdk_service.verify_sdk_token(token, api_key)
        return {
            "valid": True,
            "payload": payload
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token verification failed: {e}")
        raise HTTPException(status_code=401, detail="Invalid or expired token")
