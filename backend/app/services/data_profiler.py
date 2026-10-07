import warnings
warnings.filterwarnings('ignore')
import re
from typing import Dict, Any, List
import pandas as pd
import numpy as np

def sanitize_column_name(col: str) -> str:
    s = str(col).strip().lower()
    s = re.sub(r"[^\w\s]", "", s)
    s = re.sub(r"\s+", "_", s)
    return s if s else "col"

def infer_column_type(series: pd.Series) -> str:
    non_nulls = series.dropna()
    if len(non_nulls) == 0:
        return "text"
        
    col_name = str(series.name).lower()
    
    # 1. Explicit DateTime type
    if pd.api.types.is_datetime64_any_dtype(series):
        return "datetime"
        
    # 2. Boolean check
    if series.dtype == bool or set(non_nulls.unique()).issubset({True, False, 0, 1, "0", "1", "true", "false", "True", "False"}):
        if len(non_nulls.unique()) <= 2 and not pd.api.types.is_float_dtype(series):
            return "boolean"

    # 3. Numeric checks
    if pd.api.types.is_numeric_dtype(series):
        if pd.api.types.is_integer_dtype(series) or (series.dropna() % 1 == 0).all():
            return "integer"
        return "float"

    # 4. Date parsing on non-numeric strings
    sample = non_nulls.head(30)
    try:
        parsed = pd.to_datetime(sample, errors="coerce")
        if parsed.notna().sum() >= len(sample) * 0.8:
            return "datetime"
    except Exception:
        pass
        
    # 5. Identifier check
    if "id" in col_name or "code" in col_name or "uuid" in col_name:
        return "id"
        
    # 6. Categorical vs Free Text
    distinct_ratio = series.nunique() / max(len(series), 1)
    if series.nunique() <= 60 or distinct_ratio < 0.10:
        return "categorical"
        
    return "text"

def profile_dataframe(df: pd.DataFrame) -> List[Dict[str, Any]]:
    profiles = []
    
    for col in df.columns:
        series = df[col]
        safe_name = sanitize_column_name(col)
        detected_type = infer_column_type(series)
        
        is_date = (detected_type == "datetime")
        is_numeric = (detected_type in ("integer", "float"))
        is_categorical = (detected_type == "categorical")
        
        col_lower = str(col).lower()
        is_target_candidate = False
        if is_numeric and any(k in col_lower for k in ["revenue", "profit", "sales", "churn", "target", "score", "amount", "cost"]):
            is_target_candidate = True
        elif detected_type == "boolean" and any(k in col_lower for k in ["churn", "cancelled", "fraud", "converted"]):
            is_target_candidate = True
            
        distinct_count = int(series.nunique(dropna=True))
        missing_count = int(series.isna().sum())
        
        min_val = None
        max_val = None
        if is_numeric and len(series.dropna()) > 0:
            min_val = str(round(float(series.min()), 2))
            max_val = str(round(float(series.max()), 2))
        elif is_date and len(series.dropna()) > 0:
            min_val = str(series.min())
            max_val = str(series.max())
            
        sample_vals = [str(x) for x in series.dropna().unique()[:5]]
        
        profiles.append({
            "column_name": str(col),
            "safe_column_name": safe_name,
            "detected_type": detected_type,
            "is_date": is_date,
            "is_numeric": is_numeric,
            "is_categorical": is_categorical,
            "is_target_candidate": is_target_candidate,
            "distinct_count": distinct_count,
            "missing_count": missing_count,
            "min_value": min_val,
            "max_value": max_val,
            "sample_values": sample_vals
        })
        
    return profiles

