import os

rc_dir = r"C:\Users\HP\.gemini\antigravity\scratch\InsightX\backend\app\root_cause"
os.makedirs(rc_dir, exist_ok=True)

investigator_py = """from typing import Dict, Any, List, Optional
import pandas as pd
import numpy as np

def run_root_cause_investigation(
    df: pd.DataFrame,
    target_metric: Optional[str] = None,
    date_col: Optional[str] = None,
    crisis_start_date: Optional[str] = None,
    crisis_end_date: Optional[str] = None
) -> Dict[str, Any]:
    \"\"\"
    Executes dimensional decomposition and simultaneous metric shift analysis to uncover
    the root drivers of an anomaly without confusing correlation with causation.
    \"\"\"
    cols_lower = {str(c).lower(): c for c in df.columns}
    
    # 1. Resolve target metric
    if not target_metric or target_metric not in df.columns:
        for cand in ["revenue", "profit", "sales", "mrr_generated", "spend", "cost"]:
            if cand in cols_lower:
                target_metric = cols_lower[cand]
                break
    if not target_metric:
        target_metric = df.select_dtypes(include=[np.number]).columns[0]
        
    # 2. Resolve date column
    if not date_col or date_col not in df.columns:
        for c in df.columns:
            if pd.api.types.is_datetime64_any_dtype(df[c]) or any(k in str(c).lower() for k in ["date", "time"]):
                date_col = c
                break
                
    temp_df = df.copy()
    if date_col:
        temp_df["_dt"] = pd.to_datetime(temp_df[date_col], errors="coerce")
        temp_df = temp_df.dropna(subset=["_dt"]).sort_values("_dt")
    else:
        temp_df["_dt"] = pd.date_range(start="2024-01-01", periods=len(temp_df), freq="D")

    # 3. Partition into Period 1 (Baseline) and Period 2 (Crisis)
    if crisis_start_date:
        p1 = temp_df[temp_df["_dt"] < pd.to_datetime(crisis_start_date)]
        if crisis_end_date:
            p2 = temp_df[(temp_df["_dt"] >= pd.to_datetime(crisis_start_date)) & (temp_df["_dt"] <= pd.to_datetime(crisis_end_date))]
        else:
            p2 = temp_df[temp_df["_dt"] >= pd.to_datetime(crisis_start_date)]
    else:
        # Auto-detect: first 60% baseline, last 40% target
        mid = temp_df["_dt"].quantile(0.60)
        p1 = temp_df[temp_df["_dt"] < mid]
        p2 = temp_df[temp_df["_dt"] >= mid]

    p1_total = float(p1[target_metric].sum())
    p2_total = float(p2[target_metric].sum())
    
    # Normalize by daily average to account for different period lengths
    p1_days = max(1, p1["_dt"].nunique())
    p2_days = max(1, p2["_dt"].nunique())
    
    p1_daily = p1_total / p1_days
    p2_daily = p2_total / p2_days
    total_delta = p2_daily - p1_daily
    pct_change = round((total_delta / max(abs(p1_daily), 1.0)) * 100, 1)

    # 4. Multi-Dimensional Decomposition
    cat_columns = temp_df.select_dtypes(include=["object", "category", "string"]).columns.tolist()
    # Filter out IDs
    cat_dims = [c for c in cat_columns if not any(k in c.lower() for k in ["id", "uuid", "code"])]
    
    dimensional_breakdowns = []
    top_driver = None
    max_abs_impact = 0.0
    
    for dim in cat_dims:
        if temp_df[dim].nunique() <= 20:
            p1_dim = p1.groupby(dim)[target_metric].sum() / p1_days
            p2_dim = p2.groupby(dim)[target_metric].sum() / p2_days
            
            dim_df = pd.DataFrame({"p1": p1_dim, "p2": p2_dim}).fillna(0.0)
            dim_df["delta"] = dim_df["p2"] - dim_df["p1"]
            dim_df["abs_delta"] = dim_df["delta"].abs()
            dim_df["pct_change"] = ((dim_df["p2"] - dim_df["p1"]) / dim_df["p1"].replace(0, 1) * 100).round(1)
            
            # Contribution percentage of this dimension's items to total delta
            total_negative_shift = dim_df[dim_df["delta"] < 0]["delta"].sum()
            
            items = []
            for item_name, row in dim_df.sort_values("delta").iterrows():
                contrib_pct = round((row["delta"] / total_negative_shift * 100), 1) if total_negative_shift < 0 and row["delta"] < 0 else 0.0
                items.append({
                    "name": str(item_name),
                    "baseline_daily": round(float(row["p1"]), 2),
                    "crisis_daily": round(float(row["p2"]), 2),
                    "delta": round(float(row["delta"]), 2),
                    "pct_change": float(row["pct_change"]),
                    "contribution_percentage": contrib_pct
                })
                
                if abs(row["delta"]) > max_abs_impact:
                    max_abs_impact = abs(row["delta"])
                    top_driver = {"dimension": dim, "item": str(item_name), "delta": round(float(row["delta"]), 2), "pct_change": float(row["pct_change"])}
                    
            dimensional_breakdowns.append({
                "dimension": dim,
                "dimension_title": dim.replace("_", " ").title(),
                "items": items
            })
            
    # 5. Check Confounding / Correlated Simultaneous Metric Shifts
    num_cols = temp_df.select_dtypes(include=[np.number]).columns.tolist()
    correlated_shifts = []
    for m in num_cols:
        if m != target_metric and not any(k in m.lower() for k in ["id", "uuid"]):
            p1_m = float(p1[m].mean())
            p2_m = float(p2[m].mean())
            d_pct = round(((p2_m - p1_m) / max(abs(p1_m), 0.001)) * 100, 1)
            if abs(d_pct) >= 15.0:
                correlated_shifts.append({
                    "metric": m,
                    "metric_title": m.replace("_", " ").title(),
                    "p1_mean": round(p1_m, 2),
                    "p2_mean": round(p2_m, 2),
                    "pct_change": d_pct,
                    "direction": "Increased" if d_pct > 0 else "Decreased"
                })
                
    # 6. Generate Narrative Findings & Recommendations
    direction_word = "declined" if total_delta < 0 else "increased"
    summary_text = (
        f"{target_metric.replace('_', ' ').title()} {direction_word} by {abs(pct_change)}% "
        f"during the analyzed period (daily average shifted from ${p1_daily:,.2f} to ${p2_daily:,.2f})."
    )
    
    driver_text = ""
    if top_driver:
        driver_text = (
            f"The primary contributor was '{top_driver['item']}' in '{top_driver['dimension'].replace('_', ' ')}', "
            f"which saw a {top_driver['pct_change']}% change."
        )
        
    confound_text = ""
    if correlated_shifts:
        top_shifts = ", ".join([f"{s['metric_title']} ({s['direction']} {abs(s['pct_change'])}%)" for s in correlated_shifts[:3]])
        confound_text = f"Simultaneously, significant shifts were detected in: {top_shifts}."
        
    recommendations = []
    if total_delta < 0:
        if top_driver:
            recommendations.append({
                "action": f"Prioritize Operational Review for {top_driver['item']}",
                "detail": f"Investigate logistical, supply chain, or promotional changes impacting {top_driver['item']}."
            })
        if correlated_shifts:
            recommendations.append({
                "action": f"Address {correlated_shifts[0]['metric_title']} Bottleneck",
                "detail": f"{correlated_shifts[0]['metric_title']} moved by {correlated_shifts[0]['pct_change']}%, indicating a strong operational dependency."
            })
        recommendations.append({
            "action": "Implement Automated Guardrail Alerts",
            "detail": "Configure real-time notifications if delivery delay or complaint thresholds exceed 3-sigma tolerances."
        })
    else:
        recommendations.append({
            "action": "Scale Winning Drivers",
            "detail": f"Analyze best practices from {top_driver['item'] if top_driver else 'top segments'} to replicate across other channels."
        })

    return {
        "target_metric": target_metric,
        "change_percentage": pct_change,
        "direction": "Decline" if total_delta < 0 else "Growth",
        "baseline_daily": round(p1_daily, 2),
        "crisis_daily": round(p2_daily, 2),
        "top_driver": top_driver,
        "narrative_finding": summary_text,
        "driver_explanation": driver_text,
        "simultaneous_shifts": correlated_shifts,
        "dimensional_breakdowns": dimensional_breakdowns,
        "recommendations": recommendations,
        "causality_disclaimer": "Metrics are statistically associated. Root causes reflect empirical correlations rather than randomized controlled trial causation."
    }
"""

with open(os.path.join(rc_dir, "investigator.py"), "w", encoding="utf-8") as f:
    f.write(investigator_py)

with open(os.path.join(rc_dir, "__init__.py"), "w", encoding="utf-8") as f:
    f.write("from .investigator import run_root_cause_investigation\n__all__ = ['run_root_cause_investigation']")

print("Root Cause Investigation engine successfully written.")
