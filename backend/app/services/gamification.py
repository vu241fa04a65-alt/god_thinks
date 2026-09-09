import os
import yaml
import uuid
import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session

from backend.app.database import SessionLocal
from backend.app.models.entities import User, Reward
from backend.app.utils.logger import logger

CONFIG_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "config", "rewards.yaml"))

DEFAULT_RULES = {
    "first_disease_in_village": {
        "name": "First Disease Report in Village",
        "points": 10,
        "description": "First report of a crop disease in a village or local sector"
    },
    "validated_report": {
        "name": "Expert Validated Report",
        "points": 5,
        "description": "Crop scout report validated and confirmed by an agronomist"
    },
    "share_advisory": {
        "name": "Share Treatment Advisory",
        "points": 2,
        "description": "Sharing pest/disease prevention or IPM advisory with fellow farmers"
    },
    "routine_scout": {
        "name": "Routine Crop Scout",
        "points": 1,
        "description": "Submitting periodic field health observation"
    }
}

DEFAULT_TIERS = [
    {"id": "eco_scout", "name": "Eco Scout", "min_points": 0, "badge": "🌱 Eco Scout"},
    {"id": "plant_doctor", "name": "Plant Doctor", "min_points": 50, "badge": "🌾 Plant Doctor"},
    {"id": "master_agronomist", "name": "Master Agronomist", "min_points": 150, "badge": "⭐ Master Agronomist"},
    {"id": "crop_guardian", "name": "Village Crop Guardian", "min_points": 300, "badge": "🏆 Village Crop Guardian"}
]

DEFAULT_CATALOG = [
    {
        "id": "voucher_fertilizer_10",
        "name": "Bio-Fertilizer 10% Discount Voucher",
        "category": "Agro Inputs",
        "cost_points": 30,
        "description": "Redeemable at certified agricultural co-ops for bio-fertilizers."
    },
    {
        "id": "voucher_seeds_pack",
        "name": "Certified Disease-Resistant Seeds Pack",
        "category": "Seeds",
        "cost_points": 60,
        "description": "1kg certified hybrid disease-resistant seeds."
    },
    {
        "id": "ipm_pheromone_kit",
        "name": "IPM Pheromone Pest Trap Kit",
        "category": "Crop Protection",
        "cost_points": 100,
        "description": "Set of 5 field pheromone traps for pest monitoring."
    },
    {
        "id": "soil_test_voucher",
        "name": "Free Laboratory Soil Health Test",
        "category": "Services",
        "cost_points": 150,
        "description": "Comprehensive 12-parameter soil fertility analysis."
    }
]


def load_rewards_config() -> Dict[str, Any]:
    """Load rewards configuration from rewards.yaml with resilient defaults."""
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
                return {
                    "reward_rules": data.get("reward_rules", DEFAULT_RULES),
                    "tiers_and_badges": data.get("tiers_and_badges", DEFAULT_TIERS),
                    "claimable_rewards": data.get("claimable_rewards", DEFAULT_CATALOG)
                }
        except Exception as e:
            logger.warning(f"Failed to read rewards config from {CONFIG_PATH}: {e}")

    return {
        "reward_rules": DEFAULT_RULES,
        "tiers_and_badges": DEFAULT_TIERS,
        "claimable_rewards": DEFAULT_CATALOG
    }


def get_badge_for_points(points: int) -> Dict[str, Any]:
    """Determine user's active tier, badge, and progress to next level."""
    config = load_rewards_config()
    tiers = sorted(config.get("tiers_and_badges", DEFAULT_TIERS), key=lambda x: x["min_points"])
    active_tier = tiers[0]
    next_tier = None

    for i, tier in enumerate(tiers):
        if points >= tier["min_points"]:
            active_tier = tier
            next_tier = tiers[i + 1] if i + 1 < len(tiers) else None
        else:
            break

    points_to_next = max(0, next_tier["min_points"] - points) if next_tier else 0
    return {
        "tier_id": active_tier["id"],
        "name": active_tier["name"],
        "badge": active_tier["badge"],
        "next_tier": next_tier["name"] if next_tier else None,
        "points_to_next": points_to_next
    }


def award_points(
    user_id: int,
    reason: str,
    points: Optional[int] = None,
    db: Optional[Session] = None
) -> Dict[str, Any]:
    """
    Atomically persist a Reward record and update user.points:
    - Resolves points from rewards.yaml rules if not explicitly passed.
    - Ensures transactional integrity.
    """
    config = load_rewards_config()
    rules = config.get("reward_rules", DEFAULT_RULES)

    # 1. Resolve rule points and formatted reason if key is supplied
    resolved_points = points
    reason_label = reason

    if reason in rules:
        rule_meta = rules[reason]
        if resolved_points is None:
            resolved_points = int(rule_meta.get("points", 1))
        reason_label = rule_meta.get("name", reason)
    elif resolved_points is None:
        # Check if reason mentions standard rules
        lower_reason = reason.lower()
        if "first" in lower_reason and ("village" in lower_reason or "disease" in lower_reason):
            resolved_points = rules.get("first_disease_in_village", {}).get("points", 10)
        elif "validated" in lower_reason or "expert" in lower_reason:
            resolved_points = rules.get("validated_report", {}).get("points", 5)
        elif "advisory" in lower_reason or "share" in lower_reason:
            resolved_points = rules.get("share_advisory", {}).get("points", 2)
        else:
            resolved_points = 1

    if resolved_points <= 0:
        raise ValueError("Points value must be greater than zero")

    # 2. Atomic Database Update
    def _execute_award(session: Session) -> Dict[str, Any]:
        # Lock user record for atomic point increment
        try:
            user = session.query(User).filter(User.id == user_id).with_for_update().first()
        except Exception:
            # Fallback if with_for_update not supported by dialect (e.g. SQLite memory)
            user = session.query(User).filter(User.id == user_id).first()

        if not user:
            raise ValueError(f"User with id {user_id} not found")

        reward = Reward(
            user_id=user.id,
            points=resolved_points,
            reason=reason_label
        )
        session.add(reward)
        user.points = (user.points or 0) + resolved_points
        session.commit()
        session.refresh(user)
        session.refresh(reward)

        badge_info = get_badge_for_points(user.points)
        return {
            "reward_id": reward.id,
            "user_id": user.id,
            "user_name": user.name,
            "points_added": resolved_points,
            "total_points": user.points,
            "reason": reason_label,
            "badge": badge_info["badge"],
            "tier": badge_info["name"],
            "created_at": reward.created_at.isoformat() if reward.created_at else None
        }

    if db is not None:
        return _execute_award(db)
    else:
        with SessionLocal() as session:
            return _execute_award(session)


def get_leaderboard(limit: int = 50, db: Optional[Session] = None) -> List[Dict[str, Any]]:
    """Return ranked list of top community scouts with badges and scores."""
    def _fetch_leaderboard(session: Session) -> List[Dict[str, Any]]:
        users = (
            session.query(User)
            .order_by(User.points.desc(), User.id.asc())
            .limit(limit)
            .all()
        )
        entries = []
        for rank, u in enumerate(users, start=1):
            badge_info = get_badge_for_points(u.points or 0)
            entries.append({
                "rank": rank,
                "user_id": u.id,
                "name": u.name,
                "username": u.username or u.name,
                "total_points": u.points or 0,
                "badge": badge_info["badge"],
                "tier": badge_info["name"]
            })
        return entries

    if db is not None:
        return _fetch_leaderboard(db)
    else:
        with SessionLocal() as session:
            return _fetch_leaderboard(session)


def get_user_points_summary(user_id: int, db: Optional[Session] = None) -> Dict[str, Any]:
    """Retrieve user points balance, badges, and recent reward transactions."""
    def _fetch_summary(session: Session) -> Dict[str, Any]:
        user = session.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError(f"User with id {user_id} not found")

        total = user.points or 0
        badge_info = get_badge_for_points(total)

        history = (
            session.query(Reward)
            .filter(Reward.user_id == user_id)
            .order_by(Reward.created_at.desc())
            .limit(20)
            .all()
        )

        return {
            "user_id": user.id,
            "name": user.name,
            "total_points": total,
            "badge": badge_info["badge"],
            "tier": badge_info["name"],
            "points_to_next_tier": badge_info["points_to_next"],
            "recent_transactions": [
                {
                    "reward_id": r.id,
                    "points": r.points,
                    "reason": r.reason,
                    "created_at": r.created_at.isoformat() if r.created_at else None
                }
                for r in history
            ]
        }

    if db is not None:
        return _fetch_summary(db)
    else:
        with SessionLocal() as session:
            return _fetch_summary(session)


def get_claimable_rewards() -> List[Dict[str, Any]]:
    """Return list of redeemable rewards from configuration."""
    config = load_rewards_config()
    return config.get("claimable_rewards", DEFAULT_CATALOG)


def claim_reward(
    user_id: int,
    reward_item_id: str,
    db: Optional[Session] = None
) -> Dict[str, Any]:
    """
    Redeem points for an item from the reward catalog atomically:
    - Verifies point balance >= item cost
    - Deducts points and records a negative transaction
    - Generates redemption voucher code
    """
    catalog = get_claimable_rewards()
    selected_item = next((item for item in catalog if item["id"] == reward_item_id), None)
    if not selected_item:
        raise ValueError(f"Reward item '{reward_item_id}' not found in catalog")

    cost = int(selected_item["cost_points"])

    def _execute_claim(session: Session) -> Dict[str, Any]:
        try:
            user = session.query(User).filter(User.id == user_id).with_for_update().first()
        except Exception:
            user = session.query(User).filter(User.id == user_id).first()

        if not user:
            raise ValueError(f"User with id {user_id} not found")

        current_points = user.points or 0
        if current_points < cost:
            raise ValueError(
                f"Insufficient points: have {current_points} points, required {cost} points for '{selected_item['name']}'"
            )

        voucher_code = f"AGRI-{uuid.uuid4().hex[:8].upper()}"
        reward_record = Reward(
            user_id=user.id,
            points=-cost,
            reason=f"Claimed Reward: {selected_item['name']} (Voucher: {voucher_code})"
        )
        session.add(reward_record)
        user.points = current_points - cost
        session.commit()
        session.refresh(user)
        session.refresh(reward_record)

        return {
            "success": True,
            "voucher_code": voucher_code,
            "reward_item": selected_item,
            "points_deducted": cost,
            "remaining_points": user.points,
            "claimed_at": datetime.datetime.utcnow().isoformat()
        }

    if db is not None:
        return _execute_claim(db)
    else:
        with SessionLocal() as session:
            return _execute_claim(session)
