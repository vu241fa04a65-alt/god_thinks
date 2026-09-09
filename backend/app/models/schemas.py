from pydantic import BaseModel, EmailStr, ConfigDict
from typing import Optional, List
import datetime

# 1. User Schemas
class UserBase(BaseModel):
    name: str
    email: Optional[EmailStr] = None
    username: Optional[str] = None
    role: str = "farmer"  # farmer, expert, admin
    points: int = 0

class UserCreate(UserBase):
    password: str

class UserResponse(UserBase):
    id: int
    created_at: datetime.datetime
    model_config = ConfigDict(from_attributes=True)

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

# 2. Report Schemas
class ReportBase(BaseModel):
    crop_type: str
    image_url: Optional[str] = None
    location: str

class ReportCreate(ReportBase):
    pass

class ReportResponse(ReportBase):
    id: int
    user_id: int
    status: str
    created_at: datetime.datetime
    model_config = ConfigDict(from_attributes=True)

class ReportValidationUpdate(BaseModel):
    status: str  # verified, rejected
    expert_notes: Optional[str] = None

# 3. Disease Prediction Schemas
class DiseasePredictionBase(BaseModel):
    disease_name: str
    confidence: float
    explanation_overlay: Optional[str] = None

class DiseasePredictionCreate(DiseasePredictionBase):
    report_id: Optional[int] = None

class DiseasePredictionResponse(DiseasePredictionBase):
    id: int
    report_id: Optional[int] = None
    crop_name: Optional[str] = None
    created_at: datetime.datetime
    points_awarded: int = 20
    model_config = ConfigDict(from_attributes=True)

# 4. Reward Points Schemas
class RewardPointsBase(BaseModel):
    points: int
    reason: str

class RewardPointsCreate(RewardPointsBase):
    user_id: int

class RewardPointsResponse(RewardPointsBase):
    id: int
    user_id: int
    created_at: datetime.datetime
    model_config = ConfigDict(from_attributes=True)

# 5. Community Trend Schemas
class CommunityTrendBase(BaseModel):
    disease_name: str
    count: int = 1
    location: str

class CommunityTrendResponse(CommunityTrendBase):
    id: int
    updated_at: datetime.datetime
    model_config = ConfigDict(from_attributes=True)

# Gamification Summaries
class PointsSummary(BaseModel):
    total_points: int
    badges: List[str]
    recent_transactions: List[dict]

class LeaderboardEntry(BaseModel):
    username: str
    name: str
    total_points: int
    badge: str

# New REST API Request/Response Schemas
class LoginRequest(BaseModel):
    username: Optional[str] = None
    email: Optional[str] = None
    password: str

class RewardRequest(BaseModel):
    user_id: Optional[int] = None
    points: Optional[int] = None
    reason: str

class ClaimRewardRequest(BaseModel):
    reward_item_id: str
    user_id: Optional[int] = None

class ActionRewardRequest(BaseModel):
    action: str
    user_id: Optional[int] = None
    context: Optional[dict] = None

class ExpertValidateRequest(BaseModel):
    report_id: int
    decision: Optional[str] = None  # approve, reject
    status: Optional[str] = None    # approved, verified, rejected
    notes: Optional[str] = None
    expert_notes: Optional[str] = None
    corrected_disease: Optional[str] = None

class GeoFence(BaseModel):
    lat: float
    lng: float
    radius_km: float = 25.0

class SMSAlertRequest(BaseModel):
    phone_number: Optional[str] = None
    message: str
    lat: Optional[float] = None
    lng: Optional[float] = None
    lon: Optional[float] = None
    radius_km: Optional[float] = None
    disease: Optional[str] = None
    crop: Optional[str] = None
    geo_fence: Optional[GeoFence] = None

class TreatmentAdvisory(BaseModel):
    causes: str
    prevention: str
    treatment: str
