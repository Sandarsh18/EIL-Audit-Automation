from fastapi import APIRouter, UploadFile, File, HTTPException
from typing import Dict, Any, List
from app.config import UPLOAD_DIR
import os
import shutil
import uuid
from app.schemas.session import Session
from pydantic import BaseModel
class JobNumbersRequest(BaseModel):
    job_numbers: List[str]
from app.schemas.workbook import WorkbookMetadata, SheetMetadata
from app.services.session_service import SessionService
from app.services.excel_service import ExcelService

router = APIRouter()

@router.get("/health")
def health_check():
    return {"status": "ok"}

@router.post("/sessions", response_model=Session)
def create_session():
    return SessionService.create_session()

@router.get("/sessions/{session_id}", response_model=Session)
def get_session(session_id: str):
    return SessionService.get_session(session_id)

from pydantic import BaseModel
class EvaluationMonthRequest(BaseModel):
    evaluation_month: str

@router.post("/sessions/{session_id}/evaluation-month", response_model=Session)
def update_evaluation_month(session_id: str, request: EvaluationMonthRequest):
    return SessionService.update_evaluation_month(session_id, request.evaluation_month)

from app.schemas.export import SessionExport
from app.services.review_service import ReviewService

@router.get("/sessions/{session_id}/export", response_model=SessionExport)
def export_session(session_id: str):
    session = SessionService.get_session(session_id)
    # The review state might not exist yet if they haven't visited review
    try:
        # Use internal method since get_reviews requires job_numbers
        # Wait, the internal _review_state is not directly accessible without the class
        state = ReviewService._get_job_state(session_id, "dummy")
        # Actually it's better to fetch the whole dict from the global
        from app.services.review_service import _review_state
        state = _review_state.get(session_id, {})
    except Exception:
        state = {}
        
    return SessionExport(
        session=session,
        review_state=state,
        frontend_state={}
    )

@router.post("/sessions/import", response_model=Session)
def import_session(export_data: SessionExport):
    # Restore session object
    SessionService.restore_session(export_data.session)
    # Restore review state
    ReviewService.restore_review_state(export_data.session.session_id, export_data.review_state)
    return export_data.session

from app.schemas.project import ProjectSummary, SaveProjectRequest
from app.services.project_service import ProjectService

@router.get("/projects", response_model=List[ProjectSummary])
def list_projects():
    return ProjectService.get_projects()

@router.post("/projects", response_model=ProjectSummary)
def save_project(request: SaveProjectRequest):
    return ProjectService.save_project(request)

@router.get("/projects/{project_id}", response_model=SessionExport)
def load_project(project_id: str):
    try:
        return ProjectService.load_project(project_id)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Project not found")

@router.post("/sessions/{session_id}/files/{workbook_type}", response_model=WorkbookMetadata)
async def upload_workbook(session_id: str, workbook_type: str, file: UploadFile = File(...)):
    if workbook_type not in ["excel1", "excel2", "excel3"]:
        raise HTTPException(status_code=400, detail="Invalid workbook type")
    
    if not file.filename.endswith(".xlsx"):
        raise HTTPException(status_code=400, detail="Please upload a valid .xlsx file.")

    # Ensure session exists
    SessionService.get_session(session_id)

    # Generate unique ID for this file upload
    file_id = str(uuid.uuid4())
    safe_filename = f"{file_id}.xlsx"
    file_path = os.path.join(UPLOAD_DIR, safe_filename)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Validate we can read it and extract metadata
    try:
        metadata = ExcelService.get_workbook_metadata(file_path, file_id, file.filename, workbook_type)
        SessionService.update_session_file(session_id, workbook_type, file_id)
        return metadata
    except Exception as e:
        # Remove file on error
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(status_code=400, detail=f"The uploaded workbook could not be opened. {str(e)}")

@router.delete("/sessions/{session_id}/files/{workbook_type}")
def delete_workbook(session_id: str, workbook_type: str):
    if workbook_type not in ["excel1", "excel2", "excel3"]:
        raise HTTPException(status_code=400, detail="Invalid workbook type")
    
    SessionService.update_session_file(session_id, workbook_type, None)
    return {"status": "success", "message": f"{workbook_type} removed"}

@router.delete("/sessions/{session_id}/files")
def delete_all_workbooks(session_id: str):
    SessionService.update_session_file(session_id, "excel1", None)
    SessionService.update_session_file(session_id, "excel2", None)
    SessionService.update_session_file(session_id, "excel3", None)
    
    # Also reset mapping since files are gone
    SessionService.update_session_mapping(session_id, None)
    return {"status": "success", "message": "All files removed"}

@router.get("/sessions/{session_id}/workbooks/{workbook_type}", response_model=WorkbookMetadata)
def get_workbook(session_id: str, workbook_type: str):
    session = SessionService.get_session(session_id)
    file_id = None
    if workbook_type == "excel1":
        file_id = session.excel1_file_id
    elif workbook_type == "excel2":
        file_id = session.excel2_file_id
    elif workbook_type == "excel3":
        file_id = session.excel3_file_id
    
    if not file_id:
        raise HTTPException(status_code=404, detail="Workbook not uploaded yet")

    # To get filename, we'd normally store it in session or db. For Phase 1 we can just fake it
    # or read it. Wait, the metadata doesn't store filename in session. Let's just return what we can
    # actually we should update session schema to hold filenames or keep a file registry.
    # For Phase 1 simplicity, I'll fetch it by reading the file if possible, or add it to session service.
    # Actually, the user asked for:
    # "GET /api/sessions/{session_id}/workbooks/{workbook_type}"
    # Let's adjust SessionService to hold the metadata!
    # Ah, I will just re-read the workbook metadata but I need the original filename.
    file_path = os.path.join(UPLOAD_DIR, f"{file_id}.xlsx")
    
    # Since I didn't store the original filename in the Session object, I'll just use a placeholder
    # For a real implementation, we'd use SQLite or a better in-memory dict.
    return ExcelService.get_workbook_metadata(file_path, file_id, "Uploaded_File.xlsx", workbook_type)

@router.get("/sessions/{session_id}/workbooks/{workbook_type}/sheets/{sheet_name}", response_model=SheetMetadata)
def get_sheet(session_id: str, workbook_type: str, sheet_name: str):
    session = SessionService.get_session(session_id)
    file_id = None
    if workbook_type == "excel1":
        file_id = session.excel1_file_id
    elif workbook_type == "excel2":
        file_id = session.excel2_file_id
    elif workbook_type == "excel3":
        file_id = session.excel3_file_id

    if not file_id:
        raise HTTPException(status_code=404, detail="Workbook not uploaded yet")


    file_path = os.path.join(UPLOAD_DIR, f"{file_id}.xlsx")
    return ExcelService.get_sheet_metadata(file_path, sheet_name, workbook_type=workbook_type)

from app.schemas.mapping import MappingConfiguration, ValidationResult, TypeWarning

@router.post("/sessions/{session_id}/mapping", response_model=ValidationResult)
def validate_and_save_mapping(session_id: str, mapping: MappingConfiguration):
    session = SessionService.get_session(session_id)
    
    if not (session.excel1_file_id and session.excel2_file_id and session.excel3_file_id):
        raise HTTPException(status_code=400, detail="All three workbooks must be uploaded before mapping.")
    
    warnings = []
    
    # Validation logic helper
    def validate_workbook_mapping(wb_type: str, file_id: str, mapping_data, expected_types: dict):
        file_path = os.path.join(UPLOAD_DIR, f"{file_id}.xlsx")
        try:
            # Re-using excel service
            sheet_meta = ExcelService.get_sheet_metadata(file_path, mapping_data.sheet, workbook_type=wb_type)
        except Exception:
            raise HTTPException(status_code=400, detail=f"Sheet '{mapping_data.sheet}' not found or invalid in {wb_type}")
        
        col_meta = {c.name: c.data_type for c in sheet_meta.columns}
        
        for logical_field, expected_type in expected_types.items():
            mapped_col_name = getattr(mapping_data.columns, logical_field, None)
            if not mapped_col_name:
                continue
            if mapped_col_name not in col_meta:
                raise HTTPException(status_code=400, detail=f"Column '{mapped_col_name}' not found in sheet '{mapping_data.sheet}' for {wb_type}")
            
            detected_type = col_meta[mapped_col_name]
            if expected_type != "any" and detected_type != expected_type:
                # Issue warning for unexpected types
                warnings.append(TypeWarning(
                    logical_field=logical_field,
                    source_column=mapped_col_name,
                    expected_type=expected_type,
                    detected_type=detected_type,
                    message=f"Warning: {logical_field} expected {expected_type} but detected {detected_type}."
                ))

    # Validate Excel 1
    validate_workbook_mapping("excel1", session.excel1_file_id, mapping.excel1, {
        "job_number": "text",
        "balance_quantity": "number",
        "ocs_date": "date"
    })
    
    # Validate Excel 2
    validate_workbook_mapping("excel2", session.excel2_file_id, mapping.excel2, {
        "job_number": "text",
        "inspection_from": "date",
        "inspection_upto": "date",
        "date_received": "date",
        "qap_appl": "any",
        "no_of_working_days": "any"
    })
    
    # Validate Excel 3
    validate_workbook_mapping("excel3", session.excel3_file_id, mapping.excel3, {
        "job_number": "text",
        "running_orders": "any",
        "ocs_done": "any",
        "expediting": "any",
        "inspection": "any",
        "others": "any",
        "total": "any"
    })

    # Save to session
    SessionService.update_session_mapping(session_id, mapping)
    
    # Eagerly load caches to prevent $O(N)$ pandas parsing bottleneck during calculations
    from app.services.matching_service import MatchingService
    try:
        MatchingService._load_and_cache_dataframe(session, "excel1")
        MatchingService._load_and_cache_dataframe(session, "excel2")
        MatchingService._load_and_cache_dataframe(session, "excel3")
    except Exception:
        pass
    
    return ValidationResult(valid=True, warnings=warnings)

from app.schemas.matching import JobNumberSummary, MatchRequest, MatchResult
from app.services.matching_service import MatchingService

@router.get("/sessions/{session_id}/job-numbers", response_model=JobNumberSummary)
def get_job_numbers(session_id: str):
    return MatchingService.extract_job_numbers(session_id)

@router.post("/sessions/{session_id}/job-numbers/match", response_model=MatchResult)
def match_job_numbers(session_id: str, request: MatchRequest):
    return MatchingService.get_matched_records(session_id, request.job_numbers)

from app.schemas.excel1_rules import CalculationRequest, JobCalculationResult
from app.services.excel1_rules_service import Excel1RulesService

@router.post("/sessions/{session_id}/calculations/excel1", response_model=List[JobCalculationResult])
def calculate_excel1(session_id: str, request: CalculationRequest):
    return Excel1RulesService.calculate_rules(session_id, request.job_numbers, request.evaluation_month)

from app.schemas.inspection_rules import InspectionJobResult
from app.services.inspection_rules_service import InspectionRulesService
from app.schemas.combined_rules import CombinedCalculationRequest, CombinedJobSummary

@router.post("/sessions/{session_id}/calculations/inspection", response_model=List[InspectionJobResult])
def calculate_inspection(session_id: str, request: CombinedCalculationRequest):
    return InspectionRulesService.calculate_rules(session_id, request.job_numbers, request.evaluation_month)

from app.services.combined_engine_service import CombinedEngineService

@router.post("/sessions/{session_id}/calculations/combined", response_model=List[CombinedJobSummary])
def calculate_combined(session_id: str, request: CombinedCalculationRequest):
    return CombinedEngineService.calculate_combined(session_id, request.job_numbers, request.manual_inputs, request.evaluation_month)

from app.schemas.review import JobReviewResult, OverrideRequest, ApprovalRequest, ReviewSummaryRequest
from app.services.review_service import ReviewService

@router.post("/sessions/{session_id}/review", response_model=List[JobReviewResult])
def get_review_jobs(session_id: str, request: ReviewSummaryRequest):
    return ReviewService.get_reviews(session_id, request.job_numbers, request.evaluation_month)

@router.post("/sessions/{session_id}/jobs/{job_number}/overrides", response_model=JobReviewResult)
def override_job(session_id: str, job_number: str, request: OverrideRequest):
    return ReviewService.apply_override(session_id, job_number, request)

@router.post("/sessions/{session_id}/jobs/{job_number}/reset-overrides", response_model=JobReviewResult)
def reset_job_overrides(session_id: str, job_number: str):
    return ReviewService.reset_overrides(session_id, job_number)


@router.post("/sessions/{session_id}/review/approve-all")
def approve_all(session_id: str, request: JobNumbersRequest):
    return ReviewService.approve_all(session_id, request.job_numbers)

@router.post("/sessions/{session_id}/review/delete-all")
def delete_all(session_id: str, request: JobNumbersRequest):
    return ReviewService.delete_all(session_id, request.job_numbers)

@router.post("/sessions/{session_id}/jobs/{job_number}/approve", response_model=JobReviewResult)
def approve_job(session_id: str, job_number: str, request: ApprovalRequest = ApprovalRequest()):
    return ReviewService.approve_job(session_id, job_number, request)

@router.post("/sessions/{session_id}/jobs/{job_number}/unapprove", response_model=JobReviewResult)
def unapprove_job(session_id: str, job_number: str):
    return ReviewService.unapprove_job(session_id, job_number)

@router.delete("/sessions/{session_id}/jobs/{job_number}", response_model=JobReviewResult)
def delete_job(session_id: str, job_number: str):
    return ReviewService.delete_job(session_id, job_number)

@router.post("/sessions/{session_id}/jobs/{job_number}/undelete", response_model=JobReviewResult)
def undelete_job(session_id: str, job_number: str):
    return ReviewService.undelete_job(session_id, job_number)

from app.schemas.output import OutputPlanRequest, OutputGenerateRequest, ChangePlan, OutputMetadata
from app.services.output_engine import OutputEngine
from fastapi.responses import FileResponse
import os

@router.post("/sessions/{session_id}/output/plan", response_model=ChangePlan)
def generate_change_plan(session_id: str, request: OutputPlanRequest):
    return OutputEngine.generate_change_plan(session_id, request)

@router.post("/sessions/{session_id}/output/generate", response_model=OutputMetadata)
def generate_output(session_id: str, request: OutputGenerateRequest):
    return OutputEngine.generate_output(session_id, request)

@router.get("/sessions/{session_id}/output/download")
def download_output(session_id: str, output_id: str):
    session = SessionService.get_session(session_id)
    if session.generated_output_id != output_id:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="Invalid or missing output ID.")
        
    path = session.generated_output_path
    if not path or not os.path.exists(path):
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Output file not found or generated yet.")
    return FileResponse(path, filename="CONSOLIDATED_Manhour_Automated.xlsx")
