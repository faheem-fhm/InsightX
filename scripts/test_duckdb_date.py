import duckdb
con = duckdb.connect()
try:
    con.execute("SELECT strftime('2024-01-01', '%Y-%m-%d')").fetchall()
    print("SUCCESS VARCHAR")
except Exception as e:
    print("FAILED VARCHAR:", e)

try:
    con.execute("SELECT strftime(TRY_CAST('2024-01-01' AS DATE), '%Y-%m-%d')").fetchall()
    print("SUCCESS TRY_CAST")
except Exception as e:
    print("FAILED TRY_CAST:", e)
