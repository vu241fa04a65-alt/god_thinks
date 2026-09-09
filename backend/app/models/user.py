import datetime
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Float
from sqlalchemy.orm import relationship
from backend.app.models.base import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=True)
    username = Column(String(100), unique=True, index=True, nullable=True)
    phone = Column(String(50), nullable=True)
    role = Column(String(50), default="farmer", nullable=False)  # farmer, expert, admin
    hashed_password = Column(String(255), nullable=True)
    preferred_language = Column(String(50), default="en", nullable=False)
    points = Column(Integer, default=0, nullable=False, index=True)
    sms_opt_in = Column(Boolean, default=True, nullable=False)
    location = Column(String(255), nullable=True)
    location_lat = Column(Float, nullable=True)
    location_lng = Column(Float, nullable=True)
    geofence_radius_km = Column(Float, default=25.0, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    # Relationships with cascade delete
    reports = relationship("Report", back_populates="user", cascade="all, delete-orphan")
    rewards = relationship("Reward", back_populates="user", cascade="all, delete-orphan", foreign_keys="Reward.user_id")
    # Backward compatibility alias for reward records
    reward_records = relationship("Reward", cascade="all, delete-orphan", viewonly=True, foreign_keys="Reward.user_id")

    def __repr__(self) -> str:
        return f"<User(id={self.id}, name='{self.name}', role='{self.role}', points={self.points})>"
