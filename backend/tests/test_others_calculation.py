import pytest
import datetime
from app.services.inspection_rules_service import InspectionRulesService
from app.schemas.mapping import MappingConfiguration, Excel1Mapping, Excel1MappingFields, Excel2Mapping, Excel2MappingFields, Excel3Mapping, Excel3MappingFields
from app.schemas.session import Session
from app.services.session_service import SessionService

def test_others_priority_logic(monkeypatch):
    class MockMatchResult:
        def __init__(self):
            # Cases 1 to 5 from requirements
            self.excel2_records = {
                "CASE1": [{"DATE RECEIVED": "2026-06-15", "QAP APPL.": 2, "NO. OF DAYS": 1.5}],
                "CASE2": [{"DATE RECEIVED": "2026-06-15", "QAP APPL.": None, "NO. OF DAYS": 1.5}],
                "CASE3": [{"DATE RECEIVED": "2026-06-15", "QAP APPL.": 0, "NO. OF DAYS": 2}],
                "CASE4": [{"DATE RECEIVED": "2026-06-15", "QAP APPL.": None, "NO. OF DAYS": None}],
                "CASE5": [{"DATE RECEIVED": "2026-06-15", "QAP APPL.": 2, "NO. OF DAYS": 3}],
            }

    class MockMatchingService:
        @staticmethod
        def get_matched_records(session_id, job_numbers):
            return MockMatchResult()

    monkeypatch.setattr("app.services.matching_service.MatchingService.get_matched_records", MockMatchingService.get_matched_records)

    # Setup Session
    session = SessionService.create_session()
    session.evaluation_month = "2026-08"
    session_id = session.session_id
    
    mapping = MappingConfiguration(
        excel1=Excel1Mapping(sheet="S", columns=Excel1MappingFields(job_number="J", balance_quantity="B", ocs_date="O")),
        excel3=Excel3Mapping(sheet="S", columns=Excel3MappingFields(job_number="J", running_orders="R", orders_for_fd="F", ocs_done="O", expediting="E", inspection="I", others="Ot", total="T")),
        excel2=Excel2Mapping(
            sheet="Sheet1",
            columns=Excel2MappingFields(
                job_number="JOB NO.",
                inspection_from="FROM",
                inspection_upto="UPTO",
                date_received="DATE RECEIVED",
                qap_appl="QAP APPL.",
                no_of_working_days="NO. OF DAYS"
            )
        )
    )
    SessionService.update_session_mapping(session_id, mapping)
    SessionService.update_evaluation_month(session_id, "2026-08")

    jobs = ["CASE1", "CASE2", "CASE3", "CASE4", "CASE5"]
    results = InspectionRulesService.calculate_rules(session_id, jobs, "2026-08")
    
    # CASE 1: QAP=2, Days=1.5 -> Others=2
    assert results[0].total_others_contribution == 2.0
    
    # CASE 2: QAP=None, Days=1.5 -> Others=1.5
    assert results[1].total_others_contribution == 1.5
    
    # CASE 3: QAP=0, Days=2 -> Others=0.0
    assert results[2].total_others_contribution == 0.0
    
    # CASE 4: QAP=None, Days=None -> Others=0.0
    assert results[3].total_others_contribution == 0.0
    
    # CASE 5: QAP=2, Days=3 -> Others=2.0
    assert results[4].total_others_contribution == 2.0
