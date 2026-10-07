import os

ml_dir = r"C:\Users\HP\.gemini\antigravity\scratch\InsightX\backend\app\ml"
os.makedirs(ml_dir, exist_ok=True)

# 1. anomaly_detector.py
anomaly_py = """from typing import Dict, Any, List, Optional
import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest

def detect_anomalies(
    df: pd.DataFrame,
    date_col: str,
    metric_col: str,
    contamination: float = 0.04
) -> List[Dict[str, Any]]:
    \"\"\"Detects temporal anomalies using both Rolling 3-Sigma and Isolation Forest.\"\"\"
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
    
    # Statistical Baseline: Rolling 7-day mean & std
    daily["rolling_mean"] = daily["sum_val"].rolling(window=7, min_periods=3).mean()
    daily["rolling_std"] = daily["sum_val"].rolling(window=7, min_periods=3).std().fillna(1.0)
    daily["upper_bound"] = daily["rolling_mean"] + 2.5 * daily["rolling_std"]
    daily["lower_bound"] = (daily["rolling_mean"] - 2.5 * daily["rolling_std"]).clip(lower=0)
    
    # Machine Learning: Isolation Forest
    iso_features = daily[["sum_val", "count"]].fillna(0)
    iso = IsolationForest(contamination=contamination, random_state=42)
    daily["iso_pred"] = iso.fit_predict(iso_features) # -1 is anomaly
    daily["iso_score"] = -iso.score_samples(iso_features)
    
    for _, row in daily.iterrows():
        is_stat_anomaly = (row["sum_val"] > row["upper_bound"] or row["sum_val"] < row["lower_bound"])
        is_ml_anomaly = (row["iso_pred"] == -1)
        
        if is_stat_anomaly or is_ml_anomaly:
            diff = row["sum_val"] - row["rolling_mean"]
            pct_diff = round((diff / max(abs(row["rolling_mean"]), 1)) * 100, 1)
            
            # Severity calculation
            score = float(row["iso_score"])
            if abs(pct_diff) > 40 or score > 0.65:
                severity = "Critical"
            elif abs(pct_diff) > 25 or score > 0.55:
                severity = "Medium"
            else:
                severity = "Low"
                
            anomalies.append({
                "date": row["date"],
                "metric": metric_col,
                "actual_value": round(float(row["sum_val"]), 2),
                "expected_value": round(float(row["rolling_mean"]), 2),
                "lower_bound": round(float(row["lower_bound"]), 2),
                "upper_bound": round(float(row["upper_bound"]), 2),
                "anomaly_score": round(score, 3),
                "severity": severity,
                "change_percent": pct_diff,
                "direction": "Drop" if diff < 0 else "Spike",
                "explanation": f"{metric_col.replace('_', ' ').title()} had an unusual {('drop of ' + str(abs(pct_diff)) + '%') if diff < 0 else ('surge of +' + str(pct_diff) + '%')} compared to the moving average."
            })
            
    return anomalies
"""

# 2. forecaster.py
forecaster_py = """from typing import Dict, Any, List, Optional
import pandas as pd
import numpy as np

def run_time_series_forecast(
    df: pd.DataFrame,
    date_col: str,
    metric_col: str,
    horizon_days: int = 30
) -> Dict[str, Any]:
    \"\"\"Generates chronological time-series forecast with confidence intervals and backtesting metrics.\"\"\"
    temp_df = df.copy()
    temp_df["_dt"] = pd.to_datetime(temp_df[date_col], errors="coerce")
    clean_df = temp_df.dropna(subset=["_dt", metric_col])
    
    daily = clean_df.groupby(clean_df["_dt"].dt.strftime("%Y-%m-%d"))[metric_col].sum().reset_index()
    daily.columns = ["date", "value"]
    daily = daily.sort_values("date").reset_index(drop=True)
    
    if len(daily) < 14:
        raise ValueError("At least 14 daily data points are required for time-series forecasting.")
        
    values = daily["value"].values
    n = len(values)
    
    # Chronological train-test split (80% train, 20% test)
    split_idx = max(int(n * 0.8), n - 14)
    train = values[:split_idx]
    test = values[split_idx:]
    
    # Exponential Smoothing with Trend (Holt's linear approximation)
    alpha = 0.35
    beta = 0.15
    level = train[0]
    trend = np.mean(np.diff(train[:min(5, len(train))])) if len(train) > 1 else 0.0
    
    for t in range(len(train)):
        val = train[t]
        last_level = level
        level = alpha * val + (1 - alpha) * (last_level + trend)
        trend = beta * (level - last_level) + (1 - beta) * trend
        
    # Backtest evaluation against test set
    preds_test = [max(0.0, level + (i + 1) * trend) for i in range(len(test))]
    errors = test - preds_test
    mae = round(float(np.mean(np.abs(errors))), 2)
    rmse = round(float(np.sqrt(np.mean(errors ** 2))), 2)
    mape = round(float(np.mean(np.abs(errors / np.clip(test, 1.0, None)))) * 100, 1)
    
    # Re-train on all data for future forecast
    level = values[0]
    trend = np.mean(np.diff(values[:min(5, len(values))])) if len(values) > 1 else 0.0
    for val in values:
        last_level = level
        level = alpha * val + (1 - alpha) * (last_level + trend)
        trend = beta * (level - last_level) + (1 - beta) * trend
        
    # Standard deviation of historical changes for confidence interval
    std_residual = float(np.std(np.diff(values))) if len(values) > 1 else max(1.0, float(np.mean(values) * 0.1))
    
    last_date = pd.to_datetime(daily["date"].iloc[-1])
    forecast_points = []
    
    for h in range(1, horizon_days + 1):
        future_date = (last_date + pd.Timedelta(days=h)).strftime("%Y-%m-%d")
        pred_val = max(0.0, level + h * trend)
        # Expanding uncertainty cone
        uncertainty = 1.96 * std_residual * np.sqrt(h)
        lower_bound = max(0.0, pred_val - uncertainty)
        upper_bound = pred_val + uncertainty
        
        forecast_points.append({
            "date": future_date,
            "predicted": round(pred_val, 2),
            "lower_bound": round(lower_bound, 2),
            "upper_bound": round(upper_bound, 2)
        })
        
    historical_points = daily.tail(45).to_dict(orient="records")
    
    return {
        "metric": metric_col,
        "horizon_days": horizon_days,
        "metrics": {
            "mae": mae,
            "rmse": rmse,
            "mape": f"{mape}%",
            "model_type": "Holt Exponential Smoothing (Double ES)"
        },
        "historical": historical_points,
        "forecast": forecast_points
    }
"""

# 3. rfm_segmentation.py
rfm_py = """from typing import Dict, Any, List, Optional
import pandas as pd
import numpy as np
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

def run_rfm_segmentation(df: pd.DataFrame) -> Dict[str, Any]:
    \"\"\"Performs RFM analysis and K-Means segmentation with business-friendly clusters.\"\"\"
    cols_lower = {str(c).lower(): c for c in df.columns}
    
    # Check if customer transaction features exist
    cust_col = None
    for cand in ["customer_id", "customer", "client_id", "user_id"]:
        if cand in cols_lower:
            cust_col = cols_lower[cand]
            break
            
    date_col = None
    for cand in ["order_date", "date", "admission_date", "transaction_date"]:
        if cand in cols_lower:
            date_col = cols_lower[cand]
            break
            
    monetary_col = None
    for cand in ["revenue", "sales", "total_amount", "amount", "treatment_cost", "mrr_generated"]:
        if cand in cols_lower:
            monetary_col = cols_lower[cand]
            break
            
    if not cust_col or not date_col or not monetary_col:
        return {
            "supported": False,
            "reason": "Dataset does not contain required customer transactional columns (customer_id, date, monetary metric)."
        }
        
    temp_df = df.copy()
    temp_df["_dt"] = pd.to_datetime(temp_df[date_col], errors="coerce")
    valid_df = temp_df.dropna(subset=[cust_col, "_dt", monetary_col])
    
    if valid_df[cust_col].nunique() < 10:
        return {
            "supported": False,
            "reason": "Not enough distinct customer IDs (< 10) to perform meaningful cluster segmentation."
        }
        
    max_date = valid_df["_dt"].max()
    
    # Calculate RFM per customer
    rfm = valid_df.groupby(cust_col).agg(
        recency=("_dt", lambda d: (max_date - d.max()).days),
        frequency=(cust_col, "count"),
        monetary=(monetary_col, "sum")
    ).reset_index()
    
    # Scale features for K-Means
    scaler = StandardScaler()
    rfm_scaled = scaler.fit_transform(rfm[["recency", "frequency", "monetary"]])
    
    n_clusters = 4
    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    rfm["cluster"] = kmeans.fit_predict(rfm_scaled)
    
    # Map cluster numbers to meaningful business labels based on centroids
    cluster_means = rfm.groupby("cluster")[["recency", "frequency", "monetary"]].mean()
    
    # Assign labels
    labels = {}
    sorted_by_monetary = cluster_means.sort_values("monetary", ascending=False).index.tolist()
    labels[sorted_by_monetary[0]] = "Champions"
    labels[sorted_by_monetary[1]] = "Loyal Customers"
    
    # Between the remaining, the one with higher recency (longer since last visit) is At Risk
    remaining = [sorted_by_monetary[2], sorted_by_monetary[3]]
    if cluster_means.loc[remaining[0], "recency"] > cluster_means.loc[remaining[1], "recency"]:
        labels[remaining[0]] = "At Risk / Inactive"
        labels[remaining[1]] = "Potential Loyalists"
    else:
        labels[remaining[1]] = "At Risk / Inactive"
        labels[remaining[0]] = "Potential Loyalists"
        
    rfm["segment_name"] = rfm["cluster"].map(labels)
    
    # Aggregate segment stats
    segments_summary = []
    for seg_name, group in rfm.groupby("segment_name"):
        segments_summary.append({
            "segment": seg_name,
            "customer_count": len(group),
            "percentage": round(len(group) / len(rfm) * 100, 1),
            "avg_recency_days": round(float(group["recency"].mean()), 1),
            "avg_frequency": round(float(group["frequency"].mean()), 1),
            "total_monetary": round(float(group["monetary"].sum()), 2),
            "avg_monetary": round(float(group["monetary"].mean()), 2)
        })
        
    # Sample customer records for drill-down table
    sample_customers = rfm.head(20).to_dict(orient="records")
    
    return {
        "supported": True,
        "total_customers": len(rfm),
        "segments": segments_summary,
        "sample_customers": sample_customers
    }
"""

# 4. churn_predictor.py
churn_py = """from typing import Dict, Any, List, Optional
import pandas as pd
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score, confusion_matrix

def train_churn_model(df: pd.DataFrame) -> Dict[str, Any]:
    \"\"\"Trains a churn prediction model and computes explainability / feature contributions.\"\"\"
    cols_lower = {str(c).lower(): c for c in df.columns}
    
    target_col = None
    for cand in ["churn", "order_cancelled", "readmission_30d", "cancelled", "customer_complaint"]:
        if cand in cols_lower:
            target_col = cols_lower[cand]
            break
            
    if not target_col:
        return {
            "supported": False,
            "reason": "No binary outcome target variable (churn, cancellation, complaint) found."
        }
        
    # Select numeric features
    clean_df = df.dropna(subset=[target_col]).copy()
    num_cols = clean_df.select_dtypes(include=[np.number]).columns.tolist()
    if target_col in num_cols:
        num_cols.remove(target_col)
        
    # Remove obvious identifiers
    features = [c for c in num_cols if not any(id_k in c.lower() for id_k in ["id", "uuid", "code"])]
    
    if len(features) < 2 or clean_df[target_col].nunique() != 2:
        return {
            "supported": False,
            "reason": "Insufficient numeric features or target variable is not binary."
        }
        
    X = clean_df[features].fillna(clean_df[features].median())
    y = clean_df[target_col].astype(int)
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)
    
    rf = RandomForestClassifier(n_estimators=50, max_depth=5, random_state=42)
    rf.fit(X_train, y_train)
    
    preds = rf.predict(X_test)
    probas = rf.predict_proba(X_test)[:, 1]
    
    acc = round(float(accuracy_score(y_test, preds)), 3)
    prec = round(float(precision_score(y_test, preds, zero_division=0)), 3)
    rec = round(float(recall_score(y_test, preds, zero_division=0)), 3)
    f1 = round(float(f1_score(y_test, preds, zero_division=0)), 3)
    auc = round(float(roc_auc_score(y_test, probas)), 3) if len(np.unique(y_test)) > 1 else 0.5
    cm = confusion_matrix(y_test, preds).tolist()
    
    # Feature Importances (Tree-based SHAP proxy)
    importances = rf.feature_importances_
    ranked_features = []
    for feat, imp in sorted(zip(features, importances), key=lambda x: x[1], reverse=True):
        ranked_features.append({
            "feature": feat,
            "importance": round(float(imp), 4),
            "percentage": round(float(imp) * 100, 1),
            "impact": "High" if imp > 0.2 else ("Medium" if imp > 0.08 else "Low")
        })
        
    return {
        "supported": True,
        "target_metric": target_col,
        "evaluation_metrics": {
            "accuracy": acc,
            "precision": prec,
            "recall": rec,
            "f1_score": f1,
            "roc_auc": auc,
            "confusion_matrix": cm
        },
        "feature_contributions": ranked_features
    }
"""

init_ml_py = """from .anomaly_detector import detect_anomalies
from .forecaster import run_time_series_forecast
from .rfm_segmentation import run_rfm_segmentation
from .churn_predictor import train_churn_model

__all__ = [
    "detect_anomalies",
    "run_time_series_forecast",
    "run_rfm_segmentation",
    "train_churn_model"
]
"""

with open(os.path.join(ml_dir, "anomaly_detector.py"), "w", encoding="utf-8") as f:
    f.write(anomaly_py)

with open(os.path.join(ml_dir, "forecaster.py"), "w", encoding="utf-8") as f:
    f.write(forecaster_py)

with open(os.path.join(ml_dir, "rfm_segmentation.py"), "w", encoding="utf-8") as f:
    f.write(rfm_py)

with open(os.path.join(ml_dir, "churn_predictor.py"), "w", encoding="utf-8") as f:
    f.write(churn_py)

with open(os.path.join(ml_dir, "__init__.py"), "w", encoding="utf-8") as f:
    f.write(init_ml_py)

print("Machine Learning modules successfully created.")
