import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from backend.app.models.base import Base

class Reward(Base):
    __tablename__ = "reward_points"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    points = Column(Integer, nullable=False)
    reason = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="rewards", foreign_keys=[user_id])

    def __repr__(self) -> str:
        return f"<Reward(id={self.id}, user_id={self.user_id}, points={self.points}, reason='{self.reason}')>"

# Alias for backward compatibility
RewardPoints = Reward

__all__ = ["Reward", "RewardPoints"]
