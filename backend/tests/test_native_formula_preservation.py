import pytest
from fastapi.testclient import TestClient
from app.main import app
import pandas as pd
import os

client = TestClient(app)

def test_native_formula_and_overrides():
    resp = client.post("/api/sessions")
    s_id = resp.json()["session_id"]
    
    df1 = pd.DataFrame({"Job No.": ["B123"], "Balance Quantity": [5], "OCS Date": [None]})
    df2 = pd.DataFrame({"Job No.": ["B123"], "Inspection Attended (From)": ["2026-08-10"], "Inspection Attended (Upto)": ["2026-08-11"]})
    # Native Expediting is 25 (hardcoded or formula value extracted by pandas)
    df3 = pd.DataFrame({"Job No.": ["B123"], "Running Orders": [2], "Orders For": [1], "OCS Done": [3], "Expediting": [25], "Inspection": [0], "Others": [5], "Total": [0]})
    
    os.makedirs("tests/fixtures", exist_ok=True)
    df1.to_excel("tests/fixtures/np_e1.xlsx", index=False)
    df2.to_excel("tests/fixtures/np_e2.xlsx", index=False)
    df3.to_excel("tests/fixtures/np_e3.xlsx", index=False)
    
    with open("tests/fixtures/np_e1.xlsx", "rb") as f:
        client.post(f"/api/sessions/{s_id}/files/excel1", files={"file": ("np_e1.xlsx", f, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")})
    with open("tests/fixtures/np_e2.xlsx", "rb") as f:
        client.post(f"/api/sessions/{s_id}/files/excel2", files={"file": ("np_e2.xlsx", f, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")})
    with open("tests/fixtures/np_e3.xlsx", "rb") as f:
        client.post(f"/api/sessions/{s_id}/files/excel3", files={"file": ("np_e3.xlsx", f, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")})
        
    payload = {
        "excel1": {"sheet": "Sheet1", "columns": {"job_number": "Job No.", "balance_quantity": "Balance Quantity", "ocs_date": "OCS Date"}},
        "excel2": {"sheet": "Sheet1", "columns": {"job_number": "Job No.", "inspection_from": "Inspection Attended (From)", "inspection_upto": "Inspection Attended (Upto)"}},
        "excel3": {"sheet": "Sheet1", "columns": {"job_number": "Job No.", "running_orders": "Running Orders", "orders_for_fd": "Orders For", "ocs_done": "OCS Done", "expediting": "Expediting", "inspection": "Inspection", "others": "Others", "total": "Total"}}
    }
    client.post(f"/api/sessions/{s_id}/mapping", json=payload)
    client.post(f"/api/sessions/{s_id}/evaluation-month", json={"evaluation_month": "2026-08"})
    
    resp_calc = client.post(f"/api/sessions/{s_id}/calculations/combined", json={"job_numbers": ["B123"], "evaluation_month": "2026-08"})
    res = resp_calc.json()[0]
    
    # 1. Verify Excel 3 Decoupling (It should use 2 instead of the garbage 25 in Excel 3)
    # df1 -> bal 5 -> RO 1. Ocs date None -> Ocs done 0. Rule = (1+0)*2=2.
    assert res["expediting"] == 2
    assert res["native_expediting_used"] is False
    
    # Inspection comes from Excel 2 (2 days)
    assert res["inspection"] == 16.0
    
    # Others is defaulted to 0
    assert res["others"] == 0.0
    
    # Total is 2 + 16 + 0 = 18
    assert res["calculated_total"] == 18.0
    
    # 2. Review Override overrides the derived calculation
    resp_ovr = client.post(f"/api/sessions/{s_id}/jobs/B123/overrides", json={"field": "ocs_done", "value": 5})
    res_ovr = resp_ovr.json()
    
    assert res_ovr["ocs_done"] == 5
    # Recalculates based on (RO 1 + overridden OCS 5) * 2 = 12
    assert res_ovr["expediting"] == 12
    assert res_ovr["native_expediting_used"] is False
    
    # Total = 12 + 16 (Insp) + 0 (Others) = 28
    assert res_ovr["calculated_total"] == 28.0
    
    # 3. Resetting override goes back to derived 2, not Excel 3 25
    resp_reset = client.post(f"/api/sessions/{s_id}/jobs/B123/reset-overrides")
    res_reset = resp_reset.json()
    
    assert res_reset["ocs_done"] == 0
    assert res_reset["expediting"] == 2
    assert res_reset["calculated_total"] == 18.0
    assert res_reset["overrides"]["ocs_done"]["active"] is False # Audit historical evidence remains
    
    os.remove("tests/fixtures/np_e1.xlsx")
    os.remove("tests/fixtures/np_e2.xlsx")
    os.remove("tests/fixtures/np_e3.xlsx")
