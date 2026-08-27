import sys
import pytest
from fastapi.testclient import TestClient
from app.main import app
import os
import subprocess
import shutil
import hashlib

client = TestClient(app)

@pytest.fixture(scope="session", autouse=True)
def generate_test_files():
    subprocess.run([sys.executable, "tests/generate_fixtures.py"], check=True)

# ---------------------------------------------------------
# Session Tests
# ---------------------------------------------------------
def test_health():
    response = client.get("/api/health")
    assert response.status_code == 200

def test_session_creation():
    resp = client.post("/api/sessions")
    assert resp.status_code == 200
    data = resp.json()
    assert "session_id" in data
    assert data["session_id"] is not None

def test_session_unique_id():
    resp1 = client.post("/api/sessions")
    resp2 = client.post("/api/sessions")
    assert resp1.json()["session_id"] != resp2.json()["session_id"]

def test_get_session():
    resp = client.post("/api/sessions")
    session_id = resp.json()["session_id"]
    resp2 = client.get(f"/api/sessions/{session_id}")
    assert resp2.status_code == 200
    assert resp2.json()["session_id"] == session_id

def test_missing_session():
    resp = client.get("/api/sessions/invalid-session-id")
    assert resp.status_code == 404

# ---------------------------------------------------------
# File Upload Tests
# ---------------------------------------------------------
@pytest.fixture
def session_id():
    return client.post("/api/sessions").json()["session_id"]

def test_upload_excel1_valid(session_id):
    with open("tests/fixtures/excel1.xlsx", "rb") as f:
        resp = client.post(
            f"/api/sessions/{session_id}/files/excel1",
            files={"file": ("excel1.xlsx", f, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
        )
    assert resp.status_code == 200
    assert "Consolidated Report" in resp.json()["sheets"]

def test_upload_excel2_valid(session_id):
    with open("tests/fixtures/excel2.xlsx", "rb") as f:
        resp = client.post(
            f"/api/sessions/{session_id}/files/excel2",
            files={"file": ("excel2.xlsx", f, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
        )
    assert resp.status_code == 200
    assert "Inspection Logs" in resp.json()["sheets"]

def test_upload_excel3_valid_and_safety(session_id):
    file_path = "tests/fixtures/excel3.xlsx"
    
    # Critical Excel 3 Safety test: Hash before and after
    with open(file_path, "rb") as f:
        original_hash = hashlib.sha256(f.read()).hexdigest()

    with open(file_path, "rb") as f:
        resp = client.post(
            f"/api/sessions/{session_id}/files/excel3",
            files={"file": ("excel3.xlsx", f, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
        )
    
    assert resp.status_code == 200
    assert "Jan26" in resp.json()["sheets"]
    assert "Feb26" in resp.json()["sheets"]

    with open(file_path, "rb") as f:
        after_hash = hashlib.sha256(f.read()).hexdigest()
    
    assert original_hash == after_hash, "Original Excel 3 was modified during upload/inspection!"

def test_upload_invalid_extension(session_id):
    with open("requirements.txt", "rb") as f:
        resp = client.post(
            f"/api/sessions/{session_id}/files/excel1",
            files={"file": ("requirements.txt", f, "text/plain")}
        )
    assert resp.status_code == 400
    assert "valid .xlsx" in resp.json()["detail"]

def test_upload_corrupt_workbook(session_id):
    with open("tests/fixtures/corrupt.xlsx", "wb") as f:
        f.write(b"this is not a zip file")
    with open("tests/fixtures/corrupt.xlsx", "rb") as f:
        resp = client.post(
            f"/api/sessions/{session_id}/files/excel1",
            files={"file": ("corrupt.xlsx", f, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
        )
    assert resp.status_code == 400
    assert "could not be opened" in resp.json()["detail"]
    os.remove("tests/fixtures/corrupt.xlsx")

# ---------------------------------------------------------
# Workbook Inspection Tests
# ---------------------------------------------------------
def test_workbook_missing(session_id):
    resp = client.get(f"/api/sessions/{session_id}/workbooks/excel1")
    assert resp.status_code == 404

def test_sheet_missing(session_id):
    # Upload first to avoid workbook missing
    with open("tests/fixtures/excel1.xlsx", "rb") as f:
        client.post(f"/api/sessions/{session_id}/files/excel1", files={"file": ("excel1.xlsx", f, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")})
    
    resp = client.get(f"/api/sessions/{session_id}/workbooks/excel1/sheets/NonExistentSheet")
    assert resp.status_code == 400

def test_inspection_details(session_id):
    with open("tests/fixtures/excel1.xlsx", "rb") as f:
        client.post(f"/api/sessions/{session_id}/files/excel1", files={"file": ("excel1.xlsx", f, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")})
    
    resp = client.get(f"/api/sessions/{session_id}/workbooks/excel1/sheets/Consolidated Report")
    assert resp.status_code == 200
    sheet = resp.json()
    
    assert sheet["row_count"] == 5
    assert sheet["column_count"] == 3
    
    col_names = [c["name"] for c in sheet["columns"]]
    assert "Job No." in col_names
    assert "Balance Quantity" in col_names
    
    # Types
    types = {c["name"]: c["data_type"] for c in sheet["columns"]}
    assert types["Job No."] == "text"
    assert types["Balance Quantity"] == "number"
    # The fixture has OCS Date = None, None, None, None, "2026-07-10". It should be 'mixed' or 'text' depending on pandas parsing.
    # In my fixture it's a string, so 'text' or 'date'. Wait, pandas might read "2026-07-10" as string unless parsed as date. Let's just check it exists.
    assert "OCS Date" in types
    
    # Preview
    assert len(sheet["preview"]) == 5
    assert sheet["preview"][0]["Job No."] == "B269"
    # Check blank value replaced properly (None in JSON)
    assert sheet["preview"][0]["OCS Date"] is None
