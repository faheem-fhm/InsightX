import sys
import os

sys.path.insert(0, os.path.abspath(r"C:\Users\HP\.gemini\antigravity\scratch\InsightX\backend"))
from app.ai.sql_validator import validate_safe_sql
from app.core.exceptions import UnsafeSQLError

print("=== RUNNING AST SQL VALIDATOR SECURITY AUDIT ===")

# 1. Safe query test
safe = "SELECT region, sum(revenue) FROM orders GROUP BY region ORDER BY 2 DESC LIMIT 10"
print("[+] Test 1 (Safe SELECT):", validate_safe_sql(safe))

# 2. Blocked DROP TABLE test
try:
    validate_safe_sql("DROP TABLE orders;")
    print("[-] ERROR: DROP TABLE was not blocked!")
except UnsafeSQLError as e:
    print("[+] Test 2 (Blocked DROP): PASSED ->", e.detail)

# 3. Blocked semicolon injection test
try:
    validate_safe_sql("SELECT * FROM orders; DELETE FROM users;")
    print("[-] ERROR: Semicolon injection was not blocked!")
except UnsafeSQLError as e:
    print("[+] Test 3 (Blocked Injection): PASSED ->", e.detail)

# 4. Blocked UPDATE test
try:
    validate_safe_sql("UPDATE users SET role='admin'")
    print("[-] ERROR: UPDATE was not blocked!")
except UnsafeSQLError as e:
    print("[+] Test 4 (Blocked UPDATE): PASSED ->", e.detail)
