import os
import json
import uuid
import datetime
import shutil
from typing import List, Optional
from app.config import PROJECTS_DIR, UPLOAD_DIR
from app.schemas.project import ProjectSummary, SaveProjectRequest
from app.schemas.export import SessionExport

class ProjectService:
    @staticmethod
    def _read_project_data(path: str, item_id: str, is_legacy: bool = False) -> Optional[ProjectSummary]:
        try:
            with open(path, "r") as f:
                data = json.load(f)
                
                # Fallback parsing just in case it's an old raw session export without wrapper
                name = data.get("name", item_id)
                last_modified = data.get("last_modified", "")
                
                session = data.get("session_export", {}).get("session", {})
                eval_month = session.get("evaluation_month")
                
                # Fetch original filenames if we stored them, otherwise defaults
                frontend_state = data.get("session_export", {}).get("frontend_state", {})
                e1 = frontend_state.get("excel1Meta", {}).get("filename")
                e2 = frontend_state.get("excel2Meta", {}).get("filename")
                e3 = frontend_state.get("excel3Meta", {}).get("filename")
                
                return ProjectSummary(
                    project_id=item_id,
                    name=name,
                    last_modified=last_modified,
                    evaluation_month=eval_month,
                    excel1_filename=e1,
                    excel2_filename=e2,
                    excel3_filename=e3
                )
        except Exception as e:
            print(f"Error reading project {path}: {e}")
            return None

    @staticmethod
    def get_projects() -> List[ProjectSummary]:
        projects = []
        if not os.path.exists(PROJECTS_DIR):
            return projects
            
        for item in os.listdir(PROJECTS_DIR):
            item_path = os.path.join(PROJECTS_DIR, item)
            if item.endswith(".json"):
                # Legacy project
                project_id = item.replace(".json", "")
                summary = ProjectService._read_project_data(item_path, project_id, is_legacy=True)
                if summary:
                    projects.append(summary)
            elif os.path.isdir(item_path):
                # New project directory
                project_json_path = os.path.join(item_path, "project.json")
                if os.path.exists(project_json_path):
                    summary = ProjectService._read_project_data(project_json_path, item)
                    if summary:
                        projects.append(summary)
                        
        # Sort by last_modified descending
        projects.sort(key=lambda x: x.last_modified, reverse=True)
        return projects

    @staticmethod
    def save_project(request: SaveProjectRequest) -> ProjectSummary:
        # Check if project with name already exists. If yes, replace it?
        # The prompt says: "If the project name already exists, provide a clear choice" which is handled in frontend.
        # But we also might be saving an existing project explicitly. Let's just create a new UUID for safety if we're creating new,
        # but the request doesn't provide a project_id. If we want to replace, frontend can pass the same project_id, or
        # we just let it create a new ID and if the name matches, we can overwrite or just keep duplicates. 
        # Wait, the prompt says "handle duplicate project names safely... if project name already exists... [Replace]".
        # Since the frontend only sends SaveProjectRequest(name: str, session_export: SessionExport), 
        # we can look for an existing project by name and if it exists, maybe delete it or overwrite its dir.
        
        existing_project_id = None
        if os.path.exists(PROJECTS_DIR):
            for item in os.listdir(PROJECTS_DIR):
                item_path = os.path.join(PROJECTS_DIR, item)
                if item.endswith(".json"):
                    try:
                        with open(item_path, "r") as f:
                            data = json.load(f)
                            if data.get("name") == request.name:
                                existing_project_id = item.replace(".json", "")
                                break
                    except:
                        pass
                elif os.path.isdir(item_path):
                    project_json_path = os.path.join(item_path, "project.json")
                    if os.path.exists(project_json_path):
                        try:
                            with open(project_json_path, "r") as f:
                                data = json.load(f)
                                if data.get("name") == request.name:
                                    existing_project_id = item
                                    break
                        except:
                            pass

        project_id = existing_project_id or str(uuid.uuid4())
        
        project_dir = os.path.join(PROJECTS_DIR, project_id)
        os.makedirs(project_dir, exist_ok=True)
        
        files_dir = os.path.join(project_dir, "files")
        os.makedirs(files_dir, exist_ok=True)
        
        # Copy files to project directory
        session = request.session_export.session
        file_ids = [session.excel1_file_id, session.excel2_file_id, session.excel3_file_id]
        
        for f_id in file_ids:
            if f_id:
                src = os.path.join(UPLOAD_DIR, f"{f_id}.xlsx")
                dst = os.path.join(files_dir, f"{f_id}.xlsx")
                if os.path.exists(src):
                    shutil.copy2(src, dst)
                    
        if session.generated_output_path and os.path.exists(session.generated_output_path):
            filename = os.path.basename(session.generated_output_path)
            dst = os.path.join(files_dir, filename)
            shutil.copy2(session.generated_output_path, dst)
            # Update path in session to reflect relative/new location if necessary? 
            # We'll just copy it back on load, or we can restore it to UPLOAD_DIR.
        
        last_mod = datetime.datetime.now().isoformat()
        
        payload = {
            "project_id": project_id,
            "name": request.name,
            "last_modified": last_mod,
            "session_export": request.session_export.model_dump()
        }
        
        path = os.path.join(project_dir, "project.json")
        with open(path, "w") as f:
            json.dump(payload, f)
            
        # Clean up legacy .json if we overwrote it
        legacy_path = os.path.join(PROJECTS_DIR, f"{project_id}.json")
        if os.path.exists(legacy_path):
            os.remove(legacy_path)
            
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
        project_dir = os.path.join(PROJECTS_DIR, project_id)
        legacy_path = os.path.join(PROJECTS_DIR, f"{project_id}.json")
        
        if os.path.isdir(project_dir):
            path = os.path.join(project_dir, "project.json")
            if not os.path.exists(path):
                raise FileNotFoundError(f"Project {project_id} not found")
                
            # Restore files
            files_dir = os.path.join(project_dir, "files")
            if os.path.exists(files_dir):
                for f in os.listdir(files_dir):
                    src = os.path.join(files_dir, f)
                    dst = os.path.join(UPLOAD_DIR, f)
                    shutil.copy2(src, dst)
                    # For generated output, the path in session.generated_output_path usually points to a working dir.
                    # We might want to copy it to the exact path it expects.
            
            with open(path, "r") as f:
                data = json.load(f)
                
            session_export = SessionExport(**data.get("session_export", {}))
            
            # Ensure generated output path is correctly restored if it existed
            # It expects it in os.path.join(os.path.dirname(UPLOAD_DIR), "working", session_id)
            if session_export.session.generated_output_path:
                filename = os.path.basename(session_export.session.generated_output_path)
                src = os.path.join(files_dir, filename)
                dst = session_export.session.generated_output_path
                if os.path.exists(src):
                    os.makedirs(os.path.dirname(dst), exist_ok=True)
                    shutil.copy2(src, dst)
                    
            return session_export
            
        elif os.path.exists(legacy_path):
            with open(legacy_path, "r") as f:
                data = json.load(f)
            return SessionExport(**data.get("session_export", {}))
            
        raise FileNotFoundError(f"Project {project_id} not found")

    @staticmethod
    def delete_project(project_id: str) -> None:
        project_dir = os.path.join(PROJECTS_DIR, project_id)
        legacy_path = os.path.join(PROJECTS_DIR, f"{project_id}.json")
        
        if os.path.exists(legacy_path):
            os.remove(legacy_path)
            
        if os.path.isdir(project_dir):
            shutil.rmtree(project_dir)
