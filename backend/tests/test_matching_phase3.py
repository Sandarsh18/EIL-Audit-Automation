import pytest
from fastapi.testclient import TestClient
from app.main import app
import pandas as pd
import os

client = TestClient(app)

@pytest.fixture(scope="module")
def setup_mapped_session():
    # 1. Create Session
    resp = client.post("/api/sessions")
    session_id = resp.json()["session_id"]
    
    # We will generate a special phase 3 fixture to test the normalization and missing logic
    df1 = pd.DataFrame({
        "Job No.": ["B269", "B269", " B378 ", "B390", None, "  "],
        "Balance Quantity": [10, 20, 30, 40, 50, 60],
        "OCS Date": ["2026-01-01", "2026-01-02", "2026-01-03", "2026-01-04", "2026-01-05", "2026-01-06"],
    })
    
    df2 = pd.DataFrame({
        "Job No.": ["B269", "B378", "TEST_MISSING_IN_1"],
        "Inspection Attended (From)": ["d1", "d2", "d3"],
        "Inspection Attended (Upto)": ["d1", "d2", "d3"],
    })
    
    # Excel 3 is required just to satisfy mapping logic
    df3 = pd.DataFrame({
        "Job No.": ["B269"], "Running Orders": [0], "OCS Done": [0], "Expediting": [0], "Inspection": [0], "Others": [0], "Total": [0],
    })
    
    os.makedirs("tests/fixtures", exist_ok=True)
    df1.to_excel("tests/fixtures/p3_excel1.xlsx", index=False)
    df2.to_excel("tests/fixtures/p3_excel2.xlsx", index=False)
    df3.to_excel("tests/fixtures/p3_excel3.xlsx", index=False)
    
    # Upload files
    with open("tests/fixtures/p3_excel1.xlsx", "rb") as f:
        client.post(f"/api/sessions/{session_id}/files/excel1", files={"file": ("p3_excel1.xlsx", f, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")})
    with open("tests/fixtures/p3_excel2.xlsx", "rb") as f:
        client.post(f"/api/sessions/{session_id}/files/excel2", files={"file": ("p3_excel2.xlsx", f, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")})
    with open("tests/fixtures/p3_excel3.xlsx", "rb") as f:
        client.post(f"/api/sessions/{session_id}/files/excel3", files={"file": ("p3_excel3.xlsx", f, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")})
        
    # Map them
    payload = {
        "excel1": {"sheet": "Sheet1", "columns": {"job_number": "Job No.", "balance_quantity": "Balance Quantity", "ocs_date": "OCS Date"}},
        "excel2": {"sheet": "Sheet1", "columns": {"job_number": "Job No.", "inspection_from": "Inspection Attended (From)", "inspection_upto": "Inspection Attended (Upto)"}},
        "excel3": {"sheet": "Sheet1", "columns": {"job_number": "Job No.", "running_orders": "Running Orders", "ocs_done": "OCS Done", "expediting": "Expediting", "inspection": "Inspection", "others": "Others", "total": "Total"}}
    }
    client.post(f"/api/sessions/{session_id}/mapping", json=payload)
    client.post(f"/api/sessions/{session_id}/evaluation-month", json={"evaluation_month": "2026-08"})
    
    yield session_id
    
    # Cleanup
    os.remove("tests/fixtures/p3_excel1.xlsx")
    os.remove("tests/fixtures/p3_excel2.xlsx")
    os.remove("tests/fixtures/p3_excel3.xlsx")

def test_extract_unique_job_numbers(setup_mapped_session):
    # Test 1, 2, 3, 4 (Extract unique, blank exclusion, whitespace norm, case norm)
    resp = client.get(f"/api/sessions/{setup_mapped_session}/job-numbers")
    assert resp.status_code == 200
    data = resp.json()
    
    assert data["total_valid_job_numbers"] == 4 # b269, b378, b390, test_missing_in_1
    assert data["blank_job_numbers"] == 2 # None and "  "
    
    opts = {o["normalized_key"]: o for o in data["options"]}
    assert "B269" in opts
    assert opts["B269"]["original_value"] == "B269" # First occurrence original value preserved
    assert opts["B269"]["excel1_count"] == 2
    assert opts["B269"]["excel2_count"] == 1 # Exists in Excel 2 as "B269"
    assert opts["B269"]["excel2_found"] is True
    assert opts["B269"]["excel3_count"] == 1
    assert opts["B269"]["excel3_found"] is True
    
    assert "B378" in opts
    assert opts["B378"]["original_value"] == " B378 " # Preserved original whitespace
    assert opts["B378"]["excel1_count"] == 1
    assert opts["B378"]["excel2_count"] == 1
    assert opts["B378"]["excel2_found"] is True
    assert opts["B378"]["excel3_count"] == 0
    assert opts["B378"]["excel3_found"] is False
    
    assert "B390" in opts
    assert opts["B390"]["excel1_count"] == 1
    assert opts["B390"]["excel2_found"] is False # Test 6: No Excel 2 Match
    assert opts["B390"]["excel3_found"] is False
    
    assert "TEST_MISSING_IN_1" in opts
    assert opts["TEST_MISSING_IN_1"]["excel1_found"] is False
    assert opts["TEST_MISSING_IN_1"]["excel2_found"] is True

def test_matched_records(setup_mapped_session):
    # Test 5, 8, 9, 10, 11 (Multiple records, all records returned, unselected omitted)
    payload = {"job_numbers": ["B269", "B390"]}
    resp = client.post(f"/api/sessions/{setup_mapped_session}/job-numbers/match", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    
    assert "B269" in data["excel1_records"]
    assert len(data["excel1_records"]["B269"]) == 2 # 2 matches in Excel 1
    
    assert "B269" in data["excel2_records"]
    assert len(data["excel2_records"]["B269"]) == 1 # 1 match in Excel 2
    
    assert "B390" in data["excel1_records"]
    assert len(data["excel1_records"]["B390"]) == 1
    assert data["excel1_records"]["B390"][0]["Job No."] == "B390" # Preserved case
    
    assert "B390" not in data["excel2_records"] # Doesn't exist
    
    assert "B378" not in data["excel1_records"] # Unselected (Test 11)

def test_missing_mapping():
    # Test 12
    resp = client.post("/api/sessions")
    session_id = resp.json()["session_id"]
    resp2 = client.get(f"/api/sessions/{session_id}/job-numbers")
    assert resp2.status_code == 400
    assert "Mapping configuration is missing" in resp2.json()["detail"]

# Performance test
def test_performance_10k_rows():
    import time
    
    resp = client.post("/api/sessions")
    session_id = resp.json()["session_id"]
    
    # Generate 10k rows
    df1 = pd.DataFrame({
        "Job No.": [f"B{i}" for i in range(10000)],
        "Balance Quantity": [1] * 10000,
        "OCS Date": ["2026-01-01"] * 10000
    })
    
    df2 = pd.DataFrame({
        "Job No.": [f"B{i}" for i in range(5000)],
        "Inspection Attended (From)": ["d1"] * 5000,
        "Inspection Attended (Upto)": ["d1"] * 5000,
    })
    
    df3 = pd.DataFrame({
        "Job No.": ["B1"], "Running Orders": [0], "OCS Done": [0], "Expediting": [0], "Inspection": [0], "Others": [0], "Total": [0],
    })
    
    os.makedirs("tests/fixtures", exist_ok=True)
    df1.to_excel("tests/fixtures/perf_excel1.xlsx", index=False)
    df2.to_excel("tests/fixtures/perf_excel2.xlsx", index=False)
    df3.to_excel("tests/fixtures/perf_excel3.xlsx", index=False)
    
    with open("tests/fixtures/perf_excel1.xlsx", "rb") as f:
        client.post(f"/api/sessions/{session_id}/files/excel1", files={"file": ("perf_excel1.xlsx", f, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")})
    with open("tests/fixtures/perf_excel2.xlsx", "rb") as f:
        client.post(f"/api/sessions/{session_id}/files/excel2", files={"file": ("perf_excel2.xlsx", f, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")})
    with open("tests/fixtures/perf_excel3.xlsx", "rb") as f:
        client.post(f"/api/sessions/{session_id}/files/excel3", files={"file": ("perf_excel3.xlsx", f, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")})
        
    payload = {
        "excel1": {"sheet": "Sheet1", "columns": {"job_number": "Job No.", "balance_quantity": "Balance Quantity", "ocs_date": "OCS Date"}},
        "excel2": {"sheet": "Sheet1", "columns": {"job_number": "Job No.", "inspection_from": "Inspection Attended (From)", "inspection_upto": "Inspection Attended (Upto)"}},
        "excel3": {"sheet": "Sheet1", "columns": {"job_number": "Job No.", "running_orders": "Running Orders", "ocs_done": "OCS Done", "expediting": "Expediting", "inspection": "Inspection", "others": "Others", "total": "Total"}}
    }
    client.post(f"/api/sessions/{session_id}/mapping", json=payload)
    client.post(f"/api/sessions/{session_id}/evaluation-month", json={"evaluation_month": "2026-08"})
    
    # Test extraction performance
    start = time.time()
    resp = client.get(f"/api/sessions/{session_id}/job-numbers")
    extract_time = time.time() - start
    assert resp.status_code == 200
    assert extract_time < 5.0 # Should easily be under 5s
    
    # Test matching performance for 1000 items
    keys = [f"B{i}" for i in range(1000)]
    start = time.time()
    resp = client.post(f"/api/sessions/{session_id}/job-numbers/match", json={"job_numbers": keys})
    match_time = time.time() - start
    assert resp.status_code == 200
    assert match_time < 2.0 # Should be very fast due to caching
    
    os.remove("tests/fixtures/perf_excel1.xlsx")
    os.remove("tests/fixtures/perf_excel2.xlsx")
    os.remove("tests/fixtures/perf_excel3.xlsx")
