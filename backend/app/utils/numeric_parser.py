import datetime
import math
import pandas as pd

def parse_numeric(value) -> float | None:
    if value is None:
        return None
        
    if pd.isna(value):
        return None
        
    if isinstance(value, bool):
        return None
        
    if isinstance(value, (int, float)):
        if math.isnan(value):
            return None
        return float(value)
        
    if isinstance(value, datetime.datetime):
        return None
        
    if isinstance(value, datetime.date):
        return None
        
    text = str(value).strip()
    
    if not text:
        return None
        
    try:
        f_val = float(text)
        if math.isnan(f_val):
            return None
        return f_val
    except (ValueError, TypeError):
        return None

