import uuid
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
