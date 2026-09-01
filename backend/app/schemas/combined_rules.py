from pydantic import BaseModel
from typing import List, Optional, Dict, Any

class ManualInputs(BaseModel):
    fd: Optional[int] = None
    running_orders: Optional[int] = None
    ocs_done: Optional[float] = None
    expediting: Optional[float] = None
    inspection: Optional[float] = None
    others: Optional[float] = None
    meeting: Optional[float] = None

class CombinedCalculationRequest(BaseModel):
    job_numbers: List[str]
    evaluation_month: str
    manual_inputs: Optional[Dict[str, ManualInputs]] = None

class SourceLineage(BaseModel):
    workbook: str
    sheet: str
    row: Optional[int] = None
    column: Optional[str] = None
    header: str
    raw_value: Any

class CombinedJobSummary(BaseModel):
    job_number: str
    fd: int
    running_orders: int
    ocs_done: Optional[float]
    expediting: Optional[int]
    native_expediting_used: bool = False
    inspection_days: Optional[float] = None
    inspection: Optional[float]
    inspection_man_hours: Optional[float] = None
    others: Optional[float]
    meeting: Optional[float] = None
    calculated_total: Optional[float] = None
    status: str # "COMPLETE", "WARNING", "BLOCKED"
    warnings: List[str]
    evidence: List[str]
    lineage: Optional[Dict[str, SourceLineage]] = None
