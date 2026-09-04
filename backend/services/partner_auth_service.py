from datetime import datetime, timedelta
from fastapi import HTTPException
from sqlalchemy.orm import Session
import secrets
import hashlib
from models import Partner, PartnerAPIKey
from auth.security import get_password_hash, verify_password, create_access_token

class PartnerAuthService:
    def __init__(self, db: Session):
        self.db = db

    def register_partner(
        self,
        name: str,
        email: str,
        password: str,
        commission_rate: float = 10.0
    ) -> dict:
        """Register a new partner with initial API key"""
        
        # Check if partner exists
        existing = self.db.query(Partner).filter(Partner.email == email).first()
        if existing:
            raise HTTPException(status_code=400, detail="Partner email already registered")
        
        # Generate API key
        api_key = f"sk_live_{secrets.token_urlsafe(32)}"
        
        # Create partner
        partner = Partner(
            name=name,
            email=email,
            password_hash=get_password_hash(password),
            api_key=api_key,
            commission_rate=commission_rate,
            status="active"
        )
        
        self.db.add(partner)
        self.db.commit()
        self.db.refresh(partner)
        
        return {
            "partner_id": str(partner.id),
            "name": partner.name,
            "email": partner.email,
            "api_key": api_key,  # Only shown once during registration
            "commission_rate": partner.commission_rate,
            "message": "Partner registered successfully. Save your API key securely."
        }

    def login_partner(self, email: str, password: str) -> dict:
        """Authenticate partner and return JWT"""
        
        partner = self.db.query(Partner).filter(Partner.email == email).first()
        
        if not partner:
            raise HTTPException(status_code=401, detail="Invalid email or password")
        
        if not verify_password(password, partner.password_hash):
            raise HTTPException(status_code=401, detail="Invalid email or password")
        
        if partner.status != "active":
            raise HTTPException(status_code=403, detail="Partner account is not active")
        
        # Generate JWT for partner
        token = create_access_token(
            data={
                "partner_id": str(partner.id),
                "email": partner.email,
                "name": partner.name,
                "role": "partner"
            }
        )
        
        return {
            "access_token": token,
            "token_type": "bearer",
            "partner_id": str(partner.id),
            "name": partner.name,
            "email": partner.email
        }

    def verify_api_key(self, api_key: str) -> dict:
        """Verify partner API key and return partner info"""
        
        partner = self.db.query(Partner).filter(
            Partner.api_key == api_key,
            Partner.status == "active"
        ).first()
        
        if not partner:
            raise HTTPException(status_code=401, detail="Invalid or inactive API key")
        
        return {
            "partner_id": str(partner.id),
            "name": partner.name,
            "email": partner.email,
            "commission_rate": partner.commission_rate,
            "status": partner.status
        }

    def rotate_api_key(self, partner_id: str, old_api_key: str) -> dict:
        """Rotate partner API key for security"""
        
        partner = self.db.query(Partner).filter(Partner.id == partner_id).first()
        
        if not partner or partner.api_key != old_api_key:
            raise HTTPException(status_code=403, detail="Invalid API key")
        
        # Generate new API key
        new_api_key = f"sk_live_{secrets.token_urlsafe(32)}"
        partner.api_key = new_api_key
        partner.updated_at = datetime.utcnow()
        
        self.db.commit()
        
        return {
            "partner_id": str(partner.id),
            "new_api_key": new_api_key,
            "message": "API key rotated successfully"
        }

    def get_partner_profile(self, partner_id: str) -> dict:
        """Get partner profile with business metrics"""
        
        partner = self.db.query(Partner).filter(Partner.id == partner_id).first()
        
        if not partner:
            raise HTTPException(status_code=404, detail="Partner not found")
        
        return {
            "id": str(partner.id),
            "name": partner.name,
            "email": partner.email,
            "commission_rate": partner.commission_rate,
            "total_earnings": float(partner.total_earnings) if partner.total_earnings else 0.0,
            "total_workers": partner.total_workers,
            "status": partner.status,
            "created_at": partner.created_at.isoformat(),
            "api_key": partner.api_key[-10:] + "..." if partner.api_key else None
        }

    def update_partner(self, partner_id: str, **kwargs) -> dict:
        """Update partner settings"""
        
        partner = self.db.query(Partner).filter(Partner.id == partner_id).first()
        
        if not partner:
            raise HTTPException(status_code=404, detail="Partner not found")
        
        # Allow updating specific fields
        allowed_fields = ["webhook_url", "commission_rate", "name"]
        for field, value in kwargs.items():
            if field in allowed_fields and value is not None:
                setattr(partner, field, value)
        
        partner.updated_at = datetime.utcnow()
        self.db.commit()
        
        return {"message": "Partner updated successfully"}
