from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from jose import JWTError, jwt
from passlib.context import CryptContext

from backend.app.config import settings
from backend.app.database import get_db
from backend.app.models.entities import User
from backend.app.models.schemas import UserCreate, UserResponse, TokenData
from backend.app.routes import success_envelope, error_envelope

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login")
oauth2_optional_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login", auto_error=False)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        # Truncate to 72 bytes for bcrypt compatibility
        safe_password = plain_password.encode('utf-8')[:72].decode('utf-8', errors='ignore')
        return pwd_context.verify(safe_password, hashed_password)
    except Exception:
        import bcrypt
        try:
            return bcrypt.checkpw(plain_password.encode('utf-8')[:72], hashed_password.encode('utf-8'))
        except Exception:
            return False

def get_password_hash(password: str) -> str:
    safe_password = password.encode('utf-8')[:72].decode('utf-8', errors='ignore')
    try:
        return pwd_context.hash(safe_password)
    except Exception:
        import bcrypt
        return bcrypt.hashpw(password.encode('utf-8')[:72], bcrypt.gensalt()).decode('utf-8')

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception

    user = db.query(User).filter(User.username == token_data.username).first()
    if user is None:
        raise credentials_exception
    return user

def get_optional_current_user(token: Optional[str] = Depends(oauth2_optional_scheme), db: Session = Depends(get_db)) -> Optional[User]:
    if not token:
        return None
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            return None
        return db.query(User).filter(User.username == username).first()
    except Exception:
        return None

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/register")
def register(user_in: UserCreate, db: Session = Depends(get_db)):
    if not user_in.name or not user_in.password:
        raise HTTPException(status_code=400, detail="Name and password are required")

    username = user_in.username or (user_in.email.split("@")[0] if user_in.email else user_in.name.lower().replace(" ", "_"))
    if user_in.email and db.query(User).filter(User.email == user_in.email).first():
        raise HTTPException(status_code=400, detail="Email is already registered")
    if db.query(User).filter(User.username == username).first():
        raise HTTPException(status_code=400, detail="Username is already taken")

    new_user = User(
        name=user_in.name,
        email=user_in.email,
        username=username,
        hashed_password=get_password_hash(user_in.password),
        role=user_in.role or "farmer",
        points=user_in.points or 0
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    user_data = {
        "id": new_user.id,
        "name": new_user.name,
        "username": new_user.username,
        "email": new_user.email,
        "role": new_user.role,
        "points": new_user.points,
        "created_at": new_user.created_at.isoformat() if new_user.created_at else None
    }
    return success_envelope(data=user_data)

@router.post("/login")
async def login(request: Request, db: Session = Depends(get_db)):
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
            username = form.get("username")
            password = form.get("password")
        except Exception:
            pass

    if not username or not password:
        raise HTTPException(status_code=400, detail="Username/email and password required")

    user = db.query(User).filter(
        (User.username == username) | (User.email == username)
    ).first()
    if not user or not verify_password(password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect username or password")

    access_token = create_access_token(data={"sub": user.username, "role": user.role})
    return success_envelope(data={
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "name": user.name,
            "username": user.username,
            "role": user.role,
            "points": user.points
        }
    })

@router.get("/me")
def read_current_user(current_user: User = Depends(get_current_user)):
    user_data = {
        "id": current_user.id,
        "name": current_user.name,
        "username": current_user.username,
        "email": current_user.email,
        "role": current_user.role,
        "points": current_user.points
    }
    return success_envelope(data=user_data)
