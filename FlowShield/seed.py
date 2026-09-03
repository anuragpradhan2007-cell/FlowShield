import os
import random
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv

try:
    from supabase import create_client
except ImportError:
    create_client = None

load_dotenv()

# Connect to Supabase
SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "")

supabase = None
if create_client and SUPABASE_URL and SUPABASE_KEY:
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception as e:
        print(f"Warning: Could not initialize Supabase client: {e}")
# Configuration
DAILY_EARNING_THRESHOLD = 100.0  # Living benchmark threshold ($)
POT_CONTRIBUTION_RATE = 0.20    # 20% of surplus contributed to pot
STREAK_PERSISTENCE_DAYS = 7     # Days required to trigger a status update
# 600 Worker Profiles with Dynamic Cycle Offsets
WORKER_PROFILES = {}

# 1. 200 Initially Stable Workers
for i in range(1, 201):
    key = f"stable_{i}"
    WORKER_PROFILES[key] = {
        "id": f"11111111-1111-4111-8111-{i:012d}",
        "initial_profile": "Stable",
        "current_status": "Stable",
        "surplus_streak": 0,
        "deficit_streak": 0,
        "accumulated_pot": 0.0,
        "cycle_offset": i % 30,  # Staggers phase transitions for realistic variance
    }

# 2. 200 Initially At Risk Workers
for i in range(1, 201):
    key = f"at_risk_{i}"
    WORKER_PROFILES[key] = {
        "id": f"22222222-2222-4222-8222-{i:012d}",
        "initial_profile": "At Risk",
        "current_status": "At Risk",
        "surplus_streak": 0,
        "deficit_streak": 0,
        "accumulated_pot": 0.0,
        "cycle_offset": (i + 10) % 30,
    }

# 3. 200 Initially Critical Workers
for i in range(1, 201):
    key = f"critical_{i}"
    WORKER_PROFILES[key] = {
        "id": f"33333333-3333-4333-8333-{i:012d}",
        "initial_profile": "Critical",
        "current_status": "Critical",
        "surplus_streak": 0,
        "deficit_streak": 0,
        "accumulated_pot": 0.0,
        "cycle_offset": (i + 20) % 30,
    }


def determine_cyclical_earnings(
    worker: dict,
    day_step: int,
    total_days: int = 61,
) -> tuple[float, bool]:
    """
    Generates earnings that naturally vary and cycle across economic phases:
    - Phase 1 (Surplus):  Earnings $105 - $145 > $100 -> Generates surplus & pot contributions
    - Phase 2 (Lean):     Earnings $55 - $85 < $100   -> Shortfall ($0 pot contribution)
    - Phase 3 (Crisis):   Earnings $0 - $35           -> Severe deficit / missing data
    - Phase 4 (Recovery): Earnings $115 - $155 > $100 -> Rebound, surplus & pot contributions resume
    """
    effective_day = (day_step + worker["cycle_offset"]) % 40

    is_missing = False
    amount = 0.0

    if effective_day < 16:
        # ── Surplus Period: Above $100 threshold ──
        amount = round(random.uniform(105.0, 145.0), 2)
        is_missing = False

    elif effective_day < 28:
        # ── Lean Period: Dip below $100 threshold ──
        is_missing = random.random() < 0.15
        if not is_missing:
            amount = round(random.uniform(55.0, 85.0), 2)

    elif effective_day < 34:
        # ── Crisis Slump: Severe deficit / inactivity ──
        is_missing = random.random() < 0.60
        if not is_missing:
            amount = round(random.uniform(15.0, 35.0), 2)

    else:
        # ── Recovery Period: Rebound back above threshold ──
        amount = round(random.uniform(115.0, 155.0), 2)
        is_missing = False

    return amount, is_missing


def generate_and_seed(upload_to_supabase: bool = True):
    records = []
    now = datetime.now(timezone.utc)
    total_days = 61  # 61 days x 600 profiles = 36,600 total records

    print("=" * 70)
    print("GENERATING SYNTHETIC CYCLICAL EARNINGS WITH POT CONTRIBUTIONS")
    print(f"Benchmark Threshold : ${DAILY_EARNING_THRESHOLD:.2f} / day")
    print(f"Pot Contribution    : {int(POT_CONTRIBUTION_RATE * 100)}% of surplus (if earning > threshold)")
    print(f"Deficit Action      : Do nothing ($0 pot contribution)")
    print(f"Persistence Window  : {STREAK_PERSISTENCE_DAYS} days for status updates")
    print("=" * 70)

    # Chronological generation: from 60 days ago up to day 0 (today)
    for day_idx, days_ago in enumerate(range(total_days - 1, -1, -1)):
        current_date = now - timedelta(days=days_ago)
        period_start = current_date.replace(hour=8, minute=0, second=0, microsecond=0)
        period_end = current_date.replace(hour=19, minute=0, second=0, microsecond=0)

        for key, worker in WORKER_PROFILES.items():
            # 1. Determine daily earning based on economic cycle
            amount, is_missing = determine_cyclical_earnings(
                worker=worker,
                day_step=day_idx,
                total_days=total_days,
            )

            # 2. Compare against threshold: calculate surplus & pot contribution
            if amount > DAILY_EARNING_THRESHOLD and not is_missing:
                surplus = round(amount - DAILY_EARNING_THRESHOLD, 2)
                pot_contribution = round(surplus * POT_CONTRIBUTION_RATE, 2)
                worker["accumulated_pot"] += pot_contribution
                worker["surplus_streak"] += 1
                worker["deficit_streak"] = 0
            else:
                surplus = 0.0
                pot_contribution = 0.0  # Do nothing
                worker["deficit_streak"] += 1
                worker["surplus_streak"] = 0

            # 3. Dynamic status update based on prolonged persistence
            if worker["surplus_streak"] >= STREAK_PERSISTENCE_DAYS:
                worker["current_status"] = "Stable"
            elif worker["deficit_streak"] >= (STREAK_PERSISTENCE_DAYS * 2):  # 14+ days deficit
                worker["current_status"] = "Critical"
            elif worker["deficit_streak"] >= STREAK_PERSISTENCE_DAYS:        # 7+ days deficit
                worker["current_status"] = "At Risk"

            # 4. Construct record row (exact Supabase earnings table schema)
            records.append({
                "worker_id": worker["id"],
                "amount": amount if not is_missing else 0.0,
                "currency": "USD",
                "period_start": period_start.isoformat(),
                "period_end": period_end.isoformat(),
                "is_missing_data": is_missing,
            })

    # Summary diagnostics
    total_surplus_gen = sum(w["accumulated_pot"] / POT_CONTRIBUTION_RATE for w in WORKER_PROFILES.values())
    total_pot_gen = sum(w["accumulated_pot"] for w in WORKER_PROFILES.values())
    status_counts = {}
    for w in WORKER_PROFILES.values():
        st = w["current_status"]
        status_counts[st] = status_counts.get(st, 0) + 1

    print(f"\nGenerated {len(records)} total records across {len(WORKER_PROFILES)} workers.")
    print(f"Total Surplus Generated    : ${total_surplus_gen:,.2f}")
    print(f"Total Pot Contributions    : ${total_pot_gen:,.2f}")
    print(f"Final Status Distribution  : {status_counts}")
    print("-" * 70)

    # Push into Supabase earnings table in batches of 1,000
    if upload_to_supabase:
        if supabase is None:
            print("[ERROR] Cannot upload: SUPABASE_URL or SUPABASE_KEY is missing from .env.")
            print("Please ensure your .env contains:")
            print("  SUPABASE_URL=https://<your-project>.supabase.co")
            print("  SUPABASE_KEY=<your-service-role-key-or-anon-key>")
            return records

        print(f"Uploading {len(records)} records directly to Supabase table 'earnings'...")
        batch_size = 1000
        for i in range(0, len(records), batch_size):
            batch = records[i:i + batch_size]
            try:
                supabase.table("earnings").insert(batch).execute()
                print(f"  Uploaded batch {i // batch_size + 1}/{(len(records) + batch_size - 1) // batch_size} ({len(batch)} rows)...")
            except Exception as e:
                print(f"  Batch {i // batch_size + 1} upload failed: {e}")
                raise e
        print(f"Seeding complete! Successfully added {len(records)} rows to table 'earnings'.")
    else:
        print("[INFO] Upload disabled (dry-run mode).")

    return records


if __name__ == "__main__":
    generate_and_seed(upload_to_supabase=True)
