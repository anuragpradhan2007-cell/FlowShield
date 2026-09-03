import os
import random
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

# Connect to Supabase
supabase = create_client(
    os.environ.get("SUPABASE_URL", ""),
    os.environ.get("SUPABASE_KEY", "")
)

WORKER_PROFILES = {
    "stable": {
        "id": "11111111-1111-4111-8111-111111111111",
        "profile": "Stable"
    },
    "at_risk": {
        "id": "22222222-2222-4222-8222-222222222222",
        "profile": "At Risk"
    },
    "critical": {
        "id": "33333333-3333-4333-8333-333333333333",
        "profile": "Critical"
    }
}

def generate_and_seed():
    records = []
    now = datetime.now(timezone.utc)
    
    # 61 days x 3 profiles = 183 total records
    for days_ago in range(60, -1, -1):
        current_date = now - timedelta(days=days_ago)
        period_start = current_date.replace(hour=8, minute=0, second=0, microsecond=0)
        period_end = current_date.replace(hour=19, minute=0, second=0, microsecond=0)
        
        for key, worker in WORKER_PROFILES.items():
            is_missing = False
            amount = 0.0
            
            if key == "stable":
                amount = round(random.uniform(100.0, 130.0), 2)
            elif key == "at_risk":
                is_missing = random.random() < 0.20
                if not is_missing:
                    amount = round(random.uniform(30.0, 50.0), 2) if days_ago <= 7 else round(random.uniform(70.0, 95.0), 2)
            elif key == "critical":
                is_missing = random.random() < 0.60
                if not is_missing:
                    amount = round(random.uniform(15.0, 35.0), 2)

            records.append({
                "worker_id": worker["id"],
                "amount": amount if not is_missing else 0.0,
                "currency": "USD",
                "period_start": period_start.isoformat(),
                "period_end": period_end.isoformat(),
                "is_missing_data": is_missing
            })

    # Push into Supabase earnings table
    print(f"Uploading {len(records)} records to Supabase...")
    response = supabase.table("earnings").insert(records).execute()
    print("Seeding complete! 183 rows added to table 'earnings'.")

if __name__ == "__main__":
    generate_and_seed()