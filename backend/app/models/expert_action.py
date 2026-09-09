import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from backend.app.models.base import Base

class ExpertAction(Base):
    __tablename__ = "expert_actions"

    id = Column(Integer, primary_key=True, index=True)
    expert_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    report_id = Column(Integer, ForeignKey("reports.id", ondelete="CASCADE"), nullable=False, index=True)
    decision = Column(String(50), nullable=False)  # approved, rejected, validated
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, index=True)

    # Relationships
    expert = relationship("User", foreign_keys=[expert_id])
    report = relationship("Report", foreign_keys=[report_id])

    def __repr__(self) -> str:
        return f"<ExpertAction(id={self.id}, expert_id={self.expert_id}, report_id={self.report_id}, decision='{self.decision}')>"
