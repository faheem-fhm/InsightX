import sys
import os
import pandas as pd

sys.path.insert(0, os.path.abspath(r"C:\Users\HP\.gemini\antigravity\scratch\InsightX\backend"))
from app.root_cause.investigator import run_root_cause_investigation

df = pd.read_csv(r"C:\Users\HP\.gemini\antigravity\scratch\InsightX\data\samples\ecommerce_sales_with_hidden_root_cause.csv")
res = run_root_cause_investigation(
    df=df,
    target_metric="revenue",
    date_col="order_date",
    crisis_start_date="2024-04-01",
    crisis_end_date="2024-05-20"
)

print("=== ROOT CAUSE ENGINE DISCOVERY AUDIT ===")
print("Target Metric:", res["target_metric"])
print("Change Percentage:", res["change_percentage"], "%", res["direction"])
print("Narrative Finding:", res["narrative_finding"])
print("Top Driver Explanation:", res["driver_explanation"])
print("\nSimultaneous Metric Shifts Discovered:")
for s in res["simultaneous_shifts"]:
    print(f"  * {s['metric_title']}: {s['direction']} by {s['pct_change']}% (P1: {s['p1_mean']} -> P2: {s['p2_mean']})")

print("\nDimensional Breakdown (Top Region Shifts):")
for b in res["dimensional_breakdowns"]:
    if b["dimension"] == "region":
        for it in b["items"]:
            print(f"  - Region {it['name']}: Delta ${it['delta']}, % Change: {it['pct_change']}%, Contribution: {it['contribution_percentage']}%")

print("\nActionable Recommendations:")
for r in res["recommendations"]:
    print(f"  [>] {r['action']}: {r['detail']}")
