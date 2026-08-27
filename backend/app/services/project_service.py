import os
import json
import uuid
import datetime
from typing import List, Optional
from app.config import PROJECTS_DIR
from app.schemas.project import ProjectSummary, SaveProjectRequest
from app.schemas.export import SessionExport

class ProjectService:
    @staticmethod
    def get_projects() -> List[ProjectSummary]:
        projects = []
        if not os.path.exists(PROJECTS_DIR):
            return projects
            
        for file in os.listdir(PROJECTS_DIR):
            if file.endswith(".json"):
                path = os.path.join(PROJECTS_DIR, file)
                try:
                    with open(path, "r") as f:
                        data = json.load(f)
                        
                        # Fallback parsing just in case it's an old raw session export without wrapper
                        name = data.get("name", file.replace(".json", ""))
                        last_modified = data.get("last_modified", "")
                        
                        session = data.get("session_export", {}).get("session", {})
                        eval_month = session.get("evaluation_month")
                        
                        # Fetch original filenames if we stored them, otherwise defaults
                        frontend_state = data.get("session_export", {}).get("frontend_state", {})
                        e1 = frontend_state.get("excel1Meta", {}).get("filename")
                        e2 = frontend_state.get("excel2Meta", {}).get("filename")
                        e3 = frontend_state.get("excel3Meta", {}).get("filename")
                        
                        projects.append(ProjectSummary(
                            project_id=file.replace(".json", ""),
                            name=name,
                            last_modified=last_modified,
                            evaluation_month=eval_month,
                            excel1_filename=e1,
                            excel2_filename=e2,
                            excel3_filename=e3
                        ))
                except Exception as e:
                    print(f"Error reading project {file}: {e}")
                    
        # Sort by last_modified descending
        projects.sort(key=lambda x: x.last_modified, reverse=True)
        return projects

    @staticmethod
    def save_project(request: SaveProjectRequest) -> ProjectSummary:
        # We can either create new or update if name matches. Let's just generate an ID.
        project_id = str(uuid.uuid4())
        path = os.path.join(PROJECTS_DIR, f"{project_id}.json")
        
        last_mod = datetime.datetime.now().isoformat()
        
        payload = {
            "project_id": project_id,
            "name": request.name,
            "last_modified": last_mod,
            "session_export": request.session_export.model_dump()
        }
        
        with open(path, "w") as f:
            json.dump(payload, f)
            
        session = request.session_export.session
        frontend = request.session_export.frontend_state or {}
        
        return ProjectSummary(
            project_id=project_id,
            name=request.name,
            last_modified=last_mod,
            evaluation_month=session.evaluation_month,
            excel1_filename=frontend.get("excel1Meta", {}).get("filename"),
            excel2_filename=frontend.get("excel2Meta", {}).get("filename"),
            excel3_filename=frontend.get("excel3Meta", {}).get("filename")
        )

    @staticmethod
    def load_project(project_id: str) -> SessionExport:
        path = os.path.join(PROJECTS_DIR, f"{project_id}.json")
        if not os.path.exists(path):
            raise FileNotFoundError(f"Project {project_id} not found")
            
        with open(path, "r") as f:
            data = json.load(f)
            
        return SessionExport(**data.get("session_export", {}))
