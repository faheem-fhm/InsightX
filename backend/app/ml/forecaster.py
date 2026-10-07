from typing import Dict, Any, List, Optional
import pandas as pd
import numpy as np

def run_time_series_forecast(
    df: pd.DataFrame,
    date_col: Optional[str] = None,
    metric_col: Optional[str] = None,
    horizon_days: int = 30
) -> Dict[str, Any]:
    """
    Generates chronological time-series forecast with confidence intervals,
    trend decomposition, and backtesting metrics (MAE, RMSE, MAPE).
    Resilient to any dataset structure (auto-detects date and metric columns,
    synthesizes chronological sequence if explicit dates are absent).
    """
    if df.empty:
        raise ValueError("Dataset is empty.")

    temp_df = df.copy()
    cols_lower = {str(c).lower().replace(" ", "_"): c for c in df.columns}

    # 1. Resolve numeric metric column
    num_cols = [c for c in df.select_dtypes(include=[np.number]).columns if not any(k in str(c).lower() for k in ["id", "uuid", "year", "code", "index"])]
    
    if not metric_col or metric_col not in df.columns:
        for cand in ["revenue", "sales", "total_amount", "amount", "treatment_cost", "spend", "cost", "mrr_generated", "profit", "price", "quantity"]:
            if cand in cols_lower and cols_lower[cand] in num_cols:
                metric_col = cols_lower[cand]
                break

    if not metric_col:
        metric_col = num_cols[0] if num_cols else df.columns[-1]

    # Convert metric to float
    temp_df[metric_col] = pd.to_numeric(temp_df[metric_col], errors="coerce").fillna(0.0)

    # 2. Resolve or synthesize date column
    has_real_dates = False
    if not date_col or date_col not in df.columns:
        for cand in ["order_date", "date", "admission_date", "transaction_date", "created_at", "timestamp", "event_date", "time"]:
            if cand in cols_lower:
                date_col = cols_lower[cand]
                break

    if not date_col:
        for c in df.columns:
            if pd.api.types.is_datetime64_any_dtype(df[c]) or any(k in str(c).lower() for k in ["date", "time"]):
                date_col = c
                break

    if date_col and date_col in temp_df.columns:
        parsed_dates = pd.to_datetime(temp_df[date_col], errors="coerce")
        if parsed_dates.notna().sum() >= 5:
            temp_df["_dt"] = parsed_dates
            has_real_dates = True

    # If no valid date column or fewer than 5 valid timestamps, synthesize chronological dates
    if not has_real_dates:
        n_rows = len(temp_df)
        end_date = pd.Timestamp.now().normalize()
        start_date = end_date - pd.Timedelta(days=min(n_rows, 120))
        temp_df["_dt"] = pd.date_range(start=start_date, periods=n_rows, freq="D")

    clean_df = temp_df.dropna(subset=["_dt", metric_col]).sort_values("_dt")

    # Aggregate daily
    daily = clean_df.groupby(clean_df["_dt"].dt.strftime("%Y-%m-%d"))[metric_col].sum().reset_index()
    daily.columns = ["date", "value"]
    daily = daily.sort_values("date").reset_index(drop=True)

    # If aggregated points are few (< 14), interpolate/expand to ensure robust forecasting
    if len(daily) < 14:
        # Interpolate between existing points to create a smooth daily series
        daily["date_dt"] = pd.to_datetime(daily["date"])
        idx = pd.date_range(daily["date_dt"].min(), daily["date_dt"].max() + pd.Timedelta(days=14 - len(daily)))
        daily = daily.set_index("date_dt").reindex(idx)
        daily["value"] = daily["value"].interpolate(method="linear").bfill().ffill()
        daily["date"] = daily.index.strftime("%Y-%m-%d")
        daily = daily.reset_index(drop=True)[["date", "value"]]

    values = daily["value"].values.astype(float)
    n = len(values)

    # Chronological train-test split (80% train, 20% test)
    split_idx = max(int(n * 0.8), n - 10)
    train = values[:split_idx]
    test = values[split_idx:] if split_idx < n else values[-5:]

    # Holt's Linear Exponential Smoothing
    alpha = 0.35
    beta = 0.15
    level = train[0] if len(train) > 0 else 1.0
    trend = np.mean(np.diff(train[:min(5, len(train))])) if len(train) > 1 else 0.0

    for t in range(len(train)):
        val = train[t]
        last_level = level
        level = alpha * val + (1 - alpha) * (last_level + trend)
        trend = beta * (level - last_level) + (1 - beta) * trend

    # Backtest evaluation
    preds_test = np.array([max(0.0, level + (i + 1) * trend) for i in range(len(test))])
    errors = test - preds_test
    mae = round(float(np.mean(np.abs(errors))), 2)
    rmse = round(float(np.sqrt(np.mean(errors ** 2))), 2)
    mape_val = float(np.mean(np.abs(errors / np.clip(np.abs(test), 1.0, None)))) * 100
    mape_val = min(99.9, round(mape_val, 1))

    # Re-train on full historical series for future forecasting
    level = values[0]
    trend = np.mean(np.diff(values[:min(5, len(values))])) if len(values) > 1 else 0.0
    for val in values:
        last_level = level
        level = alpha * val + (1 - alpha) * (last_level + trend)
        trend = beta * (level - last_level) + (1 - beta) * trend

    # Residual standard deviation for expanding uncertainty cone (95% confidence interval)
    diffs = np.diff(values)
    std_residual = float(np.std(diffs)) if len(diffs) > 1 and np.std(diffs) > 0 else max(1.0, float(np.mean(values) * 0.08))

    last_date = pd.to_datetime(daily["date"].iloc[-1])
    forecast_points = []

    for h in range(1, horizon_days + 1):
        future_date = (last_date + pd.Timedelta(days=h)).strftime("%Y-%m-%d")
        pred_val = max(0.0, level + h * trend)
        uncertainty = 1.96 * std_residual * np.sqrt(h)
        lower_bound = max(0.0, pred_val - uncertainty)
        upper_bound = pred_val + uncertainty

        forecast_points.append({
            "date": future_date,
            "predicted": round(pred_val, 2),
            "lower_bound": round(lower_bound, 2),
            "upper_bound": round(upper_bound, 2)
        })

    # Summary trend narrative
    first_pred = forecast_points[0]["predicted"]
    last_pred = forecast_points[-1]["predicted"]
    proj_change_pct = round(((last_pred - first_pred) / max(abs(first_pred), 1.0)) * 100, 1)
    direction_term = "expand" if proj_change_pct >= 0 else "decline"

    metric_title = str(metric_col).replace("_", " ").title()
    summary = (
        f"Over the next {horizon_days} days, {metric_title} is projected to {direction_term} "
        f"by {abs(proj_change_pct)}% (moving from {first_pred:,.2f} to {last_pred:,.2f}) "
        f"based on historical momentum and trend analysis."
    )

    historical_points = daily.tail(45).to_dict(orient="records")

    return {
        "metric": metric_col,
        "metric_title": metric_title,
        "available_metrics": num_cols,
        "horizon_days": horizon_days,
        "summary": summary,
        "metrics": {
            "mae": mae,
            "rmse": rmse,
            "mape": f"{mape_val}%",
            "accuracy_rate": f"{max(1.0, round(100 - mape_val, 1))}%",
            "model_type": "Holt-Winters Double Exponential Smoothing"
        },
        "historical": historical_points,
        "forecast": forecast_points
    }
