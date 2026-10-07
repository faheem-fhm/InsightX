from typing import Dict, Any, List, Optional
import pandas as pd
import numpy as np

from ..services.currency_detector import dataset_has_dollar_symbol

CURRENCY_KEYWORDS = {
    "revenue", "sales", "profit", "spend", "cost", "price", "amount",
    "unit_price", "total_amount", "treatment_cost", "mrr", "arr", "mrr_generated"
}

def is_currency_col(col_name: str) -> bool:
    c = str(col_name).lower()
    return any(k in c for k in CURRENCY_KEYWORDS) or "$" in c

def format_metric_value(col_name: str, value: float, is_avg: bool = False, has_dollar: bool = False) -> str:
    c = str(col_name).lower()
    if is_currency_col(c):
        # Only prepend dollar symbol if dataset explicitly has dollar symbol
        prefix = "$" if has_dollar else ""
        if value < 0:
            return f"-{prefix}{abs(value):,.2f}"
        return f"{prefix}{value:,.2f}"
    if any(k in c for k in ["rate", "pct", "percent", "discount"]):
        return f"{value * 100:.1f}%" if value <= 1.0 else f"{value:.1f}%"
    if any(k in c for k in ["age", "days", "delay", "time", "count", "quantity", "score"]):
        if "day" in c or "delay" in c:
            return f"{value:.1f} days"
        if "score" in c and value <= 10:
            return f"{value:.1f} / 10"
        return f"{value:,.1f}" if is_avg else f"{int(value):,}" if float(value).is_integer() else f"{value:,.2f}"
    return f"{value:,.2f}"

def compute_dynamic_kpis(df: pd.DataFrame, date_col: Optional[str] = None, has_dollar: Optional[bool] = None) -> List[Dict[str, Any]]:
    kpis = []
    total_rows = len(df)
    if total_rows == 0:
        return kpis
        
    if has_dollar is None:
        has_dollar = dataset_has_dollar_symbol(df)
        
    # Check date column for period-over-period comparison
    has_dates = False
    half_1_df, half_2_df = None, None
    if date_col and date_col in df.columns:
        try:
            temp_dates = pd.to_datetime(df[date_col], errors="coerce")
            if temp_dates.notna().sum() > total_rows * 0.5:
                has_dates = True
                sorted_df = df.assign(_dt=temp_dates).sort_values("_dt")
                midpoint = sorted_df["_dt"].median()
                half_1_df = sorted_df[sorted_df["_dt"] < midpoint]
                half_2_df = sorted_df[sorted_df["_dt"] >= midpoint]
        except Exception:
            pass

    cols_lower = {str(c).lower(): c for c in df.columns}
    
    # 1. Primary Volume KPI
    prev_rows = len(half_1_df) if has_dates and half_1_df is not None else None
    curr_rows = len(half_2_df) if has_dates and half_2_df is not None else total_rows
    delta_rows = round(((curr_rows - prev_rows) / max(prev_rows, 1)) * 100, 1) if prev_rows else None
    
    kpis.append({
        "id": "total_records",
        "title": "Total Records",
        "value": f"{total_rows:,}",
        "raw_value": total_rows,
        "delta_percent": delta_rows,
        "is_positive": (delta_rows >= 0) if delta_rows is not None else True,
        "indicator": "positive" if (delta_rows or 0) >= 0 else "negative",
        "description": "Total active rows in the current filtered scope"
    })
    
    # 2. Revenue / Primary Monetary / Key Metric KPI
    rev_col = None
    for cand in ["revenue", "sales", "total_amount", "amount", "spend", "cost", "treatment_cost", "mrr_generated", "quantity", "age"]:
        if cand in cols_lower:
            rev_col = cols_lower[cand]
            break
            
    if rev_col and pd.api.types.is_numeric_dtype(df[rev_col]):
        total_rev = float(df[rev_col].sum())
        p1_rev = float(half_1_df[rev_col].sum()) if has_dates and half_1_df is not None else None
        p2_rev = float(half_2_df[rev_col].sum()) if has_dates and half_2_df is not None else None
        delta_rev = round(((p2_rev - p1_rev) / max(abs(p1_rev), 1)) * 100, 1) if p1_rev is not None else None
        
        kpis.append({
            "id": "primary_monetary",
            "title": f"Total {rev_col.replace('_', ' ').title()}",
            "value": format_metric_value(rev_col, total_rev, has_dollar=has_dollar),
            "raw_value": round(total_rev, 2),
            "delta_percent": delta_rev,
            "is_positive": (delta_rev >= 0) if delta_rev is not None else True,
            "indicator": "positive" if (delta_rev or 0) >= 0 else "negative",
            "description": f"Aggregate sum of {rev_col}"
        })
        
    # 3. Profit / ROI / Efficiency KPI
    profit_col = None
    for cand in ["profit", "roi", "net_margin", "satisfaction_score", "discount"]:
        if cand in cols_lower:
            profit_col = cols_lower[cand]
            break
            
    if profit_col and pd.api.types.is_numeric_dtype(df[profit_col]):
        if profit_col in ["roi", "satisfaction_score", "discount"]:
            avg_val = float(df[profit_col].mean())
            p1_val = float(half_1_df[profit_col].mean()) if has_dates and half_1_df is not None else None
            p2_val = float(half_2_df[profit_col].mean()) if has_dates and half_2_df is not None else None
            delta_prof = round(((p2_val - p1_val) / max(abs(p1_val), 0.001)) * 100, 1) if p1_val is not None else None
            val_str = f"{avg_val:.2f}x" if profit_col == "roi" else format_metric_value(profit_col, avg_val, is_avg=True, has_dollar=has_dollar)
            title_prefix = "Average"
        else:
            tot_prof = float(df[profit_col].sum())
            p1_val = float(half_1_df[profit_col].sum()) if has_dates and half_1_df is not None else None
            p2_val = float(half_2_df[profit_col].sum()) if has_dates and half_2_df is not None else None
            delta_prof = round(((p2_val - p1_val) / max(abs(p1_val), 1)) * 100, 1) if p1_val is not None else None
            val_str = format_metric_value(profit_col, tot_prof, has_dollar=has_dollar)
            title_prefix = "Total"
            
        kpis.append({
            "id": "primary_efficiency",
            "title": f"{title_prefix} {profit_col.replace('_', ' ').title()}",
            "value": val_str,
            "raw_value": round(float(df[profit_col].sum()), 2),
            "delta_percent": delta_prof,
            "is_positive": (delta_prof >= 0) if delta_prof is not None else True,
            "indicator": "positive" if (delta_prof or 0) >= 0 else "negative",
            "description": f"Performance tracking for {profit_col}"
        })

    # 4. Critical Risk / Delay KPI
    risk_col = None
    for cand in ["customer_complaint", "order_cancelled", "delivery_delay_days", "readmission_30d", "churn"]:
        if cand in cols_lower:
            risk_col = cols_lower[cand]
            break
            
    if risk_col and pd.api.types.is_numeric_dtype(df[risk_col]):
        avg_rate = float(df[risk_col].mean())
        is_percentage = (avg_rate <= 1.0)
        p1_rate = float(half_1_df[risk_col].mean()) if has_dates and half_1_df is not None else None
        p2_rate = float(half_2_df[risk_col].mean()) if has_dates and half_2_df is not None else None
        delta_risk = round(((p2_rate - p1_rate) / max(p1_rate, 0.001)) * 100, 1) if p1_rate is not None else None
        
        # In risk metrics, increase is negative/danger
        kpis.append({
            "id": "critical_risk",
            "title": f"{risk_col.replace('_', ' ').title()} Rate" if is_percentage else f"Avg {risk_col.replace('_', ' ').title()}",
            "value": f"{avg_rate * 100:.1f}%" if is_percentage else f"{avg_rate:.2f} days",
            "raw_value": round(avg_rate, 3),
            "delta_percent": delta_risk,
            "is_positive": (delta_risk <= 0) if delta_risk is not None else True,
            "indicator": "negative" if (delta_risk or 0) > 0 else "positive",
            "description": f"Risk and operational quality indicator for {risk_col}"
        })
        
    return kpis
