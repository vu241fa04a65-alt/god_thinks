from typing import Optional, Any
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=100, description="Full name of user")
    email: Optional[str] = Field(None, description="User email address")
    phone: Optional[str] = Field(None, description="Contact phone number with country code")
    username: Optional[str] = Field(None, min_length=3, max_length=50, description="Unique login handle")
    password: str = Field(..., min_length=6, description="User password")
    role: Optional[str] = Field("farmer", description="Role: farmer, expert, or admin")
    preferred_language: Optional[str] = Field("en", description="Preferred ISO language code")
    points: Optional[int] = Field(0, description="Initial gamification reward points")


# Alias for backward compatibility with UserCreate
UserCreate = RegisterRequest


class LoginRequest(BaseModel):
    username: Optional[str] = Field(None, description="Username or email handle")
    email: Optional[str] = Field(None, description="Direct email login")
    password: str = Field(..., min_length=1, description="Password credential")


class RefreshTokenRequest(BaseModel):
    refresh_token: str = Field(..., description="Valid JWT refresh token")


class TokenData(BaseModel):
    username: Optional[str] = None
    role: Optional[str] = None
    token_type: Optional[str] = None


class UserSummary(BaseModel):
    id: int
    name: str
    username: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    role: str
    points: int


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserSummary


class UserResponse(BaseModel):
    id: int
    name: str
    username: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    role: str
    points: int
    preferred_language: Optional[str] = "en"
    created_at: Optional[Any] = None


class LogoutResponse(BaseModel):
    message: str
