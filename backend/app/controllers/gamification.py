from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

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
    total = db.query(func.coalesce(func.sum(RewardPoints.points), 0)).filter(
        RewardPoints.user_id == current_user.id
    ).scalar()

    badges = ["🌱 Eco Scout"]
    if total >= 50:
        badges.append("🌾 Plant Doctor")
    if total >= 150:
        badges.append("⭐ Community Champion")

    transactions = (
        db.query(RewardPoints)
        .filter(RewardPoints.user_id == current_user.id)
        .order_by(RewardPoints.created_at.desc())
        .limit(5)
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
        db.query(User.username, func.coalesce(func.sum(RewardPoints.points), 0).label("points"))
        .outerjoin(RewardPoints, User.id == RewardPoints.user_id)
        .group_by(User.id)
        .order_by(func.coalesce(func.sum(RewardPoints.points), 0).desc())
        .limit(10)
        .all()
    )

    return [
        LeaderboardEntry(
            username=r.username,
            total_points=int(r.points),
            badge="Master Scout" if r.points > 100 else "Active Farmer"
        )
        for r in results
    ]
