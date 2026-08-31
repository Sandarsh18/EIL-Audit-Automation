import pytest
from fastapi.testclient import TestClient
from app.main import app
import pandas as pd
import openpyxl
import os
from datetime import datetime

client = TestClient(app)

def setup_session_with_data():
    resp = client.post("/api/sessions")
    s_id = resp.json()["session_id"]
    
    df1 = pd.DataFrame({"Job No.": ["B224"], "Balance Quantity": [10], "OCS Date": ["2026-08-01"]})
    df2 = pd.DataFrame({"Job No.": ["B224"], "Inspection Attended (From)": [datetime(2026, 8, 1)], "Inspection Attended (Upto)": [datetime(2026, 8, 3)], "No. of Days": [3]})
    df3 = pd.DataFrame({
        "Job No": ["B224"],
        "Running Orders": [1],
        "OCS Done": [1],
        "Exp.": [10],
        "Inspn": [10],
        "Others": [0],
        "Total": [20],
        "Trailing": ["Old"]
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
        "excel3": {"sheet": "Sheet1", "columns": {"job_number": "Job No", "running_orders": "Running Orders", "ocs_done": "OCS Done", "expediting": "Exp.", "inspection": "Inspn", "others": "Others", "total": "Total"}}
    }
    client.post(f"/api/sessions/{s_id}/mapping", json=payload)
    client.post(f"/api/sessions/{s_id}/evaluation-month", json={"evaluation_month": "2026-08"})
    client.post(f"/api/sessions/{s_id}/calculations/combined", json={"job_numbers": ["B224"], "evaluation_month": "2026-08"})
    
    client.post(f"/api/sessions/{s_id}/jobs/B224/approve", json={"acknowledge_warnings": True})
    
    return s_id

def verify_output(s_id, custom_columns, expected_sequence):
    payload = {"job_numbers": ["B224"]}
    if custom_columns is not None:
        payload["custom_columns"] = custom_columns
        
    resp_gen = client.post(f"/api/sessions/{s_id}/output/generate", json=payload)
    assert resp_gen.status_code == 200
    gen_data = resp_gen.json()
    output_id = gen_data["output_id"]
    
    resp_dl = client.get(f"/api/sessions/{s_id}/output/download?output_id={output_id}")
    out_path = f"tests/fixtures/downloaded_{s_id}_{len(custom_columns or [])}.xlsx"
    with open(out_path, "wb") as f:
        f.write(resp_dl.content)
        
    wb = openpyxl.load_workbook(out_path, data_only=True)
    sheet = wb.active
    headers = [str(cell.value) for cell in sheet[1] if cell.value]
    
    # Check subsequence
    for i in range(len(headers) - len(expected_sequence) + 1):
        if headers[i:i+len(expected_sequence)] == expected_sequence:
            return True
            
    # If not found, print headers for debug
    assert False, f"Expected sequence {expected_sequence} not found in headers {headers}"

def test_layout_no_custom_columns():
    s_id = setup_session_with_data()
    # No custom columns sent. Because there is no meeting data (meeting was None), Meeting won't be injected.
    # Wait, the prompt says Expected: OTHERS | MEETING | TOTAL. Let's force a meeting override so it exists.
    client.post(f"/api/sessions/{s_id}/jobs/B224/review", json={"meeting": 1})
    client.post(f"/api/sessions/{s_id}/jobs/B224/approve", json={"acknowledge_warnings": True})
    
    verify_output(s_id, None, ["Others", "Meeting", "Total", "Trailing"])

def test_layout_one_custom_column():
    s_id = setup_session_with_data()
    client.post(f"/api/sessions/{s_id}/jobs/B224/review", json={"meeting": 1})
    client.post(f"/api/sessions/{s_id}/jobs/B224/approve", json={"acknowledge_warnings": True})
    
    verify_output(s_id, [{"heading": "Price", "data": {"B224": 500}}], ["Others", "Meeting", "Price", "Total", "Trailing"])

def test_layout_multiple_custom_columns():
    s_id = setup_session_with_data()
    client.post(f"/api/sessions/{s_id}/jobs/B224/review", json={"meeting": 1})
    client.post(f"/api/sessions/{s_id}/jobs/B224/approve", json={"acknowledge_warnings": True})
    
    verify_output(s_id, [
        {"heading": "Price", "data": {"B224": 500}},
        {"heading": "Remarks", "data": {"B224": "Test"}},
        {"heading": "Quantity", "data": {"B224": 2}}
    ], ["Others", "Meeting", "Price", "Remarks", "Quantity", "Total", "Trailing"])
