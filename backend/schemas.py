from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime

class WorkerBase(BaseModel):
    occupation: str

class WorkerCreate(WorkerBase):
    pass

class WorkerResponse(WorkerBase):
    id: str
    user_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class UserBase(BaseModel):
    email: EmailStr

class UserCreate(UserBase):
    password: str = Field(..., min_length=6)
    occupation: str

class UserLogin(UserBase):
    password: str

class UserResponse(UserBase):
    id: str
    role: str
    
    class Config:
        from_attributes = True

class UserProfileResponse(UserResponse):
    ai_consent: bool
    consent_version: str
    worker: Optional[WorkerResponse] = None

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    user_id: Optional[str] = None
    role: Optional[str] = None
    ai_consent_version: Optional[str] = None
    worker_id: Optional[str] = None
