import os

base_models = r"C:\Users\HP\.gemini\antigravity\scratch\InsightX\backend\app\models"
base_db = r"C:\Users\HP\.gemini\antigravity\scratch\InsightX\backend\app\database"
os.makedirs(base_models, exist_ok=True)
os.makedirs(base_db, exist_ok=True)

# 1. database/session.py
session_py = """import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from ..core.config import settings

class Base(DeclarativeBase):
    pass

# Create DB engine supporting SQLite (with check_same_thread=False) and PostgreSQL
connect_args = {}
if settings.DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(
    settings.DATABASE_URL,
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
"""

# 2. models/user.py
user_py = """import uuid
from datetime import datetime, timezone
from sqlalchemy import String, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from ..database.session import Base

class User(Base):
    __tablename__ = "users"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(100), nullable=True)
    role: Mapped[str] = mapped_column(String(50), default="analyst")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    
    datasets = relationship("Dataset", back_populates="owner", cascade="all, delete-orphan")
"""

# 3. models/dataset.py
dataset_py = """import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Integer, BigInteger, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from ..database.session import Base

class Dataset(Base):
    __tablename__ = "datasets"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_format: Mapped[str] = mapped_column(String(20), nullable=False) # csv, xlsx, parquet, json
    file_size_bytes: Mapped[int] = mapped_column(BigInteger, default=0)
    raw_storage_path: Mapped[str] = mapped_column(Text, nullable=False)
    processed_storage_path: Mapped[str] = mapped_column(Text, nullable=True)
    sheet_name: Mapped[str] = mapped_column(String(100), nullable=True)
    domain_type: Mapped[str] = mapped_column(String(50), default="generic") # ecommerce, marketing, healthcare, generic
    row_count: Mapped[int] = mapped_column(Integer, default=0)
    column_count: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(50), default="uploaded") # uploaded, profiling, ready, failed
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc)
    )
    
    owner = relationship("User", back_populates="datasets")
    columns = relationship("DatasetSchema", back_populates="dataset", cascade="all, delete-orphan")
    quality_report = relationship("DataQualityReport", back_populates="dataset", uselist=False, cascade="all, delete-orphan")
    analysis_sessions = relationship("AnalysisSession", back_populates="dataset", cascade="all, delete-orphan")
    investigations = relationship("RootCauseInvestigation", back_populates="dataset", cascade="all, delete-orphan")
    conversations = relationship("AIConversation", back_populates="dataset", cascade="all, delete-orphan")
"""

# 4. models/data_quality.py
quality_py = """import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Integer, Float, ForeignKey, JSON, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from ..database.session import Base

class DataQualityReport(Base):
    __tablename__ = "data_quality_reports"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    dataset_id: Mapped[str] = mapped_column(String(36), ForeignKey("datasets.id", ondelete="CASCADE"), unique=True)
    quality_score: Mapped[int] = mapped_column(Integer, nullable=False) # 0-100
    total_rows: Mapped[int] = mapped_column(Integer, default=0)
    total_columns: Mapped[int] = mapped_column(Integer, default=0)
    missing_cells_count: Mapped[int] = mapped_column(Integer, default=0)
    missing_cells_percentage: Mapped[float] = mapped_column(Float, default=0.0)
    duplicate_rows_count: Mapped[int] = mapped_column(Integer, default=0)
    potential_outliers_count: Mapped[int] = mapped_column(Integer, default=0)
    constant_columns: Mapped[dict] = mapped_column(JSON, default=list)
    invalid_values: Mapped[dict] = mapped_column(JSON, default=dict)
    recommended_actions: Mapped[list] = mapped_column(JSON, default=list)
    applied_actions: Mapped[list] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    
    dataset = relationship("Dataset", back_populates="quality_report")

class DatasetSchema(Base):
    __tablename__ = "dataset_schemas"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    dataset_id: Mapped[str] = mapped_column(String(36), ForeignKey("datasets.id", ondelete="CASCADE"))
    column_name: Mapped[str] = mapped_column(String(255), nullable=False)
    safe_column_name: Mapped[str] = mapped_column(String(255), nullable=False)
    detected_type: Mapped[str] = mapped_column(String(50), nullable=False) # integer, float, datetime, categorical, text, id, boolean
    is_date: Mapped[bool] = mapped_column(default=False)
    is_numeric: Mapped[bool] = mapped_column(default=False)
    is_categorical: Mapped[bool] = mapped_column(default=False)
    is_target_candidate: Mapped[bool] = mapped_column(default=False)
    distinct_count: Mapped[int] = mapped_column(Integer, default=0)
    missing_count: Mapped[int] = mapped_column(Integer, default=0)
    min_value: Mapped[str] = mapped_column(String(255), nullable=True)
    max_value: Mapped[str] = mapped_column(String(255), nullable=True)
    sample_values: Mapped[list] = mapped_column(JSON, default=list)
    
    dataset = relationship("Dataset", back_populates="columns")
"""

# 5. models/analysis.py
analysis_py = """import uuid
from datetime import datetime, timezone
from sqlalchemy import String, ForeignKey, JSON, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from ..database.session import Base

class AnalysisSession(Base):
    __tablename__ = "analysis_sessions"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    dataset_id: Mapped[str] = mapped_column(String(36), ForeignKey("datasets.id", ondelete="CASCADE"))
    title: Mapped[str] = mapped_column(String(255), default="Automated Insights")
    kpi_summary: Mapped[dict] = mapped_column(JSON, default=dict)
    dashboard_layout: Mapped[dict] = mapped_column(JSON, default=dict)
    detected_alerts: Mapped[list] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    
    dataset = relationship("Dataset", back_populates="analysis_sessions")

class RootCauseInvestigation(Base):
    __tablename__ = "root_cause_investigations"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    dataset_id: Mapped[str] = mapped_column(String(36), ForeignKey("datasets.id", ondelete="CASCADE"))
    target_metric: Mapped[str] = mapped_column(String(100), nullable=False)
    change_type: Mapped[str] = mapped_column(String(50), default="decline") # decline, surge, spike
    change_percentage: Mapped[float] = mapped_column(default=0.0)
    time_window: Mapped[dict] = mapped_column(JSON, default=dict)
    contributors: Mapped[list] = mapped_column(JSON, default=list)
    confounding_factors: Mapped[list] = mapped_column(JSON, default=list)
    evidence_payload: Mapped[dict] = mapped_column(JSON, default=dict)
    narrative_explanation: Mapped[str] = mapped_column(default="")
    recommendations: Mapped[list] = mapped_column(JSON, default=list)
    confidence_level: Mapped[str] = mapped_column(String(20), default="High")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    
    dataset = relationship("Dataset", back_populates="investigations")

class AIConversation(Base):
    __tablename__ = "ai_conversations"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    dataset_id: Mapped[str] = mapped_column(String(36), ForeignKey("datasets.id", ondelete="CASCADE"))
    role: Mapped[str] = mapped_column(String(20), nullable=False) # user, assistant
    message: Mapped[str] = mapped_column(default="")
    sql_query: Mapped[str] = mapped_column(nullable=True)
    chart_spec: Mapped[dict] = mapped_column(JSON, nullable=True)
    findings: Mapped[dict] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    
    dataset = relationship("Dataset", back_populates="conversations")
"""

init_models_py = """from .user import User
from .dataset import Dataset
from .data_quality import DataQualityReport, DatasetSchema
from .analysis import AnalysisSession, RootCauseInvestigation, AIConversation

__all__ = [
    "User",
    "Dataset",
    "DataQualityReport",
    "DatasetSchema",
    "AnalysisSession",
    "RootCauseInvestigation",
    "AIConversation"
]
"""

with open(os.path.join(base_db, "session.py"), "w", encoding="utf-8") as f:
    f.write(session_py)

with open(os.path.join(base_models, "user.py"), "w", encoding="utf-8") as f:
    f.write(user_py)

with open(os.path.join(base_models, "dataset.py"), "w", encoding="utf-8") as f:
    f.write(dataset_py)

with open(os.path.join(base_models, "data_quality.py"), "w", encoding="utf-8") as f:
    f.write(quality_py)

with open(os.path.join(base_models, "analysis.py"), "w", encoding="utf-8") as f:
    f.write(analysis_py)

with open(os.path.join(base_models, "__init__.py"), "w", encoding="utf-8") as f:
    f.write(init_models_py)

print("Database session and ORM models successfully written.")
