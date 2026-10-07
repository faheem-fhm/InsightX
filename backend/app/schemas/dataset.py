from typing import Dict, Any, List, Optional
from pydantic import BaseModel
from datetime import datetime

class DatasetResponse(BaseModel):
    id: str
    name: str
    original_filename: str
    file_format: str
    file_size_bytes: int
    sheet_name: Optional[str] = None
    domain_type: str
    row_count: int
    column_count: int
    status: str
    created_at: datetime
    quality_score: Optional[int] = None

class PreprocessRequest(BaseModel):
    remove_duplicates: bool = True
    impute_missing: bool = True
    flag_outliers: bool = True

class AnomalyRequest(BaseModel):
    metric: Optional[str] = None
    contamination: float = 0.04

class ForecastRequest(BaseModel):
    metric: Optional[str] = None
    horizon_days: int = 30

class RootCauseRequest(BaseModel):
    target_metric: Optional[str] = None
    crisis_start_date: Optional[str] = None
    crisis_end_date: Optional[str] = None

class AIAskRequest(BaseModel):
    question: str

class TextToSqlRequest(BaseModel):
    question: str

class SampleDatasetRequest(BaseModel):
    sample_key: str # ecommerce, saas, healthcare
