import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    Column,
    Float,
    DateTime,
    Enum as SAEnum,
    CheckConstraint,
    Index,
    JSON,
    func,
)
from sqlalchemy.types import Uuid
from sqlalchemy.dialects.postgresql import JSONB

from app.database import Base
from app.schemas.risk_score import RiskTier


class RiskScore(Base):
    """
    SQLAlchemy ORM Model for the 'risk_scores' table.
    Stores computed stability scores, risk tiers, and explainability breakdowns.
    Compatible with Supabase PostgreSQL and local SQLite.
    """
    __tablename__ = "risk_scores"

    id = Column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
        doc="Unique identifier for the risk score record"
    )

    worker_id = Column(
        Uuid(as_uuid=True),
        nullable=False,
        index=True,
        doc="Anonymous UUID reference linked to Member 1's worker schema"
    )

    stability_score = Column(
        Float,
        nullable=False,
        doc="Worker stability score strictly bounded between 0.0 and 100.0"
    )

    risk_tier = Column(
        SAEnum(
            RiskTier,
            name="risk_tier_enum",
            values_callable=lambda obj: [e.value for e in obj],
            native_enum=True,
        ),
        nullable=False,
        index=True,
        doc="Risk classification tier: 'Stable', 'At Risk', or 'Critical'"
    )

    # Use JSONB on PostgreSQL / Supabase, standard JSON on SQLite
    metrics_breakdown = Column(
        JSON().with_variant(JSONB, "postgresql"),
        nullable=False,
        default=dict,
        doc="JSON/JSONB field storing intermediate feature values and weights"
    )

    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        default=lambda: datetime.now(timezone.utc),
        index=True,
        doc="ISO-8601 timestamp of score computation"
    )

    __table_args__ = (
        CheckConstraint(
            "stability_score >= 0.0 AND stability_score <= 100.0",
            name="chk_stability_score_bounds",
        ),
        Index("idx_worker_created_at", "worker_id", "created_at"),
    )

    def __repr__(self) -> str:
        return (
            f"<RiskScore(id={self.id}, worker_id={self.worker_id}, "
            f"score={self.stability_score}, tier='{self.risk_tier}')>"
        )
