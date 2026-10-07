import sys
import os
import pandas as pd

sys.path.insert(0, os.path.abspath(r"C:\Users\HP\.gemini\antigravity\scratch\InsightX\backend"))

from app.services.file_validator import validate_and_inspect_file
from app.services.data_profiler import profile_dataframe
from app.services.quality_evaluator import compute_quality_report
from app.services.preprocessor import run_preprocessing_pipeline

sample_path = r"C:\Users\HP\.gemini\antigravity\scratch\InsightX\data\samples\ecommerce_sales_with_hidden_root_cause.csv"

print(f"=== TESTING INGESTION & QUALITY PIPELINE ON {os.path.basename(sample_path)} ===")

# 1. Validation
val_res = validate_and_inspect_file(sample_path)
print(f"1. File Validation: Valid={val_res.is_valid}, Format={val_res.file_format}")

# 2. Read full dataset
df_raw = pd.read_csv(sample_path)
print(f"2. Raw Dataset Loaded: {len(df_raw)} rows, {len(df_raw.columns)} columns")

# 3. Profiling
profiles = profile_dataframe(df_raw)
print(f"3. Profiling Complete: Inferred types for {len(profiles)} columns:")
for p in profiles[:6]:
    print(f"   * {p['column_name']} -> safe: '{p['safe_column_name']}', type: {p['detected_type']}, distinct: {p['distinct_count']}, nulls: {p['missing_count']}")

# 4. Data Quality Evaluation
quality_res = compute_quality_report(df_raw, profiles)
print(f"\n4. Data Quality Score: {quality_res['quality_score']} / 100")
print(f"   * Missing cells: {quality_res['missing_cells_count']} ({quality_res['missing_cells_percentage']}%)")
print(f"   * Duplicates: {quality_res['duplicate_rows_count']}")
print(f"   * Potential Outliers: {quality_res['potential_outliers_count']}")
print(f"   * Recommended Actions: {len(quality_res['recommended_actions'])} actions proposed:")
for action in quality_res['recommended_actions']:
    print(f"     [-] {action['title']} (Impact: {action['impact']})")

# 5. Preprocessing Execution
df_clean, report = run_preprocessing_pipeline(df_raw, dataset_id="test_demo_01")
print(f"\n5. Preprocessing Pipeline Result:")
print(f"   * Original rows: {report.original_rows}")
print(f"   * Cleaned rows: {report.processed_rows}")
print(f"   * Duplicates removed: {report.duplicates_removed}")
print(f"   * Columns imputed: {list(report.imputed_columns.keys())}")
print(f"   * Saved to Parquet: {report.cleaned_parquet_path} (File exists: {os.path.exists(report.cleaned_parquet_path)})")
