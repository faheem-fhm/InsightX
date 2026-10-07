import os

api_dir = r"C:\Users\HP\.gemini\antigravity\scratch\InsightX\backend\app\api\v1"

router_py = """import os
import uuid
import shutil
from typing import List, Optional
import pandas as pd
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, status
from sqlalchemy.orm import Session

from ...core.config import settings
from ...core.exceptions import DatasetNotFoundError, InvalidFileFormatError, UnsafeSQLError
from ...database.session import get_db
from ...models import Dataset, DatasetSchema, DataQualityReport, AnalysisSession, RootCauseInvestigation, AIConversation
from ...schemas.dataset import PreprocessRequest, AnomalyRequest, ForecastRequest, RootCauseRequest, AIAskRequest, TextToSqlRequest, SampleDatasetRequest
from ...services.file_validator import validate_and_inspect_file
from ...services.data_profiler import profile_dataframe
from ...services.quality_evaluator import compute_quality_report
from ...services.preprocessor import run_preprocessing_pipeline
from ...analytics.kpi_engine import compute_dynamic_kpis
from ...analytics.eda_engine import compute_eda_summary
from ...analytics.chart_selector import recommend_automatic_charts
from ...analytics.olap_engine import olap_engine
from ...ml.anomaly_detector import detect_anomalies
from ...ml.forecaster import run_time_series_forecast
from ...ml.rfm_segmentation import run_rfm_segmentation
from ...ml.churn_predictor import train_churn_model
from ...root_cause.investigator import run_root_cause_investigation
from ...ai.sql_validator import validate_safe_sql
from ...ai.data_analyst import answer_analyst_query

router = APIRouter()

def get_dataset_or_404(dataset_id: str, db: Session) -> Dataset:
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not dataset:
        raise DatasetNotFoundError(dataset_id)
    return dataset

def load_dataset_df(dataset: Dataset) -> pd.DataFrame:
    if dataset.processed_storage_path and os.path.exists(dataset.processed_storage_path):
        return pd.read_parquet(dataset.processed_storage_path)
    elif dataset.raw_storage_path and os.path.exists(dataset.raw_storage_path):
        ext = dataset.file_format.lower()
        if ext == "csv":
            return pd.read_csv(dataset.raw_storage_path)
        elif ext in ("xlsx", "xls"):
            return pd.read_excel(dataset.raw_storage_path, sheet_name=dataset.sheet_name or 0)
        elif ext == "json":
            return pd.read_json(dataset.raw_storage_path)
        elif ext == "parquet":
            return pd.read_parquet(dataset.raw_storage_path)
    raise HTTPException(status_code=404, detail="Dataset physical file not found on disk.")

@router.post("/datasets/upload")
async def upload_dataset(
    file: UploadFile = File(...),
    sheet_name: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    dataset_id = str(uuid.uuid4())
    filename = file.filename or "uploaded_data.csv"
    ext = filename.split(".")[-1].lower()
    
    raw_path = os.path.join(settings.UPLOAD_DIR, f"{dataset_id}_{filename}")
    with open(raw_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    val_res = validate_and_inspect_file(raw_path, max_size_mb=settings.MAX_UPLOAD_SIZE_MB)
    if not val_res.is_valid:
        if os.path.exists(raw_path):
            os.remove(raw_path)
        raise InvalidFileFormatError(val_res.error_message or "Unknown validation error")
        
    # Read full raw DataFrame
    if ext == "csv":
        df_raw = pd.read_csv(raw_path)
    elif ext in ("xlsx", "xls"):
        target_sheet = sheet_name or (val_res.sheet_names[0] if val_res.sheet_names else 0)
        df_raw = pd.read_excel(raw_path, sheet_name=target_sheet)
    elif ext == "json":
        df_raw = pd.read_json(raw_path)
    elif ext == "parquet":
        df_raw = pd.read_parquet(raw_path)
    else:
        df_raw = pd.read_csv(raw_path)
        
    profiles = profile_dataframe(df_raw)
    quality_dict = compute_quality_report(df_raw, profiles)
    
    # Auto preprocess initially to create Parquet view
    df_clean, prep_rep = run_preprocessing_pipeline(
        df_raw, dataset_id=dataset_id, remove_duplicates=True, impute_missing=True, flag_outliers=True
    )
    
    dataset = Dataset(
        id=dataset_id,
        name=filename.rsplit(".", 1)[0].replace("_", " ").title(),
        original_filename=filename,
        file_format=ext,
        file_size_bytes=os.path.getsize(raw_path),
        raw_storage_path=raw_path,
        processed_storage_path=prep_rep.cleaned_parquet_path,
        sheet_name=sheet_name,
        row_count=len(df_raw),
        column_count=len(df_raw.columns),
        status="ready"
    )
    db.add(dataset)
    db.flush()
    
    # Add column schemas
    for p in profiles:
        schema_entry = DatasetSchema(
            dataset_id=dataset_id,
            column_name=p["column_name"],
            safe_column_name=p["safe_column_name"],
            detected_type=p["detected_type"],
            is_date=p["is_date"],
            is_numeric=p["is_numeric"],
            is_categorical=p["is_categorical"],
            is_target_candidate=p["is_target_candidate"],
            distinct_count=p["distinct_count"],
            missing_count=p["missing_count"],
            min_value=p["min_value"],
            max_value=p["max_value"],
            sample_values=p["sample_values"]
        )
        db.add(schema_entry)
        
    # Add quality report
    q_report = DataQualityReport(
        dataset_id=dataset_id,
        quality_score=quality_dict["quality_score"],
        total_rows=quality_dict["total_rows"],
        total_columns=quality_dict["total_columns"],
        missing_cells_count=quality_dict["missing_cells_count"],
        missing_cells_percentage=quality_dict["missing_cells_percentage"],
        duplicate_rows_count=quality_dict["duplicate_rows_count"],
        potential_outliers_count=quality_dict["potential_outliers_count"],
        constant_columns=quality_dict["constant_columns"],
        invalid_values=quality_dict["invalid_values"],
        recommended_actions=quality_dict["recommended_actions"],
        applied_actions=prep_rep.to_dict()
    )
    db.add(q_report)
    db.commit()
    
    return {
        "dataset_id": dataset_id,
        "name": dataset.name,
        "status": "ready",
        "quality_score": quality_dict["quality_score"],
        "row_count": dataset.row_count,
        "column_count": dataset.column_count
    }

@router.post("/datasets/sample")
def load_sample_dataset(req: SampleDatasetRequest, db: Session = Depends(get_db)):
    mapping = {
        "ecommerce": ("ecommerce_sales_with_hidden_root_cause.csv", "E-Commerce Logistics & Sales"),
        "saas": ("saas_marketing_funnel.csv", "B2B SaaS Marketing Funnel"),
        "healthcare": ("healthcare_patient_flow.csv", "Hospital Patient Care Flow")
    }
    key = req.sample_key.lower()
    if key not in mapping:
        raise HTTPException(status_code=400, detail=f"Unknown sample key '{key}'. Choose: ecommerce, saas, healthcare")
        
    filename, display_name = mapping[key]
    sample_file = os.path.join(settings.SAMPLES_DIR, filename)
    if not os.path.exists(sample_file):
        raise HTTPException(status_code=404, detail="Sample file not found on disk.")
        
    dataset_id = str(uuid.uuid4())
    raw_path = os.path.join(settings.UPLOAD_DIR, f"{dataset_id}_{filename}")
    shutil.copy(sample_file, raw_path)
    
    df_raw = pd.read_csv(raw_path)
    profiles = profile_dataframe(df_raw)
    quality_dict = compute_quality_report(df_raw, profiles)
    df_clean, prep_rep = run_preprocessing_pipeline(
        df_raw, dataset_id=dataset_id, remove_duplicates=True, impute_missing=True, flag_outliers=True
    )
    
    dataset = Dataset(
        id=dataset_id,
        name=display_name,
        original_filename=filename,
        file_format="csv",
        file_size_bytes=os.path.getsize(raw_path),
        raw_storage_path=raw_path,
        processed_storage_path=prep_rep.cleaned_parquet_path,
        domain_type=key,
        row_count=len(df_raw),
        column_count=len(df_raw.columns),
        status="ready"
    )
    db.add(dataset)
    db.flush()
    
    for p in profiles:
        schema_entry = DatasetSchema(
            dataset_id=dataset_id,
            column_name=p["column_name"],
            safe_column_name=p["safe_column_name"],
            detected_type=p["detected_type"],
            is_date=p["is_date"],
            is_numeric=p["is_numeric"],
            is_categorical=p["is_categorical"],
            is_target_candidate=p["is_target_candidate"],
            distinct_count=p["distinct_count"],
            missing_count=p["missing_count"],
            min_value=p["min_value"],
            max_value=p["max_value"],
            sample_values=p["sample_values"]
        )
        db.add(schema_entry)
        
    q_report = DataQualityReport(
        dataset_id=dataset_id,
        quality_score=quality_dict["quality_score"],
        total_rows=quality_dict["total_rows"],
        total_columns=quality_dict["total_columns"],
        missing_cells_count=quality_dict["missing_cells_count"],
        missing_cells_percentage=quality_dict["missing_cells_percentage"],
        duplicate_rows_count=quality_dict["duplicate_rows_count"],
        potential_outliers_count=quality_dict["potential_outliers_count"],
        constant_columns=quality_dict["constant_columns"],
        invalid_values=quality_dict["invalid_values"],
        recommended_actions=quality_dict["recommended_actions"],
        applied_actions=prep_rep.to_dict()
    )
    db.add(q_report)
    db.commit()
    
    return {
        "dataset_id": dataset_id,
        "name": dataset.name,
        "status": "ready",
        "quality_score": quality_dict["quality_score"],
        "row_count": dataset.row_count,
        "column_count": dataset.column_count
    }

@router.get("/datasets")
def list_datasets(db: Session = Depends(get_db)):
    datasets = db.query(Dataset).order_by(Dataset.created_at.desc()).all()
    results = []
    for d in datasets:
        q_score = d.quality_report.quality_score if d.quality_report else None
        results.append({
            "id": d.id,
            "name": d.name,
            "original_filename": d.original_filename,
            "file_format": d.file_format,
            "file_size_bytes": d.file_size_bytes,
            "domain_type": d.domain_type,
            "row_count": d.row_count,
            "column_count": d.column_count,
            "status": d.status,
            "quality_score": q_score,
            "created_at": d.created_at.isoformat() if d.created_at else None
        })
    return results

@router.get("/datasets/{dataset_id}")
def get_dataset(dataset_id: str, db: Session = Depends(get_db)):
    dataset = get_dataset_or_404(dataset_id, db)
    q_score = dataset.quality_report.quality_score if dataset.quality_report else None
    return {
        "id": dataset.id,
        "name": dataset.name,
        "original_filename": dataset.original_filename,
        "file_format": dataset.file_format,
        "file_size_bytes": dataset.file_size_bytes,
        "sheet_name": dataset.sheet_name,
        "domain_type": dataset.domain_type,
        "row_count": dataset.row_count,
        "column_count": dataset.column_count,
        "status": dataset.status,
        "quality_score": q_score,
        "created_at": dataset.created_at.isoformat() if dataset.created_at else None
    }

@router.get("/datasets/{dataset_id}/profile")
def get_dataset_profile(dataset_id: str, db: Session = Depends(get_db)):
    dataset = get_dataset_or_404(dataset_id, db)
    columns = db.query(DatasetSchema).filter(DatasetSchema.dataset_id == dataset_id).all()
    return {
        "dataset_id": dataset.id,
        "name": dataset.name,
        "total_rows": dataset.row_count,
        "total_columns": dataset.column_count,
        "columns": [
            {
                "column_name": c.column_name,
                "safe_column_name": c.safe_column_name,
                "detected_type": c.detected_type,
                "is_date": c.is_date,
                "is_numeric": c.is_numeric,
                "is_categorical": c.is_categorical,
                "is_target_candidate": c.is_target_candidate,
                "distinct_count": c.distinct_count,
                "missing_count": c.missing_count,
                "min_value": c.min_value,
                "max_value": c.max_value,
                "sample_values": c.sample_values
            }
            for c in columns
        ]
    }

@router.get("/datasets/{dataset_id}/quality")
def get_dataset_quality(dataset_id: str, db: Session = Depends(get_db)):
    dataset = get_dataset_or_404(dataset_id, db)
    report = dataset.quality_report
    if not report:
        raise HTTPException(status_code=404, detail="Quality report not found for this dataset.")
    return {
        "quality_score": report.quality_score,
        "total_rows": report.total_rows,
        "total_columns": report.total_columns,
        "missing_cells_count": report.missing_cells_count,
        "missing_cells_percentage": report.missing_cells_percentage,
        "duplicate_rows_count": report.duplicate_rows_count,
        "potential_outliers_count": report.potential_outliers_count,
        "constant_columns": report.constant_columns,
        "invalid_values": report.invalid_values,
        "recommended_actions": report.recommended_actions,
        "applied_actions": report.applied_actions
    }

@router.post("/datasets/{dataset_id}/preprocess")
def apply_preprocessing(dataset_id: str, req: PreprocessRequest, db: Session = Depends(get_db)):
    dataset = get_dataset_or_404(dataset_id, db)
    # Read raw data
    ext = dataset.file_format.lower()
    if ext == "csv":
        df_raw = pd.read_csv(dataset.raw_storage_path)
    elif ext in ("xlsx", "xls"):
        df_raw = pd.read_excel(dataset.raw_storage_path, sheet_name=dataset.sheet_name or 0)
    else:
        df_raw = pd.read_csv(dataset.raw_storage_path)
        
    df_clean, prep_rep = run_preprocessing_pipeline(
        df_raw,
        dataset_id=dataset.id,
        remove_duplicates=req.remove_duplicates,
        impute_missing=req.impute_missing,
        flag_outliers=req.flag_outliers
    )
    
    # Update quality report
    if dataset.quality_report:
        dataset.quality_report.applied_actions = prep_rep.to_dict()
        # Recalculate score after preprocessing
        profiles = profile_dataframe(df_clean)
        new_q = compute_quality_report(df_clean, profiles)
        dataset.quality_report.quality_score = new_q["quality_score"]
        db.commit()
        
    return {
        "status": "success",
        "report": prep_rep.to_dict(),
        "preview": df_clean.head(10).to_dict(orient="records")
    }

@router.get("/datasets/{dataset_id}/dashboard")
def get_dashboard(dataset_id: str, db: Session = Depends(get_db)):
    dataset = get_dataset_or_404(dataset_id, db)
    df = load_dataset_df(dataset)
    
    columns = db.query(DatasetSchema).filter(DatasetSchema.dataset_id == dataset_id).all()
    date_col = next((c.safe_column_name for c in columns if c.is_date), None)
    
    kpis = compute_dynamic_kpis(df, date_col=date_col)
    charts = recommend_automatic_charts(df)
    
    # Dynamic Filter values (for top categoricals)
    filters = {}
    for c in columns:
        if c.is_categorical and c.safe_column_name in df.columns:
            filters[c.safe_column_name] = [str(x) for x in df[c.safe_column_name].dropna().unique()[:15]]
            
    # Generated Alerts based on thresholds
    alerts = []
    # Check for sudden decline in efficiency or critical risk surge
    for kpi in kpis:
        if kpi["id"] == "critical_risk" and (kpi["delta_percent"] or 0) > 20:
            alerts.append({
                "type": "danger",
                "title": f"Operational Alert: Surge in {kpi['title']}",
                "message": f"{kpi['title']} escalated by {kpi['delta_percent']}% over the evaluated interval.",
                "action": "Investigate Root Cause"
            })
        elif kpi["id"] in ("primary_monetary", "primary_efficiency") and (kpi["delta_percent"] or 0) < -10:
            alerts.append({
                "type": "warning",
                "title": f"Performance Drop: {kpi['title']} Down {abs(kpi['delta_percent'])}%",
                "message": f"Trailing performance reflects a significant contraction. Investigate driver dimensions.",
                "action": "Investigate Root Cause"
            })
            
    return {
        "dataset_name": dataset.name,
        "kpis": kpis,
        "charts": charts,
        "filters": filters,
        "alerts": alerts,
        "row_count": len(df)
    }

@router.get("/datasets/{dataset_id}/analytics")
def get_analytics(dataset_id: str, db: Session = Depends(get_db)):
    dataset = get_dataset_or_404(dataset_id, db)
    df = load_dataset_df(dataset)
    eda_summary = compute_eda_summary(df)
    return eda_summary

@router.post("/datasets/{dataset_id}/anomaly")
def get_anomalies(dataset_id: str, req: AnomalyRequest, db: Session = Depends(get_db)):
    dataset = get_dataset_or_404(dataset_id, db)
    df = load_dataset_df(dataset)
    columns = db.query(DatasetSchema).filter(DatasetSchema.dataset_id == dataset_id).all()
    
    date_col = next((c.safe_column_name for c in columns if c.is_date), None)
    if not date_col:
        for c in df.columns:
            if any(k in str(c).lower() for k in ["date", "time"]):
                date_col = c
                break
                
    metric = req.metric
    if not metric or metric not in df.columns:
        num_cols = [c.safe_column_name for c in columns if c.is_numeric]
        metric = "revenue" if "revenue" in df.columns else (num_cols[0] if num_cols else None)
        
    if not date_col or not metric:
        return {"anomalies": [], "message": "Dataset lacks necessary date or numeric metrics for time-series anomaly detection."}
        
    anomalies = detect_anomalies(df, date_col=date_col, metric_col=metric, contamination=req.contamination)
    return {"metric": metric, "date_column": date_col, "total_detected": len(anomalies), "anomalies": anomalies}

@router.post("/datasets/{dataset_id}/forecast")
def get_forecast(dataset_id: str, req: ForecastRequest, db: Session = Depends(get_db)):
    dataset = get_dataset_or_404(dataset_id, db)
    df = load_dataset_df(dataset)
    columns = db.query(DatasetSchema).filter(DatasetSchema.dataset_id == dataset_id).all()
    
    date_col = next((c.safe_column_name for c in columns if c.is_date), None)
    if not date_col:
        for c in df.columns:
            if any(k in str(c).lower() for k in ["date", "time"]):
                date_col = c
                break
                
    metric = req.metric
    if not metric or metric not in df.columns:
        num_cols = [c.safe_column_name for c in columns if c.is_numeric]
        metric = "revenue" if "revenue" in df.columns else (num_cols[0] if num_cols else None)
        
    if not date_col or not metric:
        raise HTTPException(status_code=400, detail="Dataset does not contain valid temporal and numeric columns for forecasting.")
        
    result = run_time_series_forecast(df, date_col=date_col, metric_col=metric, horizon_days=req.horizon_days)
    return result

@router.get("/datasets/{dataset_id}/customers")
def get_customers(dataset_id: str, db: Session = Depends(get_db)):
    dataset = get_dataset_or_404(dataset_id, db)
    df = load_dataset_df(dataset)
    return run_rfm_segmentation(df)

@router.post("/datasets/{dataset_id}/churn")
def get_churn(dataset_id: str, db: Session = Depends(get_db)):
    dataset = get_dataset_or_404(dataset_id, db)
    df = load_dataset_df(dataset)
    return train_churn_model(df)

@router.post("/datasets/{dataset_id}/root-cause")
def get_root_cause(dataset_id: str, req: RootCauseRequest, db: Session = Depends(get_db)):
    dataset = get_dataset_or_404(dataset_id, db)
    df = load_dataset_df(dataset)
    return run_root_cause_investigation(
        df=df,
        target_metric=req.target_metric,
        crisis_start_date=req.crisis_start_date,
        crisis_end_date=req.crisis_end_date
    )

@router.post("/datasets/{dataset_id}/ai/ask")
def ask_ai_analyst(dataset_id: str, req: AIAskRequest, db: Session = Depends(get_db)):
    dataset = get_dataset_or_404(dataset_id, db)
    columns = db.query(DatasetSchema).filter(DatasetSchema.dataset_id == dataset_id).all()
    schema_info = [
        {
            "safe_column_name": c.safe_column_name,
            "detected_type": c.detected_type,
            "is_numeric": c.is_numeric,
            "is_categorical": c.is_categorical,
            "is_date": c.is_date
        }
        for c in columns
    ]
    
    parquet_path = dataset.processed_storage_path or dataset.raw_storage_path
    table_name = f"dataset_{dataset_id.replace('-', '_')}"
    
    response = answer_analyst_query(
        question=req.question,
        table_name=table_name,
        schema_info=schema_info,
        parquet_path=parquet_path
    )
    
    # Save conversation record
    conv = AIConversation(
        dataset_id=dataset_id,
        role="user",
        message=req.question
    )
    db.add(conv)
    db.commit()
    
    return response.to_dict()

@router.post("/datasets/{dataset_id}/ai/text-to-sql")
def execute_text_to_sql(dataset_id: str, req: TextToSqlRequest, db: Session = Depends(get_db)):
    dataset = get_dataset_or_404(dataset_id, db)
    parquet_path = dataset.processed_storage_path or dataset.raw_storage_path
    table_name = f"dataset_{dataset_id.replace('-', '_')}"
    olap_engine.register_parquet(table_name, parquet_path)
    
    columns = db.query(DatasetSchema).filter(DatasetSchema.dataset_id == dataset_id).all()
    schema_info = [
        {
            "safe_column_name": c.safe_column_name,
            "detected_type": c.detected_type,
            "is_numeric": c.is_numeric,
            "is_categorical": c.is_categorical,
            "is_date": c.is_date
        }
        for c in columns
    ]
    
    analyst_res = answer_analyst_query(
        question=req.question,
        table_name=table_name,
        schema_info=schema_info,
        parquet_path=parquet_path
    )
    
    return {
        "sql_query": analyst_res.sql_query,
        "explanation": analyst_res.explanation,
        "results": analyst_res.raw_data
    }

@router.get("/datasets/{dataset_id}/report")
def generate_executive_report(dataset_id: str, db: Session = Depends(get_db)):
    dataset = get_dataset_or_404(dataset_id, db)
    df = load_dataset_df(dataset)
    columns = db.query(DatasetSchema).filter(DatasetSchema.dataset_id == dataset_id).all()
    date_col = next((c.safe_column_name for c in columns if c.is_date), None)
    
    kpis = compute_dynamic_kpis(df, date_col=date_col)
    quality = dataset.quality_report
    
    return {
        "report_title": f"InsightX Executive Investigation: {dataset.name}",
        "generated_at": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"),
        "dataset_summary": {
            "name": dataset.name,
            "records": len(df),
            "columns": len(df.columns),
            "quality_score": quality.quality_score if quality else None
        },
        "kpi_executive_summary": kpis,
        "key_findings": [
            f"Dataset contains {len(df):,} validated transactions across {len(df.columns)} analytical features.",
            f"Overall Data Quality Score stands at {quality.quality_score if quality else 'N/A'} / 100 with all major discrepancies resolved in preprocessing.",
            "Operational risk metrics were tracked with period-over-period delta indicators."
        ]
    }
"""

with open(os.path.join(api_dir, "router.py"), "w", encoding="utf-8") as f:
    f.write(router_py)

with open(os.path.join(api_dir, "__init__.py"), "w", encoding="utf-8") as f:
    f.write("from .router import router\n__all__ = ['router']")

print("API v1 Router successfully written.")
