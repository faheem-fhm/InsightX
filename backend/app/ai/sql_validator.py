import re
import sqlparse
from sqlparse.sql import Statement, Token
from sqlparse.tokens import DML, DDL, Keyword
from ..core.exceptions import UnsafeSQLError

FORBIDDEN_KEYWORDS = {
    "DROP", "DELETE", "UPDATE", "INSERT", "ALTER", "TRUNCATE", 
    "CREATE", "GRANT", "REVOKE", "EXEC", "EXECUTE", "SHUTDOWN", 
    "MERGE", "REPLACE", "CALL", "RENAME"
}

def validate_safe_sql(query: str) -> str:
    """
    Performs rigorous AST-level security validation.
    Permits ONLY read operations (SELECT, CTEs).
    Blocks SQL injections, multiple statements, and destructive DDL/DML.
    """
    if not query or not query.strip():
        raise UnsafeSQLError("Query string is empty.")
        
    cleaned = query.strip().rstrip(";")
    
    # 1. Check for multiple statements (semicolon injection)
    statements = sqlparse.parse(cleaned)
    if len(statements) > 1:
        raise UnsafeSQLError("Multiple SQL statements detected in a single query.")
        
    stmt = statements[0]
    first_token = stmt.token_first(skip_ws=True, skip_cm=True)
    if not first_token:
        raise UnsafeSQLError("Unable to parse SQL query token stream.")
        
    first_kw = first_token.value.upper()
    if first_kw not in ("SELECT", "WITH"):
        raise UnsafeSQLError(f"Prohibited initial statement keyword '{first_kw}'. Only SELECT or WITH (CTEs) allowed.")
        
    # 2. Token-by-token AST inspection
    for token in stmt.flatten():
        val = token.value.upper()
        if val in FORBIDDEN_KEYWORDS:
            raise UnsafeSQLError(f"Destructive or mutating SQL keyword detected: '{val}'.")
            
    # 3. Regex guardrails for common injection tricks
    lowered = cleaned.lower()
    suspicious_patterns = [
        r";\s*drop", r";\s*delete", r";\s*update", r"into\s+outfile", 
        r"into\s+dumpfile", r"load_file\(", r"pg_sleep", r"waitfor\s+delay"
    ]
    for pattern in suspicious_patterns:
        if re.search(pattern, lowered):
            raise UnsafeSQLError("Query contains suspicious injection pattern.")
            
    return cleaned
