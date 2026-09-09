from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.models.entities import RewardPoints, User
from backend.app.models.schemas import RewardRequest
from backend.app.routes.auth import get_current_user, get_optional_current_user
from backend.app.routes import success_envelope, error_envelope

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
        raise HTTPException(status_code=400, detail="User ID is required or user must be authenticated")

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

    data = {
        "user_id": user.id,
        "user_name": user.name,
        "points_added": reward_in.points,
        "total_points": user.points,
        "reason": reward_in.reason,
        "reward_id": reward.id
    }
    return success_envelope(data=data)

@router.get("/leaderboard")
def get_leaderboard(
    limit: int = 10,
    db: Session = Depends(get_db)
):
    users = db.query(User).order_by(User.points.desc()).limit(limit).all()

    entries = []
    for rank, u in enumerate(users, start=1):
        entries.append({
            "rank": rank,
            "user_id": u.id,
            "name": u.name,
            "username": u.username or u.name,
            "total_points": u.points,
            "badge": "Master Agronomist" if u.points >= 150 else ("Plant Doctor" if u.points >= 50 else "Eco Scout")
        })

    data = {
        "leaderboard": entries,
        "total_participants": len(entries)
    }
    return success_envelope(data=data)

@router.get("/summary")
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

    data = {
        "total_points": int(total),
        "badges": badges,
        "recent_transactions": [
            {"points": t.points, "reason": t.reason, "date": t.created_at.isoformat() if t.created_at else None}
            for t in transactions
        ]
    }
    return success_envelope(data=data)
