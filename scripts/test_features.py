import sys
import os

sys.path.insert(0, os.path.abspath(r"C:\Users\HP\.gemini\antigravity\scratch\InsightX\backend"))

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

print("=== TESTING 6 CHARTS, INTERACTIVE FILTERS, AND FREE LLM AI ANALYST ===")

# 1. Load Sample Dataset
r_sample = client.post('/api/v1/datasets/sample', json={'sample_key': 'ecommerce'})
assert r_sample.status_code == 200
did = r_sample.json()['dataset_id']
print(f"[+] Loaded Sample Dataset ID: {did}")

# 2. Test 6 Automatic Charts
r_dash = client.get(f'/api/v1/datasets/{did}/dashboard')
assert r_dash.status_code == 200
data = r_dash.json()
print(f"[+] Dashboard Initial Load: {len(data['charts'])} Charts Generated")
for i, c in enumerate(data['charts'], 1):
    print(f"    Chart {i}: {c['title']} ({c['chart_type']})")
assert len(data['charts']) == 6

# 3. Test Interactive Filtered Dashboard
import json
filters_json = json.dumps({"region": "South"})
r_filtered = client.get(f'/api/v1/datasets/{did}/dashboard', params={"filters": filters_json})
assert r_filtered.status_code == 200
f_data = r_filtered.json()
print(f"[+] Filtered Dashboard (Region=South): {f_data['row_count']} filtered rows out of {data['row_count']}")
print(f"    Applied Filters: {f_data['applied_filters']}")
assert f_data['row_count'] < data['row_count']
assert len(f_data['charts']) == 6

# 4. Test AI Analyst Queries (Why, How, What)
for q in ["Why did revenue decrease?", "How did products perform?", "What is the top category?"]:
    r_ai = client.post(f'/api/v1/datasets/{did}/ai/ask', json={'question': q})
    assert r_ai.status_code == 200
    res = r_ai.json()
    print(f"[+] Query: '{q}'")
    print(f"    Finding: {res['finding']}")
    print(f"    SQL: {res['sql_query']}")
    print(f"    Explanation: {res['explanation']}")

print("\nALL FEATURE ENHANCEMENT TESTS PASSED WITH 100% SUCCESS!")
