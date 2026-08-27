from pydantic import BaseModel
from typing import List, Optional, Any

class InspectionRecordResult(BaseModel):
    source_row: Optional[int] = None
    date_field_used: Optional[str] = None
    from_date_raw: Any
    upto_date_raw: Any
    from_date_parsed: Optional[str] # ISO string
    upto_date_parsed: Optional[str] # ISO string
    days: Optional[int]
    status: str # "VALID" or "INVALID"
    warnings: List[str]
    source_no_of_days: Optional[Any] = None
    diagnostic_match: Optional[bool] = None
    excluded_reason: Optional[str] = None
    date_received_raw: Optional[Any] = None
    date_received_parsed: Optional[str] = None
    qap_appl_raw: Optional[Any] = None
    working_days_raw: Optional[Any] = None
    others_selected_source: Optional[str] = None
    others_contribution: Optional[float] = None

class InspectionJobResult(BaseModel):
    job_number: str
    evaluation_month_str: Optional[str] = None
    records_analyzed: int
    valid_records: int
    invalid_records: int
    total_inspection_days: int
    total_others_contribution: float
    status: str # "COMPLETE", "WARNING", "ERROR"
    warnings: List[str]
    evidence: List[InspectionRecordResult]
