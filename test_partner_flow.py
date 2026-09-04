import requests
import os
import sys

BASE_URL = "http://127.0.0.1:8000"

def test_partner_flow():
    import uuid
    unique_email = f"testp_{uuid.uuid4().hex[:6]}@flowshield.local"
    print(f"1. Registering a test partner: {unique_email}")
    resp = requests.post(f"{BASE_URL}/api/v1/sdk/partner/register?name=TestPartner&email={unique_email}&password=TestP@12345")
    if resp.status_code != 200:
        print("   Registration failed:", resp.text)
        sys.exit(1)
        
    partner_data = resp.json()
    print("   Partner Registration Success.")
    partner_token = partner_data.get("token")
    partner_api_key = partner_data.get("api_key")
    partner_signing_secret = partner_data.get("signing_secret")
    
    # 2. Register a worker
    print("\n2. Registering a test worker...")
    resp = requests.post(f"{BASE_URL}/api/v1/auth/register", json={
        "email": f"worker_{partner_api_key[-6:]}@test.com",
        "password": "Test@12345",
        "occupation": "delivery_worker"
    })
    if resp.status_code not in (200, 409):
        print("   Worker Registration failed:", resp.text)
        sys.exit(1)
        
    resp = requests.post(f"{BASE_URL}/api/v1/auth/login", json={
        "email": f"worker_{partner_api_key[-6:]}@test.com",
        "password": "Test@12345"
    })
    worker_token = resp.json().get("access_token")
    
    # 3. Worker initiates SDK token generation
    partner_id = partner_data.get("partner_id")
    print("\n3. Worker requesting SDK Token (auto-enrolls)...")
    resp = requests.post(
        f"{BASE_URL}/api/v1/sdk/worker/get-token?partner_id={partner_id}",
        headers={"Authorization": f"Bearer {worker_token}"}
    )
    if resp.status_code != 200:
        print("   Failed to get SDK token:", resp.text)
        sys.exit(1)
    
    sdk_token_resp = resp.json()
    sdk_token = sdk_token_resp.get("sdk_token")
    print("   SDK Token Generation Success.")
    
    # 4. Partner verifies SDK token
    import urllib.parse
    print("\n4. Partner verifying SDK Token...")
    resp = requests.post(
        f"{BASE_URL}/api/v1/sdk/token/verify?token={urllib.parse.quote(sdk_token)}",
        headers={"X-Partner-API-Key": partner_api_key}
    )
    if resp.status_code != 200:
        print("   Failed to verify SDK token:", resp.text)
        sys.exit(1)
        
    verify_resp = resp.json()
    print("   Token Verification Success!")
    print(f"   Worker ID: {verify_resp['worker_id']}")
    
    # 5. Partner tries to verify SDK token AGAIN (should fail because single-use)
    print("\n5. Partner verifying SDK Token again (should fail)...")
    resp = requests.post(
        f"{BASE_URL}/api/v1/sdk/token/verify?token={urllib.parse.quote(sdk_token)}",
        headers={"X-Partner-API-Key": partner_api_key}
    )
    if resp.status_code == 401 and "already used" in resp.text:
        print("   SUCCESS: Token correctly rejected as already used.")
    else:
        print(f"   FAILED: Token was not rejected! Status: {resp.status_code}, Response: {resp.text}")
        sys.exit(1)
        
    print("\nAll Partner Flow E2E Tests Passed Successfully!")

if __name__ == "__main__":
    test_partner_flow()
