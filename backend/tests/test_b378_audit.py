import pytest
import datetime
from app.services.matching_service import normalize_job_number
from app.schemas.inspection_rules import InspectionJobResult
from app.services.inspection_rules_service import parse_date
import pandas as pd

def test_normalize_job_number_strict_matching():
    # Base cases
    assert normalize_job_number("B378") == "B378"
    assert normalize_job_number("  B378  ") == "B378"
    
    # Must NOT broaden match
    assert normalize_job_number("B3781") == "B3781"
    assert normalize_job_number("B378-01") == "B378-01"
    assert normalize_job_number("B378/01") == "B378/01"
    assert normalize_job_number("B378 - 01") == "B378-01"
    
    # Matching check
    target = "B378"
    assert normalize_job_number("B3781") != target
    assert normalize_job_number("B378-01") != target

def test_parse_date_semantics():
    # Valid date
    blank, inv, dt = parse_date("2024-02-08")
    assert not blank and not inv and dt == datetime.date(2024, 2, 8)
    
    # Blank date
    blank, inv, dt = parse_date(None)
    assert blank and not inv and dt is None
    
    # Invalid date strings explicitly blocked
    blank, inv, dt = parse_date("NA")
    assert not blank and inv and dt is None
    
    blank, inv, dt = parse_date("pending")
    assert not blank and inv and dt is None

def test_excel2_date_duration_calculation_b378_logic():
    # From InspectionRulesService delta calculation logic
    from app.services.inspection_rules_service import parse_date
    
    def calc_days(f, u):
        fb, fi, fd = parse_date(f)
        ub, ui, ud = parse_date(u)
        if fb or ub or fi or ui:
            return -1
        if fd > ud:
            return -2
        return (ud - fd).days + 1
        
    # Same-day dates
    assert calc_days("2024-02-08", "2024-02-08") == 1
    
    # 2 days duration
    assert calc_days("2024-02-08", "2024-02-09") == 2
    
    # Multi-month duration
    assert calc_days("2024-02-28", "2024-03-01") == 3
    
    # Invalid inversion
    assert calc_days("2024-02-08", "2024-02-07") == -2
    
    # Missing From or Upto
    assert calc_days(None, "2024-08-05") == -1
    assert calc_days("2024-08-05", None) == -1
    
    # Excel datetime objects
    dt1 = datetime.datetime(2024, 2, 8)
    dt2 = datetime.datetime(2024, 2, 9)
    assert calc_days(dt1, dt2) == 2

def test_header_detection_mechanism():
    from app.services.excel_service import ExcelService
    
    # Create a synthetic dataframe with garbage in rows 0 and 1, and canonical headers in row 2
    df = pd.DataFrame([
        ["Random Title", "Random Value", None, None],
        ["Subtitle", None, None, None],
        ["Job No", "Exp.", "Inspn", "Others"],
        ["B378", 5, 10, 2],
    ])
    
    df.to_excel("test_header_temp.xlsx", header=False, index=False)
    
    # Test detection
    header_idx = ExcelService.detect_header_row("test_header_temp.xlsx", "Sheet1")
    assert header_idx == 2
    
    import os
    os.remove("test_header_temp.xlsx")
