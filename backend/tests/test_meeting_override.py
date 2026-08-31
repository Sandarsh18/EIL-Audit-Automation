import pytest
from app.schemas.review import OverrideRequest
from app.services.review_service import ReviewService
from app.services.session_service import SessionService

def test_meeting_override():
    session_id = "test-meeting-session"
    import app.services.session_service
    app.services.session_service._sessions[session_id] = type("MockSession", (), {
        "session_id": session_id,
        "evaluation_month": "2026-08",
        "excel3_file_id": None,
        "mapping": type("MockMapping", (), {
            "excel3": None
        })()
    })()
    
    # Mock CombinedEngineService
    from app.services.combined_engine_service import CombinedEngineService
    from app.schemas.combined_rules import CombinedJobSummary
    import app.services.review_service
    
    original_calc = CombinedEngineService.calculate_combined
    
    def mock_calc(sid, jobs, manual_inputs=None, eval_month=None):
        res = []
        for j in jobs:
            mi = manual_inputs.get(j) if manual_inputs else None
            meet = mi.meeting if mi and mi.meeting is not None else 0.0
            res.append(CombinedJobSummary(
                job_number=j,
                fd=10,
                running_orders=5,
                ocs_done=0,
                expediting=10,
                inspection=5,
                others=5,
                meeting=meet,
                calculated_total=20,
                status="COMPLETE",
                warnings=[],
                evidence=["mock evidence 1", "mock evidence 2"]
            ))
        return res
        
    CombinedEngineService.calculate_combined = mock_calc
    
    try:
        # Initial review
        reviews = ReviewService.get_reviews(session_id, ["JOB1"])
        assert len(reviews) == 1
        assert reviews[0].meeting == 0.0
        
        # Apply Meeting override
        req = OverrideRequest(field="meeting", value=42.5, reason="Client request")
        res = ReviewService.apply_override(session_id, "JOB1", req)
        
        assert res.meeting == 42.5
        assert "meeting" in res.overrides
        assert res.overrides["meeting"].override_value == 42.5
        
        # Verify it doesn't affect calculated total
        assert res.calculated_total == 20
        
    finally:
        CombinedEngineService.calculate_combined = original_calc
