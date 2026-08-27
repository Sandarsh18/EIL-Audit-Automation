import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

@pytest.fixture(scope="module")
def session_id():
    resp = client.post("/api/sessions")
    session_id = resp.json()["session_id"]

    # Upload all 3 workbooks
    with open("tests/fixtures/excel1.xlsx", "rb") as f:
        client.post(f"/api/sessions/{session_id}/files/excel1", files={"file": ("excel1.xlsx", f, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")})
    with open("tests/fixtures/excel2.xlsx", "rb") as f:
        client.post(f"/api/sessions/{session_id}/files/excel2", files={"file": ("excel2.xlsx", f, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")})
    with open("tests/fixtures/excel3.xlsx", "rb") as f:
        client.post(f"/api/sessions/{session_id}/files/excel3", files={"file": ("excel3.xlsx", f, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")})
    return session_id

def test_mapping_missing_workbooks():
    resp = client.post("/api/sessions")
    empty_session = resp.json()["session_id"]
    
    payload = {
        "excel1": {"sheet": "Consolidated Report", "columns": {"job_number": "Job No.", "balance_quantity": "Balance Quantity", "ocs_date": "OCS Date"}},
        "excel2": {"sheet": "Inspection Logs", "columns": {"job_number": "Job No.", "inspection_from": "Inspection Attended (From)", "inspection_upto": "Inspection Attended (Upto)"}},
        "excel3": {"sheet": "Jan26", "columns": {"job_number": "Job No.", "running_orders": "Running Orders", "ocs_done": "OCS Done", "expediting": "Expediting", "inspection": "Inspection", "others": "Others", "total": "Total"}}
    }
    resp = client.post(f"/api/sessions/{empty_session}/mapping", json=payload)
    assert resp.status_code == 400
    assert "All three workbooks must be uploaded" in resp.json()["detail"]

def test_valid_mapping_all(session_id):
    payload = {
        "excel1": {"sheet": "Consolidated Report", "columns": {"job_number": "Job No.", "balance_quantity": "Balance Quantity", "ocs_date": "OCS Date"}},
        "excel2": {"sheet": "Inspection Logs", "columns": {"job_number": "Job No.", "inspection_from": "Inspection Attended (From)", "inspection_upto": "Inspection Attended (Upto)"}},
        "excel3": {"sheet": "Jan26", "columns": {"job_number": "Job No.", "running_orders": "Running Orders", "ocs_done": "OCS Done", "expediting": "Expediting", "inspection": "Inspection", "others": "Others", "total": "Total"}}
    }
    resp = client.post(f"/api/sessions/{session_id}/mapping", json=payload)
    client.post(f"/api/sessions/{session_id}/evaluation-month", json={"evaluation_month": "2026-08"})
    assert resp.status_code == 200
    res = resp.json()
    assert res["valid"] is True

def test_mapping_missing_required_field_excel1(session_id):
    # Omit ocs_date
    payload = {
        "excel1": {"sheet": "Consolidated Report", "columns": {"job_number": "Job No.", "balance_quantity": "Balance Quantity"}},
        "excel2": {"sheet": "Inspection Logs", "columns": {"job_number": "Job No.", "inspection_from": "Inspection Attended (From)", "inspection_upto": "Inspection Attended (Upto)"}},
        "excel3": {"sheet": "Jan26", "columns": {"job_number": "Job No.", "running_orders": "Running Orders", "ocs_done": "OCS Done", "expediting": "Expediting", "inspection": "Inspection", "others": "Others", "total": "Total"}}
    }
    resp = client.post(f"/api/sessions/{session_id}/mapping", json=payload)
    client.post(f"/api/sessions/{session_id}/evaluation-month", json={"evaluation_month": "2026-08"})
    # Validation error from Pydantic
    assert resp.status_code == 422 

def test_mapping_nonexistent_column(session_id):
    payload = {
        "excel1": {"sheet": "Consolidated Report", "columns": {"job_number": "Job No.", "balance_quantity": "Fake Column", "ocs_date": "OCS Date"}},
        "excel2": {"sheet": "Inspection Logs", "columns": {"job_number": "Job No.", "inspection_from": "Inspection Attended (From)", "inspection_upto": "Inspection Attended (Upto)"}},
        "excel3": {"sheet": "Jan26", "columns": {"job_number": "Job No.", "running_orders": "Running Orders", "ocs_done": "OCS Done", "expediting": "Expediting", "inspection": "Inspection", "others": "Others", "total": "Total"}}
    }
    resp = client.post(f"/api/sessions/{session_id}/mapping", json=payload)
    client.post(f"/api/sessions/{session_id}/evaluation-month", json={"evaluation_month": "2026-08"})
    assert resp.status_code == 400
    assert "Fake Column" in resp.json()["detail"]

def test_mapping_nonexistent_sheet(session_id):
    payload = {
        "excel1": {"sheet": "Fake Sheet", "columns": {"job_number": "Job No.", "balance_quantity": "Balance Quantity", "ocs_date": "OCS Date"}},
        "excel2": {"sheet": "Inspection Logs", "columns": {"job_number": "Job No.", "inspection_from": "Inspection Attended (From)", "inspection_upto": "Inspection Attended (Upto)"}},
        "excel3": {"sheet": "Jan26", "columns": {"job_number": "Job No.", "running_orders": "Running Orders", "ocs_done": "OCS Done", "expediting": "Expediting", "inspection": "Inspection", "others": "Others", "total": "Total"}}
    }
    resp = client.post(f"/api/sessions/{session_id}/mapping", json=payload)
    client.post(f"/api/sessions/{session_id}/evaluation-month", json={"evaluation_month": "2026-08"})
    assert resp.status_code == 400
    assert "Fake Sheet" in resp.json()["detail"]

def test_type_warnings(session_id):
    # Mapping 'Balance Quantity' (number) to 'Job No.' (text)
    # Mapping 'Job No.' (text) to 'Balance Quantity' (number)
    payload = {
        "excel1": {"sheet": "Consolidated Report", "columns": {"job_number": "Balance Quantity", "balance_quantity": "Job No.", "ocs_date": "OCS Date"}},
        "excel2": {"sheet": "Inspection Logs", "columns": {"job_number": "Job No.", "inspection_from": "Inspection Attended (From)", "inspection_upto": "Inspection Attended (Upto)"}},
        "excel3": {"sheet": "Jan26", "columns": {"job_number": "Job No.", "running_orders": "Running Orders", "ocs_done": "OCS Done", "expediting": "Expediting", "inspection": "Inspection", "others": "Others", "total": "Total"}}
    }
    resp = client.post(f"/api/sessions/{session_id}/mapping", json=payload)
    client.post(f"/api/sessions/{session_id}/evaluation-month", json={"evaluation_month": "2026-08"})
    assert resp.status_code == 200
    res = resp.json()
    assert res["valid"] is True
    assert len(res["warnings"]) >= 2
    
    warning_fields = [w["logical_field"] for w in res["warnings"]]
    assert "job_number" in warning_fields
    assert "balance_quantity" in warning_fields
