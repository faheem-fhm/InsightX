import os
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
        clean_path = file_path.replace("\\", "/")
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
