from typing import Dict, Any, List, Optional
import pandas as pd
import numpy as np


def detect_rfm_domain(df: pd.DataFrame, monetary_col: str) -> str:
    cols = [str(c).lower() for c in df.columns]
    all_text = " ".join(cols) + " " + str(monetary_col).lower()
    
    if any(k in all_text for k in ["nitrogen", "phosphorus", "potassium", "crop", "soil", "fertilizer", "rainfall", "humidity", "ph", "harvest", "agriculture"]):
        return "agriculture"
    if any(k in all_text for k in ["patient", "hospital", "admission", "treatment", "doctor", "triage", "disease", "blood_pressure", "cholesterol", "heart"]):
        return "healthcare"
    if any(k in all_text for k in ["customer", "client", "buyer", "shopper", "order", "sales", "revenue", "retail", "store"]):
        return "customer"
    if any(k in all_text for k in ["subscriber", "user", "account", "churn", "mrr", "arr", "seat", "tenant"]):
        return "saas"
    return "generic"


def run_rfm_segmentation(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Performs robust RFM (Recency, Frequency, Monetary/Value) segmentation and cohort intelligence.
    Works universally across any dataset (agriculture, healthcare, SaaS, retail, operations)
    with user-friendly explanations tailored directly to the underlying dataset.
    """
    if df.empty:
        return {"supported": False, "reason": "Dataset is empty."}

    cols_lower = {str(c).lower().replace(" ", "_"): c for c in df.columns}
    
    # 1. Detect Customer / Entity identifier column
    cust_col = None
    entity_label = None
    for cand, label in [
        ("customer_id", "Customer"), ("customer", "Customer"), ("customer_name", "Customer"),
        ("client_id", "Client"), ("client", "Client"), ("user_id", "User"), ("user", "User"),
        ("patient_id", "Patient"), ("patient", "Patient"), ("member_id", "Member"),
        ("account_id", "Account"), ("account", "Account"), ("subscriber_id", "Subscriber"),
        ("subscriber", "Subscriber"), ("lead_id", "Lead"), ("order_id", "Order Entity")
    ]:
        if cand in cols_lower:
            cust_col = cols_lower[cand]
            entity_label = label
            break

    # Look for domain categorical entity columns (e.g. crop, label, variety, species, category, department)
    if not cust_col:
        for cand, label in [
            ("crop", "Crop Variety"), ("label", "Crop Variety"), ("variety", "Variety"),
            ("species", "Species"), ("category", "Category"), ("department", "Department"),
            ("segment", "Segment"), ("region", "Region"), ("product", "Product Category")
        ]:
            if cand in cols_lower:
                cust_col = cols_lower[cand]
                entity_label = label
                break

    # Fallback to categorical column with good entity cardinality (between 3 and 1000 unique values)
    if not cust_col:
        for c in df.columns:
            if df[c].dtype == object or pd.api.types.is_categorical_dtype(df[c]):
                u = df[c].nunique()
                if 3 <= u <= 1000:
                    cust_col = c
                    entity_label = str(c).replace("_", " ").title()
                    break

    # 2. Detect Date / Temporal column
    date_col = None
    for cand in ["order_date", "date", "admission_date", "transaction_date", "created_at", "timestamp", "event_date", "time"]:
        if cand in cols_lower:
            date_col = cols_lower[cand]
            break
            
    if not date_col:
        for c in df.columns:
            if pd.api.types.is_datetime64_any_dtype(df[c]) or any(k in str(c).lower() for k in ["date", "time", "year"]):
                date_col = c
                break

    # 3. Detect Value / Target metric
    monetary_col = None
    for cand in ["nitrogen", "revenue", "sales", "total_amount", "amount", "treatment_cost", "spend", "cost", "mrr_generated", "profit", "price", "value", "yield"]:
        if cand in cols_lower:
            monetary_col = cols_lower[cand]
            break

    if not monetary_col:
        num_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        num_cols = [c for c in num_cols if not any(k in str(c).lower() for k in ["id", "uuid", "code", "year", "unnamed"])]
        monetary_col = num_cols[0] if num_cols else df.columns[-1]

    domain = detect_rfm_domain(df, monetary_col)

    # Set appropriate entity label if still none
    if not entity_label:
        if domain == "agriculture":
            entity_label = "Soil Sample"
        elif domain == "healthcare":
            entity_label = "Clinical Case"
        else:
            entity_label = "Sample Record"

    temp_df = df.copy()
    if not cust_col:
        temp_df["_entity_id"] = [f"{entity_label} #{i + 1}" for i in range(len(temp_df))]
        cust_col = "_entity_id"

    # Process dates
    has_dates = False
    if date_col:
        temp_df["_dt"] = pd.to_datetime(temp_df[date_col], errors="coerce")
        if temp_df["_dt"].notna().sum() > len(temp_df) * 0.3:
            max_date = temp_df["_dt"].max()
            temp_df["_recency_days"] = (max_date - temp_df["_dt"]).dt.days.fillna(30)
            has_dates = True
        else:
            temp_df["_recency_days"] = np.linspace(90, 1, len(temp_df))
    else:
        temp_df["_recency_days"] = np.linspace(90, 1, len(temp_df))

    temp_df[monetary_col] = pd.to_numeric(temp_df[monetary_col], errors="coerce").fillna(0.0)

    # Compute RFM / cohort aggregation per entity
    rfm = temp_df.groupby(cust_col).agg(
        recency=("_recency_days", "min"),
        frequency=(cust_col, "count"),
        monetary=(monetary_col, "mean" if not has_dates else "sum")
    ).reset_index()

    total_customers = len(rfm)
    q_bins = min(4, max(2, total_customers))

    # Quantile ranking
    r_score = pd.qcut(rfm["recency"].rank(method="first"), q=q_bins, labels=False)
    f_score = pd.qcut(rfm["frequency"].rank(method="first"), q=q_bins, labels=False)
    m_score = pd.qcut(rfm["monetary"].rank(method="first"), q=q_bins, labels=False)

    rfm["r_score"] = (q_bins - 1) - r_score
    rfm["f_score"] = f_score + 1
    rfm["m_score"] = m_score + 1
    
    if has_dates:
        rfm["rfm_combined"] = rfm["r_score"] * 0.3 + rfm["f_score"] * 0.3 + rfm["m_score"] * 0.4
    else:
        # Solely based on metric distribution when no dates
        rfm["rfm_combined"] = rfm["m_score"]

    monetary_title = monetary_col.replace("_", " ").title()

    # Domain-specific Cohort Definitions and Playbooks
    if domain == "agriculture":
        studio_title = "Crop & Soil Cohort Intelligence Studio"
        studio_subtitle = f"Distribution clustering and actionable nutrient management for '{monetary_title}' across agricultural observations."
        retention_label = "Optimal Range Compliance"
        
        tier_names = [
            "Optimal Tier (High Range)",
            "Balanced Baseline Tier (Standard)",
            "Moderate Deficit Tier (Sub-Optimal)",
            "Critical Deficit Tier (Low Range)"
        ]
        segment_strategy = {
            tier_names[0]: {
                "work_action": "Nutrient & Yield Stabilization",
                "playbook": f"Benchmark soil conditions in this tier to sustain peak {monetary_title} concentration and maintain balanced replenishment cycles."
            },
            tier_names[1]: {
                "work_action": "Routine Crop Monitoring",
                "playbook": f"Maintain standard fertilization and irrigation schedules to prevent {monetary_title} levels from depleting during active growth cycles."
            },
            tier_names[2]: {
                "work_action": "Targeted Soil Amendment",
                "playbook": f"Implement targeted nutrient enrichment and calibrate soil pH to elevate {monetary_title} to the recommended optimal range."
            },
            tier_names[3]: {
                "work_action": "Root-Level Remediation Protocol",
                "playbook": f"Prioritize soil treatment and investigate environmental bottlenecks (drainage, acidity, or depletion) causing depressed {monetary_title}."
            }
        }
    elif domain == "healthcare":
        studio_title = "Patient Cohort & Clinical Intelligence Studio"
        studio_subtitle = f"Clinical stratification and healthcare protocol workflows based on '{monetary_title}' distribution."
        retention_label = "Stable Health Benchmark"
        
        tier_names = [
            "High Care Priority (Intensive Tier)",
            "Elevated Monitoring Tier",
            "Moderate Risk Tier",
            "Low Risk / Stable Tier"
        ]
        segment_strategy = {
            tier_names[0]: {
                "work_action": "Specialized Clinical Protocol",
                "playbook": f"Schedule priority diagnostic evaluations and assign specialized clinical care management for this high-{monetary_title} cohort."
            },
            tier_names[1]: {
                "work_action": "Preventative Screening Protocol",
                "playbook": f"Perform regular biometric evaluations and vital sign monitoring to catch early warning signs before condition progression."
            },
            tier_names[2]: {
                "work_action": "Outpatient Care Pathways",
                "playbook": "Deliver structured recovery plans, dietary guidance, and routine outpatient check-ins."
            },
            tier_names[3]: {
                "work_action": "Routine Wellness Maintenance",
                "playbook": "Maintain scheduled annual checkups and preventative wellness education."
            }
        }
    elif domain in ["customer", "saas"]:
        studio_title = f"{entity_label} Intelligence & Lifecycle Studio"
        studio_subtitle = "Deterministic RFM (Recency, Frequency, Value) behavioral clustering and attrition risk attribution."
        retention_label = "Health Retention"
        
        tier_names = [
            "Champions",
            "Loyal Advocates",
            "At-Risk Accounts",
            "Hibernating"
        ]
        segment_strategy = {
            tier_names[0]: {
                "work_action": "VIP Loyalty & Upsell Acceleration",
                "playbook": "Reward high engagement with executive account reviews, dedicated priority SLAs, and early access to premium offerings."
            },
            tier_names[1]: {
                "work_action": "Cross-Sell Expansion & Value Protection",
                "playbook": "Deliver bundle promotions and volume tier incentives to expand basket size and nurture repeat engagement."
            },
            tier_names[2]: {
                "work_action": "Proactive Win-Back & Retention",
                "playbook": "Deploy immediate account outreach. Audit recent delivery delays or service tickets to resolve bottlenecks before defection."
            },
            tier_names[3]: {
                "work_action": "Reactivation & Automated Discovery",
                "playbook": "Launch targeted win-back campaigns with special incentives and feedback surveys to uncover root reasons for inactivity."
            }
        }
    else:  # Generic fallback
        studio_title = "Cohort Performance & Distribution Studio"
        studio_subtitle = f"Multi-tier clustering and distribution analysis for '{monetary_title}' across dataset segments."
        retention_label = "Upper-Tier Performance Share"
        
        tier_names = [
            "Tier 1 (High Performance / Top Quartile)",
            "Tier 2 (Above Average / Upper Mid)",
            "Tier 3 (Moderate / Lower Mid)",
            "Tier 4 (Low / Opportunity Quartile)"
        ]
        segment_strategy = {
            tier_names[0]: {
                "work_action": "Scale Best Practices & Benchmark",
                "playbook": f"Analyze operational factors enabling high {monetary_title} in this cohort and standardize these practices across other segments."
            },
            tier_names[1]: {
                "work_action": "Performance Stabilization",
                "playbook": f"Ensure input resources and operational workflows remain consistent to support steady {monetary_title} generation."
            },
            tier_names[2]: {
                "work_action": "Targeted Operational Improvement",
                "playbook": f"Address specific friction points and operational variance to elevate moderate performers toward upper-tier {monetary_title} levels."
            },
            tier_names[3]: {
                "work_action": "Root Cause Audit & Remediation",
                "playbook": f"Conduct detailed diagnostics on lagging observations to uncover root bottlenecks and execute corrective action plans."
            }
        }

    # Assign Segment Labels by quartile rank
    m_quantiles = pd.qcut(rfm["monetary"].rank(method="first"), q=4, labels=False)
    rfm["segment"] = [
        tier_names[0] if q == 3 else (
            tier_names[1] if q == 2 else (
                tier_names[2] if q == 1 else tier_names[3]
            )
        )
        for q in m_quantiles
    ]

    # Aggregate Segment Profiles
    segments = []
    for seg_name in tier_names:
        sub = rfm[rfm["segment"] == seg_name]
        cnt = len(sub)
        pct = round((cnt / max(total_customers, 1)) * 100, 1)
        strategy = segment_strategy.get(seg_name, {
            "work_action": "Standard Engagement",
            "playbook": "Maintain consistent operations and track cohort metrics."
        })
        segments.append({
            "segment": seg_name,
            "customer_count": cnt,
            "percentage": pct,
            "avg_recency_days": round(float(sub["recency"].mean()), 1) if cnt > 0 else 0,
            "avg_monetary": round(float(sub["monetary"].mean()), 2) if cnt > 0 else 0,
            "work_action": strategy["work_action"],
            "playbook": strategy["playbook"]
        })

    # Top Entities preview
    top_entities = []
    for _, row in rfm.sort_values("monetary", ascending=False).head(8).iterrows():
        top_entities.append({
            "entity_name": str(row[cust_col]),
            "segment": str(row["segment"]),
            "frequency": int(row["frequency"]),
            "total_value": round(float(row["monetary"]), 2),
            "recency_days": round(float(row["recency"]), 1)
        })

    upper_cohort = len(rfm[rfm["segment"].isin([tier_names[0], tier_names[1]])])
    retention_rate = round((upper_cohort / max(total_customers, 1)) * 100, 1)

    return {
        "supported": True,
        "domain": domain,
        "studio_title": studio_title,
        "studio_subtitle": studio_subtitle,
        "entity_label": entity_label,
        "total_customers": total_customers,
        "retention_rate": retention_rate,
        "retention_label": retention_label,
        "monetary_column": monetary_title,
        "has_dates": has_dates,
        "segments": segments,
        "top_entities": top_entities
    }
