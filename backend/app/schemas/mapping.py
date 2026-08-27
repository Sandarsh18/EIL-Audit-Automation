from pydantic import BaseModel, Field
from typing import Optional

class Excel1MappingFields(BaseModel):
    job_number: str
    balance_quantity: str
    ocs_date: str

class Excel1Mapping(BaseModel):
    sheet: str
    columns: Excel1MappingFields

class Excel2MappingFields(BaseModel):
    job_number: str
    inspection_from: str
    inspection_upto: str
    date_received: str | None = None
    qap_appl: str | None = None
    no_of_working_days: str | None = None

class Excel2Mapping(BaseModel):
    sheet: str
    columns: Excel2MappingFields

class Excel3MappingFields(BaseModel):
    job_number: str
    running_orders: str
    orders_for_fd: Optional[str] = None
    ocs_done: Optional[str] = None
    expediting: str
    inspection: str
    others: str
    total: str

class Excel3Mapping(BaseModel):
    workbook_file_id: Optional[str] = None
    sheet: str
    columns: Excel3MappingFields

class MappingConfiguration(BaseModel):
    excel1: Excel1Mapping
    excel2: Excel2Mapping
    excel3: Excel3Mapping

class TypeWarning(BaseModel):
    logical_field: str
    source_column: str
    expected_type: str
    detected_type: str
    message: str

class ValidationResult(BaseModel):
    valid: bool
    warnings: list[TypeWarning] = Field(default_factory=list)
