from pydantic import BaseModel
from typing import List, Dict, Any, Optional

class JobNumberOption(BaseModel):
    original_value: str
    normalized_key: str
    excel1_count: int
    excel2_count: int
    excel3_count: int
    excel1_found: bool
    excel2_found: bool
    excel3_found: bool
    intersection_status: str

class JobNumberSummary(BaseModel):
    options: List[JobNumberOption]
    total_valid_job_numbers: int
    blank_job_numbers: int

class MatchRequest(BaseModel):
    job_numbers: List[str]

class MatchResult(BaseModel):
    job_numbers: List[str]
    excel1_records: Dict[str, List[Dict[str, Any]]]
    excel2_records: Dict[str, List[Dict[str, Any]]]
    excel3_records: Dict[str, List[Dict[str, Any]]]
