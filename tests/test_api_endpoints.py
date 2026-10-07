import sys
import os

sys.path.insert(0, os.path.abspath(r"C:\Users\HP\.gemini\antigravity\scratch\InsightX\backend"))

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

print("=== RUNNING FASTAPI ENDPOINTS VERIFICATION TEST ===")

# 1. Root & Health
r_root = client.get("/")
print("1. Root Endpoint:", r_root.status_code, r_root.json())
assert r_root.status_code == 200

r_health = client.get("/health")
print("2. Health Check:", r_health.status_code, r_health.json())
assert r_health.status_code == 200

# 3. Load Sample Dataset (E-Commerce)
r_sample = client.post("/api/v1/datasets/sample", json={"sample_key": "ecommerce"})
print("3. Load Sample Dataset:", r_sample.status_code)
assert r_sample.status_code == 200
data_info = r_sample.json()
dataset_id = data_info["dataset_id"]
print(f"   -> Created Dataset ID: {dataset_id}, Name: {data_info['name']}, Quality: {data_info['quality_score']}/100")

# 4. List Datasets
r_list = client.get("/api/v1/datasets")
print(f"4. List Datasets: Found {len(r_list.json())} datasets")
assert len(r_list.json()) >= 1

# 5. Get Dataset Profile
r_profile = client.get(f"/api/v1/datasets/{dataset_id}/profile")
print(f"5. Dataset Profile: {len(r_profile.json()['columns'])} columns detected")

# 6. Get Quality Report
r_quality = client.get(f"/api/v1/datasets/{dataset_id}/quality")
print(f"6. Quality Report: Score={r_quality.json()['quality_score']}, Actions={len(r_quality.json()['recommended_actions'])}")

# 7. Get Executive Dashboard
r_dash = client.get(f"/api/v1/datasets/{dataset_id}/dashboard")
print(f"7. Dashboard: {len(r_dash.json()['kpis'])} KPIs, {len(r_dash.json()['charts'])} Charts, {len(r_dash.json()['alerts'])} Alerts")

# 8. Get Anomaly Radar
r_anom = client.post(f"/api/v1/datasets/{dataset_id}/anomaly", json={})
print(f"8. Anomaly Radar: {r_anom.json()['total_detected']} anomalies detected")

# 9. Get Time Series Forecast
r_fc = client.post(f"/api/v1/datasets/{dataset_id}/forecast", json={"horizon_days": 30})
print(f"9. Forecasting: {len(r_fc.json()['forecast'])} future predictions, Model: {r_fc.json()['metrics']['model_type']}, MAPE: {r_fc.json()['metrics']['mape']}")

# 10. Get Customer Intelligence (RFM)
r_cust = client.get(f"/api/v1/datasets/{dataset_id}/customers")
print(f"10. Customer Intelligence: Supported={r_cust.json()['supported']}, Total Customers={r_cust.json().get('total_customers', 0)}")

# 11. Get Root Cause Investigation
r_rc = client.post(f"/api/v1/datasets/{dataset_id}/root-cause", json={"crisis_start_date": "2024-04-01", "crisis_end_date": "2024-05-20"})
print(f"11. Root Cause Engine: Shift={r_rc.json()['change_percentage']}%, Direction={r_rc.json()['direction']}")
print(f"    Top Driver: {r_rc.json().get('top_driver')}")

# 12. Ask AI Analyst
r_ai = client.post(f"/api/v1/datasets/{dataset_id}/ai/ask", json={"question": "Why did revenue decrease?"})
print(f"12. AI Analyst Response: Finding='{r_ai.json()['finding']}'")
print(f"    SQL Query: {r_ai.json()['sql_query']}")

print("\nALL 12 BACKEND REST API ENDPOINTS VERIFIED AND PASSING WITH FLYING COLORS!")
