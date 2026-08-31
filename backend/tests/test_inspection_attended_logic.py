import pytest
from fastapi.testclient import TestClient
from app.main import app
import pandas as pd
import openpyxl
import os
from datetime import datetime

client = TestClient(app)

def test_inspection_attended_calculation_isolation():
    resp = client.post("/api/sessions")
    s_id = resp.json()["session_id"]
    
    df1 = pd.DataFrame({
        "Job No.": ["B269"],
        "Balance Quantity": [10],
        "OCS Date": ["2026-08-01"],
    })
    
    # CRITICAL: Conflicting columns
    # Inspection Date is 1-Aug to 2-Aug (1 day duration)
    # Inspection Attended is 10-Aug to 12-Aug (2 days duration)
    df2 = pd.DataFrame({
        "Job No.": ["B269"],
        "Inspection Date (From)": [datetime(2026, 8, 1)],
        "Inspection Date (Upto)": [datetime(2026, 8, 2)],
        "Inspection Attended (From)": [datetime(2026, 8, 10)],
        "Inspection Attended (Upto)": [datetime(2026, 8, 12)],
        "No. of Days": [2],
    })
    
    df3 = pd.DataFrame({
        "Job No": ["B269"],
        "No. of Running orders": [1],
        "Orders for FD f/up": [0],
        "OCS done": [1],
        "Exp.": [10],
        "Inspn": [999], # old legacy data, should be replaced,
        "Others": [0],
        "Total": [20],
    })

    os.makedirs("tests/fixtures", exist_ok=True)
    df1.to_excel("tests/fixtures/tmp2_e1.xlsx", index=False)
    df2.to_excel("tests/fixtures/tmp2_e2.xlsx", index=False)
    df3.to_excel("tests/fixtures/tmp2_e3.xlsx", index=False)
    
    with open("tests/fixtures/tmp2_e1.xlsx", "rb") as f:
        client.post(f"/api/sessions/{s_id}/files/excel1", files={"file": ("tmp2_e1.xlsx", f, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")})
    with open("tests/fixtures/tmp2_e2.xlsx", "rb") as f:
        client.post(f"/api/sessions/{s_id}/files/excel2", files={"file": ("tmp2_e2.xlsx", f, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")})
    with open("tests/fixtures/tmp2_e3.xlsx", "rb") as f:
        client.post(f"/api/sessions/{s_id}/files/excel3", files={"file": ("tmp2_e3.xlsx", f, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")})

    # The backend excel_service should have automatically picked "Inspection Attended (From)"
    # We will explicitly map it here mimicking the frontend behavior with the new regex.
    payload = {
        "excel1": {"sheet": "Sheet1", "columns": {"job_number": "Job No.", "balance_quantity": "Balance Quantity", "ocs_date": "OCS Date"}},
        "excel2": {"sheet": "Sheet1", "columns": {"job_number": "Job No.", "inspection_from": "Inspection Attended (From)", "inspection_upto": "Inspection Attended (Upto)"}},
        "excel3": {"sheet": "Sheet1", "columns": {"job_number": "Job No", "running_orders": "No. of Running orders", "orders_for_fd": "Orders for FD f/up", "ocs_done": "OCS done", "expediting": "Exp.", "inspection": "Inspn", "others": "Others", "total": "Total"}}
    }
    client.post(f"/api/sessions/{s_id}/mapping", json=payload)
    client.post(f"/api/sessions/{s_id}/evaluation-month", json={"evaluation_month": "2026-08"})
    
    calc_resp = client.post(f"/api/sessions/{s_id}/calculations/combined", json={"job_numbers": ["B269"], "evaluation_month": "2026-08"})
    assert calc_resp.status_code == 200
    b269_calc = calc_resp.json()[0]
    
    # Assert it used Attended (12 - 10 = 2), not Date (2 - 1 = 1)
    assert b269_calc["inspection"] == 24.0
    
    client.post(f"/api/sessions/{s_id}/jobs/B269/approve", json={"acknowledge_warnings": True})
    
    resp_gen = client.post(f"/api/sessions/{s_id}/output/generate", json={"job_numbers": ["B269"], "evaluation_month": "2026-08"})
    assert resp_gen.status_code == 200
    output_id = resp_gen.json()["output_id"]
    
    resp_dl = client.get(f"/api/sessions/{s_id}/output/download?output_id={output_id}")
    assert resp_dl.status_code == 200
    
    out_path = f"tests/fixtures/downloaded_att_{s_id}.xlsx"
    with open(out_path, "wb") as f:
        f.write(resp_dl.content)
        
    wb = openpyxl.load_workbook(out_path, data_only=True)
    sheet = wb["ConsolidatedMHrequirementAug26"]
    
    headers = [str(cell.value) for cell in sheet[1]]
    data = list(sheet.iter_rows(min_row=2, values_only=True))
    
    b269_row = data[0]
    insp_idx = headers.index("Inspn")
    
    # Assert output workbook has the correct value calculated from Attended
    assert b269_row[insp_idx] == 24
    
    wb.close()
    
    # Cleanup
    os.remove("tests/fixtures/tmp2_e1.xlsx")
    os.remove("tests/fixtures/tmp2_e2.xlsx")
    os.remove("tests/fixtures/tmp2_e3.xlsx")
    os.remove(out_path)
