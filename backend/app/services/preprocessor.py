import os
from typing import Dict, Any, List, Optional, Tuple
import pandas as pd
import numpy as np
from ..core.config import settings
from .data_profiler import profile_dataframe, sanitize_column_name

class PreprocessingReport:
    def __init__(
        self,
        original_rows: int,
        processed_rows: int,
        duplicates_removed: int,
        imputed_columns: Dict[str, str],
        outliers_flagged: int,
        cleaned_parquet_path: str,
        column_mapping: Dict[str, str]
    ):
        self.original_rows = original_rows
        self.processed_rows = processed_rows
        self.duplicates_removed = duplicates_removed
        self.imputed_columns = imputed_columns
        self.outliers_flagged = outliers_flagged
        self.cleaned_parquet_path = cleaned_parquet_path
        self.column_mapping = column_mapping

    def to_dict(self) -> Dict[str, Any]:
        return {
            "original_rows": self.original_rows,
            "processed_rows": self.processed_rows,
            "duplicates_removed": self.duplicates_removed,
            "imputed_columns": self.imputed_columns,
            "outliers_flagged": self.outliers_flagged,
            "cleaned_parquet_path": self.cleaned_parquet_path,
            "column_mapping": self.column_mapping
        }

def run_preprocessing_pipeline(
    df_raw: pd.DataFrame,
    dataset_id: str,
    remove_duplicates: bool = True,
    impute_missing: bool = True,
    flag_outliers: bool = True
) -> Tuple[pd.DataFrame, PreprocessingReport]:
    df = df_raw.copy()
    original_rows = len(df)
    
    # 1. Deduplication
    dups_removed = 0
    if remove_duplicates:
        dups_count = int(df.duplicated().sum())
        if dups_count > 0:
            df = df.drop_duplicates().reset_index(drop=True)
            dups_removed = dups_count
            
    # 2. Column mapping & sanitization
    column_mapping = {}
    for col in df.columns:
        safe_name = sanitize_column_name(col)
        column_mapping[str(col)] = safe_name
        
    df = df.rename(columns=column_mapping)
    
    # 3. Deterministic Profiling
    profiles = profile_dataframe(df)
    imputed_summary = {}
    
    # 4. Missing value imputation
    if impute_missing:
        for p in profiles:
            col = p["safe_column_name"]
            if p["missing_count"] > 0:
                if p["is_numeric"]:
                    series = df[col].dropna()
                    if len(series) > 0:
                        skewness = series.skew()
                        if abs(skewness) > 1.0:
                            median_val = float(series.median())
                            df[col] = df[col].fillna(median_val)
                            imputed_summary[col] = f"Imputed with Median ({median_val:.2f})"
                        else:
                            mean_val = float(series.mean())
                            df[col] = df[col].fillna(mean_val)
                            imputed_summary[col] = f"Imputed with Mean ({mean_val:.2f})"
                elif p["is_categorical"]:
                    mode_series = df[col].mode()
                    if len(mode_series) > 0 and (df[col].isna().sum() / len(df)) < 0.05:
                        mode_val = mode_series[0]
                        df[col] = df[col].fillna(mode_val)
                        imputed_summary[col] = f"Imputed with Mode ('{mode_val}')"
                    else:
                        df[col] = df[col].fillna("Unknown")
                        imputed_summary[col] = "Imputed with 'Unknown'"
                elif p["is_date"]:
                    df[col] = df[col].ffill().bfill()
                    imputed_summary[col] = "Imputed with Forward/Backward fill"
                    
    # 5. Date parsing
    for p in profiles:
        col = p["safe_column_name"]
        if p["is_date"]:
            try:
                df[col] = pd.to_datetime(df[col], errors="coerce")
            except Exception:
                pass
                
    # 6. Outlier flagging (never delete valid records)
    total_outliers_flagged = 0
    if flag_outliers:
        for p in profiles:
            if p["is_numeric"]:
                col = p["safe_column_name"]
                series = df[col].dropna()
                if len(series) >= 15:
                    q1 = series.quantile(0.25)
                    q3 = series.quantile(0.75)
                    iqr = q3 - q1
                    if iqr > 0:
                        outliers = ((series < (q1 - 3.0 * iqr)) | (series > (q3 + 3.0 * iqr)))
                        total_outliers_flagged += int(outliers.sum())
                        
    # 7. Columnar Parquet persistence
    processed_dir = settings.PROCESSED_DIR
    os.makedirs(processed_dir, exist_ok=True)
    parquet_path = os.path.join(processed_dir, f"{dataset_id}_clean.parquet")
    
    df.to_parquet(parquet_path, engine="pyarrow", index=False)
    
    report = PreprocessingReport(
        original_rows=original_rows,
        processed_rows=len(df),
        duplicates_removed=dups_removed,
        imputed_columns=imputed_summary,
        outliers_flagged=total_outliers_flagged,
        cleaned_parquet_path=parquet_path,
        column_mapping=column_mapping
    )
    
    return df, report
