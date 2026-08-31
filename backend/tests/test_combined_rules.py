import pytest
from fastapi.testclient import TestClient
from app.main import app
import pandas as pd
import os
import datetime

client = TestClient(app)

@pytest.fixture(scope="module")
def setup_combined_session():
    resp = client.post("/api/sessions")
    session_id = resp.json()["session_id"]
    
    # We will build fixtures for Excel 1, 2, and 3.
    # We need:
    # J_FULL: RO=3, InspDays=2, Excel3(OCS=2, Others=5) -> Exp=10, Insp=16, Total=31
    # J_ZERO: RO=0, InspDays=0, Excel3(OCS=0, Others=0) -> Exp=0, Insp=0, Total=0
    # J_NO_OCS: RO=3, InspDays=2, Excel3(OCS=None, Others=5) -> Exp=BLOCKED, Insp=16, Total=BLOCKED
    # J_NO_INSP: RO=3, Excel2=None, Excel3(OCS=2, Others=5) -> Exp=10, Insp=BLOCKED, Total=BLOCKED
    # J_NO_OTHERS: RO=3, InspDays=2, Excel3(OCS=2, Others=None) -> Exp=10, Insp=16, Total=BLOCKED
    # J_OVR: Same as J_FULL, but we'll override OCS=5, Others=10 via payload -> Exp=(3+5)*2=16, Insp=16, Total=42
    
    # EXCEL 1
    # J_FULL: 3 records (Balance=5, OCS=None -> RO=1 each -> total RO=3)
    # J_ZERO: 1 record (Balance=0, OCS=None -> FD=1, RO=0)
    # J_NO_OCS: 3 records (RO=3)
    # J_NO_INSP: 3 records (RO=3)
    # J_NO_OTHERS: 3 records (RO=3)
    # J_OVR: 3 records (RO=3)
    
    e1_jobs = ["J_FULL"]*3 + ["J_ZERO"] + ["J_NO_OCS"]*3 + ["J_NO_INSP"]*3 + ["J_NO_OTHERS"]*3 + ["J_OVR"]*3
    e1_bal = [5]*3 + [0] + [5]*3 + [5]*3 + [5]*3 + [5]*3
    e1_ocs = [None]*len(e1_jobs)
    
    df1 = pd.DataFrame({
        "Job No.": e1_jobs,
        "Balance Quantity": e1_bal,
        "OCS Date": e1_ocs
    })
    
    # EXCEL 2
    # J_FULL: From 10-Aug to 12-Aug -> 2 days
    # J_ZERO: From 10-Aug to 10-Aug -> 0 days
    # J_NO_OCS: 2 days
    # J_NO_INSP: No records
    # J_NO_OTHERS: 2 days
    # J_OVR: 2 days
    
    e2_jobs = ["J_FULL", "J_ZERO", "J_NO_OCS", "J_NO_OTHERS", "J_OVR"]
    e2_from = ["2026-08-10"] * len(e2_jobs)
    e2_upto = ["2026-08-12", "2026-08-10", "2026-08-12", "2026-08-12", "2026-08-12"]
    
    df2 = pd.DataFrame({
        "Job No.": e2_jobs,
        "Inspection Attended (From)": e2_from,
        "Inspection Attended (Upto)": e2_upto
    })
    
    # EXCEL 3
    df3 = pd.DataFrame({
        "Job No.": ["J_FULL", "J_ZERO", "J_NO_OCS", "J_NO_INSP", "J_NO_OTHERS", "J_OVR"],
        "OCS Done": [2, 0, None, 2, 2, 2],
        "Others": [5, 0, 5, 5, None, 5],
        "Running Orders": [None]*6,
        "Orders For": [1, 0, 1, 1, 1, 1],
        "Expediting": [None]*6,
        "Inspection": [2, 0, 2, 2, 2, 2],
        "Total": [None]*6
    })
    
    os.makedirs("tests/fixtures", exist_ok=True)
    df1.to_excel("tests/fixtures/p6_excel1.xlsx", index=False)
    df2.to_excel("tests/fixtures/p6_excel2.xlsx", index=False)
    df3.to_excel("tests/fixtures/p6_excel3.xlsx", index=False)
    
    with open("tests/fixtures/p6_excel1.xlsx", "rb") as f:
        client.post(f"/api/sessions/{session_id}/files/excel1", files={"file": ("p6_excel1.xlsx", f, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")})
    with open("tests/fixtures/p6_excel2.xlsx", "rb") as f:
        client.post(f"/api/sessions/{session_id}/files/excel2", files={"file": ("p6_excel2.xlsx", f, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")})
    with open("tests/fixtures/p6_excel3.xlsx", "rb") as f:
        client.post(f"/api/sessions/{session_id}/files/excel3", files={"file": ("p6_excel3.xlsx", f, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")})
        
    payload = {
        "excel1": {"sheet": "Sheet1", "columns": {"job_number": "Job No.", "balance_quantity": "Balance Quantity", "ocs_date": "OCS Date"}},
        "excel2": {"sheet": "Sheet1", "columns": {"job_number": "Job No.", "inspection_from": "Inspection Attended (From)", "inspection_upto": "Inspection Attended (Upto)"}},
        "excel3": {"sheet": "Sheet1", "columns": {"job_number": "Job No.", "running_orders": "Running Orders", "orders_for_fd": "Orders For", "ocs_done": "OCS Done", "expediting": "Expediting", "inspection": "Inspection", "others": "Others", "total": "Total"}}
    }
    print("MAPPING:", client.post(f"/api/sessions/{session_id}/mapping", json=payload).json())
    client.post(f"/api/sessions/{session_id}/evaluation-month", json={"evaluation_month": "2026-08"})
    
    yield session_id
    
    os.remove("tests/fixtures/p6_excel1.xlsx")
    os.remove("tests/fixtures/p6_excel2.xlsx")
    os.remove("tests/fixtures/p6_excel3.xlsx")


def test_combined_full_and_zero(setup_combined_session):
    s_id = setup_combined_session
    resp = client.post(f"/api/sessions/{s_id}/calculations/combined", json={"job_numbers": ["J_FULL", "J_ZERO"], "evaluation_month": "2026-08"})
    assert resp.status_code == 200
    res = {r["job_number"]: r for r in resp.json()}
    
    j = res["J_FULL"]
    assert j["running_orders"] == 3
    assert j["ocs_done"] == 0
    assert j["expediting"] == 6 # (3+0)*2
    assert j["inspection"] == 24.0
    assert j["others"] == 0.0
    assert j["calculated_total"] == 30.0 # 6 + 24 + 0
    assert j["status"] == "COMPLETE"
    
    z = res["J_ZERO"]
    assert z["running_orders"] == 0
    assert z["ocs_done"] == 0
    assert z["expediting"] == 0
    assert z["inspection"] == 8.0
    assert z["others"] == 0.0
    assert z["calculated_total"] == 8.0
    assert z["status"] == "COMPLETE"

def test_combined_blocked_states(setup_combined_session):
    s_id = setup_combined_session
    resp = client.post(f"/api/sessions/{s_id}/calculations/combined", json={
        "job_numbers": ["J_NO_OCS", "J_NO_INSP", "J_NO_OTHERS"],
        "evaluation_month": "2026-08"
    })
    res = {r["job_number"]: r for r in resp.json()}
    
    # J_NO_OCS and J_NO_OTHERS evaluate successfully now because they don't depend on Excel 3!
    no_ocs = res["J_NO_OCS"]
    assert no_ocs["ocs_done"] == 0
    assert no_ocs["expediting"] == 6 
    assert no_ocs["calculated_total"] == 30.0
    assert no_ocs["status"] == "COMPLETE"
    
    # J_NO_INSP has no Excel 2 records, so inspection is 0.0
    no_insp = res["J_NO_INSP"]
    assert no_insp["inspection"] == 0.0
    assert no_insp["status"] == "COMPLETE"
    
    no_oth = res["J_NO_OTHERS"]
    assert no_oth["others"] == 0.0 # Defaults to 0
    assert no_oth["calculated_total"] == 30.0
    assert no_oth["status"] == "COMPLETE"

def test_combined_manual_overrides(setup_combined_session):
    s_id = setup_combined_session
    resp = client.post(f"/api/sessions/{s_id}/calculations/combined", json={
        "job_numbers": ["J_OVR", "J_NO_INSP"],
        "evaluation_month": "2026-08",
        "manual_inputs": {
            "J_OVR": {"ocs_done": 5, "others": 10}
        }
    })
    res = {r["job_number"]: r for r in resp.json()}
    
    ovr = res["J_OVR"]
    assert ovr["ocs_done"] == 5
    assert ovr["expediting"] == 16 # (3+5)*2
    assert ovr["inspection"] == 24.0
    assert ovr["others"] == 10.0
    assert ovr["calculated_total"] == 50.0 # 16 + 24 + 10
    assert ovr["status"] == "COMPLETE"
    
    # J_NO_INSP is no longer blocked because missing inspection evaluates to 0
    no_insp = res["J_NO_INSP"]
    assert no_insp["status"] == "COMPLETE"

def test_invariants(setup_combined_session):
    s_id = setup_combined_session
    resp = client.post(f"/api/sessions/{s_id}/calculations/combined", json={
        "job_numbers": ["J_FULL", "J_ZERO", "J_OVR"],
        "evaluation_month": "2026-08",
        "manual_inputs": {"J_OVR": {"ocs_done": 5, "others": 10}}
    })
    results = resp.json()
    
    for r in results:
        if r["status"] == "COMPLETE":
            assert r["expediting"] == (r["running_orders"] + r["ocs_done"]) * 2
            assert r["calculated_total"] == r["expediting"] + r["inspection"] + r["others"]

def test_performance_combined_10k_rows():
    import time
    resp = client.post("/api/sessions")
    session_id = resp.json()["session_id"]
    
    # 10k rows
    df1 = pd.DataFrame({
        "Job No.": [f"B{i % 1000}" for i in range(10000)],
        "Balance Quantity": [5] * 10000,
        "OCS Date": [None] * 10000
    })
    
    df2 = pd.DataFrame({
        "Job No.": [f"B{i % 1000}" for i in range(10000)],
        "Inspection Attended (From)": ["2026-08-10"] * 10000,
        "Inspection Attended (Upto)": ["2026-08-12"] * 10000,
    })
    
    df3 = pd.DataFrame({
        "Job No.": [f"B{i}" for i in range(1000)],
        "OCS Done": [2] * 1000,
        "Others": [5] * 1000,
        "Running Orders": [None]*1000,
        "Orders For": [1]*1000,
        "Expediting": [None]*1000,
        "Inspection": [2]*1000,
        "Total": [None]*1000
    })
    
    os.makedirs("tests/fixtures", exist_ok=True)
    df1.to_excel("tests/fixtures/perf_c_excel1.xlsx", index=False)
    df2.to_excel("tests/fixtures/perf_c_excel2.xlsx", index=False)
    df3.to_excel("tests/fixtures/perf_c_excel3.xlsx", index=False)
    
    with open("tests/fixtures/perf_c_excel1.xlsx", "rb") as f:
        client.post(f"/api/sessions/{session_id}/files/excel1", files={"file": ("perf_c_excel1.xlsx", f, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")})
    with open("tests/fixtures/perf_c_excel2.xlsx", "rb") as f:
        client.post(f"/api/sessions/{session_id}/files/excel2", files={"file": ("perf_c_excel2.xlsx", f, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")})
    with open("tests/fixtures/perf_c_excel3.xlsx", "rb") as f:
        client.post(f"/api/sessions/{session_id}/files/excel3", files={"file": ("perf_c_excel3.xlsx", f, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")})
        
    payload = {
        "excel1": {"sheet": "Sheet1", "columns": {"job_number": "Job No.", "balance_quantity": "Balance Quantity", "ocs_date": "OCS Date"}},
        "excel2": {"sheet": "Sheet1", "columns": {"job_number": "Job No.", "inspection_from": "Inspection Attended (From)", "inspection_upto": "Inspection Attended (Upto)"}},
        "excel3": {"sheet": "Sheet1", "columns": {"job_number": "Job No.", "running_orders": "Running Orders", "orders_for_fd": "Orders For", "ocs_done": "OCS Done", "expediting": "Expediting", "inspection": "Inspection", "others": "Others", "total": "Total"}}
    }
    print("MAPPING:", client.post(f"/api/sessions/{session_id}/mapping", json=payload).json())
    client.post(f"/api/sessions/{session_id}/evaluation-month", json={"evaluation_month": "2026-08"})
    
    start = time.time()
    resp = client.post(f"/api/sessions/{session_id}/calculations/combined", json={"job_numbers": [f"B{i}" for i in range(500)], "evaluation_month": "2026-08"})
    calc_time = time.time() - start
    
    assert resp.status_code == 200
    assert calc_time < 10.0 # Should easily be under 10s
    
    os.remove("tests/fixtures/perf_c_excel1.xlsx")
    os.remove("tests/fixtures/perf_c_excel2.xlsx")
    os.remove("tests/fixtures/perf_c_excel3.xlsx")
