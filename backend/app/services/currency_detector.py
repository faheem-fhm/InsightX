from typing import Optional
import os
import pandas as pd

def dataset_has_dollar_symbol(df: Optional[pd.DataFrame] = None, raw_storage_path: Optional[str] = None) -> bool:
    """
    Determines whether a dataset explicitly contains the dollar symbol ($) in its column definitions.
    Returns True ONLY IF a column header contains '$' (e.g. 'Sales ($)', 'Price ($)', 'Cost ($)').
    Returns False if the dataset only contains raw numeric metrics without '$' in column names.
    Avoids false positives from text description strings containing currency mentions.
    """
    if df is not None and not df.empty:
        # Check column headers for explicit dollar symbol
        for col in df.columns:
            if "$" in str(col):
                return True

    # Check raw storage file header line
    if raw_storage_path and os.path.exists(raw_storage_path):
        try:
            with open(raw_storage_path, "r", encoding="utf-8", errors="ignore") as f:
                header = f.readline()
                if "$" in header:
                    return True
        except Exception:
            pass

    return False
