import os
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status

from backend.app.config import settings
from backend.app.utils.logger import logger

# Initialize CryptContext with bcrypt
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Token settings
REFRESH_TOKEN_EXPIRE_DAYS = 7


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify plain password against hashed password."""
    if not plain_password or not hashed_password:
        return False
    try:
        # Bcrypt max password length is 72 bytes
        safe_password = plain_password.encode("utf-8")[:72].decode("utf-8", errors="ignore")
        return pwd_context.verify(safe_password, hashed_password)
    except Exception:
        # Direct bcrypt library fallback
        try:
            import bcrypt
            return bcrypt.checkpw(plain_password.encode("utf-8")[:72], hashed_password.encode("utf-8"))
        except Exception as e:
            logger.error(f"Password verification error: {e}")
            return False


def get_password_hash(password: str) -> str:
    """Hash password using bcrypt."""
    safe_password = password.encode("utf-8")[:72].decode("utf-8", errors="ignore")
    try:
        return pwd_context.hash(safe_password)
    except Exception:
        try:
            import bcrypt
            return bcrypt.hashpw(safe_password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
        except Exception as e:
            logger.error(f"Password hashing error: {e}")
            raise HTTPException(status_code=500, detail="Password hashing failed")


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Create a short-lived JWT access token."""
    to_encode = data.copy()
    now_utc = datetime.now(timezone.utc)
    expire = now_utc + (expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))

    to_encode.update({
        "type": "access",
        "exp": expire,
        "iat": now_utc
    })
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_refresh_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Create a long-lived JWT refresh token."""
    to_encode = data.copy()
    now_utc = datetime.now(timezone.utc)
    expire = now_utc + (expires_delta or timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS))

    to_encode.update({
        "type": "refresh",
        "exp": expire,
        "iat": now_utc
    })
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_token(token: str) -> Dict[str, Any]:
    """Decode and validate JWT signature."""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError as e:
        logger.warning(f"JWT decode error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication token",
            headers={"WWW-Authenticate": "Bearer"}
        )


def verify_token(token: str, expected_type: str = "access") -> Dict[str, Any]:
    """Validate token signature, expiration, and expected token type."""
    payload = decode_token(token)
    token_type = payload.get("type")

    if expected_type and token_type != expected_type:
        logger.warning(f"Token type mismatch: expected '{expected_type}', received '{token_type}'")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token type: expected '{expected_type}' token",
            headers={"WWW-Authenticate": "Bearer"}
        )

    return payload
