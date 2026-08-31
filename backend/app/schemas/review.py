from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Literal

class ManualOverride(BaseModel):
    field: str
    source_value: Optional[float]
    override_value: Optional[float]
    reason: Optional[str] = None
    timestamp: str
    active: bool = True

class OverrideRequest(BaseModel):
    field: Literal["ocs_done", "others", "expediting", "meeting"]
    value: Optional[float]
    reason: Optional[str] = None

class ApprovalRequest(BaseModel):
    acknowledge_warnings: bool = False

class JobReviewResult(BaseModel):
    job_number: str
    fd: int
    running_orders: int
    ocs_done: Optional[float]
    expediting: Optional[int]
    native_expediting_used: bool = False
    inspection: Optional[int]
    others: Optional[float]
    meeting: Optional[float] = None
    calculated_total: Optional[float]
    status: Literal["DRAFT", "WARNING", "BLOCKED", "APPROVED", "DELETED"]
    warnings: List[str]
    evidence: List[str]
    overrides: Dict[str, ManualOverride]

class ReviewSummaryRequest(BaseModel):
    job_numbers: List[str]
    evaluation_month: Optional[str] = None
