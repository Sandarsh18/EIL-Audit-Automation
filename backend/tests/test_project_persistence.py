import pytest
import os
import shutil
from fastapi.testclient import TestClient
from app.main import app
from app.config import PROJECTS_DIR, UPLOAD_DIR
from app.services.session_service import SessionService
from app.services.project_service import ProjectService

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_teardown():
    # Setup test env
    if os.path.exists(PROJECTS_DIR):
        shutil.rmtree(PROJECTS_DIR)
    os.makedirs(PROJECTS_DIR, exist_ok=True)
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    
    yield
    
    # Teardown
    if os.path.exists(PROJECTS_DIR):
        shutil.rmtree(PROJECTS_DIR)
    
def test_save_and_delete_project():
    # 1. Create a session
    resp = client.post("/api/sessions")
    session_id = resp.json()["session_id"]
    
    # 2. Mock a file in UPLOAD_DIR
    fake_file_id = "fake_file_123"
    fake_file_path = os.path.join(UPLOAD_DIR, f"{fake_file_id}.xlsx")
    with open(fake_file_path, "w") as f:
        f.write("mock excel content")
        
    # Set the file in session
    session = SessionService.get_session(session_id)
    session.excel3_file_id = fake_file_id
    
    # 3. Export session state
    export_resp = client.get(f"/api/sessions/{session_id}/export")
    export_data = export_resp.json()
    
    # 4. Save Project
    save_payload = {
        "name": "Test Project 1",
        "session_export": export_data
    }
    save_resp = client.post("/api/projects", json=save_payload)
    assert save_resp.status_code == 200
    project_id = save_resp.json()["project_id"]
    
    # 5. Verify it was physically saved
    project_dir = os.path.join(PROJECTS_DIR, project_id)
    assert os.path.exists(project_dir)
    assert os.path.exists(os.path.join(project_dir, "files", f"{fake_file_id}.xlsx"))
    
    # 6. Delete Project
    del_resp = client.delete(f"/api/projects/{project_id}")
    assert del_resp.status_code == 200
    assert not os.path.exists(project_dir)
    
    # Clean up fake file
    if os.path.exists(fake_file_path):
        os.remove(fake_file_path)

def test_missing_excel3_throws_400():
    # To test output plan missing Excel 3
    resp = client.post("/api/sessions")
    session_id = resp.json()["session_id"]
    
    # Set dummy file id
    session = SessionService.get_session(session_id)
    session.excel3_file_id = "missing_123"
    
    # Try to generate change plan
    resp = client.post(f"/api/sessions/{session_id}/output/plan", json={
        "job_numbers": ["B378"],
        "evaluation_month": "2026-08"
    })
    
    # Should be 400, not 500
    assert resp.status_code == 400
    assert "Original Excel 3 not found on disk" in resp.json()["detail"]
