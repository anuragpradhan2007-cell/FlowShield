from datetime import datetime, timedelta
from fastapi import HTTPException
from sqlalchemy.orm import Session
import secrets
import hashlib
import models
from auth.security import get_password_hash, verify_password, create_access_token

class PartnerAuthService:
    def __init__(self, db: Session):
        self.db = db

    def register_partner(self, name: str, email: str, password: str) -> dict:
        """Register a new partner"""
        
        # Check if partner exists
        existing = self.db.query(models.Partner).filter(models.Partner.email == email).first()
        if existing:
            raise HTTPException(status_code=400, detail="Partner already exists")
        
        # Generate API key
        api_key = f"sk_{secrets.token_urlsafe(32)}"
        api_key_hash = hashlib.sha256(api_key.encode()).hexdigest()
        signing_secret = secrets.token_urlsafe(64)
        
        # Create partner
        partner = models.Partner(
            name=name,
            email=email,
            password_hash=get_password_hash(password),
            api_key_hash=api_key_hash,
            signing_secret=signing_secret
        )
        
        self.db.add(partner)
        self.db.commit()
        self.db.refresh(partner)
        
        return {
            "partner_id": str(partner.id),
            "name": partner.name,
            "email": partner.email,
            "api_key": api_key,  # Only shown once
            "signing_secret": signing_secret # Only shown once
        }

    def login_partner(self, email: str, password: str) -> dict:
        """Authenticate partner and return JWT"""
        
        partner = self.db.query(models.Partner).filter(models.Partner.email == email).first()
        
        if not partner or not verify_password(password, partner.password_hash):
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        # Generate JWT for partner
        token = create_access_token(
            data={
                "partner_id": str(partner.id),
                "email": partner.email,
                "role": "partner"
            },
            expires_delta=timedelta(hours=24)
        )
        
        return {
            "partner_id": str(partner.id),
            "token": token,
            "name": partner.name
        }

    def verify_api_key(self, api_key: str) -> dict:
        """Verify partner API key"""
        
        api_key_hash = hashlib.sha256(api_key.encode()).hexdigest()
        partner = self.db.query(models.Partner).filter(models.Partner.api_key_hash == api_key_hash).first()
        
        if not partner or partner.status != "active":
            raise HTTPException(status_code=401, detail="Invalid API key")
        
        return {
            "partner_id": str(partner.id),
            "name": partner.name,
            "commission_rate": partner.commission_rate
        }
