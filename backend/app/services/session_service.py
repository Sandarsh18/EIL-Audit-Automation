import uuid
from datetime import datetime, timezone
from typing import Dict, Optional
from fastapi import HTTPException
from app.schemas.session import Session
from app.schemas.mapping import MappingConfiguration

# In-memory storage for Phase 1
_sessions: Dict[str, Session] = {}

# In-memory cache for DataFrames (Phase 3 performance)
import pandas as pd
_df_cache: Dict[str, Dict[str, pd.DataFrame]] = {}

class SessionService:
    @staticmethod
    def create_session() -> Session:
        session_id = str(uuid.uuid4())
        new_session = Session(
            session_id=session_id,
            created_at=datetime.now(timezone.utc).isoformat()
        )
        _sessions[session_id] = new_session
        return new_session

    @staticmethod
    def get_session(session_id: str) -> Session:
        session = _sessions.get(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        return session

    @staticmethod
    def update_session_file(session_id: str, workbook_type: str, file_id: str) -> Session:
        session = SessionService.get_session(session_id)
        if workbook_type == "excel1":
            session.excel1_file_id = file_id
        elif workbook_type == "excel2":
            session.excel2_file_id = file_id
        elif workbook_type == "excel3":
            session.excel3_file_id = file_id
        else:
            raise HTTPException(status_code=400, detail="Invalid workbook type")
        
        # Invalidate cache for this workbook
        if session_id in _df_cache and workbook_type in _df_cache[session_id]:
            del _df_cache[session_id][workbook_type]
            
        _sessions[session_id] = session
        return session

    @staticmethod
    def update_session_mapping(session_id: str, mapping: MappingConfiguration) -> Session:
        session = SessionService.get_session(session_id)
        session.mapping = mapping
        _sessions[session_id] = session
        return session
        
    @staticmethod
    def update_evaluation_month(session_id: str, month: str) -> Session:
        session = SessionService.get_session(session_id)
        session.evaluation_month = month
        _sessions[session_id] = session
        
        # Clear review state when evaluation month changes
        from app.services.review_service import _review_state
        if session_id in _review_state:
            # We don't delete it entirely, we can just clear the jobs
            _review_state[session_id] = {}
            
        return session
        
    @staticmethod
    def set_generated_output(session_id: str, path: str, output_id: str) -> Session:
        session = SessionService.get_session(session_id)
        session.generated_output_path = path
        session.generated_output_id = output_id
        _sessions[session_id] = session
        return session
        
    @staticmethod
    def set_df_cache(session_id: str, wb_type: str, df: pd.DataFrame):
        if session_id not in _df_cache:
            _df_cache[session_id] = {}
        _df_cache[session_id][wb_type] = df

    @staticmethod
    def get_df_cache(session_id: str, wb_type: str) -> Optional[pd.DataFrame]:
        return _df_cache.get(session_id, {}).get(wb_type)
        
    @staticmethod
    def restore_session(session: Session):
        _sessions[session.session_id] = session
        # Clear cache for this session just in case
        if session.session_id in _df_cache:
            del _df_cache[session.session_id]

