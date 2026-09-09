import functools
import inspect
from typing import Optional, Callable
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from backend.app.config import settings
from backend.app.database import get_db
from backend.app.models.user import User
from backend.app.utils.security import verify_token
from backend.app.utils.logger import logger

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login")
oauth2_optional_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login", auto_error=False)


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    """Validate access token and return current authenticated User model."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = verify_token(token, expected_type="access")
        username: str = payload.get("sub")
        if not username:
            raise credentials_exception
    except Exception as e:
        logger.warning(f"Auth token validation failed: {e}")
        raise credentials_exception

    user = db.query(User).filter(
        (User.username == username) | (User.email == username)
    ).first()
    if user is None:
        raise credentials_exception
    return user


def get_optional_current_user(
    token: Optional[str] = Depends(oauth2_optional_scheme),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """Gracefully return user if token provided and valid, otherwise return None."""
    if not token:
        return None
    try:
        payload = verify_token(token, expected_type="access")
        username: str = payload.get("sub")
        if not username:
            return None
        return db.query(User).filter(
            (User.username == username) | (User.email == username)
        ).first()
    except Exception:
        return None


def require_role(role: str):
    """
    Role-based access control.
    Supports both FastAPI dependency injection:
        current_user: User = Depends(require_role('expert'))
    And route decorator usage:
        @require_role('expert')
        def expert_action(current_user: User = Depends(get_current_user)):
    """
    required = role.lower().strip()

    def role_enforcer(current_user: User = Depends(get_current_user)):
        # 1. Used as decorator: @require_role('expert') where current_user receives decorated fn
        if callable(current_user) and not isinstance(current_user, User):
            fn = current_user
            if inspect.iscoroutinefunction(fn):
                @functools.wraps(fn)
                async def async_wrapper(*f_args, **f_kwargs):
                    u = f_kwargs.get("current_user")
                    if u and u.role != required and u.role != "admin":
                        logger.warning(f"[RBAC] Forbidden: User '{u.username}' (role='{u.role}') tried accessing '{required}'.")
                        raise HTTPException(
                            status_code=status.HTTP_403_FORBIDDEN,
                            detail=f"Access denied: Operation requires '{required}' role privileges"
                        )
                    return await fn(*f_args, **f_kwargs)
                return async_wrapper
            else:
                @functools.wraps(fn)
                def sync_wrapper(*f_args, **f_kwargs):
                    u = f_kwargs.get("current_user")
                    if u and u.role != required and u.role != "admin":
                        logger.warning(f"[RBAC] Forbidden: User '{u.username}' (role='{u.role}') tried accessing '{required}'.")
                        raise HTTPException(
                            status_code=status.HTTP_403_FORBIDDEN,
                            detail=f"Access denied: Operation requires '{required}' role privileges"
                        )
                    return fn(*f_args, **f_kwargs)
                return sync_wrapper

        # 2. Used as FastAPI Dependency: Depends(require_role('expert'))
        if current_user.role != required and current_user.role != "admin":
            logger.warning(
                f"[RBAC] Forbidden: User '{current_user.username}' with role '{current_user.role}' "
                f"denied access to '{required}' endpoint."
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied: Operation requires '{required}' role privileges (current: '{current_user.role}')"
            )
        return current_user

    return role_enforcer
