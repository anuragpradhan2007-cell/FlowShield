from sqlalchemy import Column, Integer, Float, String, Boolean
from database import Base


class EmergencyPot(Base):
    __tablename__ = "emergency_pots"

    id = Column(Integer, primary_key=True, index=True)
    worker_id = Column(String, unique=True, nullable=False)

    balance = Column(Float, default=0.0)
    total_contributed = Column(Float, default=0.0)
    total_used = Column(Float, default=0.0)


class CreditAssessment(Base):
    __tablename__ = "credit_assessments"

    id = Column(Integer, primary_key=True, index=True)
    worker_id = Column(String, nullable=False)

    stability_score = Column(Float, nullable=False)
    risk_level = Column(String, nullable=False)

    eligible = Column(Boolean, default=False)
    credit_limit = Column(Float, default=0.0)

    reason = Column(String, nullable=True)


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    worker_id = Column(String, nullable=False)

    type = Column(String, nullable=False)
    message = Column(String, nullable=False)