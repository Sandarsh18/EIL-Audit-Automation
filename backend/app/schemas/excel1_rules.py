from pydantic import BaseModel
from typing import List, Optional, Any

class CalculationRequest(BaseModel):
    job_numbers: List[str]
    evaluation_month: str

class RecordEvidence(BaseModel):
    source_row: Optional[int] = None
    date_field_used: Optional[str] = None
    balance_quantity_raw: Any
    ocs_date_raw: Any
    balance_quantity_parsed: Optional[float]
    ocs_date_parsed: Optional[str]
    is_balance_blank: bool
    is_ocs_blank: bool
    is_balance_invalid: bool
    is_ocs_invalid: bool
    contribution: str # "FD", "Running Order", "None"
    notes: List[str]
    eligibility: str # "INCLUDED", "EXCLUDED", "BLANK_OCS"
    exclusion_reason: Optional[str] = None

class JobCalculationResult(BaseModel):
    job_number: str
    source_record_count: int
    eligible_record_count: int
    excluded_record_count: int
    fd: int
    running_orders: int
    ocs_done: int
    warnings: List[str]
    status: str # "COMPLETE", "WARNING", "ERROR"
    evidence: List[RecordEvidence]

