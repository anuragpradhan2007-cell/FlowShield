import uuid
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Text, Float, Numeric
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
