import os

services_dir = r"C:\Users\HP\.gemini\antigravity\scratch\InsightX\backend\app\services"
api_dir = r"C:\Users\HP\.gemini\antigravity\scratch\InsightX\backend\app\api\v1"

# 1. Update file_validator.py with smart_read_csv
file_validator_code = """import os
from typing import Dict, Any, List, Optional
import pandas as pd

ALLOWED_EXTENSIONS = {"csv", "xlsx", "xls", "json", "parquet"}

class FileValidationResult:
    def __init__(self, is_valid: bool, file_format: str, error_message: Optional[str] = None, sheet_names: Optional[List[str]] = None, df_preview: Optional[pd.DataFrame] = None):
        self.is_valid = is_valid
        self.file_format = file_format
        self.error_message = error_message
        self.sheet_names = sheet_names or []
        self.df_preview = df_preview

def smart_read_csv(file_path: str, nrows: Optional[int] = None) -> pd.DataFrame:
    \"\"\"
    Reads CSV files handling UTF-8, Latin-1, CP1252 encodings,
    and automatic separator detection (comma, semicolon, tab).
    \"\"\"
    encodings = ["utf-8", "utf-8-sig", "latin-1", "cp1252", "iso-8859-1"]
    for enc in encodings:
        try:
            kwargs = {"encoding": enc, "on_bad_lines": "skip"}
            if nrows:
                kwargs["nrows"] = nrows
            df = pd.read_csv(file_path, **kwargs)
            if len(df.columns) == 1 and ";" in str(df.columns[0]):
                kwargs["sep"] = ";"
                df = pd.read_csv(file_path, **kwargs)
            elif len(df.columns) == 1 and "\\t" in str(df.columns[0]):
                kwargs["sep"] = "\\t"
                df = pd.read_csv(file_path, **kwargs)
            return df
        except Exception:
            continue
    return pd.read_csv(file_path, encoding="latin-1", on_bad_lines="skip", nrows=nrows)

def validate_and_inspect_file(file_path: str, max_size_mb: int = 50) -> FileValidationResult:
    if not os.path.exists(file_path):
        return FileValidationResult(False, "", f"File does not exist at path: {file_path}")
    
    file_size = os.path.getsize(file_path)
    if file_size > max_size_mb * 1024 * 1024:
        return FileValidationResult(False, "", f"File size ({file_size / (1024*1024):.1f}MB) exceeds limit of {max_size_mb}MB")
    
    ext = file_path.split(".")[-1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        return FileValidationResult(False, ext, f"Unsupported format '.{ext}'. Supported: {', '.join(ALLOWED_EXTENSIONS)}")
    
    sheet_names = []
    df_preview = None
    try:
        if ext == "csv":
            df_preview = smart_read_csv(file_path, nrows=5)
        elif ext in ("xlsx", "xls"):
            excel_file = pd.ExcelFile(file_path)
            sheet_names = excel_file.sheet_names
            df_preview = pd.read_excel(file_path, sheet_name=sheet_names[0], nrows=5)
        elif ext == "json":
            df_preview = pd.read_json(file_path, nrows=5)
        elif ext == "parquet":
            df_preview = pd.read_parquet(file_path)
            df_preview = df_preview.head(5)
            
        return FileValidationResult(True, ext, sheet_names=sheet_names, df_preview=df_preview)
    except Exception as e:
        return FileValidationResult(False, ext, f"Error parsing {ext.upper()} content: {str(e)}")
"""

with open(os.path.join(services_dir, "file_validator.py"), "w", encoding="utf-8") as f:
    f.write(file_validator_code)

print("Updated file_validator.py with smart_read_csv.")
