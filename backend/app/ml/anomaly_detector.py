from typing import Dict, Any, List, Optional
import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest

def detect_anomalies(
    df: pd.DataFrame,
    date_col: str,
    metric_col: str,
    contamination: float = 0.04
) -> List[Dict[str, Any]]:
    anomalies = []
    if date_col not in df.columns or metric_col not in df.columns:
        return anomalies
        
    temp_df = df.copy()
    temp_df["_dt"] = pd.to_datetime(temp_df[date_col], errors="coerce")
    clean_df = temp_df.dropna(subset=["_dt", metric_col])
    if len(clean_df) < 15:
        return anomalies
        
    # Group by date
    daily = clean_df.groupby(clean_df["_dt"].dt.strftime("%Y-%m-%d"))[metric_col].agg(["sum", "mean", "count"]).reset_index()
    daily.columns = ["date", "sum_val", "mean_val", "count"]
    daily = daily.sort_values("date").reset_index(drop=True)
    
    # Statistical Baseline: Rolling 7-day mean & std with bfill to prevent NaNs
    daily["rolling_mean"] = daily["sum_val"].rolling(window=7, min_periods=1).mean().bfill()
    daily["rolling_std"] = daily["sum_val"].rolling(window=7, min_periods=1).std().fillna(0.0).bfill()
    daily["upper_bound"] = daily["rolling_mean"] + 2.5 * daily["rolling_std"]
    daily["lower_bound"] = (daily["rolling_mean"] - 2.5 * daily["rolling_std"]).clip(lower=0)
    
    # Machine Learning: Isolation Forest
    iso_features = daily[["sum_val", "count"]].fillna(0)
    iso = IsolationForest(contamination=contamination, random_state=42)
    daily["iso_pred"] = iso.fit_predict(iso_features)
    daily["iso_score"] = -iso.score_samples(iso_features)
    
    for _, row in daily.iterrows():
        is_stat_anomaly = (row["sum_val"] > row["upper_bound"] or row["sum_val"] < row["lower_bound"])
        is_ml_anomaly = (row["iso_pred"] == -1)
        
        if is_stat_anomaly or is_ml_anomaly:
            diff = float(row["sum_val"] - row["rolling_mean"])
            pct_diff = round((diff / max(abs(float(row["rolling_mean"])), 1.0)) * 100, 1)
            
            score = float(row["iso_score"])
            if abs(pct_diff) > 40 or score > 0.65:
                severity = "Critical"
            elif abs(pct_diff) > 25 or score > 0.55:
                severity = "Medium"
            else:
                severity = "Low"
                
            anomalies.append({
                "date": str(row["date"]),
                "metric": str(metric_col),
                "actual_value": round(float(row["sum_val"]), 2),
                "expected_value": round(float(row["rolling_mean"]), 2),
                "lower_bound": round(float(row["lower_bound"]), 2),
                "upper_bound": round(float(row["upper_bound"]), 2),
                "anomaly_score": round(score, 3),
                "severity": severity,
                "change_percent": pct_diff,
                "direction": "Drop" if diff < 0 else "Spike",
                "explanation": f"{metric_col.replace('_', ' ').title()} had an unusual {('drop of ' + str(abs(pct_diff)) + '%') if diff < 0 else ('surge of +' + str(pct_diff) + '%')} compared to expected range."
            })
            
    return anomalies
