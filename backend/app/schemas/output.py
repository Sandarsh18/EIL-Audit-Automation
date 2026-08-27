from pydantic import BaseModel
from typing import List, Dict, Optional, Any
from enum import Enum

class ActionType(str, Enum):
    PRESERVE = "PRESERVE"
    MODIFY_VALUE = "MODIFY_VALUE"
    MODIFY_FORMULA = "MODIFY_FORMULA"
    FORMULA_OVERWRITE = "FORMULA_OVERWRITE"
    SKIP = "SKIP"
    BLOCKED = "BLOCKED"

class ChangePlanCell(BaseModel):
    session_id: str
    job_number: str
    sheet_name: str
    row_index: int
    column_index: int
    cell_address: str
    logical_field: str
    old_value: Any
    old_formula: Optional[str] = None
    new_value: Any
    new_formula: Optional[str] = None
    action: ActionType
    reason: str
    source: str
    approval_status: str
    is_formula: bool # Kept for backward compatibility
    formula_overwrite_approved: bool

class ChangePlan(BaseModel):
    cells_to_modify: List[ChangePlanCell]
    cells_unchanged: int
    blocked_jobs: List[str]
    approved_jobs_included: int
    formula_overwrites: int

class OutputMetadata(BaseModel):
    status: str
    filename: str
    output_path: str
    output_id: str
    original_sha256: str
    original_unchanged: bool
    jobs_processed: int
    jobs_blocked: int
    cells_modified: int
    unexpected_changes: int = 0
    formula_changes: int = 0
    unexpected_formula_changes: int = 0
    sheets_changed: List[str] = []

class CustomColumnData(BaseModel):
    heading: str
    data: Dict[str, Any] # mapping from job_number to value

class OutputGenerateRequest(BaseModel):
    job_numbers: List[str]
    custom_columns: Optional[List[CustomColumnData]] = None
    evaluation_month: Optional[str] = None
    
class OutputPlanRequest(BaseModel):
    job_numbers: List[str]
    evaluation_month: Optional[str] = None
