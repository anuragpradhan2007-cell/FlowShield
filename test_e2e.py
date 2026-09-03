import requests
import datetime

BASE_URL = "http://127.0.0.1:8000"

# 1. Register
print("Registering Ravi...")
resp = requests.post(f"{BASE_URL}/api/v1/auth/register", json={
    "email": "ravi@test.com",
    "password": "Test@12345",
    "occupation": "delivery_worker"
})
print("Register Status:", resp.status_code)
if resp.status_code not in (200, 409):
    print("Failed to register:", resp.text)
    exit(1)

# 2. Login
print("Logging in...")
resp = requests.post(f"{BASE_URL}/api/v1/auth/login", json={
    "email": "ravi@test.com",
    "password": "Test@12345"
})
print("Login Status:", resp.status_code)
if resp.status_code != 200:
    print("Failed to login:", resp.text)
    exit(1)

token = resp.json().get("access_token")
headers = {"Authorization": f"Bearer {token}"}

# Get User Profile to get worker ID
print("Fetching profile...")
resp = requests.get(f"{BASE_URL}/api/v1/me", headers=headers)
if resp.status_code != 200:
    print("Failed to get profile:", resp.text)
    exit(1)
worker_id = resp.json()["worker"]["id"]
print("Worker ID:", worker_id)

# 3. Add Earnings
print("Adding Earnings...")
now = datetime.datetime.now(datetime.timezone.utc)
amounts = [900, 850, 920, 300, 250]
for i, amount in enumerate(amounts):
    date = (now - datetime.timedelta(days=i)).isoformat()
    resp = requests.post(f"{BASE_URL}/api/v1/workers/{worker_id}/earnings", json={
        "amount": amount,
        "period_start": date,
        "period_end": date
    }, headers=headers)
    if resp.status_code != 200:
        print("Failed to add earning:", resp.text)
        exit(1)
print("Earnings added successfully.")

# 4. Run Model / Get Dashboard
print("Fetching Dashboard...")
resp = requests.get(f"{BASE_URL}/api/v1/dashboard/worker/me", headers=headers)
print("Dashboard Status:", resp.status_code)
if resp.status_code != 200:
    print("Failed to get dashboard:", resp.text)
    exit(1)

data = resp.json()
print("Dashboard Response:")
print(f"Stability Score: {data.get('stabilityScore')}")
print(f"Risk Level: {data.get('riskLevel')}")
print(f"Weekly Income: {data.get('weeklyIncome')}")
print("SUCCESS: End-to-End Test Passed!")
