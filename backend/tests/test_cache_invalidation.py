import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.services.session_service import SessionService
import pandas as pd
import os

client = TestClient(app)

def test_cache_invalidation():
    # 1. Upload Excel 1 version A.
    resp = client.post("/api/sessions")
    s_id = resp.json()["session_id"]
    
    df1_a = pd.DataFrame({"Job No.": ["B123"], "Balance Quantity": [10], "OCS Date": [None]})
    os.makedirs("tests/fixtures", exist_ok=True)
    df1_a.to_excel("tests/fixtures/cache_e1_a.xlsx", index=False)
    
    df2 = pd.DataFrame({"Job No.": ["B123"], "Inspection Attended (From)": ["2026-08-10"], "Inspection Attended (Upto)": ["2026-08-12"]})
    df3 = pd.DataFrame({"Job No.": ["B123"], "Running Orders": [0], "OCS Done": [0], "Expediting": [0], "Inspection": [0], "Others": [0], "Total": [0]})
    df2.to_excel("tests/fixtures/cache_e2.xlsx", index=False)
    df3.to_excel("tests/fixtures/cache_e3.xlsx", index=False)
    
    with open("tests/fixtures/cache_e1_a.xlsx", "rb") as f:
        client.post(f"/api/sessions/{s_id}/files/excel1", files={"file": ("cache_e1_a.xlsx", f, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")})
    with open("tests/fixtures/cache_e2.xlsx", "rb") as f:
        client.post(f"/api/sessions/{s_id}/files/excel2", files={"file": ("cache_e2.xlsx", f, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")})
    with open("tests/fixtures/cache_e3.xlsx", "rb") as f:
        client.post(f"/api/sessions/{s_id}/files/excel3", files={"file": ("cache_e3.xlsx", f, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")})
        
    payload = {
        "excel1": {"sheet": "Sheet1", "columns": {"job_number": "Job No.", "balance_quantity": "Balance Quantity", "ocs_date": "OCS Date"}},
        "excel2": {"sheet": "Sheet1", "columns": {"job_number": "Job No.", "inspection_from": "Inspection Attended (From)", "inspection_upto": "Inspection Attended (Upto)"}},
        "excel3": {"sheet": "Sheet1", "columns": {"job_number": "Job No.", "running_orders": "Running Orders", "ocs_done": "OCS Done", "expediting": "Expediting", "inspection": "Inspection", "others": "Others", "total": "Total"}}
    }
    client.post(f"/api/sessions/{s_id}/mapping", json=payload)
    client.post(f"/api/sessions/{s_id}/evaluation-month", json={"evaluation_month": "2026-08"})
    
    # Calculate Excel 1
    match1 = client.post(f"/api/sessions/{s_id}/job-numbers/match", json={"job_numbers": ["B123"]})
    assert match1.json()["excel1_records"]["B123"][0]["Balance Quantity"] == 10
    
    # Replace Excel 1 with version B
    df1_b = pd.DataFrame({"Job No.": ["B123"], "Balance Quantity": [20], "OCS Date": [None]})
    df1_b.to_excel("tests/fixtures/cache_e1_b.xlsx", index=False)
    
    with open("tests/fixtures/cache_e1_b.xlsx", "rb") as f:
        client.post(f"/api/sessions/{s_id}/files/excel1", files={"file": ("cache_e1_b.xlsx", f, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")})
        
    # Re-validate mapping
    client.post(f"/api/sessions/{s_id}/mapping", json=payload)
    client.post(f"/api/sessions/{s_id}/evaluation-month", json={"evaluation_month": "2026-08"})
    
    # Calculate again
    match2 = client.post(f"/api/sessions/{s_id}/job-numbers/match", json={"job_numbers": ["B123"]})
    assert match2.json()["excel1_records"]["B123"][0]["Balance Quantity"] == 20
    
    os.remove("tests/fixtures/cache_e1_a.xlsx")
    os.remove("tests/fixtures/cache_e1_b.xlsx")
    os.remove("tests/fixtures/cache_e2.xlsx")
    os.remove("tests/fixtures/cache_e3.xlsx")
