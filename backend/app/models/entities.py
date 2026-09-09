# Re-export models from their modular files for backward compatibility
from backend.app.models.base import Base
from backend.app.models.user import User
from backend.app.models.report import Report
from backend.app.models.disease_prediction import DiseasePrediction
from backend.app.models.reward import Reward, RewardPoints
from backend.app.models.community_trend import CommunityTrend

__all__ = [
    "Base",
    "User",
    "Report",
    "DiseasePrediction",
    "Reward",
    "RewardPoints",
    "CommunityTrend"
]
