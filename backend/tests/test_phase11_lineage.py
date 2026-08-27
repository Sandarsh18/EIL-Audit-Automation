import pytest
from app.services.matching_service import MatchingService, normalize_job_number
from app.services.combined_engine_service import CombinedEngineService
from app.schemas.session import Session, MappingConfiguration
from app.schemas.combined_rules import ManualInputs
from unittest.mock import Mock

def test_normalize_job_number():
    assert normalize_job_number("B378") == "B378"
    assert normalize_job_number("B378-01") == "B378-01"
    assert normalize_job_number(" B378 ") == "B378"

def test_inspection_days_integer(monkeypatch):
    # Mock services to return controlled data
    monkeypatch.setattr("app.services.excel1_rules_service.Excel1RulesService.calculate_rules", lambda *a: [])
    monkeypatch.setattr("app.services.inspection_rules_service.InspectionRulesService.calculate_rules", lambda *a: [
        Mock(job_number="B378", total_inspection_days=108.5, valid_records=50, total_others_contribution=0.0) # Assuming it could be float
    ])
    monkeypatch.setattr("app.services.session_service.SessionService.get_session", lambda *a: Mock(
        excel3_file_id="mock_id",
        evaluation_month="2026-08",
        mapping=Mock(excel3=Mock(
            workbook_file_id="mock_id",
            sheet="Jul25",
            columns=Mock(ocs_done="OCS done", others="Others", expediting="Exp.", total="Total", job_number="Job No", orders_for_fd="Orders For", inspection="Inspn")
        ))
    ))
    monkeypatch.setattr("app.services.session_service.SessionService.get_df_cache", lambda *a, **kw: None)
    
    # Calculate
    results = CombinedEngineService.calculate_combined("test_session", ["B378"])
    
    assert len(results) == 1
    # Check that Inspection Days is cast to integer without multiplying by 8
    assert results[0].inspection == 108.0

    # Ensure evidence string contains explicit source
    evidence_text = "\n".join(results[0].evidence)
    assert "Inspection: 108" in evidence_text
    assert "Source: Excel 2" in evidence_text

def test_evidence_string_lineage(monkeypatch):
    monkeypatch.setattr("app.services.excel1_rules_service.Excel1RulesService.calculate_rules", lambda *a: [
        Mock(job_number="B378", fd=1, running_orders=11, ocs_done=1)
    ])
    monkeypatch.setattr("app.services.inspection_rules_service.InspectionRulesService.calculate_rules", lambda *a: [
        Mock(job_number="B378", total_inspection_days=108, valid_records=50, total_others_contribution=0.0)
    ])
    
    import pandas as pd
    df3_mock = pd.DataFrame({
        "Job No": ["B378"],
        "OCS done": [1],
        "Exp.": [24],
        "Inspn": [108],
        "Others": [16],
        "Total": [56],
    })
    
    monkeypatch.setattr("app.services.session_service.SessionService.get_session", lambda *a: Mock(
        excel3_file_id="mock_id",
        evaluation_month="2026-08",
        mapping=Mock(excel3=Mock(
            workbook_file_id="mock_id",
            sheet="Jul25",
            columns=Mock(ocs_done="OCS done", others="Others", expediting="Exp.", total="Total", job_number="Job No", orders_for_fd="Orders For", inspection="Inspn")
        ))
    ))
    monkeypatch.setattr("app.services.session_service.SessionService.get_df_cache", lambda *a, **kw: df3_mock)
    
    results = CombinedEngineService.calculate_combined("test_session", ["B378"])
    
    assert len(results) == 1
    res = results[0]
    
    assert res.expediting == 24 # (11 + 1) * 2 = 24
    assert res.inspection == 108.0
    assert res.others == 0.0 # Default is 0 in Phase 15
    
    # In the updated logic, calculation succeeds even without current_month_inspection (Phase 15 change)
    assert res.status == "COMPLETE"
    
    evidence = "\n".join(res.evidence)
    
    # Check exact evidence string formats
    assert "Expediting: 24" in evidence
    assert "Source: Derived Rule" in evidence
    assert "Inspection: 108" in evidence
    assert "Source: Excel 2 (Filtered for 2026-08)" in evidence
    assert "Others: 0" in evidence
