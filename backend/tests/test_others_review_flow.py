import pytest
from fastapi.testclient import TestClient
from app.main import app
import pandas as pd

client = TestClient(app)

def test_others_preservation_in_review():
    resp = client.post("/api/sessions")
    s_id = resp.json()["session_id"]
    
    # 1. Setup Excel 1
    # B269: Balance=0, OCS=populated -> OCS Done=1
    # B224: Balance!=0 -> Running Order=1
    df1 = pd.DataFrame({
        "Job No.": ["B269", "B224"],
        "Balance Quantity": [0, 10],
        "OCS Date": ["01/08/2026", None]
    })
    
    # 2. Setup Excel 2
    # B269: Inspection (2 days), Others (0.5 days via NO. OF DAYS)
    # B224: Inspection (3 days), Others (12.5 days via QAP APPL.)
    df2 = pd.DataFrame({
        "JOB NO.": ["B269", "B224"],
        "FROM": ["2026-08-01", "2026-08-10"],
        "UPTO": ["2026-08-02", "2026-08-12"],
        "NO. OF DAYS": [0.5, None],
        "DATE RECEIVED": ["2026-06-15", "2026-05-10"],
        "QAP APPL.": [None, 12.5]
    })
    
    # 3. Setup Excel 3 (Empty)
    df3 = pd.DataFrame({
        "Job No.": ["B269", "B224"],
        "Running Orders": [0, 0],
        "Orders for FD": [0, 0],
        "OCS done": [0, 0],
        "Exp.": [0, 0],
        "Inspn": [0, 0],
        "Others": [0, 0],
        "Total": [0, 0]
    })

    df1.to_excel("tests/fixtures/test_rev_e1.xlsx", index=False)
    df2.to_excel("tests/fixtures/test_rev_e2.xlsx", index=False)
    df3.to_excel("tests/fixtures/test_rev_e3.xlsx", index=False)
    
    with open("tests/fixtures/test_rev_e1.xlsx", "rb") as f:
        client.post(f"/api/sessions/{s_id}/files/excel1", files={"file": ("test_rev_e1.xlsx", f, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")})
    with open("tests/fixtures/test_rev_e2.xlsx", "rb") as f:
        client.post(f"/api/sessions/{s_id}/files/excel2", files={"file": ("test_rev_e2.xlsx", f, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")})
    with open("tests/fixtures/test_rev_e3.xlsx", "rb") as f:
        client.post(f"/api/sessions/{s_id}/files/excel3", files={"file": ("test_rev_e3.xlsx", f, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")})
        
    mapping = {
        "excel1": {"sheet": "Sheet1", "columns": {"job_number": "Job No.", "balance_quantity": "Balance Quantity", "ocs_date": "OCS Date"}},
        "excel2": {"sheet": "Sheet1", "columns": {"job_number": "JOB NO.", "inspection_from": "FROM", "inspection_upto": "UPTO", "date_received": "DATE RECEIVED", "qap_appl": "QAP APPL.", "no_of_working_days": "NO. OF DAYS"}},
        "excel3": {"sheet": "Sheet1", "columns": {"job_number": "Job No.", "running_orders": "Running Orders", "orders_for_fd": "Orders for FD", "ocs_done": "OCS done", "expediting": "Exp.", "inspection": "Inspn", "others": "Others", "total": "Total"}}
    }
    client.post(f"/api/sessions/{s_id}/mapping", json=mapping)
    
    # --- TEST 1: Combined Calculation for B269 & B224 (Step 4 payload) ---
    r_comb = client.post(f"/api/sessions/{s_id}/calculations/combined", json={"job_numbers": ["B269", "B224"], "evaluation_month": "2026-08"})
    assert r_comb.status_code == 200
    combined_data = {item["job_number"]: item for item in r_comb.json()}
    
    assert combined_data["B269"]["others"] == 0.5
    assert combined_data["B224"]["others"] == 12.5
    
    # --- TEST 2: Review Calculation for B269 & B224 (Step 5 payload) ---
    r_rev = client.post(f"/api/sessions/{s_id}/review", json={"job_numbers": ["B269", "B224"], "evaluation_month": "2026-08"})
    assert r_rev.status_code == 200
    review_data = {item["job_number"]: item for item in r_rev.json()}
    
    # Ensure they match the combined calculation
    assert review_data["B269"]["others"] == 0.5
    assert review_data["B224"]["others"] == 12.5
    
    # --- TEST 3: State preservation (Approve/Undo) ---
    client.post(f"/api/sessions/{s_id}/jobs/B269/approve", json={"acknowledge_warnings": True})
    r_rev_after = client.post(f"/api/sessions/{s_id}/review", json={"job_numbers": ["B269"], "evaluation_month": "2026-08"})
    assert r_rev_after.json()[0]["others"] == 0.5
    assert r_rev_after.json()[0]["status"] == "APPROVED"
    
    client.post(f"/api/sessions/{s_id}/jobs/B269/unapprove")
    r_rev_undo = client.post(f"/api/sessions/{s_id}/review", json={"job_numbers": ["B269"], "evaluation_month": "2026-08"})
    assert r_rev_undo.json()[0]["others"] == 0.5
    assert r_rev_undo.json()[0]["status"] == "COMPLETE" or r_rev_undo.json()[0]["status"] == "DRAFT"
    
    # --- TEST 4: Delete preservation ---
    client.delete(f"/api/sessions/{s_id}/jobs/B224")
    r_rev_del = client.post(f"/api/sessions/{s_id}/review", json={"job_numbers": ["B224"], "evaluation_month": "2026-08"})
    assert r_rev_del.json()[0]["others"] == 12.5
    assert r_rev_del.json()[0]["status"] == "DELETED"
