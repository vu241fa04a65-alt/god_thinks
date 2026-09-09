from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.app.models.database import get_db
from backend.app.models.entities import RewardPoints, User
from backend.app.models.schemas import PointsSummary, LeaderboardEntry, RewardRequest
from backend.app.controllers.auth import get_current_user, get_optional_current_user

router = APIRouter(prefix="/gamification", tags=["Gamification"])

@router.post("/reward")
def add_reward_points(
    reward_in: RewardRequest,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
):
    if reward_in.points <= 0:
        raise HTTPException(status_code=400, detail="Points value must be greater than zero")

    target_user_id = reward_in.user_id or (current_user.id if current_user else None)
    if not target_user_id:
        raise HTTPException(status_code=400, detail="User ID is required or request must include authorization token")

    user = db.query(User).filter(User.id == target_user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail=f"User with id {target_user_id} not found")

    reward = RewardPoints(
        user_id=user.id,
        points=reward_in.points,
        reason=reward_in.reason
    )
    db.add(reward)
    user.points += reward_in.points
    db.commit()
    db.refresh(reward)

    return {
        "status": "success",
        "message": f"Successfully awarded {reward_in.points} points to {user.name}",
        "user_id": user.id,
        "points_added": reward_in.points,
        "total_points": user.points,
        "reason": reward_in.reason,
        "reward_id": reward.id
    }

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
