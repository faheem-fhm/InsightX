import os

# 1. Patch database/session.py
session_path = r"C:\Users\HP\.gemini\antigravity\scratch\InsightX\backend\app\database\session.py"
session_code = """import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from ..core.config import settings

class Base(DeclarativeBase):
    pass

db_url = settings.DATABASE_URL
if db_url == "sqlite:///./insightx.db":
    abs_db_path = os.path.join(settings.BASE_DIR, "insightx.db").replace("\\\\", "/")
    db_url = f"sqlite:///{abs_db_path}"

connect_args = {}
if db_url.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(
    db_url,
    connect_args=connect_args,
    echo=False
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
"""
with open(session_path, "w", encoding="utf-8") as f:
    f.write(session_code)

# 2. Patch analytics/olap_engine.py
olap_path = r"C:\Users\HP\.gemini\antigravity\scratch\InsightX\backend\app\analytics\olap_engine.py"
olap_code = """import os
from typing import Dict, Any, List, Optional
import duckdb
import pandas as pd
from ..core.exceptions import UnsafeSQLError

class DuckDBEngine:
    def __init__(self):
        self.conn = duckdb.connect(database=":memory:")
        
    def register_parquet(self, table_name: str, file_path: str):
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Data file not found: {file_path}")
        clean_path = file_path.replace("\\\\", "/")
        if clean_path.endswith(".csv"):
            self.conn.execute(f"CREATE OR REPLACE VIEW {table_name} AS SELECT * FROM read_csv_auto('{clean_path}')")
        else:
            self.conn.execute(f"CREATE OR REPLACE VIEW {table_name} AS SELECT * FROM read_parquet('{clean_path}')")
        
    def query(self, sql: str, limit: int = 1000) -> pd.DataFrame:
        clean_sql = sql.strip().rstrip(";")
        if "limit" not in clean_sql.lower():
            clean_sql = f"{clean_sql} LIMIT {limit}"
        return self.conn.execute(clean_sql).fetchdf()

olap_engine = DuckDBEngine()
"""
with open(olap_path, "w", encoding="utf-8") as f:
    f.write(olap_code)

# 3. Patch ai/data_analyst.py date SQL parsing
analyst_path = r"C:\Users\HP\.gemini\antigravity\scratch\InsightX\backend\app\ai\data_analyst.py"
with open(analyst_path, "r", encoding="utf-8") as f:
    analyst_code = f.read()

analyst_code = analyst_code.replace(
    "sql = f\"SELECT strftime({d_col}, '%Y-%m-%d') AS date, SUM({target_num}) AS value FROM {table_name} GROUP BY 1 ORDER BY 1 LIMIT 60\"",
    "sql = f\"SELECT SUBSTR(CAST({d_col} AS VARCHAR), 1, 10) AS date, SUM({target_num}) AS value FROM {table_name} GROUP BY 1 ORDER BY 1 LIMIT 60\""
)

with open(analyst_path, "w", encoding="utf-8") as f:
    f.write(analyst_code)

print("Backend session, OLAP engine, and AI Analyst date SQL patched.")
