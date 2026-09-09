import os
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from backend.app.config import settings

connect_args = {}
if "sqlite" in settings.DATABASE_URL:
    connect_args = {"check_same_thread": False}

try:
    engine = create_engine(
        settings.DATABASE_URL,
        connect_args=connect_args,
        pool_pre_ping=True
    )
    with engine.connect() as conn:
        pass
except Exception:
    # Graceful fallback for local development or testing when postgres is not reachable
    fallback_url = "sqlite:///./crophealth.db"
    engine = create_engine(
        fallback_url,
        connect_args={"check_same_thread": False}
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# Alembic-ready metadata export
metadata = Base.metadata

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
