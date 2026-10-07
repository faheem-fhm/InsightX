import os

router_path = r"C:\Users\HP\.gemini\antigravity\scratch\InsightX\backend\app\api\v1\router.py"
with open(router_path, "r", encoding="utf-8") as f:
    content = f.read()

# Make sure smart_read_csv is imported
if "smart_read_csv" not in content:
    content = content.replace(
        "from ...services.file_validator import validate_and_inspect_file",
        "from ...services.file_validator import validate_and_inspect_file, smart_read_csv"
    )
    content = content.replace("df_raw = pd.read_csv(raw_path)", "df_raw = smart_read_csv(raw_path)")
    content = content.replace("df_raw = pd.read_csv(dataset.raw_storage_path)", "df_raw = smart_read_csv(dataset.raw_storage_path)")
    content = content.replace("return pd.read_csv(dataset.raw_storage_path)", "return smart_read_csv(dataset.raw_storage_path)")

with open(router_path, "w", encoding="utf-8") as f:
    f.write(content)

print("Updated backend router.py with smart_read_csv.")
