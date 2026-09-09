from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session

from backend.app.config import settings
from backend.app.database import get_db
from backend.app.models.user import User
from backend.app.schemas.auth import (
    RegisterRequest,
    UserCreate,
    LoginRequest,
    RefreshTokenRequest,
    TokenResponse,
    UserResponse,
    LogoutResponse,
    TokenData
)
from backend.app.utils.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    create_refresh_token,
    verify_token
)
from backend.app.auth.dependencies import (
    get_current_user,
    get_optional_current_user,
    require_role,
    oauth2_scheme,
    oauth2_optional_scheme
)
from backend.app.auth.limiter import login_limiter
from backend.app.routes import success_envelope, error_envelope
from backend.app.utils.logger import logger

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register")
def register(user_in: RegisterRequest, db: Session = Depends(get_db)):
    """
    Register a new user with email and phone uniqueness validation.
    """
    if not user_in.name or not user_in.password:
        raise HTTPException(status_code=400, detail="Name and password are required")

    # Email uniqueness check
    if user_in.email:
        existing_email = db.query(User).filter(User.email == user_in.email.strip()).first()
        if existing_email:
            raise HTTPException(status_code=400, detail="Email is already registered")

    # Phone uniqueness check
    if user_in.phone:
        existing_phone = db.query(User).filter(User.phone == user_in.phone.strip()).first()
        if existing_phone:
            raise HTTPException(status_code=400, detail="Phone number is already registered")

    # Username generation & uniqueness check
    username = (
        user_in.username.strip() if user_in.username
        else (user_in.email.split("@")[0] if user_in.email else user_in.name.lower().replace(" ", "_"))
    )
    existing_username = db.query(User).filter(User.username == username).first()
    if existing_username:
        raise HTTPException(status_code=400, detail="Username is already taken")

    # Create user with hashed password
    new_user = User(
        name=user_in.name.strip(),
        email=user_in.email.strip() if user_in.email else None,
        phone=user_in.phone.strip() if user_in.phone else None,
        username=username,
        hashed_password=get_password_hash(user_in.password),
        role=user_in.role or "farmer",
        preferred_language=user_in.preferred_language or "en",
        points=user_in.points or 0
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    logger.info(f"User registered successfully: id={new_user.id}, username='{new_user.username}', role='{new_user.role}'")

    user_data = {
        "id": new_user.id,
        "name": new_user.name,
        "username": new_user.username,
        "email": new_user.email,
        "phone": new_user.phone,
        "role": new_user.role,
        "points": new_user.points,
        "preferred_language": new_user.preferred_language,
        "created_at": new_user.created_at.isoformat() if new_user.created_at else None
    }
    return success_envelope(data=user_data)


@router.post("/login")
async def login(request: Request, db: Session = Depends(get_db)):
    """
    Authenticate user, enforce in-memory rate limiting, and issue access and refresh tokens.
    """
    client_ip = request.client.host if request.client else "unknown"

    # Rate Limit Check
    if login_limiter.is_rate_limited(client_ip):
        logger.warning(f"Rate limit triggered for login from IP='{client_ip}'")
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many failed login attempts. Please try again after 5 minutes."
        )

    # Parse JSON or form body
    content_type = request.headers.get("content-type", "")
    username = None
    password = None

    if "application/json" in content_type:
        try:
            body = await request.json()
            username = body.get("username") or body.get("email")
            password = body.get("password")
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid JSON body")
    else:
        try:
            form = await request.form()
            username = form.get("username") or form.get("email")
            password = form.get("password")
        except Exception:
            pass

    if not username or not password:
        raise HTTPException(status_code=400, detail="Username/email and password required")

    # Locate user by username or email
    user = db.query(User).filter(
        (User.username == username.strip()) | (User.email == username.strip())
    ).first()

    if not user or not verify_password(password, user.hashed_password):
        # Record failure for rate limiting and audit logging
        login_limiter.record_failure(client_ip, username=username, client_ip=client_ip)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect username or password"
        )

    # Success: Reset rate limiter and generate tokens
    login_limiter.record_success(client_ip)
    logger.info(f"Successful login for user '{user.username}' (role='{user.role}') from IP='{client_ip}'")

    token_data = {"sub": user.username, "role": user.role, "uid": user.id}
    access_token = create_access_token(data=token_data)
    refresh_token = create_refresh_token(data={"sub": user.username, "uid": user.id})

    response_data = {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "name": user.name,
            "username": user.username,
            "email": user.email,
            "phone": user.phone,
            "role": user.role,
            "points": user.points
        }
    }
    return success_envelope(data=response_data)


@router.post("/refresh")
async def refresh_access_token(request: Request, db: Session = Depends(get_db)):
    """
    Exchange valid refresh token for a newly minted access token and refresh token.
    """
    refresh_token = None
    try:
        body = await request.json()
        refresh_token = body.get("refresh_token")
    except Exception:
        pass

    if not refresh_token:
        # Check Authorization header fallback
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            refresh_token = auth_header.replace("Bearer ", "").strip()

    if not refresh_token:
        raise HTTPException(status_code=400, detail="refresh_token is required")

    try:
        payload = verify_token(refresh_token, expected_type="refresh")
        username: str = payload.get("sub")
        if not username:
            raise HTTPException(status_code=401, detail="Invalid refresh token payload")
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Invalid or expired refresh token: {str(e)}")

    user = db.query(User).filter(
        (User.username == username) | (User.email == username)
    ).first()
    if not user:
        raise HTTPException(status_code=401, detail="User associated with token does not exist")

    # Issue new access token
    new_access_token = create_access_token(data={"sub": user.username, "role": user.role, "uid": user.id})
    new_refresh_token = create_refresh_token(data={"sub": user.username, "uid": user.id})

    logger.info(f"Refreshed access token for user '{user.username}'")

    return success_envelope(data={
        "access_token": new_access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer"
    })


@router.post("/logout")
def logout(current_user: Optional[User] = Depends(get_optional_current_user)):
    """
    Invalidate session / logout endpoint.
    """
    username = current_user.username if current_user else "anonymous"
    logger.info(f"User '{username}' logged out successfully.")
    return success_envelope(data={
        "message": f"User '{username}' successfully logged out."
    })


@router.get("/me")
def read_current_user(current_user: User = Depends(get_current_user)):
    """
    Return currently authenticated profile.
    """
    user_data = {
        "id": current_user.id,
        "name": current_user.name,
        "username": current_user.username,
        "email": current_user.email,
        "phone": current_user.phone,
        "role": current_user.role,
        "points": current_user.points,
        "preferred_language": current_user.preferred_language
    }
    return success_envelope(data=user_data)
