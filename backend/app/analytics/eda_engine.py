from typing import Dict, Any, List, Optional
import pandas as pd
import numpy as np

def compute_eda_summary(df: pd.DataFrame) -> Dict[str, Any]:
    """Computes summary statistics, distributions, and correlation matrix."""
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
