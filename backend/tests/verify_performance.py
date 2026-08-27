import pytest
from fastapi.testclient import TestClient
from app.main import app
import pandas as pd
import os
import time

client = TestClient(app)

def run_combined_10k():
    resp = client.post("/api/sessions")
    session_id = resp.json()["session_id"]
    
    df1 = pd.DataFrame({"Job No.": [f"B{i % 1000}" for i in range(10000)], "Balance Quantity": [0 if i % 2 == 0 else 5 for i in range(10000)], "OCS Date": [None] * 10000})
    df2 = pd.DataFrame({"Job No.": ["B1"], "Inspection Attended (From)": ["2026-08-10"], "Inspection Attended (Upto)": ["2026-08-11"]})
    df3 = pd.DataFrame({"Job No.": ["B1"], "Running Orders": [0], "OCS Done": [0], "Expediting": [0], "Inspection": [0], "Others": [0], "Total": [0]})
    
    os.makedirs("tests/fixtures", exist_ok=True)
    df1.to_excel("tests/fixtures/vp_c_e1.xlsx", index=False)
    df2.to_excel("tests/fixtures/vp_c_e2.xlsx", index=False)
    df3.to_excel("tests/fixtures/vp_c_e3.xlsx", index=False)
    
    with open("tests/fixtures/vp_c_e1.xlsx", "rb") as f:
        client.post(f"/api/sessions/{session_id}/files/excel1", files={"file": ("vp_c_e1.xlsx", f, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")})
    with open("tests/fixtures/vp_c_e2.xlsx", "rb") as f:
        client.post(f"/api/sessions/{session_id}/files/excel2", files={"file": ("vp_c_e2.xlsx", f, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")})
    with open("tests/fixtures/vp_c_e3.xlsx", "rb") as f:
        client.post(f"/api/sessions/{session_id}/files/excel3", files={"file": ("vp_c_e3.xlsx", f, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")})
        
    payload = {
        "excel1": {"sheet": "Sheet1", "columns": {"job_number": "Job No.", "balance_quantity": "Balance Quantity", "ocs_date": "OCS Date"}},
        "excel2": {"sheet": "Sheet1", "columns": {"job_number": "Job No.", "inspection_from": "Inspection Attended (From)", "inspection_upto": "Inspection Attended (Upto)"}},
        "excel3": {"sheet": "Sheet1", "columns": {"job_number": "Job No.", "running_orders": "Running Orders", "ocs_done": "OCS Done", "expediting": "Expediting", "inspection": "Inspection", "others": "Others", "total": "Total"}}
    }
    client.post(f"/api/sessions/{session_id}/mapping", json=payload)
    client.post(f"/api/sessions/{session_id}/evaluation-month", json={"evaluation_month": "2026-08"})
    
    start = time.time()
    client.post(f"/api/sessions/{session_id}/calculations/combined", json={"job_numbers": [f"b{i}" for i in range(500)]})
    t = time.time() - start
    
    os.remove("tests/fixtures/vp_c_e1.xlsx")
    os.remove("tests/fixtures/vp_c_e2.xlsx")
    os.remove("tests/fixtures/vp_c_e3.xlsx")
    
    return t

def run_inspection_10k():
    resp = client.post("/api/sessions")
    session_id = resp.json()["session_id"]
    
    df1 = pd.DataFrame({"Job No.": ["B1"], "Balance Quantity": [5], "OCS Date": [None]})
    df2 = pd.DataFrame({"Job No.": [f"B{i % 1000}" for i in range(10000)], "Inspection Attended (From)": ["2026-08-10"] * 10000, "Inspection Attended (Upto)": ["2026-08-12"] * 10000})
    df3 = pd.DataFrame({"Job No.": ["B1"], "Running Orders": [0], "OCS Done": [0], "Expediting": [0], "Inspection": [0], "Others": [0], "Total": [0]})
    
    df1.to_excel("tests/fixtures/vp_i_e1.xlsx", index=False)
    df2.to_excel("tests/fixtures/vp_i_e2.xlsx", index=False)
    df3.to_excel("tests/fixtures/vp_i_e3.xlsx", index=False)
    
    with open("tests/fixtures/vp_i_e1.xlsx", "rb") as f:
        client.post(f"/api/sessions/{session_id}/files/excel1", files={"file": ("vp_i_e1.xlsx", f, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")})
    with open("tests/fixtures/vp_i_e2.xlsx", "rb") as f:
        client.post(f"/api/sessions/{session_id}/files/excel2", files={"file": ("vp_i_e2.xlsx", f, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")})
    with open("tests/fixtures/vp_i_e3.xlsx", "rb") as f:
        client.post(f"/api/sessions/{session_id}/files/excel3", files={"file": ("vp_i_e3.xlsx", f, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")})
        
    payload = {
        "excel1": {"sheet": "Sheet1", "columns": {"job_number": "Job No.", "balance_quantity": "Balance Quantity", "ocs_date": "OCS Date"}},
        "excel2": {"sheet": "Sheet1", "columns": {"job_number": "Job No.", "inspection_from": "Inspection Attended (From)", "inspection_upto": "Inspection Attended (Upto)"}},
        "excel3": {"sheet": "Sheet1", "columns": {"job_number": "Job No.", "running_orders": "Running Orders", "ocs_done": "OCS Done", "expediting": "Expediting", "inspection": "Inspection", "others": "Others", "total": "Total"}}
    }
    client.post(f"/api/sessions/{session_id}/mapping", json=payload)
    client.post(f"/api/sessions/{session_id}/evaluation-month", json={"evaluation_month": "2026-08"})
    
    start = time.time()
    client.post(f"/api/sessions/{session_id}/calculations/excel2", json={"job_numbers": [f"b{i}" for i in range(500)]})
    t = time.time() - start
    
    os.remove("tests/fixtures/vp_i_e1.xlsx")
    os.remove("tests/fixtures/vp_i_e2.xlsx")
    os.remove("tests/fixtures/vp_i_e3.xlsx")
    
    return t

c_runs = []
for i in range(5):
    c_runs.append(run_combined_10k())

i_runs = []
for i in range(5):
    i_runs.append(run_inspection_10k())

def stats(runs):
    return {
        "Run 1": runs[0], "Run 2": runs[1], "Run 3": runs[2], "Run 4": runs[3], "Run 5": runs[4],
        "Minimum": min(runs), "Maximum": max(runs), "Average": sum(runs)/5, "Median": sorted(runs)[2],
    }

print("COMBINED 10K ROWS PERFORMANCE STATS:")
for k,v in stats(c_runs).items():
    print(f"{k}: {v:.3f}s")
    
print("\nINSPECTION 10K ROWS PERFORMANCE STATS:")
for k,v in stats(i_runs).items():
    print(f"{k}: {v:.3f}s")
