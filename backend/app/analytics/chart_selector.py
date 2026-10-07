from typing import Dict, Any, List, Optional
import pandas as pd
import numpy as np

CURRENCY_KEYWORDS = {
    "revenue", "sales", "profit", "spend", "cost", "price", "amount",
    "unit_price", "total_amount", "treatment_cost", "mrr", "arr", "mrr_generated"
}

def is_currency_name(name: str) -> bool:
    c = str(name).lower()
    return any(k in c for k in CURRENCY_KEYWORDS) or "$" in c

def fmt_val(val: float, is_curr: bool = False, has_dollar: bool = False) -> str:
    if val is None or pd.isna(val):
        return "0"
    prefix = "$" if (has_dollar and is_curr) else ""
    if val < 0:
        return f"-{prefix}{abs(val):,.2f}"
    if float(val).is_integer():
        return f"{prefix}{int(val):,}"
    return f"{prefix}{val:,.2f}"

def recommend_automatic_charts(df: pd.DataFrame, has_dollar: bool = False) -> List[Dict[str, Any]]:
    """Recommends 6 dataset-aware charts with user-friendly explanations grounded in the data."""
    charts = []
    if df.empty:
        return charts
        
    cols_lower = {str(c).lower(): c for c in df.columns}
    
    # Identify key date column
    date_col = None
    for c in df.columns:
        if pd.api.types.is_datetime64_any_dtype(df[c]) or any(k in str(c).lower() for k in ["date", "time", "day"]):
            date_col = c
            break
            
    # Identify key numeric metrics
    num_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    num_cols = [c for c in num_cols if not any(id_k in str(c).lower() for id_k in ["id", "uuid", "code"])]
    
    metric_col = None
    for cand in ["revenue", "profit", "sales", "mrr_generated", "spend", "cost", "treatment_cost", "quantity", "leads"]:
        if cand in cols_lower:
            metric_col = cols_lower[cand]
            break
    if not metric_col and num_cols:
        metric_col = num_cols[0]
        
    # Categorical columns
    cat_columns = df.select_dtypes(include=["object", "category", "string"]).columns.tolist()
    cat_columns = [c for c in cat_columns if not any(id_k in str(c).lower() for id_k in ["id", "uuid", "code"])]
    
    cat_col = None
    for cand in ["region", "product_category", "category", "channel", "department", "segment", "customer_segment"]:
        if cand in cols_lower:
            cat_col = cols_lower[cand]
            break
    if not cat_col and cat_columns:
        cat_col = cat_columns[0]
        
    secondary_cat = None
    for c in cat_columns:
        if c != cat_col:
            secondary_cat = c
            break

    is_curr = is_currency_name(metric_col) if metric_col else False

    # --- Chart 1: Time Series Trend (Line Chart) ---
    if date_col and metric_col:
        try:
            temp_df = df.copy()
            temp_df["_dt"] = pd.to_datetime(temp_df[date_col], errors="coerce")
            ts_data = temp_df.dropna(subset=["_dt"]).groupby(temp_df["_dt"].dt.strftime("%Y-%m-%d"))[metric_col].sum().reset_index()
            ts_data.columns = ["date", "value"]
            ts_data = ts_data.sort_values("date").tail(60)
            records = ts_data.to_dict(orient="records")
            
            # Dynamic Explanation
            start_val = records[0]["value"] if records else 0
            end_val = records[-1]["value"] if records else 0
            diff_pct = round(((end_val - start_val) / max(abs(start_val), 1)) * 100, 1)
            trend_word = "increased" if diff_pct >= 0 else "declined"
            
            start_str = fmt_val(start_val, is_curr, has_dollar)
            end_str = fmt_val(end_val, is_curr, has_dollar)
            
            explanation = {
                "what_it_shows": f"Chronological trajectory of {metric_col.replace('_', ' ').title()} over time based on verified records.",
                "key_takeaway": f"The metric moved from {start_str} to {end_str} ({trend_word} by {abs(diff_pct)}%) across the observed interval.",
                "recommendation": f"Monitor cyclical peaks and build proactive operational buffers ahead of recurring demand contractions."
            }

            charts.append({
                "id": "trend_over_time",
                "title": f"1. {metric_col.replace('_', ' ').title()} Progression Over Time",
                "chart_type": "line",
                "x_axis": "date",
                "y_axis": "value",
                "data": records,
                "description": f"Daily chronological trend of {metric_col}.",
                "user_friendly_explanation": explanation
            })
        except Exception:
            pass

    # --- Chart 2: Categorical Breakdown (Bar Chart) ---
    if cat_col and metric_col:
        try:
            bar_data = df.groupby(cat_col)[metric_col].sum().reset_index()
            bar_data.columns = ["category", "value"]
            bar_data = bar_data.sort_values("value", ascending=False).head(10)
            records = bar_data.to_dict(orient="records")
            
            top_row = records[0] if records else {"category": "N/A", "value": 0}
            low_row = records[-1] if records else {"category": "N/A", "value": 0}
            tot_val = sum(r["value"] for r in records) or 1
            top_share = round((top_row["value"] / tot_val) * 100, 1)
            
            top_str = fmt_val(top_row["value"], is_curr, has_dollar)
            low_str = fmt_val(low_row["value"], is_curr, has_dollar)

            explanation = {
                "what_it_shows": f"Ranked comparison of total {metric_col.replace('_', ' ').title()} grouped across {cat_col.replace('_', ' ').title()} segments.",
                "key_takeaway": f"'{top_row['category']}' is the clear leader with {top_str} ({top_share}% of top segment volume), whereas '{low_row['category']}' is lowest at {low_str}.",
                "recommendation": f"Scale best practices from '{top_row['category']}' while conducting targeted margin and pricing reviews on underperforming segments."
            }

            charts.append({
                "id": "category_breakdown",
                "title": f"2. {metric_col.replace('_', ' ').title()} by {cat_col.replace('_', ' ').title()}",
                "chart_type": "bar",
                "x_axis": "category",
                "y_axis": "value",
                "data": records,
                "description": f"Top performing {cat_col} categories ranked by total {metric_col}.",
                "user_friendly_explanation": explanation
            })
        except Exception:
            pass

    # --- Chart 3: Share / Composition (Donut Chart) ---
    target_donut_col = secondary_cat or cat_col
    if target_donut_col and metric_col:
        try:
            donut_data = df.groupby(target_donut_col)[metric_col].sum().reset_index()
            donut_data.columns = ["label", "value"]
            donut_data = donut_data.sort_values("value", ascending=False).head(6)
            records = donut_data.to_dict(orient="records")
            
            top_slice = records[0] if records else {"label": "N/A", "value": 0}
            total_slice_sum = sum(r["value"] for r in records) or 1
            pct_share = round((top_slice["value"] / total_slice_sum) * 100, 1)
            slice_str = fmt_val(top_slice["value"], is_curr, has_dollar)

            explanation = {
                "what_it_shows": f"Proportional share of total {metric_col.replace('_', ' ').title()} distributed among {target_donut_col.replace('_', ' ').title()} segments.",
                "key_takeaway": f"'{top_slice['label']}' captures {pct_share}% share ({slice_str}), demonstrating significant volume concentration.",
                "recommendation": f"Protect high loyalty in '{top_slice['label']}' while diversifying campaigns to prevent single-cohort dependency."
            }

            charts.append({
                "id": "share_composition",
                "title": f"3. Relative Share of {metric_col.replace('_', ' ').title()} by {target_donut_col.replace('_', ' ').title()}",
                "chart_type": "donut",
                "name_key": "label",
                "value_key": "value",
                "data": records,
                "description": f"Percentage contribution of {target_donut_col} segments.",
                "user_friendly_explanation": explanation
            })
        except Exception:
            pass

    # --- Chart 4: Bivariate Relationship (Scatter Plot) ---
    if len(num_cols) >= 2:
        try:
            x_c = num_cols[0]
            y_c = num_cols[1] if num_cols[1] != x_c else (num_cols[2] if len(num_cols) > 2 else num_cols[0])
            sample_pts = df[[x_c, y_c]].dropna().head(80)
            sample_pts.columns = ["x", "y"]
            records = sample_pts.to_dict(orient="records")

            x_curr = is_currency_name(x_c)
            y_curr = is_currency_name(y_c)

            explanation = {
                "what_it_shows": f"Correlation mapping between individual {x_c.replace('_', ' ').title()} and {y_c.replace('_', ' ').title()} across sampled transactions.",
                "key_takeaway": f"Reveals whether increases in {x_c.replace('_', ' ')} consistently generate higher {y_c.replace('_', ' ')}, exposing margin leakages or non-linear trade-offs.",
                "recommendation": f"Audit isolated outlier transactions that yield low returns despite requiring high operational investment."
            }

            charts.append({
                "id": "scatter_relationship",
                "title": f"4. Scatter Relationship: {x_c.replace('_', ' ').title()} vs {y_c.replace('_', ' ').title()}",
                "chart_type": "scatter",
                "x_axis": "x",
                "y_axis": "y",
                "data": records,
                "description": f"Correlation plot showing trade-offs between {x_c} and {y_c}.",
                "user_friendly_explanation": explanation
            })
        except Exception:
            pass

    # --- Chart 5: Operational Risk / Efficiency Metrics (Bar / Column Chart) ---
    risk_col = None
    for cand in ["delivery_delay_days", "wait_time_minutes", "customer_complaint", "order_cancelled", "readmission_30d", "bounce_rate", "cpa", "discount"]:
        if cand in cols_lower:
            risk_col = cols_lower[cand]
            break
    if not risk_col and len(num_cols) >= 3:
        risk_col = num_cols[2]
        
    if risk_col and cat_col:
        try:
            risk_data = df.groupby(cat_col)[risk_col].mean().reset_index()
            risk_data.columns = ["category", "value"]
            risk_data["value"] = risk_data["value"].round(2)
            risk_data = risk_data.sort_values("value", ascending=False).head(8)
            records = risk_data.to_dict(orient="records")

            top_risk = records[0] if records else {"category": "N/A", "value": 0}
            is_risk_curr = is_currency_name(risk_col)
            risk_val_str = fmt_val(top_risk["value"], is_risk_curr, has_dollar)

            explanation = {
                "what_it_shows": f"Average {risk_col.replace('_', ' ').title()} benchmarked across {cat_col.replace('_', ' ').title()} to identify operational risk areas.",
                "key_takeaway": f"'{top_risk['category']}' experiences the highest operational burden at {risk_val_str} on average.",
                "recommendation": f"Deploy automated threshold alerts and operational remediation specifically for '{top_risk['category']}'."
            }

            charts.append({
                "id": "risk_efficiency_metric",
                "title": f"5. Average {risk_col.replace('_', ' ').title()} by {cat_col.replace('_', ' ').title()}",
                "chart_type": "bar",
                "x_axis": "category",
                "y_axis": "value",
                "data": records,
                "description": f"Operational bottleneck & efficiency metric across {cat_col}.",
                "user_friendly_explanation": explanation
            })
        except Exception:
            pass

    # --- Chart 6: Volume / Entity Count Distribution (Bar / Column Chart) ---
    ranking_dim = None
    for cand in ["product_name", "product_id", "channel", "department", "doctor_specialty", "campaign_name", "carrier", "sub_category"]:
        if cand in cols_lower and cols_lower[cand] not in [cat_col, secondary_cat]:
            ranking_dim = cols_lower[cand]
            break
    if not ranking_dim and cat_columns:
        ranking_dim = cat_columns[-1]
        
    if ranking_dim and metric_col:
        try:
            rank_data = df.groupby(ranking_dim)[metric_col].sum().reset_index()
            rank_data.columns = ["category", "value"]
            rank_data = rank_data.sort_values("value", ascending=False).head(10)
            records = rank_data.to_dict(orient="records")

            top_entity = records[0] if records else {"category": "N/A", "value": 0}
            top_entity_str = fmt_val(top_entity["value"], is_curr, has_dollar)

            explanation = {
                "what_it_shows": f"Top 10 ranked {ranking_dim.replace('_', ' ').title()} entities driving cumulative {metric_col.replace('_', ' ').title()}.",
                "key_takeaway": f"'{top_entity['category']}' is the #1 ranked contributor delivering {top_entity_str} in total value.",
                "recommendation": f"Implement dedicated retention and capacity guarantees for the top ranked {ranking_dim} entities."
            }

            charts.append({
                "id": "entity_ranking",
                "title": f"6. Top {ranking_dim.replace('_', ' ').title()} Entity Ranking",
                "chart_type": "bar",
                "x_axis": "category",
                "y_axis": "value",
                "data": records,
                "description": f"Top 10 {ranking_dim} entities ranked by cumulative {metric_col}.",
                "user_friendly_explanation": explanation
            })
        except Exception:
            pass

    # --- Fallback Fillers to ALWAYS guarantee 6 charts ---
    fallback_index = 1
    while len(charts) < 6:
        if cat_columns and fallback_index <= len(cat_columns):
            col_to_use = cat_columns[fallback_index - 1]
            c_data = df[col_to_use].value_counts().head(8).reset_index()
            c_data.columns = ["category", "value"]
            records = c_data.to_dict(orient="records")
            
            top_item = records[0] if records else {"category": "N/A", "value": 0}
            explanation = {
                "what_it_shows": f"Record count distribution grouped by {col_to_use.replace('_', ' ').title()}.",
                "key_takeaway": f"'{top_item['category']}' accounts for the largest transaction frequency ({top_item['value']:,} occurrences).",
                "recommendation": f"Ensure sufficient operational throughput for '{top_item['category']}' to prevent processing delays."
            }
            
            charts.append({
                "id": f"fallback_cat_{fallback_index}",
                "title": f"{len(charts)+1}. Distribution of Record Count by {col_to_use.replace('_', ' ').title()}",
                "chart_type": "bar",
                "x_axis": "category",
                "y_axis": "value",
                "data": records,
                "description": f"Total transaction count grouped by {col_to_use}.",
                "user_friendly_explanation": explanation
            })
        elif num_cols and fallback_index <= len(num_cols):
            col_to_use = num_cols[fallback_index - 1]
            n_data = df[col_to_use].head(30).reset_index()
            n_data.columns = ["category", "value"]
            records = n_data.to_dict(orient="records")
            
            is_n_curr = is_currency_name(col_to_use)
            avg_n = fmt_val(float(df[col_to_use].mean()), is_n_curr, has_dollar)
            explanation = {
                "what_it_shows": f"Sequential distribution of {col_to_use.replace('_', ' ').title()} across sample records.",
                "key_takeaway": f"Overall dataset mean for {col_to_use.replace('_', ' ')} is {avg_n}.",
                "recommendation": f"Monitor variance around the mean to detect potential outlier clusters."
            }
            
            charts.append({
                "id": f"fallback_num_{fallback_index}",
                "title": f"{len(charts)+1}. Sample Values for {col_to_use.replace('_', ' ').title()}",
                "chart_type": "line",
                "x_axis": "category",
                "y_axis": "value",
                "data": records,
                "description": f"Sequential distribution of {col_to_use} across sample records.",
                "user_friendly_explanation": explanation
            })
        else:
            break
        fallback_index += 1

    return charts[:6]
