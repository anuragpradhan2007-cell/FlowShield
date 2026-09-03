import requests

BASE_URL = "http://127.0.0.1:8000/api/v1"

def test_api():
    print("1. Registering worker...")
    reg_response = requests.post(f"{BASE_URL}/auth/register", json={
        "email": "worker@example.com",
        "password": "strong-password",
        "occupation": "delivery_worker"
    })
    print("Register Status:", reg_response.status_code)
    print("Register Body:", reg_response.json())
    assert reg_response.status_code == 200

    print("\n2. Duplicate registration...")
    dup_response = requests.post(f"{BASE_URL}/auth/register", json={
        "email": "worker@example.com",
        "password": "strong-password",
        "occupation": "delivery_worker"
    })
    print("Duplicate Status:", dup_response.status_code)
    assert dup_response.status_code == 409

    print("\n3. Login worker...")
    login_response = requests.post(f"{BASE_URL}/auth/login", json={
        "email": "worker@example.com",
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
    other_reg_response = requests.post(f"{BASE_URL}/auth/register", json={
        "email": "worker2@example.com",
        "password": "strong-password",
        "occupation": "delivery_worker"
    })
    other_worker_id = other_reg_response.json()["worker"]["id"]
    other_worker_response = requests.get(f"{BASE_URL}/workers/{other_worker_id}", headers=headers)
    print("Other Worker Status:", other_worker_response.status_code)
    assert other_worker_response.status_code == 403

    print("\nAll tests passed successfully.")

if __name__ == "__main__":
    test_api()
