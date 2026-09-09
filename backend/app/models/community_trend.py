import datetime
from sqlalchemy import Column, Integer, String, DateTime, JSON
from sqlalchemy.orm import synonym
from backend.app.models.base import Base

class CommunityTrend(Base):
    __tablename__ = "community_trends"

    id = Column(Integer, primary_key=True, index=True)
    disease_name = Column(String(150), nullable=False, index=True)
    location_geojson = Column(JSON, nullable=True)
    location = Column(String(255), nullable=True, index=True)  # Backward-compatible textual location
    count = Column(Integer, default=1, nullable=False)
    last_seen = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    # Synonym for backward compatibility
    updated_at = synonym("last_seen")

    def __repr__(self) -> str:
        return f"<CommunityTrend(id={self.id}, disease='{self.disease_name}', count={self.count})>"
