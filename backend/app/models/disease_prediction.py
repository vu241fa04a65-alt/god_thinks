import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship, synonym
from backend.app.models.base import Base

class DiseasePrediction(Base):
    __tablename__ = "disease_predictions"

    id = Column(Integer, primary_key=True, index=True)
    report_id = Column(Integer, ForeignKey("reports.id", ondelete="CASCADE"), nullable=True)
    disease_name = Column(String(150), nullable=False, index=True)
    confidence = Column(Float, nullable=False)
    overlay_path = Column(String(500), nullable=True)
    explanation_text = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    # Synonym for backward compatibility
    explanation_overlay = synonym("overlay_path")

    # Relationships
    report = relationship("Report", back_populates="predictions")

    def __repr__(self) -> str:
        return f"<DiseasePrediction(id={self.id}, disease='{self.disease_name}', confidence={self.confidence})>"
