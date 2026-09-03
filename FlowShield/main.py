import os
import uuid
import random
from datetime import datetime, timedelta, timezone
from typing import List, Optional

from fastapi import FastAPI, HTTPException, APIRouter
from pydantic import BaseModel, Field
from supabase import create_client, Client
from dotenv import load_dotenv  # Add this line

# Load environment variables from the .env file
load_dotenv()  # Add this line

app = FastAPI(title="FlowShield Income & Transaction Engine")

# Initialize Supabase Client (it will now successfully find the variables)
supabase: Client = create_client(
    os.environ.get("SUPABASE_URL", ""),
    os.environ.get("SUPABASE_KEY", "")
)

# -----------------------------------------------------------------------------
# PYDANTIC MODELS
# -----------------------------------------------------------------------------

# Earnings Models
class EarningRecord(BaseModel):
    worker_id: str
    amount: float = Field(..., description="Unified baseline currency format")
    currency: str = "USD"
    period_start: datetime
    period_end: datetime
    is_missing_data: bool = False

class AggregatedEarningsResponse(BaseModel):
    worker_id: str
    total_earnings_7_days: float
    total_earnings_30_days: float
    baseline_weekly_metric: float
    earnings: List[EarningRecord]

# Transactions Models
class TransactionRecord(BaseModel):
    worker_id: str
    amount: float = Field(..., description="Transaction amount in baseline currency")
    transaction_type: str = Field(..., description="e.g., 'payout', 'emergency_disbursement'")
    status: str = Field(..., description="e.g., 'completed', 'pending', 'failed'")
    transaction_time: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class TransactionResponse(TransactionRecord):
    id: str
    created_at: datetime

class WorkerTransactionsResponse(BaseModel):
    worker_id: str
    transactions: List[TransactionResponse]


# -----------------------------------------------------------------------------
# CORE EARNINGS ENDPOINTS (Member 2 Deliverables)
# -----------------------------------------------------------------------------

@app.post("/earnings")
def create_earning(earning: EarningRecord):
    """Record a worker's daily/weekly earnings with strict ISO-8601 timestamps."""
    data = earning.model_dump()
    data['period_start'] = data['period_start'].isoformat()
    data['period_end'] = data['period_end'].isoformat()
    
    response = supabase.table("earnings").insert(data).execute()
    if not response.data:
        raise HTTPException(status_code=400, detail="Failed to insert earning record")
    return response.data[0]
@app.get("/workers/{worker_id}/earnings", response_model=AggregatedEarningsResponse)
def get_worker_earnings(worker_id: str):
    response = supabase.table("earnings").select("*").eq("worker_id", worker_id).execute()
    
    if not response.data:
        return AggregatedEarningsResponse(
            worker_id=worker_id,
            total_earnings_7_days=0.0,
            total_earnings_30_days=0.0,
            baseline_weekly_metric=0.0,
            earnings=[]
        )
    
    records = response.data
    now = datetime.now(timezone.utc)
    sum_7_days, sum_30_days = 0.0, 0.0
    
    for r in records:
        if not r.get("is_missing_data"):
            try:
                raw_time = r["period_end"].replace('Z', '+00:00')
                end_time = datetime.fromisoformat(raw_time)
                if end_time.tzinfo is None:
                    end_time = end_time.replace(tzinfo=timezone.utc)
                
                amount = float(r["amount"])
                days_ago = (now - end_time).days
                
                if days_ago <= 7:
                    sum_7_days += amount
                if days_ago <= 30:
                    sum_30_days += amount
            except Exception as e:
                print(f"Skipping record due to parse error: {e}")
                continue

    return AggregatedEarningsResponse(
        worker_id=worker_id,
        total_earnings_7_days=round(sum_7_days, 2),
        total_earnings_30_days=round(sum_30_days, 2),
        baseline_weekly_metric=round(sum_30_days / 4, 2),
        earnings=records
    )

# -----------------------------------------------------------------------------
# TRANSACTION & PAYOUT ENDPOINTS (Member 2 Deliverables)
# -----------------------------------------------------------------------------

@app.post("/transactions", response_model=TransactionResponse)
def create_transaction(transaction: TransactionRecord):
    """Record worker payouts and financial protection events."""
    data = transaction.model_dump()
    data['transaction_time'] = data['transaction_time'].isoformat()
    
    response = supabase.table("transactions").insert(data).execute()
    if not response.data:
        raise HTTPException(status_code=400, detail="Failed to record transaction")
    return response.data[0]

@app.get("/workers/{worker_id}/transactions", response_model=WorkerTransactionsResponse)
def get_worker_transactions(worker_id: str):
    """Track historical payouts and transaction logs."""
    response = (
        supabase.table("transactions")
        .select("*")
        .eq("worker_id", worker_id)
        .order("transaction_time", desc=True)
        .execute()
    )
    return WorkerTransactionsResponse(
        worker_id=worker_id,
        transactions=response.data or []
    )


# -----------------------------------------------------------------------------
# MOCK PARTNER PLATFORM SIMULATOR (AI Engine Testing)
# -----------------------------------------------------------------------------

mock_router = APIRouter(prefix="/partner", tags=["Mock Partner Data"])

@mock_router.get("/simulate-earnings")
def get_simulated_partner_data():
    """Simulate gig platform data for Member 3's AI model validation."""
    workers = {
        "stable": {"id": str(uuid.uuid4()), "profile": "Stable"},
        "at_risk": {"id": str(uuid.uuid4()), "profile": "At Risk"},
        "critical": {"id": str(uuid.uuid4()), "profile": "Critical"}
    }
    
    earnings_data = []
    now = datetime.now(timezone.utc)
    
    for days_ago in range(30, -1, -1):
        current_date = now - timedelta(days=days_ago)
        period_start = current_date.replace(hour=8, minute=0, second=0, microsecond=0)
        period_end = current_date.replace(hour=17, minute=0, second=0, microsecond=0)
        
        for key, worker in workers.items():
            is_missing = False
            amount = 0.0
            
            if key == "stable":
                amount = round(random.uniform(100.0, 120.0), 2)
            elif key == "at_risk":
                is_missing = random.random() < 0.2
                if not is_missing:
                    amount = round(random.uniform(30.0, 50.0), 2) if days_ago <= 7 else round(random.uniform(70.0, 90.0), 2)
            elif key == "critical":
                is_missing = random.random() < 0.6
                if not is_missing:
                    amount = round(random.uniform(15.0, 35.0), 2)

            earnings_data.append({
                "worker_id": worker["id"],
                "amount": amount if not is_missing else 0.0,
                "currency": "USD",
                "period_start": period_start.isoformat(),
                "period_end": period_end.isoformat(),
                "is_missing_data": is_missing
            })

    return {
        "source": "Simulated Gig Platform",
        "timestamp": now.isoformat(),
        "mock_profiles": workers,
        "earnings": earnings_data
    }

# Register the mock router
app.include_router(mock_router)