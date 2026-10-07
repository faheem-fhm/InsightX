from typing import Dict, Any, List, Optional
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import r2_score, accuracy_score, mean_squared_error

def detect_best_target_column(df: pd.DataFrame, schema_info: List[Dict[str, Any]]) -> Optional[str]:
    """
    Intelligently discovers the best target column from a dataset if none is set.
    Looks for:
    1. Columns with names matching standard target/KPI keywords (revenue, profit, sales, churn, cost, price, target)
    2. Continuous numeric metrics with good variance (not IDs or indexes)
    3. Low-cardinality outcome flags (binary outcomes)
    """
    cols_lower = {str(c).lower(): c for c in df.columns}
    
    # Priority keywords
    priority_keywords = [
        "revenue", "profit", "sales", "mrr_generated", "spend", "cost", 
        "treatment_cost", "churn", "order_cancelled", "cancelled", "readmission_30d",
        "conversion", "converted", "roi", "cpa", "target", "score", "price", "amount",
        "output", "label", "outcome", "status", "crop", "disease", "heartdisease", "diagnosis", "class", "category"
    ]
    for kw in priority_keywords:
        for c_lower, c_orig in cols_lower.items():
            if kw == c_lower or (kw in c_lower and not any(id_k in c_lower for id_k in ["id", "uuid", "code"])):
                return c_orig
                
    # Fallback to schema_info flagged target candidates
    for c in schema_info:
        if c.get("is_target_candidate") and not any(id_k in str(c.get("safe_column_name")).lower() for id_k in ["id", "uuid"]):
            return c.get("safe_column_name")
            
    # Fallback to first numeric column with variance > 0
    num_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    num_cols = [c for c in num_cols if not any(id_k in str(c).lower() for id_k in ["id", "uuid", "code", "index", "unnamed"])]
    for c in num_cols:
        if df[c].nunique() > 5:
            return c
            
    return num_cols[0] if num_cols else None


def train_target_ml_explainability(
    df: pd.DataFrame, 
    target_column: str,
    domain_type: str = "generic"
) -> Dict[str, Any]:
    """
    Trains an ML model (RandomForest Regressor or Classifier) on the target column.
    Extracts:
    1. Feature importances (What drives this target)
    2. Direction of influence (Why does it increase or decrease?)
    3. Actionable levers (How to prevent decrease or increase target)
    4. Model performance score (R2 or Accuracy)
    """
    if target_column not in df.columns:
        return {"supported": False, "reason": f"Target column '{target_column}' not found in dataset."}
        
    clean_df = df.dropna(subset=[target_column]).copy()
    if len(clean_df) < 10:
        return {"supported": False, "reason": "Insufficient rows to train ML explainability model."}
        
    y_series = clean_df[target_column]
    is_numeric = pd.api.types.is_numeric_dtype(y_series)
    is_classification = (
        not is_numeric
        or pd.api.types.is_bool_dtype(y_series) 
        or (is_numeric and y_series.nunique() <= 10)
    )
    
    # Feature candidate selection
    numeric_cols = clean_df.select_dtypes(include=[np.number]).columns.tolist()
    if target_column in numeric_cols:
        numeric_cols.remove(target_column)
        
    features = [c for c in numeric_cols if not any(id_k in str(c).lower() for id_k in ["id", "uuid", "code", "index", "unnamed"])]
    
    if len(features) == 0:
        return {"supported": False, "reason": "No numeric feature columns available to model target."}
        
    # Impute medians
    X = clean_df[features].fillna(clean_df[features].median())
    
    if is_classification:
        y = pd.Categorical(y_series).codes
        if len(np.unique(y)) < 2:
            return {"supported": False, "reason": "Target has only one unique class."}
            
        model = RandomForestClassifier(n_estimators=50, max_depth=6, random_state=42)
        model.fit(X, y)
        preds = model.predict(X)
        score = round(float(accuracy_score(y, preds)), 3)
        score_name = "Accuracy"
        task_type = "Classification"
    else:
        y = pd.to_numeric(y_series, errors="coerce").fillna(0.0)
        model = RandomForestRegressor(n_estimators=50, max_depth=6, random_state=42)
        model.fit(X, y)
        preds = model.predict(X)
        score = round(float(max(0.0, r2_score(y, preds))), 3)
        score_name = "R² Fit Score"
        task_type = "Regression"
        
    importances = model.feature_importances_
    
    # Analyze correlations with target to determine Why/How (increase vs decrease direction)
    drivers = []
    for feat, imp in sorted(zip(features, importances), key=lambda x: x[1], reverse=True):
        if imp < 0.01:
            continue
        try:
            corr = float(X[feat].corr(pd.Series(y, index=X.index)))
        except Exception:
            corr = 0.0
            
        direction = "Positive (Higher values increase target)" if corr > 0.05 else ("Negative (Higher values decrease target)" if corr < -0.05 else "Non-linear Complex Influence")
        
        # Actionable recommendation based on direction
        feat_label = feat.replace('_', ' ').title()
        target_label = target_column.replace('_', ' ').title()
        
        if corr > 0.05:
            how_to_optimize = f"Scale up or incentivize '{feat_label}'. Each increase directly correlates with growth in {target_label}."
            how_to_prevent = f"Guard against sudden drops in '{feat_label}', which historically drag down {target_label}."
        elif corr < -0.05:
            how_to_optimize = f"Streamline and minimize '{feat_label}'. Reducing friction/delays here elevates {target_label}."
            how_to_prevent = f"Set threshold alert limits on '{feat_label}'. Elevated levels are a leading cause of decrease in {target_label}."
        else:
            how_to_optimize = f"Keep '{feat_label}' stabilized within optimal operational bounds."
            how_to_prevent = f"Audit segment outliers in '{feat_label}' to prevent variance."
            
        drivers.append({
            "feature": feat,
            "feature_label": feat_label,
            "importance": round(float(imp), 4),
            "percentage": round(float(imp) * 100, 1),
            "correlation": round(corr, 2),
            "direction": direction,
            "why_explanation": f"'{feat_label}' accounts for {round(float(imp)*100, 1)}% of predictive variance in {target_label}. Relationship is {direction.lower()}.",
            "how_to_increase": how_to_optimize,
            "how_to_prevent": how_to_prevent,
            "impact": "High" if imp > 0.2 else ("Medium" if imp > 0.08 else "Moderate")
        })
        
    top_3_drivers = drivers[:3]
    top_driver_names = ", ".join([d["feature_label"] for d in top_3_drivers])
    
    synthesis = {
        "what_drives_target": f"The primary operational drivers of '{target_column.replace('_', ' ').title()}' are {top_driver_names}.",
        "why_shifts_happen": f"Variance occurs primarily when {top_3_drivers[0]['feature_label'] if top_3_drivers else 'features'} fluctuates ({top_3_drivers[0]['direction'] if top_3_drivers else 'unknown'}).",
        "how_to_increase": [d["how_to_increase"] for d in top_3_drivers],
        "how_to_prevent_decrease": [d["how_to_prevent"] for d in top_3_drivers]
    }
    
    return {
        "supported": True,
        "target_column": target_column,
        "task_type": task_type,
        "model_used": "RandomForest (Tree Ensembles)",
        "score_name": score_name,
        "score_value": score,
        "drivers": drivers,
        "synthesis": synthesis
    }
