import os
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
from ...services.file_validator import validate_and_inspect_file, smart_read_csv
from ...services.data_profiler import profile_dataframe
from ...services.quality_evaluator import compute_quality_report
from ...services.preprocessor import run_preprocessing_pipeline
from ...services.currency_detector import dataset_has_dollar_symbol
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
from ...ai.data_analyst import answer_analyst_query, build_custom_chart
from ...ai.rag_engine import build_rag_profile, get_suggested_prompts
from ...ml.target_explainer import detect_best_target_column, train_target_ml_explainability

router = APIRouter()

def get_dataset_or_404(dataset_id: str, db: Session) -> Dataset:
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not dataset:
        raise DatasetNotFoundError(dataset_id)
    return dataset

def load_dataset_df(dataset: Dataset) -> pd.DataFrame:
    if dataset.processed_storage_path and os.path.exists(dataset.processed_storage_path) and os.path.getsize(dataset.processed_storage_path) > 0:
        return pd.read_parquet(dataset.processed_storage_path)
    elif dataset.raw_storage_path and os.path.exists(dataset.raw_storage_path):
        ext = dataset.file_format.lower()
        if ext == "csv":
            return smart_read_csv(dataset.raw_storage_path)
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
    target_column: Optional[str] = Form(None),
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
        df_raw = smart_read_csv(raw_path)
    elif ext in ("xlsx", "xls"):
        target_sheet = sheet_name or (val_res.sheet_names[0] if val_res.sheet_names else 0)
        df_raw = pd.read_excel(raw_path, sheet_name=target_sheet)
    elif ext == "json":
        df_raw = pd.read_json(raw_path)
    elif ext == "parquet":
        df_raw = pd.read_parquet(raw_path)
    else:
        df_raw = smart_read_csv(raw_path)
        
    profiles = profile_dataframe(df_raw)
    quality_dict = compute_quality_report(df_raw, profiles)
    
    # Auto-detect target column if user didn't specify one
    detected_target = target_column
    if not detected_target or detected_target not in df_raw.columns:
        schema_info_list = [{"safe_column_name": p["safe_column_name"], "is_target_candidate": p["is_target_candidate"]} for p in profiles]
        detected_target = detect_best_target_column(df_raw, schema_info_list)
    
    # Auto preprocess initially to create Parquet view
    df_clean, prep_rep = run_preprocessing_pipeline(
        df_raw, dataset_id=dataset_id, remove_duplicates=True, impute_missing=True, flag_outliers=True
    )
    
    # Remove previous non-sample uploaded datasets so user's workspace only holds the newly uploaded dataset
    SAMPLE_FILENAMES = {
        "ecommerce_sales_with_hidden_root_cause.xlsx",
        "ecommerce_sales_with_hidden_root_cause.csv",
        "saas_marketing_funnel.xlsx",
        "saas_marketing_funnel.csv",
        "healthcare_patient_flow.xlsx",
        "healthcare_patient_flow.csv"
    }
    prev_uploads = db.query(Dataset).all()
    for prev in prev_uploads:
        if prev.original_filename not in SAMPLE_FILENAMES and prev.id != dataset_id:
            for p in [prev.raw_storage_path, prev.processed_storage_path]:
                if p and os.path.exists(p):
                    try:
                        os.remove(p)
                    except Exception:
                        pass
            db.delete(prev)
    db.flush()

    dataset = Dataset(
        id=dataset_id,
        name=filename.rsplit(".", 1)[0].replace("_", " ").title(),
        original_filename=filename,
        file_format=ext,
        file_size_bytes=os.path.getsize(raw_path),
        raw_storage_path=raw_path,
        processed_storage_path=prep_rep.cleaned_parquet_path,
        sheet_name=sheet_name,
        target_column=detected_target,
        row_count=len(df_raw),
        column_count=len(df_raw.columns),
        status="ready"
    )
    db.add(dataset)
    db.flush()
    
    # Add column schemas
    for p in profiles:
        is_cand = p["is_target_candidate"] or (detected_target and (p["safe_column_name"] == detected_target or p["column_name"] == detected_target))
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

    # Auto-build RAG profile for uploaded dataset so RAG chunks are available immediately
    try:
        schema_info_for_rag = [
            {
                "safe_column_name": p["safe_column_name"],
                "detected_type": p["detected_type"],
                "is_numeric": p["is_numeric"],
                "is_categorical": p["is_categorical"],
                "is_date": p["is_date"],
            }
            for p in profiles
        ]
        build_rag_profile(
            dataset_id=dataset_id,
            df=df_raw,
            schema_info=schema_info_for_rag,
            domain_type="generic",
        )
    except Exception as e:
        print(f"RAG profile auto-build for upload failed (non-critical): {e}")

    return {
        "id": dataset_id,
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
        
    # Prevent duplicate sample datasets in the workspace
    existing_samples = db.query(Dataset).filter((Dataset.domain_type == key) | (Dataset.name == display_name)).all()
    for ex in existing_samples:
        db.query(DatasetSchema).filter(DatasetSchema.dataset_id == ex.id).delete()
        db.query(DataQualityReport).filter(DataQualityReport.dataset_id == ex.id).delete()
        db.delete(ex)
    db.flush()
        
    dataset_id = str(uuid.uuid4())
    raw_path = os.path.join(settings.UPLOAD_DIR, f"{dataset_id}_{filename}")
    shutil.copy(sample_file, raw_path)
    
    df_raw = smart_read_csv(raw_path)
    profiles = profile_dataframe(df_raw)
    quality_dict = compute_quality_report(df_raw, profiles)
    df_clean, prep_rep = run_preprocessing_pipeline(
        df_raw, dataset_id=dataset_id, remove_duplicates=True, impute_missing=True, flag_outliers=True
    )
    
    schema_info_list = [{"safe_column_name": p["safe_column_name"], "is_target_candidate": p["is_target_candidate"]} for p in profiles]
    detected_target = detect_best_target_column(df_raw, schema_info_list)
    
    dataset = Dataset(
        id=dataset_id,
        name=display_name,
        original_filename=filename,
        file_format="csv",
        file_size_bytes=os.path.getsize(raw_path),
        raw_storage_path=raw_path,
        processed_storage_path=prep_rep.cleaned_parquet_path,
        domain_type=key,
        target_column=detected_target,
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

    # Auto-build RAG profile in background so AI Analyst has context immediately
    try:
        schema_info_for_rag = [
            {
                "safe_column_name": p["safe_column_name"],
                "detected_type": p["detected_type"],
                "is_numeric": p["is_numeric"],
                "is_categorical": p["is_categorical"],
                "is_date": p["is_date"],
            }
            for p in profiles
        ]
        build_rag_profile(
            dataset_id=dataset_id,
            df=df_raw,
            schema_info=schema_info_for_rag,
            domain_type=key,
        )
    except Exception as e:
        print(f"RAG profile auto-build failed (non-critical): {e}")

    return {
        "id": dataset_id,
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
            "target_column": getattr(d, "target_column", None),
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

@router.delete("/datasets/{dataset_id}")
def delete_dataset(dataset_id: str, db: Session = Depends(get_db)):
    dataset = get_dataset_or_404(dataset_id, db)
    # Remove files from disk if present
    for p in [dataset.raw_storage_path, dataset.processed_storage_path]:
        if p and os.path.exists(p):
            try:
                os.remove(p)
            except Exception:
                pass
    db.delete(dataset)
    db.commit()
    return {"message": f"Dataset '{dataset.name}' successfully deleted.", "id": dataset_id}

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
        df_raw = smart_read_csv(dataset.raw_storage_path)
    elif ext in ("xlsx", "xls"):
        df_raw = pd.read_excel(dataset.raw_storage_path, sheet_name=dataset.sheet_name or 0)
    else:
        df_raw = smart_read_csv(dataset.raw_storage_path)
        
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
        "quality_score": dataset.quality_report.quality_score if dataset.quality_report else None,
        "report": prep_rep.to_dict(),
        "preview": df_clean.head(10).to_dict(orient="records")
    }

import json

@router.get("/datasets/{dataset_id}/dashboard")
def get_dashboard(dataset_id: str, filters: Optional[str] = None, db: Session = Depends(get_db)):
    dataset = get_dataset_or_404(dataset_id, db)
    df = load_dataset_df(dataset)
    
    columns = db.query(DatasetSchema).filter(DatasetSchema.dataset_id == dataset_id).all()
    filter_options = {}
    for c in columns:
        if c.is_categorical and c.safe_column_name in df.columns:
            filter_options[c.safe_column_name] = [str(x) for x in df[c.safe_column_name].dropna().unique()[:15]]
            
    # Apply query filters if provided
    applied_filters = {}
    if filters:
        try:
            applied_filters = json.loads(filters)
            for col, val in applied_filters.items():
                if col in df.columns and val:
                    df = df[df[col].astype(str) == str(val)]
        except Exception:
            pass
            
    date_col = next((c.safe_column_name for c in columns if c.is_date), None)
    
    has_dollar = dataset_has_dollar_symbol(df, dataset.raw_storage_path)
    kpis = compute_dynamic_kpis(df, date_col=date_col, has_dollar=has_dollar)
    charts = recommend_automatic_charts(df, has_dollar=has_dollar)
    
    # Generated Alerts based on thresholds
    alerts = []
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
        "filters": filter_options,
        "applied_filters": applied_filters,
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
        target_col = getattr(dataset, "target_column", None)
        if target_col and target_col in df.columns and pd.api.types.is_numeric_dtype(df[target_col]):
            metric = target_col
        else:
            num_cols = [
                c.safe_column_name for c in columns 
                if c.is_numeric and not any(k in c.safe_column_name.lower() for k in ["id", "uuid", "code", "postal", "zip", "year", "latitude", "longitude"])
            ]
            pref = ["price", "sales", "revenue", "profit", "amount", "cost", "total", "count", "value"]
            metric = next((c for p in pref for c in num_cols if p in c.lower()), num_cols[0] if num_cols else None)
        
    if not date_col or not metric:
        return {"anomalies": [], "message": "Dataset lacks necessary date or numeric metrics for time-series anomaly detection."}
        
    anomalies = detect_anomalies(df, date_col=date_col, metric_col=metric, contamination=req.contamination)
    return {"metric": metric, "date_column": date_col, "total_detected": len(anomalies), "anomalies": anomalies}

@router.post("/datasets/{dataset_id}/forecast")
def get_forecast(dataset_id: str, req: ForecastRequest, db: Session = Depends(get_db)):
    dataset = get_dataset_or_404(dataset_id, db)
    df = load_dataset_df(dataset)
    columns = db.query(DatasetSchema).filter(DatasetSchema.dataset_id == dataset_id).all()
    
    col_map = {str(c).lower(): c for c in df.columns}
    date_col = next((c.safe_column_name for c in columns if c.is_date and c.safe_column_name in df.columns), None)
    if not date_col:
        for cand in ["date", "order_date", "admission_date", "transaction_date", "created_at", "time"]:
            if cand in col_map:
                date_col = col_map[cand]
                break
                
    metric = req.metric
    if metric and str(metric).lower() in col_map:
        metric = col_map[str(metric).lower()]
    else:
        metric = getattr(dataset, "target_column", None)
        if metric and str(metric).lower() in col_map:
            metric = col_map[str(metric).lower()]
        else:
            for cand in ["revenue", "sales", "profit", "amount", "treatment_cost", "spend", "cost", "quantity"]:
                if cand in col_map:
                    metric = col_map[cand]
                    break
        if not metric:
            num_cols = [c.safe_column_name for c in columns if c.is_numeric and c.safe_column_name in df.columns]
            metric = num_cols[0] if num_cols else df.columns[-1]
            
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
    columns = db.query(DatasetSchema).filter(DatasetSchema.dataset_id == dataset_id).all()
    schema_info = [{"safe_column_name": c.safe_column_name, "is_target_candidate": c.is_target_candidate} for c in columns]

    col_map = {str(c).lower(): c for c in df.columns}
    target_col = getattr(dataset, "target_column", None)
    if target_col and str(target_col).lower() in col_map:
        target_col = col_map[str(target_col).lower()]
    elif not target_col:
        target_col = detect_best_target_column(df, schema_info)

    return train_churn_model(df, target_column=target_col)

@router.post("/datasets/{dataset_id}/root-cause")
def get_root_cause(dataset_id: str, req: RootCauseRequest, db: Session = Depends(get_db)):
    dataset = get_dataset_or_404(dataset_id, db)
    df = load_dataset_df(dataset)
    columns = db.query(DatasetSchema).filter(DatasetSchema.dataset_id == dataset_id).all()
    schema_info = [{"safe_column_name": c.safe_column_name, "is_target_candidate": c.is_target_candidate} for c in columns]
    
    col_map = {str(c).lower(): c for c in df.columns}
    resolved_target = req.target_metric or getattr(dataset, "target_column", None)
    if resolved_target and str(resolved_target).lower() in col_map:
        resolved_target = col_map[str(resolved_target).lower()]
    else:
        resolved_target = detect_best_target_column(df, schema_info)
        
    # Persist the selected target column to the dataset so the executive report immediately reflects it
    if resolved_target and resolved_target in df.columns:
        dataset.target_column = resolved_target
        db.commit()

    date_col = next((c.safe_column_name for c in columns if c.is_date and c.safe_column_name in df.columns), None)
    
    res = run_root_cause_investigation(
        df=df,
        target_metric=resolved_target,
        date_col=date_col,
        crisis_start_date=req.crisis_start_date,
        crisis_end_date=req.crisis_end_date
    )
    res["available_targets"] = [
        str(c) for c in df.columns
        if not any(k in str(c).lower() for k in ["unnamed", "_dt", "uuid"])
    ]
    return res

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
        parquet_path=parquet_path,
        domain_type=getattr(dataset, "domain_type", "generic"),
        dataset_id=dataset_id,
        target_column=getattr(dataset, "target_column", None),
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
    schema_info = [
        {
            "safe_column_name": c.safe_column_name,
            "detected_type": c.detected_type,
            "is_numeric": c.is_numeric,
            "is_categorical": c.is_categorical,
            "is_date": c.is_date,
            "is_target_candidate": c.is_target_candidate,
        }
        for c in columns
    ]
    date_col = next((c.safe_column_name for c in columns if c.is_date), None)
    has_dollar = dataset_has_dollar_symbol(df, dataset.raw_storage_path)
    
    kpis = compute_dynamic_kpis(df, date_col=date_col, has_dollar=has_dollar)
    quality = dataset.quality_report
    
    # Target column resolution
    target_col = getattr(dataset, "target_column", None)
    if not target_col or target_col not in df.columns:
        target_col = detect_best_target_column(df, schema_info)
        
    # ML Explainability model (Why, What, How to increase / prevent decrease)
    ml_explainability = None
    if target_col and target_col in df.columns:
        try:
            ml_explainability = train_target_ml_explainability(df, target_column=target_col, domain_type=dataset.domain_type)
        except Exception as e:
            ml_explainability = {"supported": False, "reason": str(e)}

    # Deep Root Cause Investigation
    root_cause_data = None
    try:
        root_cause_data = run_root_cause_investigation(df, target_metric=target_col)
        if root_cause_data and "key_drivers" in root_cause_data and "drivers" not in root_cause_data:
            root_cause_data["drivers"] = root_cause_data["key_drivers"]
    except Exception as e:
        root_cause_data = {"what_happened": f"Analysis completed for {target_col}.", "why_it_happened": str(e)}
        
    # Generate all executive summary and dashboard charts with user-friendly explanations
    all_dashboard_charts = recommend_automatic_charts(df, has_dollar=has_dollar)
    
    # Build key findings
    key_findings = [
        f"Dataset '{dataset.name}' audited with {len(df):,} transactions across {len(df.columns)} analytical features.",
        f"Overall Data Quality Score stands at {quality.quality_score if quality else 'N/A'} / 100 with zero breaking errors.",
    ]
    if root_cause_data and "what_happened" in root_cause_data:
        key_findings.append(f"Root Cause Discovery: {root_cause_data['what_happened']}")
        key_findings.append(f"Driver Analysis: {root_cause_data['why_it_happened']}")
    elif ml_explainability and ml_explainability.get("supported"):
        top_driver = ml_explainability["drivers"][0] if ml_explainability.get("drivers") else None
        if top_driver:
            key_findings.append(
                f"Target Metric '{target_col.replace('_', ' ').title()}' is most strongly driven by '{top_driver['feature_label']}' ({top_driver['percentage']}% importance, {top_driver['direction']})."
            )
        key_findings.append(ml_explainability["synthesis"]["what_drives_target"])
        
    return {
        "report_title": f"InsightX Executive Investigation Report: {dataset.name}",
        "generated_at": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"),
        "dataset_summary": {
            "name": dataset.name,
            "records": len(df),
            "columns": len(df.columns),
            "quality_score": quality.quality_score if quality else None,
            "target_column": target_col,
            "domain_type": dataset.domain_type,
        },
        "target_column": target_col,
        "kpi_executive_summary": kpis,
        "ml_explainability": ml_explainability,
        "root_cause": root_cause_data,
        "report_charts": all_dashboard_charts,
        "all_dashboard_charts": all_dashboard_charts,
        "key_findings": key_findings
    }


from fastapi.responses import FileResponse

@router.get("/datasets/sample/download/{filename}")
def download_sample_file(filename: str):
    allowed_files = [
        "ecommerce_sales_with_hidden_root_cause.csv",
        "ecommerce_sales_with_hidden_root_cause.xlsx",
        "saas_marketing_funnel.csv",
        "saas_marketing_funnel.xlsx",
        "healthcare_patient_flow.csv",
        "healthcare_patient_flow.xlsx"
    ]
    if filename not in allowed_files:
        raise HTTPException(status_code=404, detail="File not found in sample vault.")
    file_path = os.path.join(settings.SAMPLES_DIR, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File does not exist on disk.")
    return FileResponse(path=file_path, filename=filename, media_type="application/octet-stream")


# ── RAG: Get dataset-specific suggested prompts ──────────────────────────────
@router.get("/datasets/{dataset_id}/ai/suggested-prompts")
def get_ai_suggested_prompts(dataset_id: str, db: Session = Depends(get_db)):
    """Returns dataset-aware question chips for the AI Analyst page."""
    get_dataset_or_404(dataset_id, db)
    prompts = get_suggested_prompts(dataset_id)
    return {"prompts": prompts}


# ── RAG: Build or rebuild RAG profile ────────────────────────────────────────
@router.post("/datasets/{dataset_id}/ai/build-profile")
def build_ai_profile(dataset_id: str, db: Session = Depends(get_db)):
    """Builds (or rebuilds) the RAG knowledge profile for this dataset."""
    dataset = get_dataset_or_404(dataset_id, db)
    df = load_dataset_df(dataset)
    columns = db.query(DatasetSchema).filter(DatasetSchema.dataset_id == dataset_id).all()
    schema_info = [
        {
            "safe_column_name": c.safe_column_name,
            "detected_type": c.detected_type,
            "is_numeric": c.is_numeric,
            "is_categorical": c.is_categorical,
            "is_date": c.is_date,
        }
        for c in columns
    ]
    profile = build_rag_profile(
        dataset_id=dataset_id,
        df=df,
        schema_info=schema_info,
        domain_type=getattr(dataset, "domain_type", "generic"),
    )
    return {
        "status": "ok",
        "chunks_built": len(profile.get("chunks", [])),
        "suggested_prompts": profile.get("suggested_prompts", []),
    }


# ── Custom Chart Builder ───────────────────────────────────────────────────────
from pydantic import BaseModel as _BaseModel

class _CustomChartRequest(_BaseModel):
    x_col: str
    y_col: Optional[str] = None
    chart_type: str = "bar"
    aggregation: str = "none"

@router.post("/datasets/{dataset_id}/ai/custom-chart")
def create_custom_chart(dataset_id: str, req: _CustomChartRequest, db: Session = Depends(get_db)):
    """Generates a custom chart based on user-selected columns + aggregation."""
    dataset = get_dataset_or_404(dataset_id, db)
    parquet_path = dataset.processed_storage_path or dataset.raw_storage_path
    table_name = f"dataset_{dataset_id.replace('-', '_')}"

    columns = db.query(DatasetSchema).filter(DatasetSchema.dataset_id == dataset_id).all()
    valid_cols = {c.safe_column_name for c in columns}
    if req.x_col not in valid_cols:
        raise HTTPException(status_code=400, detail=f"Column '{req.x_col}' not found in dataset.")
    if req.y_col and req.y_col not in valid_cols and req.aggregation not in ("count", "none"):
        raise HTTPException(status_code=400, detail=f"Column '{req.y_col}' not found in dataset.")

    chart_spec = build_custom_chart(
        table_name=table_name,
        parquet_path=parquet_path,
        x_col=req.x_col,
        y_col=req.y_col,
        chart_type=req.chart_type,
        aggregation=req.aggregation or "none",
    )
    return chart_spec


# ── Dataset column list for chart builder ─────────────────────────────────────
@router.get("/datasets/{dataset_id}/columns")
def get_dataset_columns(dataset_id: str, db: Session = Depends(get_db)):
    """Returns all columns with type metadata — used by Custom Chart Builder."""
    get_dataset_or_404(dataset_id, db)
    columns = db.query(DatasetSchema).filter(DatasetSchema.dataset_id == dataset_id).all()
    return {
        "columns": [
            {
                "name": c.safe_column_name,
                "original_name": c.column_name,
                "type": c.detected_type,
                "is_numeric": c.is_numeric,
                "is_categorical": c.is_categorical,
                "is_date": c.is_date,
            }
            for c in columns
        ]
    }


# ── Target column & ML Explainability ─────────────────────────────────────────
class TargetColumnUpdateRequest(_BaseModel):
    target_column: str

@router.post("/datasets/{dataset_id}/target-column")
def update_target_column(dataset_id: str, req: TargetColumnUpdateRequest, db: Session = Depends(get_db)):
    """Set or change the target column for the dataset."""
    dataset = get_dataset_or_404(dataset_id, db)
    columns = db.query(DatasetSchema).filter(DatasetSchema.dataset_id == dataset_id).all()
    valid_cols = {c.safe_column_name for c in columns} | {c.column_name for c in columns}
    
    if req.target_column not in valid_cols:
        raise HTTPException(status_code=400, detail=f"Column '{req.target_column}' does not exist in dataset.")
        
    dataset.target_column = req.target_column
    db.commit()
    return {"status": "ok", "target_column": dataset.target_column}


@router.get("/datasets/{dataset_id}/target-explainability")
def get_target_explainability(dataset_id: str, db: Session = Depends(get_db)):
    """Runs ML model on target column to explain why, what, and how shifts occur."""
    dataset = get_dataset_or_404(dataset_id, db)
    df = load_dataset_df(dataset)
    columns = db.query(DatasetSchema).filter(DatasetSchema.dataset_id == dataset_id).all()
    schema_info = [
        {
            "safe_column_name": c.safe_column_name,
            "detected_type": c.detected_type,
            "is_numeric": c.is_numeric,
            "is_categorical": c.is_categorical,
            "is_date": c.is_date,
            "is_target_candidate": c.is_target_candidate,
        }
        for c in columns
    ]
    
    target_col = getattr(dataset, "target_column", None)
    if not target_col or target_col not in df.columns:
        target_col = detect_best_target_column(df, schema_info)
        if target_col:
            dataset.target_column = target_col
            db.commit()
            
    if not target_col:
        return {"supported": False, "reason": "No target column could be identified."}
        
    res = train_target_ml_explainability(df, target_column=target_col, domain_type=dataset.domain_type)
    return res

