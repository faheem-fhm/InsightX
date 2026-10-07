import os

router_path = r"C:\Users\HP\.gemini\antigravity\scratch\InsightX\backend\app\api\v1\router.py"
with open(router_path, "r", encoding="utf-8") as f:
    content = f.read()

# Fix return in upload_dataset and load_sample_dataset
content = content.replace(
    '    return {\n        "dataset_id": dataset_id,\n        "name": dataset.name,',
    '    return {\n        "id": dataset_id,\n        "dataset_id": dataset_id,\n        "name": dataset.name,'
)

# Add endpoint for sample file download if not already added
if "download_sample_file" not in content:
    download_endpoint = """

from fastapi.responses import FileResponse

@router.get("/datasets/sample/download/{filename}")
def download_sample_file(filename: str):
    allowed_files = [
        "ecommerce_sales_with_hidden_root_cause.csv",
        "ecommerce_sales_with_hidden_root_cause.xlsx",
        "saas_marketing_funnel.csv",
        "saas_marketing_funnel.xlsx",
        "healthcare_patient_flow.csv",
        "healthcare_patient_flow.xlsx"
    ]
    if filename not in allowed_files:
        raise HTTPException(status_code=404, detail="File not found in sample vault.")
    file_path = os.path.join(settings.SAMPLES_DIR, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File does not exist on disk.")
    return FileResponse(path=file_path, filename=filename, media_type="application/octet-stream")
"""
    content += download_endpoint

with open(router_path, "w", encoding="utf-8") as f:
    f.write(content)

print("Updated backend router.py successfully.")
