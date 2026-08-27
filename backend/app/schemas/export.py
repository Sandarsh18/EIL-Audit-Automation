from pydantic import BaseModel
from typing import Dict, Any, List, Optional
from app.schemas.session import Session

class SessionExport(BaseModel):
    session: Session
    review_state: Dict[str, Dict[str, Any]]
    frontend_state: Optional[Dict[str, Any]] = None
