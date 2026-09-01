import pytest
from app.services.combined_engine_service import CombinedEngineService
from app.schemas.combined_rules import ManualInputs
from app.schemas.inspection_rules import InspectionJobResult
from app.services.session_service import SessionService
from app.schemas.session import Session
from app.schemas.mapping import MappingConfiguration, Excel3Mapping, Excel3MappingFields, Excel2Mapping, Excel2MappingFields, Excel1Mapping, Excel1MappingFields
from unittest.mock import patch, Mock

def test_inspection_multiples():
    session_id = "test-session"
    session = Session(session_id=session_id, created_at="now", excel3_file_id="dummy")
    session.mapping = MappingConfiguration(
        excel1=Excel1Mapping(sheet="Sheet1", columns=Excel1MappingFields(job_number="Job", balance_quantity="Bal", ocs_date="OCS")),
        excel2=Excel2Mapping(sheet="Sheet1", columns=Excel2MappingFields(job_number="Job", inspection_from="From", inspection_upto="Upto")),
        excel3=Excel3Mapping(sheet="Sheet1", columns=Excel3MappingFields(
            job_number="Job", running_orders="RO", orders_for_fd="FD", ocs_done="OCS", total="Tot",
            expediting="Exp", inspection="Insp", others="Oth"
        ))
    )
    
    def mock_e1(s, j, m): return []
    def mock_e2(s, j, m):
        return [
            Mock(job_number="J0", valid_records=0, total_inspection_days=0, evidence=[], total_others_contribution=0.0),
            Mock(job_number="J1", valid_records=1, total_inspection_days=1, evidence=[], total_others_contribution=0.0),
            Mock(job_number="J2", valid_records=2, total_inspection_days=2, evidence=[], total_others_contribution=0.0),
            Mock(job_number="J5", valid_records=5, total_inspection_days=5, evidence=[], total_others_contribution=0.0),
            Mock(job_number="JM", valid_records=0, total_inspection_days=None, evidence=[], total_others_contribution=0.0),
        ]

    with patch('app.services.combined_engine_service.SessionService.get_session', return_value=session):
        with patch('app.services.combined_engine_service.Excel1RulesService.calculate_rules', side_effect=mock_e1):
            with patch('app.services.combined_engine_service.InspectionRulesService.calculate_rules', side_effect=mock_e2):
                with patch('app.services.combined_engine_service.SessionService.get_df_cache', return_value=None):
                    
                    results = CombinedEngineService.calculate_combined(
                        session_id=session_id,
                        job_numbers=["J0", "J1", "J2", "J5", "JM"],
                        manual_inputs={},
                        evaluation_month="2026-08"
                    )
                    
                    res_dict = {r.job_number: r for r in results}
                    
                    assert res_dict["J0"].inspection == 0
                    assert res_dict["J1"].inspection == 8
                    assert res_dict["J2"].inspection == 16
                    assert res_dict["J5"].inspection == 40
                    assert res_dict["JM"].inspection == 0
                
def test_inspection_manual_override_not_multiplied():
    session_id = "test-session-2"
    session = Session(session_id=session_id, created_at="now", excel3_file_id="dummy")
    session.mapping = MappingConfiguration(
        excel1=Excel1Mapping(sheet="Sheet1", columns=Excel1MappingFields(job_number="Job", balance_quantity="Bal", ocs_date="OCS")),
        excel2=Excel2Mapping(sheet="Sheet1", columns=Excel2MappingFields(job_number="Job", inspection_from="From", inspection_upto="Upto")),
        excel3=Excel3Mapping(sheet="Sheet1", columns=Excel3MappingFields(
            job_number="Job", running_orders="RO", orders_for_fd="FD", ocs_done="OCS", total="Tot",
            expediting="Exp", inspection="Insp", others="Oth"
        ))
    )
    
    def mock_e1(s, j, m): return []
    def mock_e2(s, j, m):
        return [Mock(job_number="J1", valid_records=1, total_inspection_days=1, evidence=[], total_others_contribution=0.0)]

    with patch('app.services.combined_engine_service.SessionService.get_session', return_value=session):
        with patch('app.services.combined_engine_service.Excel1RulesService.calculate_rules', side_effect=mock_e1):
            with patch('app.services.combined_engine_service.InspectionRulesService.calculate_rules', side_effect=mock_e2):
                with patch('app.services.combined_engine_service.SessionService.get_df_cache', return_value=None):
                    
                    results = CombinedEngineService.calculate_combined(
                        session_id=session_id,
                        job_numbers=["J1"],
                        manual_inputs={"J1": ManualInputs(inspection=16)},
                        evaluation_month="2026-08"
                    )
                    
                    assert results[0].inspection == 16 # NOT 128
