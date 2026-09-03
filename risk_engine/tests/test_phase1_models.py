import uuid
import pytest
from pydantic import ValidationError
from fastapi.testclient import TestClient

from app.schemas.risk_score import (
    RiskTier,
    RiskScoreCreate,
    RiskScoreResponse,
    MetricDetail,
    MetricsBreakdown,
)
from app.models.risk_score import RiskScore
from app.database import Base, engine, SessionLocal
from app.main import app

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_test_db():
    # Setup test tables
    Base.metadata.create_all(bind=engine)
    yield
    # Teardown
    Base.metadata.drop_all(bind=engine)


# --------------------------------------------------------------------------
# 1. Pydantic Contract Validation Tests
# --------------------------------------------------------------------------

def test_pydantic_valid_risk_score():
    worker_uuid = uuid.uuid4()
    valid_payload = {
        "worker_id": worker_uuid,
        "stability_score": 85.5,
        "risk_tier": "Stable",
        "metrics_breakdown": {
            "income_consistency": {
                "name": "Income Consistency",
                "weight": 0.30,
                "raw_value": 0.15,
                "normalized_score": 85.0,
                "tooltip": "High consistency in daily earnings"
            }
        }
    }
    schema = RiskScoreCreate(**valid_payload)
    assert schema.worker_id == worker_uuid
    assert schema.stability_score == 85.5
    assert schema.risk_tier == RiskTier.STABLE


def test_pydantic_bounds_validation_negative():
    with pytest.raises(ValidationError) as exc_info:
        RiskScoreCreate(
            worker_id=uuid.uuid4(),
            stability_score=-0.1,
            risk_tier=RiskTier.CRITICAL,
            metrics_breakdown={}
        )
    assert "stability_score" in str(exc_info.value)


def test_pydantic_bounds_validation_over_100():
    with pytest.raises(ValidationError) as exc_info:
        RiskScoreCreate(
            worker_id=uuid.uuid4(),
            stability_score=100.01,
            risk_tier=RiskTier.STABLE,
            metrics_breakdown={}
        )
    assert "stability_score" in str(exc_info.value)


def test_pydantic_invalid_risk_tier_enum():
    with pytest.raises(ValidationError) as exc_info:
        RiskScoreCreate(
            worker_id=uuid.uuid4(),
            stability_score=50.0,
            risk_tier="Moderate",  # Invalid enum
            metrics_breakdown={}
        )
    assert "risk_tier" in str(exc_info.value)


def test_pydantic_invalid_uuid():
    with pytest.raises(ValidationError) as exc_info:
        RiskScoreCreate(
            worker_id="not-a-valid-uuid",
            stability_score=50.0,
            risk_tier=RiskTier.AT_RISK,
            metrics_breakdown={}
        )
    assert "worker_id" in str(exc_info.value)


# --------------------------------------------------------------------------
# 2. SQLAlchemy ORM Tests
# --------------------------------------------------------------------------

def test_sqlalchemy_risk_score_crud():
    db = SessionLocal()
    worker_id = uuid.uuid4()
    record_id = uuid.uuid4()

    breakdown = {
        "income_consistency": {"normalized_score": 80.0, "weight": 0.30},
        "work_frequency": {"normalized_score": 90.0, "weight": 0.25},
    }

    record = RiskScore(
        id=record_id,
        worker_id=worker_id,
        stability_score=78.5,
        risk_tier=RiskTier.STABLE,
        metrics_breakdown=breakdown,
    )

    db.add(record)
    db.commit()

    # Query back
    queried = db.query(RiskScore).filter(RiskScore.worker_id == worker_id).first()
    assert queried is not None
    assert queried.id == record_id
    assert queried.stability_score == 78.5
    assert queried.risk_tier == RiskTier.STABLE
    assert queried.metrics_breakdown["income_consistency"]["normalized_score"] == 80.0
    assert queried.created_at is not None
    db.close()


# --------------------------------------------------------------------------
# 3. FastAPI Endpoint Integration Tests
# --------------------------------------------------------------------------

def test_create_and_fetch_risk_score_endpoint():
    worker_id = str(uuid.uuid4())
    payload = {
        "worker_id": worker_id,
        "stability_score": 75.0,
        "risk_tier": "Stable",
        "metrics_breakdown": {
            "work_frequency": {
                "name": "Work Frequency",
                "weight": 0.25,
                "raw_value": 24,
                "normalized_score": 96.0,
                "tooltip": "24 active days out of 25 capacity"
            }
        }
    }

    # POST /workers/scores
    post_resp = client.post("/workers/scores", json=payload)
    assert post_resp.status_code == 201
    data = post_resp.json()
    assert data["worker_id"] == worker_id
    assert data["stability_score"] == 75.0
    assert data["risk_tier"] == "Stable"
    assert "id" in data
    assert "created_at" in data

    # GET /workers/{worker_id}/stability-score
    get_resp = client.get(f"/workers/{worker_id}/stability-score")
    assert get_resp.status_code == 200
    score_data = get_resp.json()
    assert score_data["worker_id"] == worker_id
    assert score_data["stability_score"] == 75.0
    assert score_data["risk_tier"] == "Stable"

    # GET /workers/{worker_id}/risk
    risk_resp = client.get(f"/workers/{worker_id}/risk")
    assert risk_resp.status_code == 200
    risk_data = risk_resp.json()
    assert risk_data["worker_id"] == worker_id
    assert risk_data["stability_score"] == 75.0
    assert risk_data["risk_tier"] == "Stable"


def test_endpoint_validation_rejects_out_of_bounds():
    payload = {
        "worker_id": str(uuid.uuid4()),
        "stability_score": 120.0,  # Out of bounds
        "risk_tier": "Stable",
        "metrics_breakdown": {}
    }
    resp = client.post("/workers/scores", json=payload)
    assert resp.status_code == 422  # Unprocessable Entity
