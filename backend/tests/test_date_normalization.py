import pytest
import datetime
from app.utils.date_parser import parse_normalized_date
from app.services.excel1_rules_service import is_within_six_months, get_window_dates

def test_date_parsing_formats():
    cases = [
        ("25/08/2025", datetime.date(2025, 8, 25)),
        ("01/03/2026", datetime.date(2026, 3, 1)),
        ("2026-08-29", datetime.date(2026, 8, 29)),
        ("2026-08-29T00:00:00", datetime.date(2026, 8, 29)),
        (datetime.datetime(2025, 8, 25, 12, 0), datetime.date(2025, 8, 25))
    ]
    
    for val, expected in cases:
        b_blank, b_inv, parsed = parse_normalized_date(val)
        assert not b_blank
        assert not b_inv
        assert parsed == expected

def test_six_month_window():
    eval_month = "2026-08" # August 2026
    start, end = get_window_dates(eval_month)
    
    assert start == datetime.date(2026, 3, 1)
    assert end == datetime.date(2026, 8, 31)
    
    # 01/03/2026 -> included
    assert is_within_six_months(datetime.date(2026, 3, 1), eval_month)
    
    # 31/08/2026 -> included
    assert is_within_six_months(datetime.date(2026, 8, 31), eval_month)
    
    # 28/02/2026 -> excluded
    assert not is_within_six_months(datetime.date(2026, 2, 28), eval_month)
    
    # 31/01/2026 -> excluded
    assert not is_within_six_months(datetime.date(2026, 1, 31), eval_month)
    
    # 25/08/2025 -> excluded
    assert not is_within_six_months(datetime.date(2025, 8, 25), eval_month)
