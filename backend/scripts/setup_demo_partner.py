import sys
import os

# Add the parent directory to the python path so it can find database, models, etc.
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from database import SessionLocal
import models
from auth.security import get_password_hash

def setup_demo_partner():
    """Create a demo partner for testing"""
    
    session = SessionLocal()
    
    # Check if demo partner exists
    existing = session.query(models.Partner).filter(
        models.Partner.email == "demo-partner@flowshield.local"
    ).first()
    
    if existing:
        print(f"[SUCCESS] Demo partner already exists: {existing.api_key}")
        session.close()
        return
    
    # Create demo partner
    demo_partner = models.Partner(
        name="Demo Partner",
        email="demo-partner@flowshield.local",
        password_hash=get_password_hash("DemoPassword123!"),
        api_key="sk_live_demo_partner_key_123456",
        commission_rate=10.0,
        status="active"
    )
    
    session.add(demo_partner)
    session.commit()
    
    print(f"[SUCCESS] Demo partner created")
    print(f"  Email: demo-partner@flowshield.local")
    print(f"  Password: DemoPassword123!")
    print(f"  API Key: {demo_partner.api_key}")
    
    session.close()

if __name__ == "__main__":
    setup_demo_partner()
