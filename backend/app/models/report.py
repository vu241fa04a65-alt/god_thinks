import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship, synonym
from backend.app.models.base import Base

class Report(Base):
    __tablename__ = "reports"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    crop_type = Column(String(100), nullable=False)
    image_path = Column(String(500), nullable=True)
    location_lat = Column(Float, nullable=True)
    location_lng = Column(Float, nullable=True)
    location = Column(String(255), nullable=True)  # Textual location representation / backward compatibility
    submitted_at = Column(DateTime, default=datetime.datetime.utcnow, index=True, nullable=False)
    status = Column(String(50), default="pending", nullable=False)  # pending, validated, rejected
    notes = Column(Text, nullable=True)

    # Synonyms for SQL query and attribute access backward compatibility
    created_at = synonym("submitted_at")
    image_url = synonym("image_path")

    # Relationships
    user = relationship("User", back_populates="reports")
    predictions = relationship("DiseasePrediction", back_populates="report", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Report(id={self.id}, user_id={self.user_id}, crop_type='{self.crop_type}', status='{self.status}')>"
