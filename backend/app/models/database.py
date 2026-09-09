from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from backend.app.config import settings

# Initialize SQLAlchemy Engine for PostgreSQL with automatic fallback
connect_args = {}
if "sqlite" in settings.DATABASE_URL:
    connect_args = {"check_same_thread": False}

try:
    engine = create_engine(
        settings.DATABASE_URL,
        connect_args=connect_args,
        pool_pre_ping=True
    )
    # Ping database
    with engine.connect() as conn:
        pass
except Exception:
    # If remote PostgreSQL instance is not reachable during local test, fallback to sqlite
    fallback_url = "sqlite:///./crophealth.db"
    engine = create_engine(
        fallback_url,
        connect_args={"check_same_thread": False}
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
