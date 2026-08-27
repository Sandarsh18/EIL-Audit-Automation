import pandas as pd
import datetime
from typing import Any, Tuple
from dateutil import parser

def is_blank(val: Any) -> bool:
    if pd.isna(val) or val is None:
        return True
    if isinstance(val, str) and val.strip() == "":
        return True
    return False

def parse_normalized_date(val: Any) -> Tuple[bool, bool, datetime.date | None]:
    """
    Returns (is_blank, is_invalid, parsed_date).
    Robustly parses Excel serial dates, JS Date objects, ISO strings,
    DD/MM/YYYY, YYYY-MM-DD, etc., into a canonical datetime.date object.
    """
    if is_blank(val):
        return True, False, None
        
    if isinstance(val, datetime.datetime):
        return False, False, val.date()
    if isinstance(val, datetime.date):
        return False, False, val

    s_val = str(val).strip()
    if s_val.lower() in ["bad_date", "na", "n/a", "pending", "unknown", "invalid"]:
        return False, True, None
        
    try:
        # If the string contains a slash, assume it might be DD/MM/YYYY
        use_dayfirst = "/" in s_val or "-" in s_val and len(s_val.split("-")[0]) != 4
        dt = pd.to_datetime(val, dayfirst=use_dayfirst)
        if pd.isna(dt):
            return False, True, None
        return False, False, dt.date()
    except (ValueError, TypeError, parser.ParserError):
        # Additional fallback or regex could go here if needed
        return False, True, None
