from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.models.entities import User
from backend.app.models.schemas import (
    RewardRequest,
    ClaimRewardRequest,
    ActionRewardRequest
)
from backend.app.routes.auth import get_current_user, get_optional_current_user
from backend.app.routes import success_envelope, error_envelope
from backend.app.services.gamification import (
    award_points,
    get_leaderboard as fetch_leaderboard,
    get_user_points_summary,
    get_claimable_rewards,
    claim_reward as redeem_reward_service,
    load_rewards_config
)

router = APIRouter(prefix="/gamification", tags=["Gamification & Rewards"])


@router.post("/reward")
def add_reward_points(
    reward_in: RewardRequest,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
):
    """
    Award points to a user for field scouting or disease reporting.
    Supports explicit points or rule-based deduction from rewards.yaml.
    """
    if reward_in.points is not None and reward_in.points <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Points value must be greater than zero"
        )

    target_user_id = reward_in.user_id or (current_user.id if current_user else None)
    if not target_user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User ID is required or user must be authenticated"
        )

    try:
        result = award_points(
            user_id=target_user_id,
            reason=reward_in.reason,
            points=reward_in.points,
            db=db
        )
        return success_envelope(data=result)
    except ValueError as e:
        detail = str(e)
        status_code = status.HTTP_404_NOT_FOUND if "not found" in detail.lower() else status.HTTP_400_BAD_REQUEST
        raise HTTPException(status_code=status_code, detail=detail)


@router.post("/action")
def reward_community_action(
    action_in: ActionRewardRequest,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
):
    """
    Award rule-based points for standard community actions:
    - 'first_disease_in_village': +10 points
    - 'validated_report': +5 points
    - 'share_advisory': +2 points
    - 'routine_scout': +1 point
    """
    target_user_id = action_in.user_id or (current_user.id if current_user else None)
    if not target_user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User ID is required or user must be authenticated"
        )

    try:
        result = award_points(
            user_id=target_user_id,
            reason=action_in.action,
            points=None,
            db=db
        )
        return success_envelope(data=result)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/leaderboard")
def get_leaderboard_endpoint(
    limit: int = Query(50, ge=1, le=100, description="Max leaderboard entries (default 50)"),
    db: Session = Depends(get_db)
):
    """
    Get ranked community leaderboard of top agronomists and scouts.
    Defaults to top 50 participants.
    """
    entries = fetch_leaderboard(limit=limit, db=db)
    data = {
        "leaderboard": entries,
        "total_participants": len(entries),
        "limit": limit
    }
    return success_envelope(data=data)


@router.get("/points")
@router.get("/summary")
def get_points_endpoint(
    user_id: Optional[int] = Query(None, description="Optional user ID to inspect"),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
):
    """
    View user's current points balance, rank badge, and reward transaction ledger.
    """
    target_id = user_id or (current_user.id if current_user else None)
    if not target_id:
        # Fallback to first active user if in open dev/demo mode
        first_user = db.query(User).first()
        if first_user:
            target_id = first_user.id
        else:
            raise HTTPException(status_code=400, detail="Authentication required or user_id must be provided")

    try:
        summary = get_user_points_summary(target_id, db=db)
        return success_envelope(data=summary)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/catalog")
def get_rewards_catalog():
    """
    View all claimable prizes and vouchers in the gamification reward catalog.
    """
    catalog = get_claimable_rewards()
    config = load_rewards_config()
    return success_envelope(data={
        "catalog": catalog,
        "rules": config.get("reward_rules", {}),
        "tiers": config.get("tiers_and_badges", [])
    })


@router.post("/claim")
def claim_reward_endpoint(
    claim_in: ClaimRewardRequest,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
):
    """
    Redeem points for catalog items (e.g. bio-fertilizer vouchers, certified seed packs).
    Points are atomically deducted and a unique claim voucher is issued.
    """
    target_user_id = claim_in.user_id or (current_user.id if current_user else None)
    if not target_user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User ID is required or user must be authenticated to claim rewards"
        )

    try:
        redemption = redeem_reward_service(
            user_id=target_user_id,
            reward_item_id=claim_in.reward_item_id,
            db=db
        )
        return success_envelope(data=redemption)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
