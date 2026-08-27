from pydantic import BaseModel, ConfigDict
from typing import Optional, Dict, Any
from .mapping import MappingConfiguration

class SessionCreate(BaseModel):
    pass

class Session(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    session_id: str
    excel1_file_id: Optional[str] = None
    excel2_file_id: Optional[str] = None
    excel3_file_id: Optional[str] = None
    created_at: str
    mapping: Optional[MappingConfiguration] = None
    evaluation_month: Optional[str] = None
    generated_output_path: Optional[str] = None
    generated_output_id: Optional[str] = None

