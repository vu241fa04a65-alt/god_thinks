from pydantic import BaseModel, EmailStr
from typing import Optional, List
import datetime

# User Schemas
class UserBase(BaseModel):
    email: EmailStr
    username: str
    phone_number: Optional[str] = None
    role: Optional[str] = "farmer"

class UserCreate(UserBase):
    password: str

class UserResponse(UserBase):
    id: int
    created_at: datetime.datetime
    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

# Report Schemas
class ReportCreate(BaseModel):
    title: str
    crop_name: str
    description: Optional[str] = None
    location_lat: Optional[float] = None
    location_lon: Optional[float] = None

class ReportResponse(ReportCreate):
    id: int
    user_id: int
    status: str
    expert_notes: Optional[str] = None
    created_at: datetime.datetime
    class Config:
        from_attributes = True

class ReportValidationUpdate(BaseModel):
    status: str  # verified, rejected
    expert_notes: Optional[str] = None

# Disease Prediction Schemas
class DiseasePredictionResponse(BaseModel):
    id: Optional[int] = None
    crop_name: str
    disease_name: str
    confidence: float
    severity: str
    causes: str
    prevention: str
    treatment: str
    points_awarded: int = 20

# Gamification Schemas
class PointsSummary(BaseModel):
    total_points: int
    badges: List[str]
    recent_transactions: List[dict]

class LeaderboardEntry(BaseModel):
    username: str
    total_points: int
    badge: str
