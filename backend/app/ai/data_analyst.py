import json
import os
import re
from typing import Dict, Any, List, Optional, Tuple
import pandas as pd
from ..core.config import settings
from ..analytics.olap_engine import olap_engine
from .sql_validator import validate_safe_sql
from .llm_provider import query_free_llm

# ─── Domain context registry ─────────────────────────────────────────────────
DOMAIN_CONTEXT = {
    "ecommerce": {
        "label": "E-Commerce / Retail",
        "primary_metrics": ["revenue", "sales", "profit", "quantity", "order_value"],
        "risk_metrics": ["delivery_delay_days", "order_cancelled", "return_rate", "discount"],
        "dimensions": ["region", "product_category", "category", "channel", "customer_segment", "product_name", "customer_name", "state"],
        "business_context": (
            "This is an e-commerce/retail dataset. Focus on revenue, order fulfilment, "
            "delivery performance, product categories, and regional sales breakdown."
        ),
    },
    "saas": {
        "label": "B2B SaaS / Growth",
        "primary_metrics": ["mrr_generated", "arr", "leads", "roi", "conversions", "spend"],
        "risk_metrics": ["cpa", "bounce_rate", "churn_rate", "cac", "roi"],
        "dimensions": ["channel", "segment", "region", "campaign_name", "plan_type"],
        "business_context": (
            "This is a B2B SaaS / growth funnel dataset. Focus on MRR, ARR, lead conversions, "
            "channel ROI, CAC, churn, and marketing spend efficiency."
        ),
    },
    "healthcare": {
        "label": "Hospital / Healthcare",
        "primary_metrics": ["treatment_cost", "length_of_stay", "wait_time_minutes", "readmission_30d"],
        "risk_metrics": ["readmission_30d", "wait_time_minutes", "length_of_stay", "mortality_rate"],
        "dimensions": ["department", "doctor_specialty", "admission_type", "insurance_type", "region"],
        "business_context": (
            "This is a healthcare/hospital dataset. Focus on patient treatment costs, length of stay, "
            "readmission rates, wait times, departmental efficiency, and care quality."
        ),
    },
    "marketing": {
        "label": "Marketing / Campaigns",
        "primary_metrics": ["spend", "impressions", "clicks", "conversions", "revenue", "roi"],
        "risk_metrics": ["cpa", "bounce_rate", "cpc", "ctr"],
        "dimensions": ["channel", "campaign_name", "region", "audience_segment"],
        "business_context": (
            "This is a marketing/campaign dataset. Focus on ad spend, impressions, click-through rate, "
            "cost-per-acquisition, ROI, and channel performance comparisons."
        ),
    },
    "generic": {
        "label": "General Business Dataset",
        "primary_metrics": [],
        "risk_metrics": [],
        "dimensions": [],
        "business_context": (
            "This is a general dataset. Focus on key metrics, numerical distributions, and categorical breakdowns."
        ),
    },
}


class AIAnalystResponse:
    def __init__(
        self,
        finding: str,
        evidence: str,
        explanation: str,
        recommendation: str,
        confidence: str = "High",
        sql_query: Optional[str] = None,
        chart_spec: Optional[Dict[str, Any]] = None,
        raw_data: Optional[List[Dict[str, Any]]] = None,
        rag_chunks_used: int = 0,
        how_to_prevent: Optional[str] = None,
        how_to_improve: Optional[str] = None,
    ):
        self.finding = finding
        self.evidence = evidence
        self.explanation = explanation
        self.recommendation = recommendation
        self.confidence = confidence
        self.sql_query = sql_query
        self.chart_spec = chart_spec
        self.raw_data = raw_data
        self.rag_chunks_used = rag_chunks_used
        self.how_to_prevent = how_to_prevent
        self.how_to_improve = how_to_improve

    def to_dict(self) -> Dict[str, Any]:
        return {
            "finding": self.finding,
            "evidence": self.evidence,
            "explanation": self.explanation,
            "recommendation": self.recommendation,
            "confidence": self.confidence,
            "sql_query": self.sql_query,
            "chart_spec": self.chart_spec,
            "raw_data": self.raw_data,
            "rag_chunks_used": self.rag_chunks_used,
            "how_to_prevent": self.how_to_prevent,
            "how_to_improve": self.how_to_improve,
        }


def _resolve_columns(schema_info, domain_type: str):
    """Resolve target metric, dimension, risk metric dynamically."""
    col_names_lower = {c["safe_column_name"].lower(): c["safe_column_name"] for c in schema_info}
    numeric_cols = [c["safe_column_name"] for c in schema_info if c.get("is_numeric")]
    cat_cols = [c["safe_column_name"] for c in schema_info if c.get("is_categorical")]
    date_cols = [c["safe_column_name"] for c in schema_info if c.get("is_date")]
    domain = DOMAIN_CONTEXT.get(domain_type or "generic", DOMAIN_CONTEXT["generic"])

    target_num = None
    for cand in domain["primary_metrics"] + [
        "revenue", "sales", "profit", "spend", "cost", "value", "amount", "price", "performance_score", "score"
    ]:
        if cand in col_names_lower:
            target_num = col_names_lower[cand]
            break
    if not target_num:
        target_num = numeric_cols[0] if numeric_cols else "count(*)"

    risk_metric = None
    for cand in domain["risk_metrics"] + [
        "delivery_delay_days", "wait_time_minutes", "bounce_rate", "cpa", "error_rate"
    ]:
        if cand in col_names_lower:
            risk_metric = col_names_lower[cand]
            break
    if not risk_metric:
        risk_metric = next((c for c in numeric_cols if c != target_num), target_num)

    dim_col = None
    for cand in domain["dimensions"] + [
        "region", "category", "channel", "segment", "department", "type", "status", "product_name", "customer_name", "state"
    ]:
        if cand in col_names_lower:
            dim_col = col_names_lower[cand]
            break
    if not dim_col:
        dim_col = cat_cols[0] if cat_cols else "1"

    return target_num, dim_col, risk_metric, cat_cols, date_cols, domain


def _smart_semantic_sql_builder(
    question: str,
    table_name: str,
    schema_info: List[Dict[str, Any]],
    active_target: str,
    target_num: str,
    cat_cols: List[str],
    numeric_cols: List[str],
    date_cols: List[str],
) -> Tuple[str, str, Optional[str], str, int]:
    """
    Intelligently parses user query intent, columns, aggregation, direction,
    and row limit (top 10, top 20, etc.) to produce accurate SQL without hallucinations.
    Returns: (sql_query, detected_metric, detected_dimension, agg_type, limit)
    """
    q_low = question.lower().strip()
    words = re.findall(r'[a-zA-Z0-9_]+', q_low)

    # 1. Detect row limit (e.g., top 10, top 20, 5 best, etc.)
    limit = 10
    limit_match = re.search(r'\b(?:top|first|highest|best|lowest|bottom|worst|limit)\s*(\d+)\b', q_low)
    if limit_match:
        limit = min(max(int(limit_match.group(1)), 1), 50)
    else:
        num_match = re.search(r'\b(\d+)\s*(?:items|records|rows|products|customers|departments|categories|states|regions|accounts|cohorts|segments)\b', q_low)
        if num_match:
            limit = min(max(int(num_match.group(1)), 1), 50)
        elif "top 20" in q_low or "20 best" in q_low or "first 20" in q_low:
            limit = 20
        elif "top 10" in q_low or "10 best" in q_low or "first 10" in q_low:
            limit = 10
        elif "top 5" in q_low or "5 best" in q_low:
            limit = 5

    # 2. Detect sort direction
    direction = "DESC"
    if any(k in q_low for k in ["lowest", "least", "bottom", "worst", "smallest", "min", "minimum", "fewer", "fewest", "lower", "drop"]):
        direction = "ASC"

    # 3. Synonym matching dictionaries
    dim_synonyms = {
        "product": ["product", "products", "item", "items", "sku", "title", "goods", "merchandise"],
        "customer": ["customer", "customers", "client", "clients", "user", "users", "buyer", "buyers", "account", "accounts"],
        "state": ["state", "states", "province", "provinces"],
        "region": ["region", "regions", "zone", "zones", "territory", "area", "areas"],
        "city": ["city", "cities", "town", "metro"],
        "category": ["category", "categories", "segment", "segments", "group", "class", "genre"],
        "department": ["department", "departments", "dept", "team", "teams", "division", "divisions"],
        "channel": ["channel", "channels", "source", "medium"],
        "status": ["status", "stage", "condition"],
        "country": ["country", "nation"],
        "segment": ["segment", "segments", "cohort", "cohorts", "tier"],
    }

    metric_synonyms = {
        "sales": ["sale", "sales", "revenue", "turnover", "income", "gmv", "amount"],
        "profit": ["profit", "profits", "margin", "earnings", "net"],
        "quantity": ["quantity", "quantities", "volume", "units", "ordered", "order_count"],
        "discount": ["discount", "discounts", "rate", "rebate"],
        "cost": ["cost", "costs", "expense", "expenses", "spend", "spending", "cpa", "cpc"],
        "delay": ["delay", "delays", "shipping", "delivery", "late"],
        "salary": ["salary", "salaries", "pay", "wage", "compensation"],
        "score": ["score", "rating", "performance", "kpi", "grade", "feedback"],
        "time": ["time", "hours", "duration", "wait"],
    }

    # 4. Identify dimension (grouping column)
    matched_dim = None
    all_col_names = [c["safe_column_name"] for c in schema_info]

    # Direct column name match in query
    for c in cat_cols + date_cols:
        c_clean = c.lower().replace("_", " ")
        if c.lower() in q_low or c_clean in q_low or any(w in c.lower().split("_") for w in words):
            matched_dim = c
            break

    # Synonym match if direct match not found
    if not matched_dim:
        for concept, syns in dim_synonyms.items():
            if any(syn in q_low for syn in syns):
                # Look for a column containing this concept
                for c in cat_cols + date_cols:
                    c_low = c.lower()
                    if any(syn in c_low for syn in syns):
                        matched_dim = c
                        break
            if matched_dim:
                break

    # If asking for "which <col>"
    if not matched_dim:
        which_match = re.search(r'\b(?:which|what)\s+([a-zA-Z0-9_]+)', q_low)
        if which_match:
            candidate_word = which_match.group(1).lower()
            for c in cat_cols:
                if candidate_word in c.lower() or c.lower() in candidate_word:
                    matched_dim = c
                    break

    # Default dimension
    if not matched_dim:
        matched_dim = cat_cols[0] if cat_cols else (date_cols[0] if date_cols else None)

    # 5. Identify metric (numeric column)
    matched_metric = None
    for c in numeric_cols:
        c_clean = c.lower().replace("_", " ")
        if c.lower() in q_low or c_clean in q_low or any(w in c.lower().split("_") for w in words):
            matched_metric = c
            break

    if not matched_metric:
        for concept, syns in metric_synonyms.items():
            if any(syn in q_low for syn in syns):
                for c in numeric_cols:
                    c_low = c.lower()
                    if any(syn in c_low for syn in syns):
                        matched_metric = c
                        break
            if matched_metric:
                break

    if not matched_metric:
        matched_metric = active_target if (active_target in numeric_cols) else (target_num if target_num in numeric_cols else (numeric_cols[0] if numeric_cols else None))

    # 6. Aggregation logic
    if any(k in q_low for k in ["average", "avg", "mean", "rate", "percentage", "ratio"]):
        agg_type = "avg"
        agg_expr = f"ROUND(AVG({matched_metric}), 2)" if matched_metric else "ROUND(AVG(1), 2)"
    elif any(k in q_low for k in ["count", "how many", "number of", "total orders", "order count"]):
        agg_type = "count"
        agg_expr = "COUNT(*)"
    elif any(k in q_low for k in ["max", "maximum", "peak"]):
        agg_type = "max"
        agg_expr = f"ROUND(MAX({matched_metric}), 2)" if matched_metric else "MAX(1)"
    elif any(k in q_low for k in ["min", "minimum"]):
        agg_type = "min"
        agg_expr = f"ROUND(MIN({matched_metric}), 2)" if matched_metric else "MIN(1)"
    else:
        # Check if metric is naturally an average/rate or cumulative sum
        if matched_metric and any(k in matched_metric.lower() for k in ["delay", "rate", "percent", "score", "ratio", "age", "rating", "satisfaction"]):
            agg_type = "avg"
            agg_expr = f"ROUND(AVG({matched_metric}), 2)"
        elif matched_metric:
            agg_type = "sum"
            agg_expr = f"ROUND(SUM({matched_metric}), 2)"
        else:
            agg_type = "count"
            agg_expr = "COUNT(*)"

    # 7. Construct SQL Query
    if matched_dim:
        sql = (
            f"SELECT {matched_dim} AS label, {agg_expr} AS value, COUNT(*) AS count "
            f"FROM {table_name} "
            f"WHERE {matched_dim} IS NOT NULL "
            f"GROUP BY {matched_dim} "
            f"ORDER BY value {direction} "
            f"LIMIT {limit}"
        )
    elif matched_metric:
        sql = (
            f"SELECT {agg_expr} AS value, COUNT(*) AS count "
            f"FROM {table_name}"
        )
    else:
        sql = f"SELECT COUNT(*) AS total_records FROM {table_name}"

    return sql, matched_metric, matched_dim, agg_type, limit


def _detect_chart_request(question: str) -> Optional[str]:
    """
    Detects if the user explicitly requested a chart/graph/plot/visualization,
    and returns the specific chart type ('bar', 'line', 'pie', 'scatter', or 'auto').
    Returns None if no chart was requested.
    """
    q_low = question.lower()
    chart_indicator_words = [
        "chart", "graph", "plot", "visualize", "visualization", "visual",
        "diagram", "histogram", "pie", "donut", "doughnut", "scatter"
    ]
    requested = any(re.search(rf"\b{re.escape(w)}\b", q_low) for w in chart_indicator_words)
    if not requested:
        if re.search(r"\b(?:bar|bars|line|lines|pie)\s+(?:chart|graph|plot|of)\b", q_low):
            requested = True

    if not requested:
        return None

    if any(k in q_low for k in ["pie", "donut", "doughnut"]):
        return "pie"
    if any(k in q_low for k in ["scatter", "scatter plot"]):
        return "scatter"
    if any(k in q_low for k in ["line", "trend", "timeline", "over time", "run chart"]):
        return "line"
    if any(k in q_low for k in ["bar", "column", "bars"]):
        return "bar"

    return "auto"


def _is_unrelated_question(question: str, schema_info: List[Dict[str, Any]]) -> bool:
    """
    Checks if the user question is unrelated to the provided dataset.
    """
    q_low = question.lower().strip()
    words = set(re.findall(r'[a-zA-Z0-9_]+', q_low))
    if not words:
        return True

    if q_low in ["hello", "hi", "hey", "help", "who are you", "what can you do"]:
        return False

    for c in schema_info:
        c_name = c.get("safe_column_name", "").lower()
        if c_name in q_low or any(w in words for w in c_name.split("_") if len(w) > 2):
            return False

    analytical_vocabulary = {
        "top", "bottom", "highest", "lowest", "best", "worst", "most", "least",
        "average", "avg", "mean", "median", "sum", "total", "count", "number",
        "max", "min", "breakdown", "distribution", "trend", "correlation", "ranking",
        "rank", "ranks", "percentage", "percent", "rate", "ratio", "chart", "graph",
        "plot", "bar", "pie", "line", "scatter", "table", "outlier", "anomaly",
        "records", "record", "rows", "row", "data", "dataset", "metric", "column",
        "feature", "driver", "summary", "explain", "show", "give", "list", "compare",
        "performance", "pattern", "sale", "sales", "revenue", "profit", "cost",
        "price", "product", "item", "customer", "client", "buyer", "user", "order",
        "state", "region", "city", "country", "category", "department", "segment",
        "discount", "quantity", "volume", "unit", "units", "delay", "time", "date"
    }

    if words & analytical_vocabulary:
        return False

    return True


def answer_analyst_query(
    question: str,
    table_name: str,
    schema_info: List[Dict[str, Any]],
    parquet_path: str,
    domain_type: Optional[str] = None,
    dataset_id: Optional[str] = None,
    target_column: Optional[str] = None,
) -> "AIAnalystResponse":
    from .rag_engine import retrieve_context

    olap_engine.register_parquet(table_name, parquet_path)
    q_clean = question.strip()
    q_low = q_clean.lower()

    col_names_lower = {c["safe_column_name"].lower(): c["safe_column_name"] for c in schema_info}
    all_col_names = [c["safe_column_name"] for c in schema_info]
    numeric_cols = [c["safe_column_name"] for c in schema_info if c.get("is_numeric")]
    cat_cols = [c["safe_column_name"] for c in schema_info if c.get("is_categorical")]
    date_cols = [c["safe_column_name"] for c in schema_info if c.get("is_date")]

    target_num, dim_col, risk_metric, _, _, domain = _resolve_columns(schema_info, domain_type)
    active_target = target_column or target_num

    domain_label = domain.get("label", "Business Dataset")
    schema_cols = ", ".join(all_col_names)

    # ── Retrieve RAG context ────────────────────────────────────────────────
    rag_chunks = []
    rag_context_str = ""
    if dataset_id:
        try:
            rag_chunks = retrieve_context(dataset_id, question, top_k=4)
            if rag_chunks:
                rag_context_str = "\n\n📚 RETRIEVED DATASET KNOWLEDGE:\n" + "\n".join(
                    [f"  • {c['text']}" for c in rag_chunks]
                )
        except Exception:
            rag_chunks = []

    # ── Check for casual greetings or help ───
    is_greeting = q_low in [
        "hello", "hi", "hey", "help", "who are you", "what can you do", "test", "sup",
        "good morning", "good evening", "how are you"
    ]
    if is_greeting:
        sample_questions = []
        if cat_cols and numeric_cols:
            sample_questions.append(f"Show the top 10 {cat_cols[0].replace('_', ' ')} by {numeric_cols[0].replace('_', ' ')}.")
        if len(cat_cols) > 1 and numeric_cols:
            sample_questions.append(f"Give top 20 {cat_cols[1].replace('_', ' ')} with highest {numeric_cols[0].replace('_', ' ')}.")
        if numeric_cols:
            sample_questions.append(f"What is the average {numeric_cols[0].replace('_', ' ')} across categories?")
        sample_questions.append(f"Show the ranking of {active_target.replace('_', ' ')} across segments.")

        options_list = "\n".join([f"  • {q}" for q in sample_questions[:4]])
        polite_reply = (
            f"Hello! I am your InsightX AI Data Analyst connected to your **{domain_label}** dataset.\n\n"
            f"Ask me any analytical question based on your dataset (e.g. top 10 rankings, averages, totals, or request specific charts like bar, line, or pie).\n\n"
            f"Suggested questions to try:\n{options_list}"
        )
        return AIAnalystResponse(
            finding=f"InsightX Analyst Ready — Connected to {domain_label} ({len(schema_info)} active columns).",
            evidence=f"Active dataset columns: {schema_cols[:140]}...",
            explanation=polite_reply,
            recommendation="Type any question based on your dataset, or ask for a specific chart.",
            confidence="High",
            sql_query=None,
            chart_spec=None,
            raw_data=None,
            rag_chunks_used=len(rag_chunks),
        )

    # ── Check for completely unrelated questions ───────────────────────────
    if _is_unrelated_question(question, schema_info):
        unrelated_msg = "I'm sorry, but I couldn't find that information in the data you've provided. Please ask a question related to your uploaded data."
        return AIAnalystResponse(
            finding=unrelated_msg,
            evidence="No matching columns or empirical records found in the uploaded data.",
            explanation="InsightX is an AI-powered data insights assistant. All answers are derived strictly and exclusively from your uploaded dataset without external assumptions.",
            recommendation="Please ask a question related to your uploaded data (e.g. top rankings, averages, totals, or breakdowns of your columns).",
            confidence="Low",
            sql_query=None,
            chart_spec=None,
            raw_data=None,
            rag_chunks_used=0,
        )

    # ── Generate Deterministic Semantic SQL (Guaranteed accuracy for question)
    semantic_sql, detected_metric, detected_dim, agg_type, detected_limit = _smart_semantic_sql_builder(
        question=question,
        table_name=table_name,
        schema_info=schema_info,
        active_target=active_target,
        target_num=target_num,
        cat_cols=cat_cols,
        numeric_cols=numeric_cols,
        date_cols=date_cols,
    )

    # ── Dynamic Text-to-SQL Generation using LLM (if available) ─────────────
    col_descriptions = [
        f"{c['safe_column_name']} ({c.get('detected_type', 'string')}{', TARGET' if c['safe_column_name'] == active_target else ''})"
        for c in schema_info
    ]

    sql_prompt = (
        f"You are an expert SQL engineer for DuckDB.\n"
        f"Write a single, safe DuckDB SQL SELECT query that directly answers the user's specific question.\n\n"
        f"Table: {table_name}\n"
        f"Available Columns: {', '.join(col_descriptions)}\n"
        f"User Question: \"{question}\"\n\n"
        f"Rules:\n"
        f"1. Return ONLY the raw SQL query. No markdown, no backticks, no explanation.\n"
        f"2. Must start with SELECT and query from {table_name}.\n"
        f"3. If the user asks for 'top 10', use LIMIT 10. If 'top 20', use LIMIT 20. If not specified, use LIMIT 10.\n"
        f"4. If asking for highest/top, ORDER BY ... DESC. If lowest/bottom, ORDER BY ... ASC.\n"
        f"5. Always alias grouping column as 'label' and aggregated value as 'value'.\n"
        f"6. Example: SELECT Category AS label, ROUND(SUM(Sales), 2) AS value, COUNT(*) AS count FROM {table_name} GROUP BY Category ORDER BY value DESC LIMIT 10"
    )

    res_df = None
    validated_sql = None

    try:
        raw_llm_sql = query_free_llm(sql_prompt)
        if raw_llm_sql:
            clean_sql = raw_llm_sql.replace("```sql", "").replace("```", "").strip().rstrip(";")
            cand_sql = validate_safe_sql(clean_sql)
            res_df = olap_engine.query(cand_sql)
            if res_df is not None and len(res_df) > 0:
                validated_sql = cand_sql
    except Exception:
        res_df = None
        validated_sql = None

    # Fallback to intelligent semantic SQL if LLM query was unavailable or failed
    if res_df is None or len(res_df) == 0:
        try:
            validated_sql = validate_safe_sql(semantic_sql)
            res_df = olap_engine.query(validated_sql)
        except Exception:
            # Ultimate safe fallback
            validated_sql = f"SELECT {cat_cols[0] if cat_cols else '1'} AS label, COUNT(*) AS value FROM {table_name} GROUP BY 1 ORDER BY value DESC LIMIT 10"
            res_df = olap_engine.query(validated_sql)

    records = res_df.to_dict(orient="records") if res_df is not None else []

    # Check if dataset has dollar symbol
    has_dollar = any("$" in str(c.get("original_column_name", "")) or "$" in str(c.get("safe_column_name", "")) for c in schema_info)
    if not has_dollar and parquet_path and os.path.exists(parquet_path):
        try:
            import pyarrow.parquet as pq
            from ..services.currency_detector import dataset_has_dollar_symbol
            pf = pq.ParquetFile(parquet_path)
            sample_df = pf.read_row_group(0).to_pandas()
            has_dollar = dataset_has_dollar_symbol(sample_df)
        except Exception:
            has_dollar = False

    is_currency_metric = False
    if detected_metric:
        is_currency_metric = any(k in detected_metric.lower() for k in ["sales", "profit", "revenue", "price", "cost", "amount", "spend", "mrr", "arr", "value"])

    def fmt_val(v):
        if v is None or pd.isna(v):
            return "0"
        pfx = "$" if (has_dollar and is_currency_metric) else ""
        try:
            val_f = float(v)
            if val_f < 0:
                return f"-{pfx}{abs(val_f):,.2f}"
            if val_f.is_integer():
                return f"{pfx}{int(val_f):,}"
            return f"{pfx}{val_f:,.2f}"
        except Exception:
            return str(v)

    # ── Chart Specification: Only generate chart when explicitly requested by user ───
    requested_chart = _detect_chart_request(question)
    chart_spec = None

    if requested_chart and res_df is not None and len(records) >= 1:
        cols = list(res_df.columns)
        x_col = "label" if "label" in cols else cols[0]
        y_col = "value" if "value" in cols else (cols[1] if len(cols) > 1 else cols[0])

        is_temporal = any(k in str(x_col).lower() or k in str(detected_dim).lower() for k in ["date", "time", "day", "month", "year"])

        if requested_chart == "auto":
            final_chart_type = "line" if is_temporal else "bar"
        else:
            final_chart_type = requested_chart

        dim_label_str = (detected_dim or x_col).replace("_", " ").title()
        metric_label_str = (detected_metric or "Volume").replace("_", " ").title()
        agg_label_str = agg_type.title() if agg_type else "Total"
        chart_title = f"{final_chart_type.title()} Chart: {agg_label_str} {metric_label_str} by {dim_label_str} ({len(records)} items)"

        chart_spec = {
            "chart_type": final_chart_type,
            "title": chart_title,
            "x_axis": x_col,
            "y_axis": y_col,
            "name_key": x_col,
            "value_key": y_col,
            "data": records,
        }

    # ── Answer Synthesis: Clear, Direct, Dataset-Grounded ────────────────────
    data_summary_str = json.dumps(records[:15], default=str)
    if has_dollar and is_currency_metric:
        curr_inst = "Format monetary amounts with dollar signs ($), e.g. $1,250.00."
    else:
        curr_inst = "Do not use dollar signs ($) unless the dataset explicitly uses them. Use clean commas, e.g. 1,250.00."

    answer_prompt = (
        "You are InsightX, an AI-powered data insights assistant. "
        "Answer questions using ONLY the context retrieved from the user's uploaded data. "
        "Never use external knowledge, assumptions, or invented information. "
        "If a question is unrelated to the provided data or its answer is missing, politely respond: "
        "\"I'm sorry, but I couldn't find that information in the data you've provided. Please ask a question related to your uploaded data.\" "
        "If only partial information is available, answer only the supported part. Keep responses clear, concise, and professional.\n\n"
        f"User Question: \"{question}\"\n"
        f"Executed SQL: {validated_sql}\n"
        f"Actual Query Data: {data_summary_str}\n"
        f"{rag_context_str}\n\n"
        f"Instructions:\n"
        f"1. Answer directly and truthfully using ONLY the exact numbers from the query data above.\n"
        f"2. Do NOT output raw tables or markdown tables. Focus directly on key figures and clear analytical answers.\n"
        f"3. {curr_inst}\n"
        f"4. Output in this exact format:\n"
        f"FINDING: (1 direct sentence stating the clear answer with the exact top numbers)\n"
        f"EVIDENCE: (1-2 sentences summarizing key metrics, totals, or percentages from the data)\n"
        f"EXPLANATION: (1-2 sentences explaining why this pattern occurs based on the dataset drivers)\n"
        f"RECOMMENDATION: (1 practical, actionable takeaway for leadership)"
    )

    llm_synthesis = query_free_llm(question, system_context=answer_prompt)

    finding_text = ""
    evidence_text = ""
    explanation_text = ""
    recommendation_text = ""

    if llm_synthesis:
        lines = llm_synthesis.split("\n")
        current_section = "explanation"
        collected = {
            "finding": [],
            "evidence": [],
            "explanation": [],
            "recommendation": []
        }
        for line in lines:
            line_str = line.strip()
            if not line_str:
                continue
            clean_lower = line_str.lower().replace("*", "").replace("#", "").strip()
            if clean_lower.startswith("finding:"):
                current_section = "finding"
                val = line_str.replace("*", "").replace("#", "")
                collected["finding"].append(val.split(":", 1)[1].strip())
            elif clean_lower.startswith("evidence:"):
                current_section = "evidence"
                val = line_str.replace("*", "").replace("#", "")
                collected["evidence"].append(val.split(":", 1)[1].strip())
            elif clean_lower.startswith("explanation:"):
                current_section = "explanation"
                val = line_str.replace("*", "").replace("#", "")
                collected["explanation"].append(val.split(":", 1)[1].strip())
            elif clean_lower.startswith("recommendation:"):
                current_section = "recommendation"
                val = line_str.replace("*", "").replace("#", "")
                collected["recommendation"].append(val.split(":", 1)[1].strip())
            else:
                collected[current_section].append(line_str)

        finding_text = " ".join(collected["finding"]).strip()
        evidence_text = " ".join(collected["evidence"]).strip()
        explanation_text = "\n".join(collected["explanation"]).strip()
        recommendation_text = " ".join(collected["recommendation"]).strip()

    # Deterministic natural synthesis if LLM was unavailable
    if records:
        top_row = records[0]
        top_name = str(top_row.get("label", list(top_row.values())[0]))
        top_val_raw = top_row.get("value", list(top_row.values())[1] if len(top_row) > 1 else 0)
        top_val_str = fmt_val(top_val_raw)

        metric_name = (detected_metric or "metric").replace("_", " ").title()
        dim_name = (detected_dim or "category").replace("_", " ").title()

        if not finding_text:
            if len(records) > 1:
                finding_text = f"'{top_name}' leads the ranking with {top_val_str} {metric_name.lower()}, ranking #1 among the top {len(records)} {dim_name.lower()} groups."
            else:
                finding_text = f"The {agg_type} {metric_name.lower()} is {top_val_str} based on your query."

        if not evidence_text:
            if len(records) > 1:
                last_row = records[-1]
                last_name = str(last_row.get("label", "other groups"))
                last_val_str = fmt_val(last_row.get("value", 0))
                evidence_text = f"The top segment ('{top_name}') accounts for {top_val_str}, while '{last_name}' recorded {last_val_str}. Total analyzed groups: {len(records)}."
            else:
                evidence_text = f"Calculated directly from verified dataset records via in-memory DuckDB query."

        if not explanation_text:
            explanation_text = f"Performance is driven by strong volume concentration in '{top_name}'. Review the interactive chart above to evaluate how distribution varies across segments."

        if not recommendation_text:
            recommendation_text = f"Prioritize operational capacity and resource allocation toward high-yielding segments like '{top_name}' to maximize overall performance."
    else:
        if not finding_text:
            finding_text = "No records matched the specified query parameters in the dataset."
        if not evidence_text:
            evidence_text = "Query evaluated 0 matching rows."
        if not explanation_text:
            explanation_text = "The requested columns or filter criteria did not return any records in the current dataset."
        if not recommendation_text:
            recommendation_text = "Try broadening your query or selecting another column to explore."

    return AIAnalystResponse(
        finding=finding_text,
        evidence=evidence_text,
        explanation=explanation_text,
        recommendation=recommendation_text,
        confidence="High",
        sql_query=validated_sql,
        chart_spec=chart_spec,
        raw_data=records,
        rag_chunks_used=len(rag_chunks),
    )


def build_custom_chart(
    table_name: str,
    parquet_path: str,
    x_col: str,
    y_col: Optional[str] = None,
    chart_type: str = "bar",
    aggregation: str = "none",
) -> Dict[str, Any]:
    """
    Build a custom chart from user-selected columns.
    aggregation: 'none' (raw individual values) | 'sum' | 'avg' | 'count' | 'max' | 'min'
    """
    olap_engine.register_parquet(table_name, parquet_path)

    agg = (aggregation or "none").lower()

    if agg == "none" or not y_col or y_col == x_col:
        # User does not want aggregation: plot raw record values directly
        if y_col and y_col != x_col:
            sql = f"SELECT {x_col} AS label, {y_col} AS value FROM {table_name} WHERE {x_col} IS NOT NULL AND {y_col} IS NOT NULL LIMIT 40"
            title = f"{y_col.replace('_',' ').title()} by {x_col.replace('_',' ').title()} (Raw Values)"
        else:
            sql = f"SELECT {x_col} AS label, COUNT(*) AS value FROM {table_name} GROUP BY {x_col} ORDER BY value DESC LIMIT 20"
            title = f"Distribution of {x_col.replace('_',' ').title()}"
        agg_label = "Raw Values"
    else:
        agg_map = {
            "sum": f"SUM({y_col})",
            "avg": f"AVG({y_col})",
            "count": "COUNT(*)",
            "max": f"MAX({y_col})",
            "min": f"MIN({y_col})",
        }
        agg_expr = agg_map.get(agg, f"SUM({y_col})")
        sql = (
            f"SELECT {x_col} AS label, {agg_expr} AS value "
            f"FROM {table_name} GROUP BY {x_col} ORDER BY value DESC LIMIT 20"
        )
        agg_label = {"sum": "Total", "avg": "Average", "count": "Count", "max": "Max", "min": "Min"}.get(
            agg, agg.title()
        )
        title = f"{agg_label} {y_col.replace('_',' ').title()} by {x_col.replace('_',' ').title()}"

    validated_sql = validate_safe_sql(sql)
    res_df = olap_engine.query(validated_sql)
    records = res_df.to_dict(orient="records") if res_df is not None else []

    # Check if dataset has dollar symbol
    has_dollar = False
    if parquet_path and os.path.exists(parquet_path):
        try:
            import pyarrow.parquet as pq
            from ..services.currency_detector import dataset_has_dollar_symbol
            pf = pq.ParquetFile(parquet_path)
            sample_df = pf.read_row_group(0).to_pandas()
            has_dollar = dataset_has_dollar_symbol(sample_df)
        except Exception:
            has_dollar = False

    is_curr = any(k in str(y_col or x_col).lower() for k in ["sales", "profit", "revenue", "price", "cost", "amount", "spend"]) or "$" in str(y_col or x_col)

    def fmt_custom_val(v):
        if v is None or pd.isna(v):
            return "0"
        prefix = "$" if (has_dollar and is_curr) else ""
        if v < 0:
            return f"-{prefix}{abs(v):,.2f}"
        if float(v).is_integer():
            return f"{prefix}{int(v):,}"
        return f"{prefix}{v:,.2f}"

    if records:
        top_item = records[0]
        low_item = records[-1]
        tot_val = sum(r.get("value", 0) for r in records if isinstance(r.get("value"), (int, float))) or 1
        top_val = top_item.get("value", 0)
        low_val = low_item.get("value", 0)
        top_share = round((top_val / tot_val) * 100, 1) if tot_val else 0
        
        top_str = fmt_custom_val(top_val)
        low_str = fmt_custom_val(low_val)
        
        y_name = (y_col or x_col).replace("_", " ").title()
        x_name = x_col.replace("_", " ").title()

        user_friendly_explanation = {
            "what_it_shows": f"Plots {agg_label.lower()} of {y_name} distributed across {x_name} categories based on your custom query.",
            "key_takeaway": f"'{top_item.get('label', 'N/A')}' leads the distribution with {top_str} ({top_share}% of total analyzed volume), while '{low_item.get('label', 'N/A')}' ranks lowest at {low_str}.",
            "recommendation": f"Focus capacity and operational efficiency on high-volume {x_name} categories like '{top_item.get('label', 'N/A')}' while investigating margin variations in lower cohorts."
        }
    else:
        user_friendly_explanation = {
            "what_it_shows": f"Custom query tracking {y_col or x_col} grouped by {x_col}.",
            "key_takeaway": "No record groups met the query criteria.",
            "recommendation": "Try selecting different dimensions or aggregations."
        }

    return {
        "chart_type": chart_type,
        "title": title,
        "description": f"Custom chart: {agg_label} of {y_col or x_col} grouped by {x_col}.",
        "x_axis": "label",
        "y_axis": "value",
        "data": records,
        "sql_query": validated_sql,
        "id": f"custom_{x_col}_{y_col}_{agg}_{int(pd.Timestamp.now().timestamp())}",
        "user_friendly_explanation": user_friendly_explanation,
    }
