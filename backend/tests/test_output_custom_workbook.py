import pytest
from fastapi.testclient import TestClient
from app.main import app
import pandas as pd
import openpyxl
import os
import shutil
from datetime import datetime

client = TestClient(app)

def test_output_custom_workbook():
    resp = client.post("/api/sessions")
    s_id = resp.json()["session_id"]
    
    df1 = pd.DataFrame({
        "Job No.": ["B224", "B269", "B378"],
        "Balance Quantity": [10, 10, 10],
        "OCS Date": ["2026-08-01", "2026-08-01", "2026-08-01"],
    })
    
    df2 = pd.DataFrame({
        "Job No.": ["B224", "B269", "B378"],
        "Inspection Attended (From)": [datetime(2026, 8, 1), datetime(2026, 8, 10), datetime(2026, 8, 15)],
        "Inspection Attended (Upto)": [datetime(2026, 8, 3), datetime(2026, 8, 12), datetime(2026, 8, 18)],
        "No. of Days": [3, 2, 3] 
    })
    
    # Let's create an Excel 3 file with all 14 columns
    df3 = pd.DataFrame({
        "Job No": ["B224", "B269", "B378", "EXCLUDE1"],
        "No. of Running orders": [1, 1, 1, 1],
        "Orders for FD f/up": [0, 0, 0, 0],
        "OCS done": [1, 1, 1, 1],
        "Exp.": [10, 10, 10, 10],
        "Inspn": [10, 10, 10, 10],
        "Others": [0, 0, 0, 0],
        "Total": [20, 20, 20, 20],
        "*Others/ Remarks": ["Old", "Old", "Old", "Old"],
        "Insp/ Project Coordinators": ["Old", "Old", "Old", "Old"],
        "MH available as on": ["Old", "Old", "Old", "Old"],
        "MH to be released for Aug'26": ["Old", "Old", "Old", "Old"],
        "Allotted": ["Old", "Old", "Old", "Old"],
        "8518 reqd": ["Old", "Old", "Old", "Old"],
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
        "excel3": {"sheet": "Sheet1", "columns": {"job_number": "Job No", "running_orders": "No. of Running orders", "orders_for_fd": "Orders for FD f/up", "ocs_done": "OCS done", "expediting": "Exp.", "inspection": "Inspn", "others": "Others", "total": "Total"}}
    }
    client.post(f"/api/sessions/{s_id}/mapping", json=payload)
    client.post(f"/api/sessions/{s_id}/evaluation-month", json={"evaluation_month": "2026-08"})
    client.post(f"/api/sessions/{s_id}/calculations/combined", json={"job_numbers": ["B224", "B269", "B378"], "evaluation_month": "2026-08"})
    
    # Approve them
    client.post(f"/api/sessions/{s_id}/jobs/B224/approve", json={"acknowledge_warnings": True})
    client.post(f"/api/sessions/{s_id}/jobs/B269/approve", json={"acknowledge_warnings": True})
    client.post(f"/api/sessions/{s_id}/jobs/B378/approve", json={"acknowledge_warnings": True})
    
    # Generate output
    resp_gen = client.post(f"/api/sessions/{s_id}/output/generate", json={"job_numbers": ["B224", "B269", "B378"]})
    assert resp_gen.status_code == 200
    gen_data = resp_gen.json()
    assert gen_data["jobs_processed"] == 3
    output_id = gen_data["output_id"]
    
    # Download output
    resp_dl = client.get(f"/api/sessions/{s_id}/output/download?output_id={output_id}")
    assert resp_dl.status_code == 200
    
    out_path = f"tests/fixtures/downloaded_{s_id}.xlsx"
    with open(out_path, "wb") as f:
        f.write(resp_dl.content)
        
    wb = openpyxl.load_workbook(out_path, data_only=True)
    sheet = wb.active
    
    # Assert headers exist
    headers = [str(cell.value) for cell in sheet[1]]
    assert "Job No" in headers
    assert "*Others/ Remarks" in headers
    assert "MH available as on" in headers
    
    # Read rows
    data = list(sheet.iter_rows(min_row=2, values_only=True))
    assert len(data) == 5 # 3 jobs + Leave + Total
    
    jobs_in_out = [row[0] for row in data[:3]]
    assert jobs_in_out == ["B224", "B269", "B378"] # Exclude 'EXCLUDE1'
    
    assert data[3][0] == "Leave"
    assert data[4][0] == "Total"
    
    # Check blank columns for job rows
    others_idx = headers.index("*Others/ Remarks")
    for row in data[:3]:
        assert row[others_idx] is None # Must be blank, not "Old"
        
    # Check calculated values
    b269_row = data[1]
    insp_idx = headers.index("Inspn")
    assert b269_row[insp_idx] == 3 # 2026-08 10 to 12 is 3 days
    
    wb.close()
    
    # Cleanup
    os.remove("tests/fixtures/tmp_e1.xlsx")
    os.remove("tests/fixtures/tmp_e2.xlsx")
    os.remove("tests/fixtures/tmp_e3.xlsx")
    os.remove(out_path)
