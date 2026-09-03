import uuid
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Text, Float, Numeric, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import datetime

from database import Base

def generate_uuid():
    return str(uuid.uuid4())

class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=generate_uuid, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(Text, nullable=False)
    role = Column(String, default="WORKER", nullable=False)
    is_active = Column(Boolean, default=True)
    ai_consent = Column(Boolean, default=True)
    consent_version = Column(String, default="v1")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    worker = relationship("Worker", back_populates="user", uselist=False)

class Worker(Base):
    __tablename__ = "workers"

    id = Column(String, primary_key=True, default=generate_uuid, index=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False, unique=True)
    occupation = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    user = relationship("User", back_populates="worker")
    earnings = relationship("Earning", back_populates="worker")
    transactions = relationship("Transaction", back_populates="worker")
    emergency_pot = relationship("EmergencyPot", back_populates="worker", uselist=False)
    credit_assessments = relationship("CreditAssessment", back_populates="worker")
    notifications = relationship("Notification", back_populates="worker")

class Earning(Base):
    __tablename__ = "earnings"

    id = Column(String, primary_key=True, default=generate_uuid, index=True)
    worker_id = Column(String, ForeignKey("workers.id"), nullable=False, index=True)
    amount = Column(Numeric(10, 2), nullable=False)
    currency = Column(String, default="USD")
    period_start = Column(DateTime, nullable=False)
    period_end = Column(DateTime, nullable=False)
    is_missing_data = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    worker = relationship("Worker", back_populates="earnings")

class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(String, primary_key=True, default=generate_uuid, index=True)
    worker_id = Column(String, ForeignKey("workers.id"), nullable=False, index=True)
    amount = Column(Numeric(10, 2), nullable=False)
    transaction_type = Column(String, nullable=False)
    status = Column(String, nullable=False)
    transaction_time = Column(DateTime, default=datetime.datetime.utcnow)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    worker = relationship("Worker", back_populates="transactions")

class EmergencyPot(Base):
    __tablename__ = "emergency_pots"

    id = Column(String, primary_key=True, default=generate_uuid, index=True)
    worker_id = Column(String, ForeignKey("workers.id"), unique=True, nullable=False)
    balance = Column(Numeric(10, 2), nullable=False, default=0.0)
    total_contributed = Column(Numeric(10, 2), nullable=False, default=0.0)
    total_used = Column(Numeric(10, 2), nullable=False, default=0.0)
    period_contributed = Column(Numeric(10, 2), nullable=False, default=0.0)
    period_start = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)

    worker = relationship("Worker", back_populates="emergency_pot")

class CreditAssessment(Base):
    __tablename__ = "credit_assessments"

    id = Column(String, primary_key=True, default=generate_uuid, index=True)
    worker_id = Column(String, ForeignKey("workers.id"), nullable=False)
    stability_score = Column(Float, nullable=False)
    risk_level = Column(String, nullable=False)
    eligible = Column(Boolean, default=False)
    credit_limit = Column(Numeric(10, 2), default=0.0)
    reason = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    worker = relationship("Worker", back_populates="credit_assessments")

class Notification(Base):
    __tablename__ = "notifications"

    id = Column(String, primary_key=True, default=generate_uuid, index=True)
    worker_id = Column(String, ForeignKey("workers.id"), nullable=False)
    type = Column(String, nullable=False)
    message = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    worker = relationship("Worker", back_populates="notifications")

class Partner(Base):
    __tablename__ = "partners"
    id = Column(String, primary_key=True, default=generate_uuid, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    api_key = Column(String, unique=True, index=True, nullable=False)
    webhook_url = Column(Text, nullable=True)
    status = Column(String, default="active")
    commission_rate = Column(Numeric(5, 2), default=10.00)
    total_earnings = Column(Numeric(15, 2), default=0.00)
    total_workers = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    api_keys = relationship("PartnerAPIKey", back_populates="partner")
    sdk_tokens = relationship("SDKToken", back_populates="partner")
    enrolled_workers = relationship("PartnerWorker", back_populates="partner")
    commissions = relationship("PartnerCommission", back_populates="partner")

class PartnerAPIKey(Base):
    __tablename__ = "partner_api_keys"
    id = Column(String, primary_key=True, default=generate_uuid, index=True)
    partner_id = Column(String, ForeignKey("partners.id", ondelete="CASCADE"), nullable=False, index=True)
    key_value = Column(String, unique=True, nullable=False)
    secret_hash = Column(String, nullable=False)
    name = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    rotated_at = Column(DateTime, nullable=True)

    partner = relationship("Partner", back_populates="api_keys")

class SDKToken(Base):
    __tablename__ = "sdk_tokens"
    id = Column(String, primary_key=True, default=generate_uuid, index=True)
    worker_id = Column(String, ForeignKey("workers.id", ondelete="CASCADE"), nullable=False, index=True)
    partner_id = Column(String, ForeignKey("partners.id", ondelete="CASCADE"), nullable=False, index=True)
    token = Column(String(512), unique=True, nullable=False)
    token_hash = Column(String, nullable=True)
    expires_at = Column(DateTime, nullable=False)
    used_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    worker = relationship("Worker")
    partner = relationship("Partner", back_populates="sdk_tokens")

class PartnerWorker(Base):
    __tablename__ = "partner_workers"
    id = Column(String, primary_key=True, default=generate_uuid, index=True)
    partner_id = Column(String, ForeignKey("partners.id", ondelete="CASCADE"), nullable=False, index=True)
    worker_id = Column(String, ForeignKey("workers.id", ondelete="CASCADE"), nullable=False, index=True)
    status = Column(String, default="active")
    enrolled_at = Column(DateTime, default=datetime.datetime.utcnow)

    partner = relationship("Partner", back_populates="enrolled_workers")
    worker = relationship("Worker")

class PartnerCommission(Base):
    __tablename__ = "partner_commissions"
    id = Column(String, primary_key=True, default=generate_uuid, index=True)
    partner_id = Column(String, ForeignKey("partners.id", ondelete="CASCADE"), nullable=False, index=True)
    worker_id = Column(String, ForeignKey("workers.id", ondelete="CASCADE"), nullable=False, index=True)
    transaction_id = Column(String, nullable=True)
    amount = Column(Numeric(15, 2), nullable=False)
    commission_rate = Column(Numeric(5, 2), nullable=True)
    earned_at = Column(DateTime, default=datetime.datetime.utcnow)
    paid_at = Column(DateTime, nullable=True)

    partner = relationship("Partner", back_populates="commissions")
    worker = relationship("Worker")
