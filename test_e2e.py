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
# 5. Test Protection Auto Contribute
print("Auto Contributing to Emergency Pot...")
resp = requests.post(f"{BASE_URL}/api/v1/protection/emergency-pot/auto-contribute", headers=headers)
print("Auto Contribute Status:", resp.status_code)
if resp.status_code != 200:
    print("Failed to auto contribute:", resp.text)
    exit(1)
auto_resp = resp.json()
print("Auto Contribute Response:", auto_resp)
assert "contribution" in auto_resp, "Missing contribution in response"
assert "emergency_pot_balance" in auto_resp, "Missing emergency_pot_balance in response"

# 6. Test Credit Eligibility
print("Checking Credit Eligibility...")
resp = requests.get(f"{BASE_URL}/api/v1/protection/credit-eligibility", headers=headers)
print("Credit Eligibility Status:", resp.status_code)
if resp.status_code != 200:
    print("Failed to check credit eligibility:", resp.text)
    exit(1)
credit_resp = resp.json()
print("Credit Eligibility Response:", credit_resp)
assert "eligible" in credit_resp, "Missing eligible in credit response"
assert "credit_limit" in credit_resp, "Missing credit_limit in credit response"

# 7. Re-check dashboard for emergency fund persistence
print("Verifying Dashboard emergencyFund...")
resp = requests.get(f"{BASE_URL}/api/v1/dashboard/worker/me", headers=headers, timeout=10)
if resp.status_code != 200:
    print("Failed to get dashboard:", resp.text)
    exit(1)
dash_data = resp.json()
assert dash_data["emergencyFund"] == auto_resp["emergency_pot_balance"], "Dashboard emergencyFund does not match pot balance"

print("SUCCESS: End-to-End Test Passed with Financial Protection!")
