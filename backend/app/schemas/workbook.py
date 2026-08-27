from pydantic import BaseModel
from typing import List, Any, Optional

class ColumnMetadata(BaseModel):
    name: str
    index: int
    data_type: str
    canonical: Optional[str] = None

class SheetMetadata(BaseModel):
    sheet_name: str
    row_count: int
    column_count: int
    columns: List[ColumnMetadata]
    preview: List[dict[str, Any]]

class SheetSummary(BaseModel):
    name: str
    is_candidate: bool
    schema_type: str # "modern", "legacy", "unknown"
    row_count: int
    columns: List[str]

class WorkbookMetadata(BaseModel):
    file_id: str
    workbook_type: str
    filename: str
    size: int
    sheets: List[str]
    sheet_summaries: Optional[List[SheetSummary]] = None
