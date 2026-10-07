import duckdb

con = duckdb.connect()
path_with_backslash = r"C:\Users\HP\test.parquet"
try:
    con.execute(f"SELECT * FROM read_parquet('{path_with_backslash}')")
except Exception as e:
    print("BACKSLASH ERROR:", e)

path_with_forward = path_with_backslash.replace("\\", "/")
try:
    con.execute(f"SELECT * FROM read_parquet('{path_with_forward}')")
except Exception as e:
    print("FORWARDSLASH (expected file not found, not parse error):", e)
