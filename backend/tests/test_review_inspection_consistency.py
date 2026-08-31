import pytest
from fastapi.testclient import TestClient
from app.main import app
import pandas as pd
import os
from datetime import datetime

client = TestClient(app)

def test_review_inspection_consistency():
    resp = client.post("/api/sessions")
    s_id = resp.json()["session_id"]
    
    # B269 with cross month and current month inspections
    df1 = pd.DataFrame({
        "Job No.": ["B269", "B269"],
        "Balance Quantity": [0, 10],
        "OCS Date": ["2026-08-01", None],
    }) # FD=0, RO=1, OCS=1 => Exp = (1+0)*2 = 2
    
    df2 = pd.DataFrame({
        "Job No.": ["B269", "B269", "B269"],
        "Inspection Attended (From)": [datetime(2026, 8, 10), datetime(2026, 7, 10), datetime(2026, 8, 15)],
        "Inspection Attended (Upto)": [datetime(2026, 8, 12), datetime(2026, 7, 12), datetime(2026, 8, 18)],
        "No. of Days": [2, 2, 3] # Valid = 2+3=5, Invalid = 2 (wrong month)
    })
    
    df3 = pd.DataFrame({
        "Job No": ["B269"], "Running orders": [1], "Orders for": [0], "OCS done": [1], "Exp.": [2], "Inspn": [5], "Others": [0], "Total": [7],
    })

    os.makedirs("tests/fixtures", exist_ok=True)
    df1.to_excel("tests/fixtures/tmp_e1.xlsx", index=False)
    df2.to_excel("tests/fixtures/tmp_e2.xlsx", index=False)
    df3.to_excel("tests/fixtures/tmp_e3.xlsx", index=False)
    
    with open("tests/fixtures/tmp_e1.xlsx", "rb") as f:
        client.post(f"/api/sessions/{s_id}/files/excel1", files={"file": ("tmp_e1.xlsx", f, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")})
    with open("tests/fixtures/tmp_e2.xlsx", "rb") as f:
        client.post(f"/api/sessions/{s_id}/files/excel2", files={"file": ("tmp_e2.xlsx", f, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")})
    with open("tests/fixtures/tmp_e3.xlsx", "rb") as f:
        client.post(f"/api/sessions/{s_id}/files/excel3", files={"file": ("tmp_e3.xlsx", f, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")})

    payload = {
        "excel1": {"sheet": "Sheet1", "columns": {"job_number": "Job No.", "balance_quantity": "Balance Quantity", "ocs_date": "OCS Date"}},
        "excel2": {"sheet": "Sheet1", "columns": {"job_number": "Job No.", "inspection_from": "Inspection Attended (From)", "inspection_upto": "Inspection Attended (Upto)"}},
        "excel3": {"sheet": "Sheet1", "columns": {"job_number": "Job No", "running_orders": "Running orders", "orders_for_fd": "Orders for", "ocs_done": "OCS done", "expediting": "Exp.", "inspection": "Inspn", "others": "Others", "total": "Total"}}
    }
    client.post(f"/api/sessions/{s_id}/mapping", json=payload)
    
    # 1. SET EVALUATION MONTH TO 2026-08 (Crucial Step!)
    client.post(f"/api/sessions/{s_id}/evaluation-month", json={"evaluation_month": "2026-08"})
    
    # 2. COMBINED CALCULATION
    resp_calc = client.post(f"/api/sessions/{s_id}/calculations/combined", json={"job_numbers": ["B269"], "evaluation_month": "2026-08"})
    calc_res = resp_calc.json()[0]

    # 3. VERIFY INSPECTION DAYS (10-12 = 3 days, 15-18 = 4 days => 7 days)
    assert calc_res["inspection"] == 56.0
    assert calc_res["expediting"] == 4.0
    assert calc_res["calculated_total"] == 60.0
    
    # 3. REVIEW CALCULATION
    resp_rev = client.post(f"/api/sessions/{s_id}/review", json={"job_numbers": ["B269"]})
    rev_res = resp_rev.json()[0]
    
    assert rev_res["inspection"] == 56.0 # MUST MATCH COMBINED!
    assert rev_res["expediting"] == 4.0
    assert rev_res["calculated_total"] == 60.0
    
    # 4. NOW CHANGE EVALUATION MONTH TO 2026-07
    client.post(f"/api/sessions/{s_id}/evaluation-month", json={"evaluation_month": "2026-07"})
    
    # 5. RE-RUN COMBINED
    resp_calc_7 = client.post(f"/api/sessions/{s_id}/calculations/combined", json={"job_numbers": ["B269"], "evaluation_month": "2026-07"})
    calc_res_7 = resp_calc_7.json()[0]
    assert calc_res_7["inspection"] == 24 # Only 1 record from July!
    
    # 6. RE-RUN REVIEW
    resp_rev_7 = client.post(f"/api/sessions/{s_id}/review", json={"job_numbers": ["B269"]})
    rev_res_7 = resp_rev_7.json()[0]
    assert rev_res_7["inspection"] == 24 # MUST MATCH COMBINED AND 2026-07 MONTH!

    os.remove("tests/fixtures/tmp_e1.xlsx")
    os.remove("tests/fixtures/tmp_e2.xlsx")
    os.remove("tests/fixtures/tmp_e3.xlsx")

