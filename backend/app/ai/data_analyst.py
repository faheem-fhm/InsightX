import json
import os
from typing import Dict, Any, List, Optional
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
        "dimensions": ["region", "product_category", "category", "channel", "customer_segment"],
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
    numeric_cols = [c["safe_column_name"] for c in schema_info if c["is_numeric"]]
    cat_cols = [c["safe_column_name"] for c in schema_info if c["is_categorical"]]
    date_cols = [c["safe_column_name"] for c in schema_info if c["is_date"]]
    domain = DOMAIN_CONTEXT.get(domain_type or "generic", DOMAIN_CONTEXT["generic"])

    target_num = None
    for cand in domain["primary_metrics"] + [
        "revenue", "sales", "profit", "spend", "cost", "value", "amount", "price"
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
        "region", "category", "channel", "segment", "department", "type", "status"
    ]:
        if cand in col_names_lower:
            dim_col = col_names_lower[cand]
            break
    if not dim_col:
        dim_col = cat_cols[0] if cat_cols else "1"

    return target_num, dim_col, risk_metric, cat_cols, date_cols, domain


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
    biz_context = domain.get("business_context", "")
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

    # ── Check for casual greetings, help, or unwanted/off-topic questions ───
    is_greeting = q_low in [
        "hello", "hi", "hey", "help", "who are you", "what can you do", "test", "sup",
        "good morning", "good evening", "how are you"
    ]
    # Check if question is completely unrelated to data analysis or dataset columns
    has_column_mention = any(c.lower() in q_low for c in all_col_names)
    analytical_keywords = [
        "average", "avg", "sum", "total", "count", "how many", "rate", "percent",
        "why", "how", "what", "which", "increase", "decrease", "drop", "change",
        "distribution", "trend", "compare", "chart", "graph", "maximum", "minimum",
        "max", "min", "highest", "lowest", "correlation", "cause", "reason", "target"
    ]
    has_analytic_intent = any(k in q_low for k in analytical_keywords)
    is_off_topic = not has_column_mention and not has_analytic_intent and len(q_clean.split()) < 6

    if is_greeting or is_off_topic:
        sample_questions = []
        if numeric_cols and cat_cols:
            sample_questions.append(f"What is the average {numeric_cols[0].replace('_', ' ')} by {active_target.replace('_', ' ')}?")
            sample_questions.append(f"Why does {active_target.replace('_', ' ')} increase or decrease across {cat_cols[0].replace('_', ' ')}?")
        if len(numeric_cols) >= 2:
            sample_questions.append(f"What is the relationship between {numeric_cols[0].replace('_', ' ')} and {numeric_cols[1].replace('_', ' ')}?")
        sample_questions.append(f"Show a summary breakdown of the dataset target variable ({active_target.replace('_', ' ')}).")

        options_list = "\n".join([f"  • {q}" for q in sample_questions[:4]])
        polite_reply = (
            f"Hello! I am your InsightX AI Data Analyst connected to your **{domain_label}** dataset.\n\n"
            f"I analyze your dataset directly (target variable: **{active_target.replace('_', ' ')}**, columns: {schema_cols[:120]}...).\n\n"
            f"Here are specific analytical questions you can ask me:\n{options_list}"
        )
        return AIAnalystResponse(
            finding=f"InsightX Analyst Ready — Connected to {domain_label} (Target: {active_target}).",
            evidence=f"Active columns ({len(schema_info)}): {schema_cols[:120]}...",
            explanation=polite_reply,
            recommendation="Select any suggested question or type your question about the dataset.",
            confidence="High",
            sql_query=None,
            chart_spec=None,
            raw_data=None,
            rag_chunks_used=len(rag_chunks),
        )

    # ── Check if user specifically wants or refuses a graph ─────────────────
    wants_graph = any(
        k in q_low for k in ["chart", "graph", "plot", "visualize", "visualization", "histogram", "trend", "show curve"]
    )
    # If user explicitly asks for simple text or says no graph, do NOT send graph
    if any(
        k in q_low
        for k in [
            "no graph", "no chart", "without graph", "without chart", "tell only",
            "simple way", "just answer", "just tell", "why it give the graph", "dont give graph", "don't give graph"
        ]
    ):
        wants_graph = False

    # ── Dynamic Text-to-SQL Generation using LLM ────────────────────────────
    col_descriptions = [
        f"{c['safe_column_name']} ({c.get('detected_type', 'string')}{', TARGET' if c['safe_column_name'] == active_target else ''})"
        for c in schema_info
    ]

    sql_prompt = (
        f"You are an expert SQL engineer for DuckDB.\n"
        f"Write a single, safe DuckDB SQL SELECT query that directly computes the answer to the user's question.\n\n"
        f"Table: {table_name}\n"
        f"Available Columns: {', '.join(col_descriptions)}\n"
        f"Target Column: {active_target}\n"
        f"User Question: \"{question}\"\n\n"
        f"Rules:\n"
        f"1. Return ONLY the raw SQL query. No markdown, no backticks, no explanations.\n"
        f"2. Must start with SELECT and query from {table_name}.\n"
        f"3. Use appropriate aggregations (AVG, SUM, COUNT, MIN, MAX). Round decimal averages to 2 decimals using ROUND(..., 2).\n"
        f"4. If comparing groups or calculating rates by category, GROUP BY that column and include COUNT(*) AS count.\n"
        f"5. Limit results to at most 20 rows."
    )

    res_df = None
    validated_sql = None

    try:
        raw_llm_sql = query_free_llm(sql_prompt)
        if raw_llm_sql:
            clean_sql = raw_llm_sql.replace("```sql", "").replace("```", "").strip().rstrip(";")
            validated_sql = validate_safe_sql(clean_sql)
            res_df = olap_engine.query(validated_sql)
    except Exception:
        res_df = None
        validated_sql = None

    # Fallback SQL generation if LLM query failed or was empty
    if res_df is None or len(res_df) == 0:
        # Check which column appears in question
        found_cols = [c for c in all_col_names if c.lower() in q_low]
        group_col = active_target if active_target in all_col_names else (cat_cols[0] if cat_cols else "1")
        metric_col = target_num if target_num in numeric_cols else (numeric_cols[0] if numeric_cols else "1")

        for c in found_cols:
            if c in cat_cols or c == active_target:
                group_col = c
            elif c in numeric_cols:
                metric_col = c

        if metric_col in numeric_cols and group_col in all_col_names and group_col != "1":
            sql = (
                f"SELECT {group_col} AS label, ROUND(AVG({metric_col}), 2) AS avg_value, COUNT(*) AS count "
                f"FROM {table_name} GROUP BY {group_col} ORDER BY avg_value DESC LIMIT 20"
            )
        elif metric_col in numeric_cols:
            sql = (
                f"SELECT ROUND(AVG({metric_col}), 2) AS avg_value, ROUND(MIN({metric_col}), 2) AS min_value, "
                f"ROUND(MAX({metric_col}), 2) AS max_value, COUNT(*) AS count FROM {table_name}"
            )
        else:
            sql = f"SELECT {group_col} AS label, COUNT(*) AS count FROM {table_name} GROUP BY {group_col} ORDER BY count DESC LIMIT 15"

        try:
            validated_sql = validate_safe_sql(sql)
            res_df = olap_engine.query(validated_sql)
        except Exception:
            # Ultimate safe count fallback
            validated_sql = f"SELECT COUNT(*) AS total_records FROM {table_name}"
            res_df = olap_engine.query(validated_sql)

    records = res_df.to_dict(orient="records") if res_df is not None else []
    data_summary_str = json.dumps(records[:10], default=str)

    # Check if dataset explicitly has dollar symbol
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

    if has_dollar:
        currency_instruction = "4. If citing monetary amounts (such as Sales, Profit, Revenue, Cost, Price), format them clearly with dollar signs ($), e.g., $1,250.00 or -$450.00. Never put dollar signs on non-currency counts, quantities, ages, or percentages."
    else:
        currency_instruction = "4. CRITICAL: This dataset does NOT use dollar symbols ($). Do NOT use any dollar signs ($) anywhere in your response. Report all amounts and numbers cleanly with commas, e.g., 1,250.00 or -450.00."

    # ── Answer Synthesis: Clear, Simple, Dataset-Grounded ────────────────────
    answer_prompt = (
        f"You are the InsightX AI Data Analyst. Give a simple, direct, plain-English answer to the user's question.\n"
        f"User Question: \"{question}\"\n"
        f"Dataset Domain: {domain_label}.\n"
        f"Target Column: {active_target}.\n"
        f"{rag_context_str}\n\n"
        f"Executed SQL: {validated_sql}\n"
        f"Actual Query Data: {data_summary_str}\n\n"
        f"Instructions:\n"
        f"1. Answer simply, directly, and truthfully using the actual numbers from the query data above.\n"
        f"2. Explain the reasons or drivers in 1-2 simple sentences based on the data patterns.\n"
        f"3. Provide 1 practical, actionable recommendation based on the data.\n"
        f"{currency_instruction}\n"
        f"5. Do NOT make excuses about missing data or columns; the query has computed the exact numbers.\n"
        f"6. Output in this exact format:\n"
        f"FINDING: (1 direct sentence with the exact answer and numbers)\n"
        f"EVIDENCE: (1 concise sentence specifying the counts, rates, or averages)\n"
        f"EXPLANATION: (1-2 clear sentences explaining the analytical result based on the dataset)\n"
        f"RECOMMENDATION: (1 practical, actionable takeaway based on the dataset)"
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
            elif clean_lower.startswith("explanation:") or clean_lower.startswith("why it happened:"):
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

    # Fallback formatting if parsing was empty
    if not finding_text and records:
        first_row = records[0]
        finding_text = f"Analysis shows: {', '.join([f'{k}: {v}' for k, v in list(first_row.items())[:3]])}."
    if not evidence_text:
        evidence_text = f"Calculated from DuckDB SQL query across {len(records)} record group(s)."
    if not explanation_text:
        explanation_text = llm_synthesis or (
            f"The query analyzed '{question}' directly against {active_target}. "
            f"Review the breakdown to understand how performance varies across groups."
        )

    if not recommendation_text:
        recommendation_text = f"Analyze variations across categories to prioritize high-performing segments."

    # ── Chart Specification: Only provide a graph if requested or relevant ──
    chart_spec = None
    if wants_graph and res_df is not None and len(res_df) >= 2 and len(res_df.columns) >= 2:
        cols = list(res_df.columns)
        x_axis = cols[0]
        # Look for numeric column for y
        y_candidates = [c for c in cols[1:] if c != x_axis]
        y_axis = y_candidates[0] if y_candidates else cols[1]

        chart_title = (
            f"{y_axis.replace('_', ' ').title()} by {x_axis.replace('_', ' ').title()}"
        )
        chart_spec = {
            "chart_type": "line" if any(k in q_low for k in ["trend", "over time", "month", "day"]) else "bar",
            "title": chart_title,
            "x_axis": x_axis,
            "y_axis": y_axis,
            "data": records,
        }

    return AIAnalystResponse(
        finding=finding_text or "Analysis completed.",
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
