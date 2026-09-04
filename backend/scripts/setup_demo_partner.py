import sys
import os

# Add the parent directory to the python path so it can find database, models, etc.
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from database import SessionLocal
import models
from auth.security import get_password_hash
import hashlib
import secrets

def setup_demo_partner():
    """Create a demo partner for testing"""
    
    if os.environ.get("ENVIRONMENT") != "development":
        print("ERROR: Refusing to execute demo setup outside of a development environment.")
        sys.exit(1)
        
    password = os.environ.get("DEMO_PARTNER_PASSWORD")
    if not password:
        print("ERROR: DEMO_PARTNER_PASSWORD environment variable must be set.")
        sys.exit(1)
        
    session = SessionLocal()
    
    # Check if demo partner exists
    existing = session.query(models.Partner).filter(
        models.Partner.email == "demo-partner@flowshield.local"
    ).first()
    
    if existing:
        print(f"[SUCCESS] Demo partner already exists: {existing.api_key}")
        session.close()
        return
    
    api_key = f"sk_demo_{secrets.token_urlsafe(32)}"
    api_key_hash = hashlib.sha256(api_key.encode()).hexdigest()
    signing_secret = secrets.token_urlsafe(64)
    
    # Create demo partner
    demo_partner = models.Partner(
        name="Demo Partner",
        email="demo-partner@flowshield.local",
        password_hash=get_password_hash(password),
        api_key_hash=api_key_hash,
        signing_secret=signing_secret,
        commission_rate=10.0,
        status="active"
    )
    
    session.add(demo_partner)
    session.commit()
    
    print(f"[SUCCESS] Demo partner created")
    print(f"  Email: demo-partner@flowshield.local")
    print(f"  Password: (from DEMO_PARTNER_PASSWORD)")
    print(f"  API Key: {api_key}")
    print(f"  Signing Secret: {signing_secret}")
    
    session.close()

if __name__ == "__main__":
    setup_demo_partner()
