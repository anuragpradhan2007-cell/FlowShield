from datetime import datetime, timedelta
import secrets
import hashlib
import json
import base64
from sqlalchemy.orm import Session
import models

class SDKTokenService:
    def __init__(self, db: Session):
        self.db = db

    def generate_sdk_token(
        self,
        worker_id: str,
        partner_id: str,
        expires_in_hours: int = 24
    ) -> dict:
        """Generate a real SDK token for worker to access partner services"""
        
        # Verify worker exists
        worker = self.db.query(models.Worker).filter(models.Worker.id == worker_id).first()
        if not worker:
            raise ValueError("Worker not found")
        
        # Verify partner exists and is active
        partner = self.db.query(models.Partner).filter(models.Partner.id == partner_id).first()
        if not partner or partner.status != "active":
            raise ValueError("Partner not found or inactive")
        
        # Check if worker is enrolled with this partner (auto-enroll for hackathon)
        enrollment = self.db.query(models.PartnerWorker).filter(
            models.PartnerWorker.worker_id == worker_id,
            models.PartnerWorker.partner_id == partner_id
        ).first()
        
        if not enrollment:
            enrollment = models.PartnerWorker(
                worker_id=worker_id,
                partner_id=partner_id,
                status="active"
            )
            self.db.add(enrollment)
            self.db.flush() # flush to get id without committing outer transaction yet
        
        # Generate token payload
        token_data = {
            "worker_id": str(worker_id),
            "partner_id": str(partner_id),
            "partner_name": partner.name,
            "issued_at": datetime.utcnow().isoformat(),
            "expires_at": (datetime.utcnow() + timedelta(hours=expires_in_hours)).isoformat(),
            "nonce": secrets.token_urlsafe(16)
        }
        
        # Encode token (base64 + signature)
        token_json = json.dumps(token_data)
        token_base64 = base64.b64encode(token_json.encode()).decode()
        
        # Sign token with partner secret
        signature = hashlib.sha256(
            f"{token_base64}{partner.api_key}".encode()
        ).hexdigest()
        
        signed_token = f"{token_base64}.{signature}"
        
        # Store token in database
        expires_at = datetime.utcnow() + timedelta(hours=expires_in_hours)
        sdk_token = models.SDKToken(
            worker_id=worker_id,
            partner_id=partner_id,
            token=signed_token,
            token_hash=hashlib.sha256(signed_token.encode()).hexdigest(),
            expires_at=expires_at
        )
        
        self.db.add(sdk_token)
        self.db.commit()
        
        return {
            "sdk_token": signed_token,
            "worker_id": str(worker_id),
            "partner_id": str(partner_id),
            "partner_name": partner.name,
            "expires_at": expires_at.isoformat(),
            "expires_in_seconds": int(expires_in_hours * 3600)
        }

    def verify_sdk_token(self, token: str, partner_api_key: str) -> dict:
        """Verify SDK token validity and return payload"""
        
        try:
            # Split token
            token_base64, signature = token.rsplit(".", 1)
            
            # Verify signature
            expected_signature = hashlib.sha256(
                f"{token_base64}{partner_api_key}".encode()
            ).hexdigest()
            
            if signature != expected_signature:
                raise ValueError("Invalid signature")
            
            # Decode payload
            token_json = base64.b64decode(token_base64).decode()
            payload = json.loads(token_json)
            
            # Check expiration
            expires_at = datetime.fromisoformat(payload["expires_at"])
            if datetime.utcnow() > expires_at:
                raise ValueError("Token expired")
            
            return payload
        
        except Exception as e:
            raise ValueError(f"Invalid token: {e}")
