import os

services_dir = r"C:\Users\HP\.gemini\antigravity\scratch\InsightX\backend\app\services"
os.makedirs(services_dir, exist_ok=True)

# 1. file_validator.py
file_validator_py = """import os
from typing import Dict, Any, List, Optional
import pandas as pd

ALLOWED_EXTENSIONS = {"csv", "xlsx", "xls", "json", "parquet"}

class FileValidationResult:
    def __init__(self, is_valid: bool, file_format: str, error_message: Optional[str] = None, sheet_names: Optional[List[str]] = None, df_preview: Optional[pd.DataFrame] = None):
        self.is_valid = is_valid
        self.file_format = file_format
        self.error_message = error_message
        self.sheet_names = sheet_names or []
        self.df_preview = df_preview

def validate_and_inspect_file(file_path: str, max_size_mb: int = 50) -> FileValidationResult:
    if not os.path.exists(file_path):
        return FileValidationResult(False, "", f"File does not exist at path: {file_path}")
    
    file_size = os.path.getsize(file_path)
    if file_size > max_size_mb * 1024 * 1024:
        return FileValidationResult(False, "", f"File size ({file_size / (1024*1024):.1f}MB) exceeds limit of {max_size_mb}MB")
    
    ext = file_path.split(".")[-1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        return FileValidationResult(False, ext, f"Unsupported format '.{ext}'. Supported: {', '.join(ALLOWED_EXTENSIONS)}")
    
    sheet_names = []
    df_preview = None
    try:
        if ext == "csv":
            df_preview = pd.read_csv(file_path, nrows=5)
        elif ext in ("xlsx", "xls"):
            excel_file = pd.ExcelFile(file_path)
            sheet_names = excel_file.sheet_names
            df_preview = pd.read_excel(file_path, sheet_name=sheet_names[0], nrows=5)
        elif ext == "json":
            df_preview = pd.read_json(file_path, nrows=5)
        elif ext == "parquet":
            df_preview = pd.read_parquet(file_path)
            df_preview = df_preview.head(5)
            
        return FileValidationResult(True, ext, sheet_names=sheet_names, df_preview=df_preview)
    except Exception as e:
        return FileValidationResult(False, ext, f"Error parsing {ext.upper()} content: {str(e)}")
"""

# 2. data_profiler.py
data_profiler_py = """import re
from typing import Dict, Any, List
import pandas as pd
import numpy as np

def sanitize_column_name(col: str) -> str:
    \"\"\"Converts raw column name into a safe, SQL-compliant snake_case name while preserving analytical context.\"\"\"
    s = str(col).strip().lower()
    s = re.sub(r"[^\w\s]", "", s)
    s = re.sub(r"\s+", "_", s)
    return s if s else "col"

def infer_column_type(series: pd.Series) -> str:
    \"\"\"Deterministically infers the semantic business type of a series.\"\"\"
    non_nulls = series.dropna()
    if len(non_nulls) == 0:
        return "text"
    
    # Check boolean
    if series.dtype == bool or set(non_nulls.unique()).issubset({True, False, 0, 1, "0", "1", "true", "false", "True", "False"}):
        if len(non_nulls.unique()) <= 2 and series.dtype != float:
            return "boolean"
            
    # Check datetime
    if pd.api.types.is_datetime64_any_dtype(series):
        return "datetime"
    
    if series.dtype == object:
        # Check if can be parsed as date
        sample = non_nulls.head(20).astype(str)
        date_patterns = [
            r"^\d{4}-\d{2}-\d{2}", # YYYY-MM-DD
            r"^\d{2}/\d{2}/\d{4}", # MM/DD/YYYY or DD/MM/YYYY
            r"^\d{4}/\d{2}/\d{2}"  # YYYY/MM/DD
        ]
        if any(sample.str.match(p).all() for p in date_patterns):
            try:
                pd.to_datetime(sample, errors="raise")
                return "datetime"
            except:
                pass
                
    # Check numeric
    if pd.api.types.is_numeric_dtype(series):
        if pd.api.types.is_integer_dtype(series) or (series.dropna() % 1 == 0).all():
            return "integer"
        return "float"
        
    # Check if ID
    col_name = str(series.name).lower()
    if "id" in col_name or "code" in col_name or "uuid" in col_name:
        return "id"
        
    # Check categorical vs text
    distinct_ratio = series.nunique() / max(len(series), 1)
    if series.nunique() <= 50 or distinct_ratio < 0.15:
        return "categorical"
        
    return "text"

def profile_dataframe(df: pd.DataFrame) -> List[Dict[str, Any]]:
    \"\"\"Profiles all columns in a dataset and returns deterministic column metadata.\"\"\"
    profiles = []
    
    for col in df.columns:
        series = df[col]
        safe_name = sanitize_column_name(col)
        detected_type = infer_column_type(series)
        
        is_date = (detected_type == "datetime")
        is_numeric = (detected_type in ("integer", "float"))
        is_categorical = (detected_type == "categorical")
        
        # Candidate target variable: usually continuous revenue/profit or binary churn/outcome
        col_lower = str(col).lower()
        is_target_candidate = False
        if is_numeric and any(k in col_lower for k in ["revenue", "profit", "sales", "churn", "target", "score", "amount"]):
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
"""

# 3. quality_evaluator.py
quality_evaluator_py = """from typing import Dict, Any, List
import pandas as pd
import numpy as np

def compute_quality_report(df: pd.DataFrame, column_profiles: List[Dict[str, Any]]) -> Dict[str, Any]:
    \"\"\"Generates an enterprise-grade Data Quality Score (0-100) and actionable remediation checklist.\"\"\"
    total_rows = len(df)
    total_cols = len(df.columns)
    total_cells = total_rows * total_cols if total_rows * total_cols > 0 else 1
    
    # 1. Missing cell metrics
    missing_cells = int(df.isna().sum().sum())
    missing_pct = round((missing_cells / total_cells) * 100, 2)
    
    # 2. Duplicate rows
    dup_rows = int(df.duplicated().sum())
    
    # 3. Constant columns (cardinality == 1)
    constant_cols = [p["column_name"] for p in column_profiles if p["distinct_count"] <= 1 and total_rows > 1]
    
    # 4. Outlier detection using IQR
    potential_outliers = 0
    numeric_cols = [p["column_name"] for p in column_profiles if p["is_numeric"]]
    for col in numeric_cols:
        series = df[col].dropna()
        if len(series) >= 10:
            q1 = series.quantile(0.25)
            q3 = series.quantile(0.75)
            iqr = q3 - q1
            if iqr > 0:
                outliers = ((series < (q1 - 3.0 * iqr)) | (series > (q3 + 3.0 * iqr))).sum()
                potential_outliers += int(outliers)
                
    # 5. Invalid values check (e.g. negative prices/quantities where impossible)
    invalid_records = {}
    for col in numeric_cols:
        col_lower = col.lower()
        if any(k in col_lower for k in ["price", "age", "quantity", "cost", "wait_time"]):
            negatives = int((df[col] < 0).sum())
            if negatives > 0:
                invalid_records[col] = f"{negatives} negative values detected"
                
    # 6. Quality Score Deduction Formula
    penalty = 0.0
    # Missing cells: up to 25 penalty points
    penalty += min(25.0, (missing_cells / total_cells) * 100 * 2.5)
    # Duplicate rows: up to 20 penalty points
    penalty += min(20.0, (dup_rows / max(1, total_rows)) * 100 * 3.0)
    # Constant columns: 5 penalty points per column (max 15)
    penalty += min(15.0, len(constant_cols) * 5.0)
    # Outliers: up to 15 penalty points
    outlier_ratio = potential_outliers / max(1, total_rows)
    penalty += min(15.0, outlier_ratio * 100 * 1.5)
    # Invalid values: 10 points
    penalty += min(10.0, len(invalid_records) * 5.0)
    
    quality_score = max(10, min(100, int(round(100.0 - penalty))))
    
    # 7. Recommended Actions List
    recommended_actions = []
    if dup_rows > 0:
        recommended_actions.append({
            "id": "remove_duplicates",
            "title": "Remove Duplicate Records",
            "description": f"Found {dup_rows} identical duplicate rows. Deduplicating will improve statistical accuracy.",
            "impact": "High",
            "auto_apply": True
        })
        
    date_cols_to_convert = [p["column_name"] for p in column_profiles if p["detected_type"] == "datetime" and not pd.api.types.is_datetime64_any_dtype(df[p["column_name"]])]
    for d_col in date_cols_to_convert:
        recommended_actions.append({
            "id": f"parse_date_{d_col}",
            "title": f"Convert '{d_col}' to DateTime",
            "description": f"Column '{d_col}' matches date pattern. Standardizing to ISO-8601 enables time-series forecasting.",
            "impact": "High",
            "auto_apply": True
        })
        
    missing_by_col = df.isna().sum()
    for col, null_count in missing_by_col.items():
        if null_count > 0:
            pct = round((null_count / total_rows) * 100, 1)
            recommended_actions.append({
                "id": f"impute_{col}",
                "title": f"Handle Missing Values in '{col}'",
                "description": f"{null_count} values ({pct}%) are missing. Apply skew-aware imputation (Median for skewed numeric, Mode/'Unknown' for categorical).",
                "impact": "Medium",
                "auto_apply": True
            })
            
    if potential_outliers > 0:
        recommended_actions.append({
            "id": "flag_outliers",
            "title": "Flag Statistical Outliers",
            "description": f"{potential_outliers} values lie outside 3x IQR. Flag them for analytical review without deleting valid business transactions.",
            "impact": "Low",
            "auto_apply": False
        })
        
    return {
        "quality_score": quality_score,
        "total_rows": total_rows,
        "total_columns": total_cols,
        "missing_cells_count": missing_cells,
        "missing_cells_percentage": missing_pct,
        "duplicate_rows_count": dup_rows,
        "potential_outliers_count": potential_outliers,
        "constant_columns": constant_cols,
        "invalid_values": invalid_records,
        "recommended_actions": recommended_actions
    }
"""

init_services_py = """from .file_validator import validate_and_inspect_file, FileValidationResult
from .data_profiler import profile_dataframe, sanitize_column_name, infer_column_type
from .quality_evaluator import compute_quality_report

__all__ = [
    "validate_and_inspect_file",
    "FileValidationResult",
    "profile_dataframe",
    "sanitize_column_name",
    "infer_column_type",
    "compute_quality_report"
]
"""

with open(os.path.join(services_dir, "file_validator.py"), "w", encoding="utf-8") as f:
    f.write(file_validator_py)

with open(os.path.join(services_dir, "data_profiler.py"), "w", encoding="utf-8") as f:
    f.write(data_profiler_py)

with open(os.path.join(services_dir, "quality_evaluator.py"), "w", encoding="utf-8") as f:
    f.write(quality_evaluator_py)

with open(os.path.join(services_dir, "__init__.py"), "w", encoding="utf-8") as f:
    f.write(init_services_py)

print("Ingestion, profiler, and data quality services written successfully.")
