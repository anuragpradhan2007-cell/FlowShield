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
    sdk_tokens = relationship("SDKToken", back_populates="worker", cascade="all, delete-orphan")
    partner_enrollments = relationship("PartnerWorker", back_populates="worker", cascade="all, delete-orphan")

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
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    
    # API Management
    api_key = Column(String(255), unique=True, nullable=False, index=True)
    webhook_url = Column(String(500))
    
    # Business Metrics
    commission_rate = Column(Float, default=10.0)  # Percentage
    total_earnings = Column(Float, default=0.0)
    total_workers = Column(Integer, default=0)
    
    # Status
    status = Column(String(50), default="active")  # active, suspended, inactive
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    
    # Relationships
    api_keys = relationship("PartnerAPIKey", back_populates="partner", cascade="all, delete-orphan")
    sdk_tokens = relationship("SDKToken", back_populates="partner", cascade="all, delete-orphan")
    workers = relationship("PartnerWorker", back_populates="partner", cascade="all, delete-orphan")
    commissions = relationship("PartnerCommission", back_populates="partner", cascade="all, delete-orphan")


class PartnerAPIKey(Base):
    __tablename__ = "partner_api_keys"

    id = Column(String, primary_key=True, default=generate_uuid, index=True)
    partner_id = Column(String, ForeignKey("partners.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Key Management
    key_value = Column(String(255), unique=True, nullable=False)
    secret_hash = Column(String(255), nullable=False)
    name = Column(String(100))
    
    # Status
    is_active = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    rotated_at = Column(DateTime)
    
    # Relationships
    partner = relationship("Partner", back_populates="api_keys")


class SDKToken(Base):
    __tablename__ = "sdk_tokens"

    id = Column(String, primary_key=True, default=generate_uuid, index=True)
    worker_id = Column(String, ForeignKey("workers.id", ondelete="CASCADE"), nullable=False, index=True)
    partner_id = Column(String, ForeignKey("partners.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Token Data
    token = Column(String(512), unique=True, nullable=False)
    token_hash = Column(String(255), unique=True)
    
    # Lifecycle
    expires_at = Column(DateTime, nullable=False)
    used_at = Column(DateTime)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    # Relationships
    worker = relationship("Worker", back_populates="sdk_tokens")
    partner = relationship("Partner", back_populates="sdk_tokens")


class PartnerWorker(Base):
    __tablename__ = "partner_workers"

    id = Column(String, primary_key=True, default=generate_uuid, index=True)
    partner_id = Column(String, ForeignKey("partners.id", ondelete="CASCADE"), nullable=False, index=True)
    worker_id = Column(String, ForeignKey("workers.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Status
    status = Column(String(50), default="active")  # active, inactive
    
    # Timestamps
    enrolled_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    # Relationships
    partner = relationship("Partner", back_populates="workers")
    worker = relationship("Worker", back_populates="partner_enrollments")


class PartnerCommission(Base):
    __tablename__ = "partner_commissions"

    id = Column(String, primary_key=True, default=generate_uuid, index=True)
    partner_id = Column(String, ForeignKey("partners.id", ondelete="CASCADE"), nullable=False, index=True)
    worker_id = Column(String, ForeignKey("workers.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Transaction Data
    transaction_id = Column(String)
    amount = Column(Float, nullable=False)
    commission_rate = Column(Float)
    
    # Lifecycle
    earned_at = Column(DateTime, default=datetime.datetime.utcnow)
    paid_at = Column(DateTime)
    
    # Relationships
    partner = relationship("Partner", back_populates="commissions")
