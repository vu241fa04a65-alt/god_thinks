from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.app.models.database import get_db
from backend.app.models.entities import RewardPoints, User
from backend.app.models.schemas import PointsSummary, LeaderboardEntry
from backend.app.controllers.auth import get_current_user

router = APIRouter(prefix="/gamification", tags=["Gamification"])

@router.get("/summary", response_model=PointsSummary)
def get_points_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    total = current_user.points

    badges = ["🌱 Eco Scout"]
    if total >= 50:
        badges.append("🌾 Plant Doctor")
    if total >= 150:
        badges.append("⭐ Community Champion")

    transactions = (
        db.query(RewardPoints)
        .filter(RewardPoints.user_id == current_user.id)
        .order_by(RewardPoints.created_at.desc())
        .limit(10)
        .all()
    )

    return PointsSummary(
        total_points=int(total),
        badges=badges,
        recent_transactions=[
            {"points": t.points, "reason": t.reason, "date": t.created_at.isoformat()}
            for t in transactions
        ]
    )

@router.get("/leaderboard", response_model=List[LeaderboardEntry])
def get_leaderboard(db: Session = Depends(get_db)):
    results = (
        db.query(User)
        .order_by(User.points.desc())
        .limit(10)
        .all()
    )

    return [
        LeaderboardEntry(
            username=u.username or u.name,
            name=u.name,
            total_points=u.points,
            badge="Master Scout" if u.points > 100 else "Active Farmer"
        )
        for u in results
    ]
