import uuid
from datetime import date, timedelta
import pytest
from fastapi.testclient import TestClient

from app.database import Base, engine
from app.main import app
from app.schemas.risk_score import DailyIncomeRecord, WorkerDataInput

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


def create_sample_worker_payload(worker_id: uuid.UUID, daily_amount: float = 150.0, days: int = 30):
    start = date(2026, 1, 1)
    records = [
        DailyIncomeRecord(
            date=str(start + timedelta(days=i)),
            amount=daily_amount + (10.0 if i % 2 == 0 else -10.0),
            hours_worked=8.0,
            trips_completed=10,
        )
        for i in range(days)
    ]
    return {
        "worker_id": str(worker_id),
        "income_history": [r.model_dump() for r in records],
        "current_savings": 2000.0,
        "weekly_expenses": 400.0,
        "weather_condition": "CLEAR",
        "expected_capacity_days": 24,
    }


# -------------------------------------------------------------------------
# Phase 4 API Endpoint Tests
# -------------------------------------------------------------------------

def test_post_calculate_endpoint_creates_score_and_explainability():
    worker_id = uuid.uuid4()
    payload = create_sample_worker_payload(worker_id, daily_amount=160.0)

    # 1. Call POST /workers/{worker_id}/calculate
    response = client.post(f"/workers/{worker_id}/calculate", json=payload)
    assert response.status_code == 201
    data = response.json()

    # Verify Bounded Contract
    assert data["worker_id"] == str(worker_id)
    assert 0.0 <= data["stability_score"] <= 100.0
    assert data["risk_tier"] in ["Stable", "At Risk", "Critical"]
    assert "id" in data
    assert "created_at" in data

    # Verify Explainability Logging Details in metrics_breakdown
    breakdown = data["metrics_breakdown"]
    assert breakdown["income_consistency"]["weight"] == 0.30
    assert breakdown["income_consistency"]["standard_deviation"] is not None
    assert breakdown["income_consistency"]["mean"] is not None
    assert "tooltip" in breakdown["income_consistency"]

    assert breakdown["work_frequency"]["weight"] == 0.25
    assert breakdown["recent_income_trend"]["weight"] == 0.20
    assert breakdown["savings_buffer"]["weight"] == 0.15
    assert breakdown["external_risk_factors"]["weight"] == 0.10

    # Verify Explainability Notes for Member 5 frontend
    notes = breakdown["explainability_notes"]
    assert "score_formula" in notes
    assert "tier_explanation" in notes


def test_get_stability_score_latest():
    worker_id = uuid.uuid4()
    payload = create_sample_worker_payload(worker_id, daily_amount=150.0)

    # First calculate
    calc_resp = client.post(f"/workers/{worker_id}/calculate", json=payload)
    assert calc_resp.status_code == 201

    # Now fetch via GET /workers/{worker_id}/stability-score
    get_resp = client.get(f"/workers/{worker_id}/stability-score")
    assert get_resp.status_code == 200
    score_data = get_resp.json()

    assert score_data["worker_id"] == str(worker_id)
    assert score_data["stability_score"] == calc_resp.json()["stability_score"]
    assert score_data["risk_tier"] == calc_resp.json()["risk_tier"]
    assert "metrics_breakdown" in score_data


def test_get_risk_summary_for_member_4():
    worker_id = uuid.uuid4()
    # Volatile worker with dropped earnings and $0 savings
    start = date(2026, 1, 1)
    records = [
        DailyIncomeRecord(date=str(start + timedelta(days=i)), amount=150.0 if i < 15 else 0.0)
        for i in range(30)
    ]
    payload = {
        "worker_id": str(worker_id),
        "income_history": [r.model_dump() for r in records],
        "current_savings": 0.0,
        "weekly_expenses": 400.0,
        "weather_condition": "SEVERE_ALERT",
        "expected_capacity_days": 24,
    }

    # Calculate
    client.post(f"/workers/{worker_id}/calculate", json=payload)

    # Call GET /workers/{worker_id}/risk
    risk_resp = client.get(f"/workers/{worker_id}/risk")
    assert risk_resp.status_code == 200
    risk_data = risk_resp.json()

    assert risk_data["worker_id"] == str(worker_id)
    assert 0.0 <= risk_data["stability_score"] <= 100.0
    assert risk_data["risk_tier"] in ["At Risk", "Critical"]
    assert isinstance(risk_data["anomaly_flags"], list)
    # Volatile worker should have triggered anomaly flags
    assert len(risk_data["anomaly_flags"]) > 0
    assert "DEPLETED_SAVINGS_BUFFER" in risk_data["anomaly_flags"]
    assert "last_calculated_at" in risk_data


def test_get_nonexistent_worker_returns_404():
    random_uuid = str(uuid.uuid4())
    resp = client.get(f"/workers/{random_uuid}/stability-score")
    assert resp.status_code == 404
    assert "No risk score records found" in resp.json()["detail"]

    risk_resp = client.get(f"/workers/{random_uuid}/risk")
    assert risk_resp.status_code == 404


def test_get_worker_history_endpoint():
    worker_id = uuid.uuid4()
    payload = create_sample_worker_payload(worker_id, daily_amount=120.0)

    # Call calculate twice to create history
    client.post(f"/workers/{worker_id}/calculate", json=payload)
    client.post(f"/workers/{worker_id}/calculate", json=payload)

    history_resp = client.get(f"/workers/{worker_id}/history?limit=5")
    assert history_resp.status_code == 200
    records = history_resp.json()
    assert len(records) == 2
    assert records[0]["worker_id"] == str(worker_id)


def test_post_calculate_invalid_empty_history_returns_422():
    worker_id = uuid.uuid4()
    payload = {
        "worker_id": str(worker_id),
        "income_history": [],  # Empty list violates min_length=1
        "current_savings": 100.0,
    }
    resp = client.post(f"/workers/{worker_id}/calculate", json=payload)
    assert resp.status_code == 422
