import uuid
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
