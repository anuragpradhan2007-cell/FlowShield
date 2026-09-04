from datetime import datetime, timedelta
import secrets
import hashlib
import json
import base64
from sqlalchemy.orm import Session
from fastapi import HTTPException
from models import SDKToken, Partner, Worker, PartnerWorker, Earning, EmergencyPot
import logging

logger = logging.getLogger(__name__)

class SDKTokenService:
    def __init__(self, db: Session):
        self.db = db

    def generate_sdk_token(
        self,
        worker_id: str,
        partner_id: str,
        expires_in_hours: int = 24
    ) -> dict:
        """
        Generate a cryptographically signed SDK token for a worker to access partner services
        
        Flow:
        1. Verify worker exists
        2. Verify partner is active
        3. Verify worker is enrolled with this partner
        4. Generate token payload with worker + partner info
        5. Sign token with partner API key
        6. Store token in database
        7. Return signed token to caller
        """
        
        # Step 1: Verify worker exists
        worker = self.db.query(Worker).filter(Worker.id == worker_id).first()
        if not worker:
            logger.warning(f"SDK token generation failed: worker {worker_id} not found")
            raise HTTPException(status_code=404, detail="Worker not found")
        
        # Step 2: Verify partner exists and is active
        partner = self.db.query(Partner).filter(
            Partner.id == partner_id,
            Partner.status == "active"
        ).first()
        if not partner:
            logger.warning(f"SDK token generation failed: partner {partner_id} not found or inactive")
            raise HTTPException(status_code=404, detail="Partner not found or inactive")
        
        # Step 3: Check if worker is enrolled with this partner (Auto-enroll for demo)
        enrollment = self.db.query(PartnerWorker).filter(
            PartnerWorker.worker_id == worker_id,
            PartnerWorker.partner_id == partner_id,
            PartnerWorker.status == "active"
        ).first()
        
        if not enrollment:
            logger.info(f"Worker {worker_id} not enrolled with partner {partner_id}. Auto-enrolling for demo.")
            new_enrollment = PartnerWorker(
                worker_id=worker_id,
                partner_id=partner_id,
                status="active"
            )
            self.db.add(new_enrollment)
            self.db.commit()
        
        # Step 4: Calculate FlowShield ML Risk Score & Emergency Fund
        from app.ml.predictor import predict_risk, is_model_available
        
        earnings = self.db.query(Earning).filter(
            Earning.worker_id == worker_id
        ).all()
        
        stability_score = 0.0
        risk_level = "UNKNOWN"
        
        if is_model_available() and earnings:
            earnings_records = [{"date": e.period_end, "amount": float(e.amount), "is_missing_data": e.is_missing_data} for e in earnings]
            try:
                score, tier, details = predict_risk(earnings_records)
                stability_score = score
                risk_level = tier.value
            except Exception as e:
                logger.error(f"Failed to calculate ML risk score for SDK token: {e}")

        # Get FlowShield Emergency Pot
        emergency_pot = self.db.query(EmergencyPot).filter(
            EmergencyPot.worker_id == worker_id
        ).first()
        flowshield_balance = float(emergency_pot.balance) if emergency_pot else 0.0

        # Step 5: Generate token payload
        issued_at = datetime.utcnow()
        expires_at = issued_at + timedelta(hours=expires_in_hours)
        
        token_data = {
            "worker_id": str(worker_id),
            "partner_id": str(partner_id),
            "partner_name": partner.name,
            "worker_email": worker.user.email if hasattr(worker, 'user') and worker.user else 'unknown',
            "risk_score": stability_score,
            "risk_tier": risk_level,
            "flowshield_balance": flowshield_balance,
            "issued_at": issued_at.isoformat(),
            "expires_at": expires_at.isoformat(),
            "nonce": secrets.token_urlsafe(16)
        }
        
        # Step 6: Encode and sign token
        token_json = json.dumps(token_data, separators=(',', ':'))
        token_base64 = base64.b64encode(token_json.encode()).decode()
        
        # Sign with partner API key
        signature = hashlib.sha256(
            f"{token_base64}{partner.api_key}".encode()
        ).hexdigest()
        
        signed_token = f"{token_base64}.{signature}"
        
        # Step 7: Store token in database
        sdk_token = SDKToken(
            worker_id=worker_id,
            partner_id=partner_id,
            token=signed_token,
            token_hash=hashlib.sha256(signed_token.encode()).hexdigest(),
            expires_at=expires_at
        )
        
        self.db.add(sdk_token)
        self.db.commit()
        
        logger.info(f"SDK token generated for worker {worker_id} with partner {partner.name}")
        
        # Step 8: Return token
        return {
            "sdk_token": signed_token,
            "worker_id": str(worker_id),
            "partner_id": str(partner_id),
            "partner_name": partner.name,
            "expires_at": expires_at.isoformat(),
            "expires_in_seconds": int(expires_in_hours * 3600)
        }

    def verify_sdk_token(self, token: str, partner_api_key: str) -> dict:
        """
        Verify SDK token signature and expiration
        
        Returns token payload if valid, raises exception if invalid
        """
        
        try:
            # Split token into payload and signature
            parts = token.rsplit(".", 1)
            if len(parts) != 2:
                raise ValueError("Invalid token format")
            
            token_base64, signature = parts
            
            # Verify signature using partner API key
            expected_signature = hashlib.sha256(
                f"{token_base64}{partner_api_key}".encode()
            ).hexdigest()
            
            if not secrets.compare_digest(signature, expected_signature):
                logger.warning("SDK token verification failed: invalid signature")
                raise ValueError("Invalid token signature")
            
            # Decode payload
            token_json = base64.b64decode(token_base64).decode()
            payload = json.loads(token_json)
            
            # Check expiration
            expires_at = datetime.fromisoformat(payload["expires_at"])
            if datetime.utcnow() > expires_at:
                logger.warning(f"SDK token verification failed: token expired")
                raise ValueError("Token expired")
            
            logger.info(f"SDK token verified for worker {payload['worker_id']}")
            return payload
        
        except Exception as e:
            logger.error(f"SDK token verification failed: {e}")
            raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")

    def revoke_sdk_token(self, token: str) -> dict:
        """Revoke an SDK token (mark as used)"""
        
        sdk_token = self.db.query(SDKToken).filter(SDKToken.token == token).first()
        
        if not sdk_token:
            raise HTTPException(status_code=404, detail="Token not found")
        
        sdk_token.used_at = datetime.utcnow()
        self.db.commit()
        
        return {"message": "Token revoked successfully"}

    def cleanup_expired_tokens(self) -> dict:
        """Clean up expired tokens (run as periodic task)"""
        
        expired_tokens = self.db.query(SDKToken).filter(
            SDKToken.expires_at < datetime.utcnow(),
            SDKToken.used_at.is_(None)
        ).all()
        
        count = len(expired_tokens)
        
        for token in expired_tokens:
            self.db.delete(token)
        
        self.db.commit()
        
        logger.info(f"Cleaned up {count} expired SDK tokens")
        return {"cleaned_up": count}
