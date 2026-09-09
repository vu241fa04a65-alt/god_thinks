import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from backend.app.models.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=True)
    username = Column(String(100), unique=True, index=True, nullable=True)
    hashed_password = Column(String(255), nullable=True)
    role = Column(String(50), default="farmer", nullable=False)  # farmer, expert, admin
    points = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    reports = relationship("Report", back_populates="user", cascade="all, delete-orphan")
    reward_records = relationship("RewardPoints", back_populates="user", cascade="all, delete-orphan")

class Report(Base):
    __tablename__ = "reports"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    crop_type = Column(String(100), nullable=False)
    image_url = Column(String(500), nullable=True)
    location = Column(String(255), nullable=False)
    status = Column(String(50), default="pending", nullable=False)  # pending, verified, rejected
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    user = relationship("User", back_populates="reports")
    predictions = relationship("DiseasePrediction", back_populates="report", cascade="all, delete-orphan")

class DiseasePrediction(Base):
    __tablename__ = "disease_predictions"

    id = Column(Integer, primary_key=True, index=True)
    report_id = Column(Integer, ForeignKey("reports.id"), nullable=True)
    disease_name = Column(String(150), nullable=False)
    confidence = Column(Float, nullable=False)
    explanation_overlay = Column(Text, nullable=True)  # Visual overlay data, diagnostic explanation, or bounding boxes
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    report = relationship("Report", back_populates="predictions")

class RewardPoints(Base):
    __tablename__ = "reward_points"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    points = Column(Integer, nullable=False)
    reason = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    user = relationship("User", back_populates="reward_records")

class CommunityTrend(Base):
    __tablename__ = "community_trends"

    id = Column(Integer, primary_key=True, index=True)
    disease_name = Column(String(150), nullable=False, index=True)
    count = Column(Integer, default=1, nullable=False)
    location = Column(String(255), nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
