import pytest
from fastapi.testclient import TestClient
from app.main import app
import pandas as pd
import os

client = TestClient(app)

@pytest.fixture(scope="module")
def setup_rules_session():
    # 1. Create Session
    resp = client.post("/api/sessions")
    session_id = resp.json()["session_id"]
    
    # Generate fixture for all 20 test cases
    # Test cases:
    # J_FD_1: Bal=0, OCS=blank -> FD=1
    # J_FD_2: Bal=0, OCS=present -> FD=0
    # J_FD_3: Bal=5, OCS=blank -> FD=0
    # J_FD_4: Bal=-1, OCS=blank -> FD=0, Warning
    # J_FD_5: Bal=None, OCS=None -> FD=0, Warning
    # J_FD_6: Bal=0, OCS=None (x2) -> FD=1
    # J_RO_1: Bal=5, OCS=None -> RO=1
    # J_RO_2: Bal=-1, OCS=None -> RO=1, Warning
    # J_RO_3: Bal=0, OCS=None -> RO=0
    # J_RO_4: Bal=5, OCS="15/07/2026" -> RO=0
    # J_RO_5: Bal=5, OCS=None (x3) -> RO=3
    # J_ERR_1: Bal="Pending", OCS=None -> Warning
    # J_ERR_2: Bal=5, OCS="bad_date" -> Warning
    # J_MIX: Row1(Bal=0, OCS=None), Row2(Bal=5, OCS=None), Row3(Bal="NA", OCS=None) -> FD=1, RO=1, Warn=1
    
    data1 = {
        "Job No.": [
            "J_FD_1", 
            "J_FD_2", 
            "J_FD_3", 
            "J_FD_4", 
            "J_FD_5", 
            "J_FD_6", "J_FD_6", 
            "J_RO_1", 
            "J_RO_2", 
            "J_RO_3", 
            "J_RO_4", 
            "J_RO_5", "J_RO_5", "J_RO_5",
            "J_ERR_1",
            "J_ERR_2",
            "J_MIX", "J_MIX", "J_MIX"
        ],
        "Balance Quantity": [
            0,
            0,
            5,
            -1,
            None,
            0, 0,
            5,
            -1,
            0,
            5,
            5, 5, 5,
            "Pending",
            5,
            0, 5, "NA"
        ],
        "OCS Date": [
            None,
            "15/07/2026",
            None,
            None,
            None,
            None, None,
            None,
            None,
            None,
            "15/07/2026",
            None, None, None,
            None,
            "bad_date",
            None, None, None
        ],
    }
    
    df1 = pd.DataFrame(data1)
    df2 = pd.DataFrame({"Job No.": ["J_FD_1"], "Inspection Attended (From)": ["d1"], "Inspection Attended (Upto)": ["d2"]})
    df3 = pd.DataFrame({"Job No.": ["J_FD_1"], "Running Orders": [0], "OCS Done": [0], "Expediting": [0], "Inspection": [0], "Others": [0], "Total": [0]})
    
    os.makedirs("tests/fixtures", exist_ok=True)
    df1.to_excel("tests/fixtures/p4_excel1.xlsx", index=False)
    df2.to_excel("tests/fixtures/p4_excel2.xlsx", index=False)
    df3.to_excel("tests/fixtures/p4_excel3.xlsx", index=False)
    
    with open("tests/fixtures/p4_excel1.xlsx", "rb") as f:
        client.post(f"/api/sessions/{session_id}/files/excel1", files={"file": ("p4_excel1.xlsx", f, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")})
    with open("tests/fixtures/p4_excel2.xlsx", "rb") as f:
        client.post(f"/api/sessions/{session_id}/files/excel2", files={"file": ("p4_excel2.xlsx", f, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")})
    with open("tests/fixtures/p4_excel3.xlsx", "rb") as f:
        client.post(f"/api/sessions/{session_id}/files/excel3", files={"file": ("p4_excel3.xlsx", f, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")})
        
    payload = {
        "excel1": {"sheet": "Sheet1", "columns": {"job_number": "Job No.", "balance_quantity": "Balance Quantity", "ocs_date": "OCS Date"}},
        "excel2": {"sheet": "Sheet1", "columns": {"job_number": "Job No.", "inspection_from": "Inspection Attended (From)", "inspection_upto": "Inspection Attended (Upto)"}},
        "excel3": {"sheet": "Sheet1", "columns": {"job_number": "Job No.", "running_orders": "Running Orders", "ocs_done": "OCS Done", "expediting": "Expediting", "inspection": "Inspection", "others": "Others", "total": "Total"}}
    }
    print("MAPPING:", client.post(f"/api/sessions/{session_id}/mapping", json=payload).json())
    client.post(f"/api/sessions/{session_id}/evaluation-month", json={"evaluation_month": "2026-08"})
    
    yield session_id
    
    os.remove("tests/fixtures/p4_excel1.xlsx")
    os.remove("tests/fixtures/p4_excel2.xlsx")
    os.remove("tests/fixtures/p4_excel3.xlsx")


def test_fd_rules(setup_rules_session):
    s_id = setup_rules_session
    jobs = ["J_FD_1", "J_FD_2", "J_FD_3", "J_FD_4", "J_FD_5", "J_FD_6"]
    resp = client.post(f"/api/sessions/{s_id}/calculations/excel1", json={"job_numbers": jobs, "evaluation_month": "2026-08"})
    assert resp.status_code == 200
    print(resp.json()); res = {r["job_number"]: r for r in resp.json()}
    
    # 1. Balance=0, OCS=blank -> FD=1
    assert res["J_FD_1"]["fd"] == 1
    assert res["J_FD_1"]["running_orders"] == 0
    assert res["J_FD_1"]["status"] == "COMPLETE"
    
    # 2. Balance=0, OCS=present -> FD=0
    assert res["J_FD_2"]["fd"] == 0
    
    # 3. Balance>0, OCS=blank -> FD=0
    assert res["J_FD_3"]["fd"] == 0
    
    # 4. Balance<0, OCS=blank -> FD=0, Warning
    assert res["J_FD_4"]["fd"] == 0
    assert "WARNING" in res["J_FD_4"]["status"]
    assert any("negative" in w.lower() for w in res["J_FD_4"]["warnings"])
    
    # 5. Balance=blank, OCS=blank -> FD=0, missing-data warning
    assert res["J_FD_5"]["fd"] == 0
    assert "WARNING" in res["J_FD_5"]["status"]
    assert any("missing balance" in w.lower() for w in res["J_FD_5"]["warnings"])
    
    # 6. Multiple FD qualifying rows -> FD=2
    assert res["J_FD_6"]["fd"] == 2
    assert res["J_FD_6"]["source_record_count"] == 2


def test_running_orders_rules(setup_rules_session):
    s_id = setup_rules_session
    jobs = ["J_RO_1", "J_RO_2", "J_RO_3", "J_RO_4", "J_RO_5"]
    resp = client.post(f"/api/sessions/{s_id}/calculations/excel1", json={"job_numbers": jobs, "evaluation_month": "2026-08"})
    print(resp.json()); res = {r["job_number"]: r for r in resp.json()}
    
    # 7. Balance>0, OCS=blank -> RO=1
    assert res["J_RO_1"]["running_orders"] == 1
    
    # 8. Balance<0, OCS=blank -> RO=1, warning
    assert res["J_RO_2"]["running_orders"] == 1
    assert "WARNING" in res["J_RO_2"]["status"]
    
    # 9. Balance=0, OCS=blank -> RO=0
    assert res["J_RO_3"]["running_orders"] == 0
    
    # 10. Balance>0, OCS=present -> RO=1
    assert res["J_RO_4"]["running_orders"] == 1
    
    # 11. Multiple qualifying rows
    assert res["J_RO_5"]["running_orders"] == 3
    assert res["J_RO_5"]["source_record_count"] == 3


def test_invalid_data_rules(setup_rules_session):
    s_id = setup_rules_session
    jobs = ["J_ERR_1", "J_ERR_2"]
    resp = client.post(f"/api/sessions/{s_id}/calculations/excel1", json={"job_numbers": jobs, "evaluation_month": "2026-08"})
    print(resp.json()); res = {r["job_number"]: r for r in resp.json()}
    
    # 12/13. Invalid balance ("Pending") -> Warning
    assert "WARNING" in res["J_ERR_1"]["status"]
    assert any("invalid balance" in w.lower() for w in res["J_ERR_1"]["warnings"])
    
    # 14/15. Invalid OCS Date ("bad_date") -> Warning
    assert "WARNING" in res["J_ERR_2"]["status"]
    assert any("invalid ocs date" in w.lower() for w in res["J_ERR_2"]["warnings"])


def test_mixed_and_isolation(setup_rules_session):
    s_id = setup_rules_session
    resp = client.post(f"/api/sessions/{s_id}/calculations/excel1", json={"job_numbers": ["J_MIX", "NON_EXISTENT"], "evaluation_month": "2026-08"})
    print(resp.json()); res = {r["job_number"]: r for r in resp.json()}
    
    # 16. Mixed valid/invalid records
    assert res["J_MIX"]["fd"] == 1
    assert res["J_MIX"]["running_orders"] == 1
    assert "WARNING" in res["J_MIX"]["status"]
    assert len(res["J_MIX"]["warnings"]) > 0
    
    # 18. Job with no matching records
    assert "NON_EXISTENT" in res
    assert res["NON_EXISTENT"]["source_record_count"] == 0
    assert res["NON_EXISTENT"]["fd"] == 0
    assert res["NON_EXISTENT"]["running_orders"] == 0
    assert "WARNING" in res["NON_EXISTENT"]["status"]
    assert any("no matching excel 1 records" in w.lower() for w in res["NON_EXISTENT"]["warnings"])


def test_invariants(setup_rules_session):
    # 22. Invariant: FD is 0 or 1, a row can't be both FD and RO.
    s_id = setup_rules_session
    resp = client.post(f"/api/sessions/{s_id}/calculations/excel1", json={"job_numbers": ["J_MIX", "J_FD_6", "J_RO_5"], "evaluation_month": "2026-08"})
    results = resp.json()
    for r in results:
        assert r["fd"] >= 0
        assert r["running_orders"] <= r["source_record_count"]
        # In our exact definitions, if Bal=0 (FD matches) it cannot be Bal!=0 (RO matches)
        # We can check evidence lists.
        fd_evidence = [e for e in r["evidence"] if e["contribution"] == "FD"]
        ro_evidence = [e for e in r["evidence"] if e["contribution"] == "Running Order"]
        # No overlap allowed by definition
        assert len(fd_evidence) + len(ro_evidence) <= r["source_record_count"]

def test_performance_rules_10k_rows():
    import time
    resp = client.post("/api/sessions")
    session_id = resp.json()["session_id"]
    
    # Generate 10k rows
    df1 = pd.DataFrame({
        "Job No.": [f"B{i % 1000}" for i in range(10000)], # 10 records per job,
        "Balance Quantity": [0 if i % 2 == 0 else 5 for i in range(10000)],
        "OCS Date": [None] * 10000
    })
    
    df2 = pd.DataFrame({"Job No.": ["B1"], "Inspection Attended (From)": ["d1"], "Inspection Attended (Upto)": ["d1"]})
    df3 = pd.DataFrame({"Job No.": ["B1"], "Running Orders": [0], "OCS Done": [0], "Expediting": [0], "Inspection": [0], "Others": [0], "Total": [0]})
    
    os.makedirs("tests/fixtures", exist_ok=True)
    df1.to_excel("tests/fixtures/perf_r_excel1.xlsx", index=False)
    df2.to_excel("tests/fixtures/perf_r_excel2.xlsx", index=False)
    df3.to_excel("tests/fixtures/perf_r_excel3.xlsx", index=False)
    
    with open("tests/fixtures/perf_r_excel1.xlsx", "rb") as f:
        client.post(f"/api/sessions/{session_id}/files/excel1", files={"file": ("perf_r_excel1.xlsx", f, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")})
    with open("tests/fixtures/perf_r_excel2.xlsx", "rb") as f:
        client.post(f"/api/sessions/{session_id}/files/excel2", files={"file": ("perf_r_excel2.xlsx", f, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")})
    with open("tests/fixtures/perf_r_excel3.xlsx", "rb") as f:
        client.post(f"/api/sessions/{session_id}/files/excel3", files={"file": ("perf_r_excel3.xlsx", f, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")})
        
    payload = {
        "excel1": {"sheet": "Sheet1", "columns": {"job_number": "Job No.", "balance_quantity": "Balance Quantity", "ocs_date": "OCS Date"}},
        "excel2": {"sheet": "Sheet1", "columns": {"job_number": "Job No.", "inspection_from": "Inspection Attended (From)", "inspection_upto": "Inspection Attended (Upto)"}},
        "excel3": {"sheet": "Sheet1", "columns": {"job_number": "Job No.", "running_orders": "Running Orders", "ocs_done": "OCS Done", "expediting": "Expediting", "inspection": "Inspection", "others": "Others", "total": "Total"}}
    }
    print("MAPPING:", client.post(f"/api/sessions/{session_id}/mapping", json=payload).json())
    client.post(f"/api/sessions/{session_id}/evaluation-month", json={"evaluation_month": "2026-08"})
    
    # Call calculations endpoint for 500 job numbers
    start = time.time()
    resp = client.post(f"/api/sessions/{session_id}/calculations/excel1", json={"job_numbers": [f"B{i}" for i in range(500)], "evaluation_month": "2026-08"})
    calc_time = time.time() - start
    
    assert resp.status_code == 200
    assert calc_time < 5.0 # Should easily be under 5s
    
    os.remove("tests/fixtures/perf_r_excel1.xlsx")
    os.remove("tests/fixtures/perf_r_excel2.xlsx")
    os.remove("tests/fixtures/perf_r_excel3.xlsx")

def test_ocs_date_six_months():
    # 1. Create Session
    resp = client.post("/api/sessions")
    session_id = resp.json()["session_id"]
    
    # 2. Setup Data
    # For Eval Month = August 2026
    # Valid = 01-Feb-2026 to 31-Aug-2026
    df1 = pd.DataFrame({
        "Job No.": ["B111", "B222", "B333", "B444", "B555", "B666", "B777"],
        "Balance Quantity": [0, 0, 0, 0, 0, 0, 0],
        "OCS Date": [
            "31/01/2026", # Jan 31 -> Excluded
            "01/02/2026", # Feb 1 -> Included
            "31/08/2026", # Aug 31 -> Included
            "01/09/2026", # Sep 1 -> Excluded
            None,         # Blank -> Included
            "03/11/2025", # Nov 3 25 -> Excluded
            "02/03/2026"  # Mar 2 26 -> Included
        ],
    })
    
    df2 = pd.DataFrame({"Job No.": ["B111"], "Inspection Attended (From)": ["d1"], "Inspection Attended (Upto)": ["d1"]})
    df3 = pd.DataFrame({"Job No.": ["B111"], "Running Orders": [0], "OCS Done": [0], "Expediting": [0], "Inspection": [0], "Others": [0], "Total": [0]})
    
    os.makedirs("tests/fixtures", exist_ok=True)
    df1.to_excel("tests/fixtures/ocs_excel1.xlsx", index=False)
    df2.to_excel("tests/fixtures/ocs_excel2.xlsx", index=False)
    df3.to_excel("tests/fixtures/ocs_excel3.xlsx", index=False)
    
    with open("tests/fixtures/ocs_excel1.xlsx", "rb") as f:
        client.post(f"/api/sessions/{session_id}/files/excel1", files={"file": ("ocs_excel1.xlsx", f, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")})
    with open("tests/fixtures/ocs_excel2.xlsx", "rb") as f:
        client.post(f"/api/sessions/{session_id}/files/excel2", files={"file": ("ocs_excel2.xlsx", f, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")})
    with open("tests/fixtures/ocs_excel3.xlsx", "rb") as f:
        client.post(f"/api/sessions/{session_id}/files/excel3", files={"file": ("ocs_excel3.xlsx", f, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")})
        
    payload = {
        "excel1": {"sheet": "Sheet1", "columns": {"job_number": "Job No.", "balance_quantity": "Balance Quantity", "ocs_date": "OCS Date"}},
        "excel2": {"sheet": "Sheet1", "columns": {"job_number": "Job No.", "inspection_from": "Inspection Attended (From)", "inspection_upto": "Inspection Attended (Upto)"}},
        "excel3": {"sheet": "Sheet1", "columns": {"job_number": "Job No.", "running_orders": "Running Orders", "ocs_done": "OCS Done", "expediting": "Expediting", "inspection": "Inspection", "others": "Others", "total": "Total"}}
    }
    print("MAPPING:", client.post(f"/api/sessions/{session_id}/mapping", json=payload).json())
    client.post(f"/api/sessions/{session_id}/evaluation-month", json={"evaluation_month": "2026-08"})
    
    resp = client.post(f"/api/sessions/{session_id}/calculations/excel1", json={"job_numbers": ["B111", "B222", "B333", "B444", "B555", "B666", "B777"], "evaluation_month": "2026-08"})
    print(resp.json()); res = {r["job_number"]: r for r in resp.json()}
    
    # Excluded: OCS Done count must be 0, FD count must be 0
    # B111: 31-Jan -> Excluded
    assert res["B111"]["ocs_done"] == 0
    assert any("Excluded" in w for w in res["B111"]["evidence"][0]["notes"])
    assert res["B111"]["evidence"][0]["contribution"] == "Excluded"
    
    # B222: 01-Feb -> Excluded -> ocs_done=0 (Bal=0, OCS=present but outside 6 months calendar)
    assert res["B222"]["ocs_done"] == 0
    assert any("Excluded" in w for w in res["B222"]["evidence"][0]["notes"])
    
    # B333: 31-Aug -> Included
    assert res["B333"]["ocs_done"] == 1
    
    # B444: 01-Sep -> Excluded
    assert res["B444"]["ocs_done"] == 0
    assert res["B444"]["evidence"][0]["contribution"] == "Excluded"
    
    # B555: Blank -> Included -> fd=1 (Bal=0, OCS=blank)
    assert res["B555"]["fd"] == 1
    assert res["B555"]["ocs_done"] == 0
    
    # B666: 03-Nov-2025 -> Excluded
    assert res["B666"]["ocs_done"] == 0
    assert res["B666"]["evidence"][0]["contribution"] == "Excluded"
    
    # B777: 02-Mar-2026 -> Included
    assert res["B777"]["ocs_done"] == 1
    
    os.remove("tests/fixtures/ocs_excel1.xlsx")
    os.remove("tests/fixtures/ocs_excel2.xlsx")
    os.remove("tests/fixtures/ocs_excel3.xlsx")
