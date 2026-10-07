import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from ..core.config import settings

class Base(DeclarativeBase):
    pass

db_url = settings.DATABASE_URL
if db_url == "sqlite:///./insightx.db":
    abs_db_path = os.path.join(settings.BASE_DIR, "insightx.db").replace("\\", "/")
    db_url = f"sqlite:///{abs_db_path}"

connect_args = {}
if db_url.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(
    db_url,
    connect_args=connect_args,
    echo=False
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
