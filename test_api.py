import requests
import uuid
import subprocess
import time
import sys

BASE_URL = "http://127.0.0.1:8000/api/v1"

def test_api():
    test_email = f"worker_{uuid.uuid4().hex[:8]}@example.com"
    
    print("1. Registering worker...")
    reg_response = requests.post(f"{BASE_URL}/auth/register", json={
        "email": test_email,
        "password": "strong-password",
        "occupation": "delivery_worker"
    })
    print("Register Status:", reg_response.status_code)
    print("Register Body:", reg_response.json())
    assert reg_response.status_code == 200

    print("\n2. Duplicate registration...")
    dup_response = requests.post(f"{BASE_URL}/auth/register", json={
        "email": test_email,
        "password": "strong-password",
        "occupation": "delivery_worker"
    })
    print("Duplicate Status:", dup_response.status_code)
    assert dup_response.status_code == 409

    print("\n3. Login worker...")
    login_response = requests.post(f"{BASE_URL}/auth/login", json={
        "email": test_email,
        "password": "strong-password"
    })
    print("Login Status:", login_response.status_code)
    token = login_response.json().get("access_token")
    assert token is not None
    headers = {"Authorization": f"Bearer {token}"}

    print("\n4. Get /me...")
    me_response = requests.get(f"{BASE_URL}/me", headers=headers)
    print("Me Status:", me_response.status_code)
    print("Me Body:", me_response.json())
    assert me_response.status_code == 200

    worker_id = me_response.json()["worker"]["id"]
    print(f"\n5. Get /workers/{worker_id}...")
    worker_response = requests.get(f"{BASE_URL}/workers/{worker_id}", headers=headers)
    print("Worker Status:", worker_response.status_code)
    print("Worker Body:", worker_response.json())
    assert worker_response.status_code == 200

    print("\n6. Get another worker (Forbidden)...")
    other_email = f"other_{uuid.uuid4().hex[:8]}@example.com"
    other_reg_response = requests.post(f"{BASE_URL}/auth/register", json={
        "email": other_email,
        "password": "strong-password",
        "occupation": "delivery_worker"
    })
    other_worker_id = other_reg_response.json()["worker"]["id"]
    other_worker_response = requests.get(f"{BASE_URL}/workers/{other_worker_id}", headers=headers)
    print("Other Worker Status:", other_worker_response.status_code)
    assert other_worker_response.status_code == 403

    print("\n7. Test B2B SDK Token...")
    sdk_response = requests.post(f"{BASE_URL}/auth/sdk/token", json={
        "partner_api_key": "mock-partner-key-123",
        "host_worker_id": "swiggy-driver-987",
        "occupation": "delivery_driver"
    })
    print("SDK Token Status:", sdk_response.status_code)
    assert sdk_response.status_code == 200
    sdk_token = sdk_response.json()["access_token"]
    
    print("   Fetching profile with SDK token...")
    sdk_me_response = requests.get(f"{BASE_URL}/me", headers={"Authorization": f"Bearer {sdk_token}"})
    print("   SDK Me Status:", sdk_me_response.status_code)
    assert sdk_me_response.status_code == 200
    assert sdk_me_response.json()["worker"]["occupation"] == "delivery_driver"

    print("\nAll tests passed successfully.")

if __name__ == "__main__":
    print("Starting FastAPI server in the background...")
    server_process = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "main:app", "--port", "8000"],
        cwd="backend",
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    
    # Wait for server to boot up
    time.sleep(3)
    
    try:
        test_api()
    finally:
        print("\nShutting down server...")
        server_process.terminate()
        server_process.wait()
