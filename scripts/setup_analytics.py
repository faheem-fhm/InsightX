import os

analytics_dir = r"C:\Users\HP\.gemini\antigravity\scratch\InsightX\backend\app\analytics"
os.makedirs(analytics_dir, exist_ok=True)

# 1. olap_engine.py
olap_engine_py = """import os
from typing import Dict, Any, List, Optional
import duckdb
import pandas as pd
from ..core.exceptions import UnsafeSQLError

class DuckDBEngine:
    def __init__(self):
        self.conn = duckdb.connect(database=":memory:")
        
    def register_parquet(self, table_name: str, parquet_path: str):
        if not os.path.exists(parquet_path):
            raise FileNotFoundError(f"Parquet file not found: {parquet_path}")
        self.conn.execute(f"CREATE OR REPLACE VIEW {table_name} AS SELECT * FROM read_parquet('{parquet_path}')")
        
    def query(self, sql: str, limit: int = 1000) -> pd.DataFrame:
        clean_sql = sql.strip().rstrip(";")
        # Ensure query has limit for safety
        if "limit" not in clean_sql.lower():
            clean_sql = f"{clean_sql} LIMIT {limit}"
        return self.conn.execute(clean_sql).fetchdf()

olap_engine = DuckDBEngine()
"""

# 2. kpi_engine.py
kpi_engine_py = """from typing import Dict, Any, List, Optional
import pandas as pd
import numpy as np

def compute_dynamic_kpis(df: pd.DataFrame, date_col: Optional[str] = None) -> List[Dict[str, Any]]:
    kpis = []
    total_rows = len(df)
    if total_rows == 0:
        return kpis
        
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
    
    # 2. Revenue / Monetary KPI
    rev_col = None
    for cand in ["revenue", "sales", "total_amount", "amount", "spend", "cost", "treatment_cost", "mrr_generated"]:
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
            "value": f"${total_rev:,.2f}" if total_rev > 100 else f"{total_rev:,.2f}",
            "raw_value": round(total_rev, 2),
            "delta_percent": delta_rev,
            "is_positive": (delta_rev >= 0) if delta_rev is not None else True,
            "indicator": "positive" if (delta_rev or 0) >= 0 else "negative",
            "description": f"Aggregate sum of {rev_col}"
        })
        
    # 3. Profit / ROI KPI
    profit_col = None
    for cand in ["profit", "roi", "net_margin", "satisfaction_score"]:
        if cand in cols_lower:
            profit_col = cols_lower[cand]
            break
            
    if profit_col and pd.api.types.is_numeric_dtype(df[profit_col]):
        if profit_col == "roi" or profit_col == "satisfaction_score":
            avg_val = float(df[profit_col].mean())
            p1_val = float(half_1_df[profit_col].mean()) if has_dates and half_1_df is not None else None
            p2_val = float(half_2_df[profit_col].mean()) if has_dates and half_2_df is not None else None
            delta_prof = round(((p2_val - p1_val) / max(abs(p1_val), 0.001)) * 100, 1) if p1_val is not None else None
            val_str = f"{avg_val:.2f}x" if profit_col == "roi" else f"{avg_val:.1f} / 10"
        else:
            tot_prof = float(df[profit_col].sum())
            p1_val = float(half_1_df[profit_col].sum()) if has_dates and half_1_df is not None else None
            p2_val = float(half_2_df[profit_col].sum()) if has_dates and half_2_df is not None else None
            delta_prof = round(((p2_val - p1_val) / max(abs(p1_val), 1)) * 100, 1) if p1_val is not None else None
            val_str = f"${tot_prof:,.2f}"
            
        kpis.append({
            "id": "primary_efficiency",
            "title": f"Average {profit_col.replace('_', ' ').title()}" if profit_col in ["roi", "satisfaction_score"] else f"Total {profit_col.replace('_', ' ').title()}",
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
"""

# 3. eda_engine.py
eda_engine_py = """from typing import Dict, Any, List, Optional
import pandas as pd
import numpy as np

def compute_eda_summary(df: pd.DataFrame) -> Dict[str, Any]:
    \"\"\"Computes summary statistics, distributions, and correlation matrix.\"\"\"
    summary_stats = {}
    distributions = {}
    
    numeric_df = df.select_dtypes(include=[np.number])
    for col in numeric_df.columns:
        series = numeric_df[col].dropna()
        if len(series) > 0:
            summary_stats[col] = {
                "mean": round(float(series.mean()), 2),
                "std": round(float(series.std()), 2) if len(series) > 1 else 0.0,
                "median": round(float(series.median()), 2),
                "min": round(float(series.min()), 2),
                "max": round(float(series.max()), 2),
                "q25": round(float(series.quantile(0.25)), 2),
                "q75": round(float(series.quantile(0.75)), 2)
            }
            # Bin distribution for charts (10 bins)
            counts, bin_edges = np.histogram(series, bins=10)
            distributions[col] = [
                {"bin": f"{round(bin_edges[i], 1)} - {round(bin_edges[i+1], 1)}", "count": int(counts[i])}
                for i in range(len(counts))
            ]
            
    # Pearson correlation matrix
    correlations = []
    if len(numeric_df.columns) >= 2:
        corr_matrix = numeric_df.corr().round(2)
        for row_col in corr_matrix.index:
            for col_col in corr_matrix.columns:
                val = corr_matrix.loc[row_col, col_col]
                if not np.isnan(val):
                    correlations.append({
                        "x": row_col,
                        "y": col_col,
                        "correlation": float(val)
                    })
                    
    # Categorical distributions (top 8 values per categorical column)
    categorical_counts = {}
    cat_df = df.select_dtypes(include=["object", "category", "string"])
    for col in cat_df.columns:
        if df[col].nunique() <= 30:
            top_vals = df[col].value_counts().head(8)
            categorical_counts[col] = [
                {"category": str(k), "count": int(v)} for k, v in top_vals.items()
            ]
            
    return {
        "summary_statistics": summary_stats,
        "distributions": distributions,
        "correlations": correlations,
        "categorical_counts": categorical_counts
    }
"""

# 4. chart_selector.py
chart_selector_py = """from typing import Dict, Any, List, Optional
import pandas as pd

def recommend_automatic_charts(df: pd.DataFrame) -> List[Dict[str, Any]]:
    \"\"\"Recommends dataset-aware charts based on analytical purpose.\"\"\"
    charts = []
    cols_lower = {str(c).lower(): c for c in df.columns}
    
    # Identify key date column
    date_col = None
    for c in df.columns:
        if pd.api.types.is_datetime64_any_dtype(df[c]) or any(k in str(c).lower() for k in ["date", "time", "day"]):
            date_col = c
            break
            
    # Identify key numeric metric (Revenue / Sales / Amount)
    metric_col = None
    for cand in ["revenue", "profit", "sales", "mrr_generated", "spend", "cost", "treatment_cost", "quantity"]:
        if cand in cols_lower:
            metric_col = cols_lower[cand]
            break
            
    # Identify primary categorical dimension
    cat_col = None
    for cand in ["region", "product_category", "category", "channel", "department", "segment", "customer_segment"]:
        if cand in cols_lower:
            cat_col = cols_lower[cand]
            break
            
    # 1. Primary Time Series Chart (Line Chart)
    if date_col and metric_col:
        try:
            temp_df = df.copy()
            temp_df["_dt"] = pd.to_datetime(temp_df[date_col], errors="coerce")
            ts_data = temp_df.dropna(subset=["_dt"]).groupby(temp_df["_dt"].dt.strftime("%Y-%m-%d"))[metric_col].sum().reset_index()
            ts_data.columns = ["date", "value"]
            ts_data = ts_data.sort_values("date").tail(60) # Last 60 points for clear rendering
            
            charts.append({
                "id": "trend_over_time",
                "title": f"{metric_col.replace('_', ' ').title()} Over Time",
                "chart_type": "line",
                "x_axis": "date",
                "y_axis": "value",
                "data": ts_data.to_dict(orient="records"),
                "description": f"Daily progression of {metric_col} across the dataset."
            })
        except Exception:
            pass

    # 2. Categorical Breakdown (Bar Chart)
    if cat_col and metric_col:
        try:
            bar_data = df.groupby(cat_col)[metric_col].sum().reset_index()
            bar_data.columns = ["category", "value"]
            bar_data = bar_data.sort_values("value", ascending=False).head(10)
            
            charts.append({
                "id": "category_breakdown",
                "title": f"{metric_col.replace('_', ' ').title()} by {cat_col.replace('_', ' ').title()}",
                "chart_type": "bar",
                "x_axis": "category",
                "y_axis": "value",
                "data": bar_data.to_dict(orient="records"),
                "description": f"Top performing {cat_col} categories ranked by total {metric_col}."
            })
        except Exception:
            pass
            
    # 3. Share / Composition (Donut Chart)
    secondary_cat = None
    for cand in ["customer_segment", "shipping_carrier", "channel", "admission_type", "gender"]:
        if cand in cols_lower and cols_lower[cand] != cat_col:
            secondary_cat = cols_lower[cand]
            break
            
    if secondary_cat and metric_col:
        try:
            donut_data = df.groupby(secondary_cat)[metric_col].sum().reset_index()
            donut_data.columns = ["label", "value"]
            donut_data = donut_data.sort_values("value", ascending=False).head(6)
            
            charts.append({
                "id": "share_composition",
                "title": f"Share of {metric_col.replace('_', ' ').title()} by {secondary_cat.replace('_', ' ').title()}",
                "chart_type": "donut",
                "name_key": "label",
                "value_key": "value",
                "data": donut_data.to_dict(orient="records"),
                "description": f"Relative distribution of {metric_col} across {secondary_cat}."
            })
        except Exception:
            pass
            
    # 4. Correlation / Scatter Relationship
    num_cols = df.select_dtypes(include=["number"]).columns.tolist()
    if len(num_cols) >= 2:
        x_col = num_cols[0]
        y_col = num_cols[1]
        sample_pts = df[[x_col, y_col]].dropna().head(80)
        sample_pts.columns = ["x", "y"]
        charts.append({
            "id": "scatter_relationship",
            "title": f"Relationship: {x_col.replace('_', ' ').title()} vs {y_col.replace('_', ' ').title()}",
            "chart_type": "scatter",
            "x_axis": "x",
            "y_axis": "y",
            "data": sample_pts.to_dict(orient="records"),
            "description": f"Bivariate scatter distribution showing interaction between {x_col} and {y_col}."
        })
        
    return charts
"""

init_analytics_py = """from .olap_engine import olap_engine
from .kpi_engine import compute_dynamic_kpis
from .eda_engine import compute_eda_summary
from .chart_selector import recommend_automatic_charts

__all__ = [
    "olap_engine",
    "compute_dynamic_kpis",
    "compute_eda_summary",
    "recommend_automatic_charts"
]
"""

with open(os.path.join(analytics_dir, "olap_engine.py"), "w", encoding="utf-8") as f:
    f.write(olap_engine_py)

with open(os.path.join(analytics_dir, "kpi_engine.py"), "w", encoding="utf-8") as f:
    f.write(kpi_engine_py)

with open(os.path.join(analytics_dir, "eda_engine.py"), "w", encoding="utf-8") as f:
    f.write(eda_engine_py)

with open(os.path.join(analytics_dir, "chart_selector.py"), "w", encoding="utf-8") as f:
    f.write(chart_selector_py)

with open(os.path.join(analytics_dir, "__init__.py"), "w", encoding="utf-8") as f:
    f.write(init_analytics_py)

print("Analytics modules successfully created.")
