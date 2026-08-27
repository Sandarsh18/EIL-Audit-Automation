import pytest
import datetime
from app.services.inspection_rules_service import InspectionRulesService
from app.services.session_service import SessionService
from app.schemas.mapping import MappingConfiguration, Excel1Mapping, Excel2Mapping, Excel1MappingFields, Excel2MappingFields, Excel3Mapping, Excel3MappingFields
from app.schemas.session import Session
from app.services.matching_service import MatchingService
from unittest.mock import patch, MagicMock

@pytest.fixture
def mock_session():
    session_id = "test_c028_session"
    session = Session(
        session_id=session_id,
        created_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        evaluation_month="2026-08",
        mapping=MappingConfiguration(
            excel1=Excel1Mapping(
                sheet="Sheet1",
                columns=Excel1MappingFields(job_number="JOB", balance_quantity="BAL", ocs_date="OCS")
            ),
            excel2=Excel2Mapping(
                sheet="Sheet1",
                columns=Excel2MappingFields(job_number="JOB", inspection_from="FROM", inspection_upto="UPTO",
                                      date_received="DATE RECEIVED", qap_appl="QAP Appl.",
                                      no_of_working_days="Number of Working Days")
            ),
            excel3=Excel3Mapping(
                sheet="Sheet1",
                columns=Excel3MappingFields(job_number="JOB", ocs_done="OCS", others="OTH", orders_for_fd="ORD", inspection="INS", running_orders="RUN", expediting="EXP", total="TOT")
            )
        )
    )
    import app.services.session_service as session_service_mod
    session_service_mod._sessions[session_id] = session
    yield session_id
    if session_id in session_service_mod._sessions:
        del session_service_mod._sessions[session_id]

def test_c028_working_days_logic(mock_session):
    # Setup mock matching service to return a specific set of Excel 2 records for C028
    
    c028_records = [
        # Record 1: Inside window, QAP empty, Working Days 0.5
        {
            "JOB": "C028",
            "DATE RECEIVED": "2026-07-24", # Inside 6-month window (2026-03-01 to 2026-08-31)
            "QAP Appl.": "", # Empty QAP
            "Number of Working Days": "0.5",
            "FROM": None,
            "UPTO": None
        },
        # Record 2: Outside window, QAP empty, Working Days 1.5
        {
            "JOB": "C028",
            "DATE RECEIVED": "2026-02-28", # Outside 6-month window!
            "QAP Appl.": "",
            "Number of Working Days": "1.5",
            "FROM": None,
            "UPTO": None
        }
    ]

    # Create a mock for MatchingService.get_matched_records
    class MockMatchResult:
        excel2_records = {"C028": c028_records}

    with patch('app.services.matching_service.MatchingService.get_matched_records', return_value=MockMatchResult()):
        # Act
        results = InspectionRulesService.calculate_rules(mock_session, ["C028"], "2026-08")
        
        # Assert
        assert len(results) == 1
        res = results[0]
        
        assert res.job_number == "C028"
        assert res.evaluation_month_str == "2026-08"
        assert res.records_analyzed == 2
        assert res.valid_records == 0  # No valid inspection days
        
        # The core assertion: Others must be exactly 0.5 because the other record is excluded
        assert res.total_others_contribution == 0.5

def test_auto_detect_working_days(mock_session):
    # Setup session with mapping MISSING no_of_working_days
    session = SessionService.get_session(mock_session)
    session.mapping.excel2.columns.no_of_working_days = None
    
    c028_records = [
        {
            "JOB": "C028",
            "DATE RECEIVED": "2026-07-24", 
            "QAP Appl.": "",
            "NO. OF DAYS": "1.25", # Should be auto-detected
            "FROM": None,
            "UPTO": None
        }
    ]

    class MockMatchResult:
        excel2_records = {"C028": c028_records}

    with patch('app.services.matching_service.MatchingService.get_matched_records', return_value=MockMatchResult()):
        # Act
        results = InspectionRulesService.calculate_rules(mock_session, ["C028"], "2026-08")
        
        # Assert
        assert len(results) == 1
        res = results[0]
        assert res.total_others_contribution == 1.25
