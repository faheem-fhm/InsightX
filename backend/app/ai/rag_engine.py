"""
RAG Engine — Retrieval-Augmented Generation for InsightX
"""

import json
import os
import math
from pathlib import Path
from typing import List, Dict, Any, Optional
import pandas as pd
import numpy as np

PROFILE_DIR = Path(__file__).parent.parent.parent.parent / "data" / "processed"


def _safe(val):
    if isinstance(val, (np.integer,)):
        return int(val)
    if isinstance(val, (np.floating,)):
        return float(val) if not math.isnan(val) else None
    if isinstance(val, (np.ndarray,)):
        return val.tolist()
    return val


def build_rag_profile(
    dataset_id: str,
    df: pd.DataFrame,
    schema_info: List[Dict[str, Any]],
    domain_type: str = "generic",
) -> Dict[str, Any]:
    chunks: List[Dict[str, Any]] = []
    row_count = len(df)
    col_count = len(df.columns)

    overview_text = (
        f"Dataset overview: {row_count:,} total records and {col_count} columns. "
        f"Domain classification: {domain_type}. "
        f"Available attributes: {', '.join([str(c) for c in df.columns])}."
    )
    chunks.append({
        "id": "overview",
        "keywords": ["overview", "size", "rows", "columns", "dataset", "total", "count", "summary", domain_type, "hello", "hi", "help"],
        "text": overview_text,
    })

    for col in df.columns:
        col_lower = str(col).lower()
        series = df[col].dropna()
        null_pct = round((df[col].isna().sum() / max(row_count, 1)) * 100, 1)
        unique_count = df[col].nunique()

        if pd.api.types.is_numeric_dtype(df[col]):
            col_min = _safe(series.min()) if len(series) > 0 else None
            col_max = _safe(series.max()) if len(series) > 0 else None
            col_avg = round(_safe(series.mean()), 2) if len(series) > 0 else None
            col_std = round(_safe(series.std()), 2) if len(series) > 0 else None
            col_med = round(_safe(series.median()), 2) if len(series) > 0 else None
            text = (
                f"Column '{col}' (numeric): min={col_min}, max={col_max}, "
                f"average={col_avg}, median={col_med}, std_dev={col_std}, "
                f"null_percent={null_pct}%, unique_values={unique_count}."
            )
            chunks.append({
                "id": f"col_num_{col}",
                "keywords": [col_lower, "numeric", "average", "mean", "max", "min", "median",
                             "total", "sum", col_lower.replace("_", " ")],
                "text": text,
                "col": col,
                "type": "numeric",
                "stats": {"min": col_min, "max": col_max, "avg": col_avg, "std": col_std, "median": col_med},
            })

        elif pd.api.types.is_datetime64_any_dtype(df[col]) or any(
            k in col_lower for k in ["date", "time", "day", "month", "year"]
        ):
            try:
                dt_series = pd.to_datetime(series, errors="coerce").dropna()
                if len(dt_series) > 0:
                    date_min = str(dt_series.min().date())
                    date_max = str(dt_series.max().date())
                    text = (
                        f"Column '{col}' (date/time): date range from {date_min} to {date_max}. "
                        f"Null percent={null_pct}%."
                    )
                    chunks.append({
                        "id": f"col_date_{col}",
                        "keywords": [col_lower, "date", "time", "period", "range", "when", "trend",
                                     "monthly", "daily", "over time", "history"],
                        "text": text,
                        "col": col,
                        "type": "date",
                    })
            except Exception:
                pass

        else:
            top_vals = df[col].value_counts().head(10)
            top_list = ", ".join([f"'{v}' ({c:,})" for v, c in top_vals.items()])
            text = (
                f"Column '{col}' (categorical): {unique_count} unique values. "
                f"Top values: {top_list}. "
                f"Null percent={null_pct}%."
            )
            chunks.append({
                "id": f"col_cat_{col}",
                "keywords": [col_lower, "category", "segment", "group", "which", "top", "best",
                             "worst", col_lower.replace("_", " ")] + 
                            [str(v).lower() for v in top_vals.index[:5]],
                "text": text,
                "col": col,
                "type": "categorical",
                "top_values": top_vals.index.tolist()[:10],
            })

    # Numeric correlations
    num_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    num_cols = [c for c in num_cols if not any(k in c.lower() for k in ["id", "uuid", "code"])]
    if len(num_cols) >= 2:
        try:
            corr_matrix = df[num_cols].corr()
            strong_pairs = []
            for i, c1 in enumerate(num_cols):
                for c2 in num_cols[i + 1:]:
                    val = corr_matrix.loc[c1, c2]
                    if not math.isnan(val) and abs(val) >= 0.4:
                        strong_pairs.append(f"'{c1}' & '{c2}' (r={round(val, 2)})")
            if strong_pairs:
                corr_text = (
                    f"Significant correlations found: {'; '.join(strong_pairs[:8])}. "
                    "Strong positive correlation suggests one drives the other."
                )
                chunks.append({
                    "id": "correlations",
                    "keywords": ["correlation", "relationship", "impact", "drives", "affect",
                                 "cause", "why", "influence"] + 
                                [c.lower() for c in num_cols[:6]],
                    "text": corr_text,
                })
        except Exception:
            pass

    from .data_analyst import DOMAIN_CONTEXT
    domain = DOMAIN_CONTEXT.get(domain_type, DOMAIN_CONTEXT["generic"])
    col_names_lower = {str(c).lower(): str(c) for c in df.columns}

    found_metrics = [
        col_names_lower[m] for m in domain["primary_metrics"] if m in col_names_lower
    ]
    found_risks = [
        col_names_lower[r] for r in domain["risk_metrics"] if r in col_names_lower
    ]

    if found_metrics:
        domain_text = (
            f"Domain context ({domain['label']}): "
            f"Primary KPI columns detected: {', '.join(found_metrics)}. "
            f"Risk/efficiency columns: {', '.join(found_risks) if found_risks else 'none detected'}. "
            f"{domain['business_context']}"
        )
        chunks.append({
            "id": "domain_context",
            "keywords": ["business", "domain", "kpi", "metric", "performance", domain_type,
                        "revenue", "sales", "cost", "efficiency"] + 
                       [m.lower() for m in found_metrics],
            "text": domain_text,
        })

    suggested_prompts = _build_suggested_prompts(df, domain_type, domain, col_names_lower)

    profile = {
        "dataset_id": dataset_id,
        "domain_type": domain_type,
        "row_count": row_count,
        "col_count": col_count,
        "chunks": chunks,
        "suggested_prompts": suggested_prompts,
    }

    try:
        PROFILE_DIR.mkdir(parents=True, exist_ok=True)
        profile_path = PROFILE_DIR / f"{dataset_id}_rag_profile.json"
        with open(profile_path, "w", encoding="utf-8") as f:
            json.dump(profile, f, default=str, indent=2)
    except Exception as e:
        print(f"RAG profile cache write failed: {e}")

    return profile


def _build_suggested_prompts(df, domain_type, domain, col_names_lower) -> List[str]:
    prompts = []
    num_cols = [c for c in df.select_dtypes(include=[np.number]).columns
                if not any(k in c.lower() for k in ["id", "uuid", "code"])]
    cat_cols = [c for c in df.select_dtypes(include=["object", "category"]).columns
                if not any(k in c.lower() for k in ["id", "uuid", "code"])]
    date_cols = [c for c in df.columns if any(k in c.lower() for k in ["date", "time", "day"])]

    primary = None
    for m in domain["primary_metrics"]:
        if m in col_names_lower:
            primary = col_names_lower[m]
            break
    if not primary and num_cols:
        primary = num_cols[0]

    dim = None
    for d in domain["dimensions"]:
        if d in col_names_lower:
            dim = col_names_lower[d]
            break
    if not dim and cat_cols:
        dim = cat_cols[0]

    risk = None
    for r in domain["risk_metrics"]:
        if r in col_names_lower:
            risk = col_names_lower[r]
            break
    if not risk and len(num_cols) > 1:
        risk = num_cols[1]

    metric_label = primary.replace("_", " ") if primary else "performance"
    dim_label = dim.replace("_", " ") if dim else "category"

    if primary:
        prompts.append(f"Why did {metric_label} decrease?")
        prompts.append(f"Which {dim_label} has the highest {metric_label}?")
        prompts.append(f"Show top 10 by {metric_label}.")
    if date_cols and primary:
        prompts.append(f"Show monthly {metric_label} trend.")
    if risk:
        prompts.append(f"What drives {risk.replace('_',' ')} the most?")
    if len(num_cols) >= 2:
        prompts.append(f"How does {num_cols[0].replace('_',' ')} correlate with {num_cols[1].replace('_',' ')}?")
    prompts.append("Find unusual patterns in the data.")
    prompts.append(f"Give me a full summary of this dataset.")

    return prompts[:7]


def load_rag_profile(dataset_id: str) -> Optional[Dict[str, Any]]:
    try:
        profile_path = PROFILE_DIR / f"{dataset_id}_rag_profile.json"
        if profile_path.exists():
            with open(profile_path, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception as e:
        print(f"RAG profile load failed: {e}")
    return None


def retrieve_context(dataset_id: str, question: str, top_k: int = 4) -> List[Dict[str, Any]]:
    """
    Retrieve top-K most relevant knowledge chunks.
    Guarantees at least the dataset overview chunk is included so queries never return 0 RAG chunks.
    """
    profile = load_rag_profile(dataset_id)
    if not profile:
        return []

    all_chunks = profile.get("chunks", [])
    if not all_chunks:
        return []

    q_tokens = set(question.lower().replace("?", "").replace(",", "").replace(".", "").split())
    scored = []
    for chunk in all_chunks:
        chunk_keywords = set(chunk.get("keywords", []))
        chunk_text_tokens = set(chunk.get("text", "").lower().split())
        kw_overlap = len(q_tokens & chunk_keywords)
        text_overlap = len(q_tokens & chunk_text_tokens)
        score = kw_overlap * 3 + text_overlap
        if score > 0:
            scored.append((score, chunk))

    scored.sort(key=lambda x: x[0], reverse=True)
    results = [chunk for _, chunk in scored[:top_k]]

    # If no chunk matched query words (e.g. "hello", "hi", or unrelated words),
    # include overview and primary domain chunks as baseline context
    if not results:
        results = all_chunks[:min(3, len(all_chunks))]

    return results


def get_suggested_prompts(dataset_id: str) -> List[str]:
    profile = load_rag_profile(dataset_id)
    if profile and profile.get("suggested_prompts"):
        return profile["suggested_prompts"]
    return [
        "Show a summary of this dataset.",
        "What are the top performing segments?",
        "Show the trend over time.",
        "Which category has the highest value?",
        "Find unusual patterns in the data.",
    ]
