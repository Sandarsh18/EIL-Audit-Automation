from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from app.schemas.export import SessionExport

class ProjectSummary(BaseModel):
    project_id: str
    name: str
    last_modified: str
    evaluation_month: Optional[str] = None
    excel1_filename: Optional[str] = None
    excel2_filename: Optional[str] = None
    excel3_filename: Optional[str] = None

class SaveProjectRequest(BaseModel):
    name: str
    session_export: SessionExport
