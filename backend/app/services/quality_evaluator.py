from typing import Dict, Any, List
import pandas as pd
import numpy as np

def compute_quality_report(df: pd.DataFrame, column_profiles: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Generates an enterprise-grade Data Quality Score (0-100) and actionable remediation checklist."""
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
