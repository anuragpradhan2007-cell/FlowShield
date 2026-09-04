from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from database import get_db
from services.sdk_token_service import SDKTokenService
from auth.security import verify_jwt_token
from models import Partner
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/worker/get-token")
async def get_sdk_token_for_worker(
    partner_id: str = None,  # Optional: specific partner, or use default
    request: Request = None,
    db: Session = Depends(get_db)
):
    """
    Worker endpoint: Get SDK token to access partner services
    
    Flow:
    1. Extract worker from JWT (authentication)
    2. Resolve partner (use specified partner_id or default)
    3. Generate SDK token
    4. Return token to worker
    
    Frontend then uses this token to initialize embedded SDK modal
    """
    
    # Step 1: Extract worker from JWT
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        logger.warning("SDK token request: missing authorization")
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    token = auth_header[7:]
    
    try:
        payload = verify_jwt_token(token)
        worker_id = payload.get("user_id")
        if not worker_id:
            # Fallback to sub or worker_id based on our JWT structure
            worker_id = payload.get("sub") or payload.get("worker_id")
            
        if not worker_id:
            raise ValueError("No user_id in token")
    except Exception as e:
        logger.error(f"JWT verification failed: {e}")
        raise HTTPException(status_code=401, detail="Invalid token")
    
    # Step 2: Resolve partner
    if partner_id:
        # Use specified partner
        partner = db.query(Partner).filter(
            Partner.id == partner_id,
            Partner.status == "active"
        ).first()
    else:
        # Use first active partner (demo behavior)
        # In production, this might use worker's default partner or config
        partner = db.query(Partner).filter(Partner.status == "active").first()
    
    if not partner:
        logger.warning(f"No active partner found for worker {worker_id}")
        raise HTTPException(status_code=404, detail="No partner available")
    
    # Step 3: Generate SDK token
    sdk_service = SDKTokenService(db)
    try:
        token_response = sdk_service.generate_sdk_token(
            worker_id=worker_id,
            partner_id=str(partner.id),
            expires_in_hours=24
        )
        
        logger.info(f"SDK token generated for worker {worker_id}")
        return token_response
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to generate SDK token: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate token")
