import uuid
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
    target_column: Mapped[str] = mapped_column(String(255), nullable=True) # User-selected or ML-discovered target column
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
