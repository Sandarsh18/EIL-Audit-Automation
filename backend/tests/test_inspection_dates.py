import pytest
import pandas as pd
import os
from app.services.inspection_rules_service import InspectionRulesService
from app.services.matching_service import MatchingService
import app.services.session_service

@pytest.fixture(scope="module")
def setup_mocks():
    fixture_path = os.path.join(os.path.dirname(__file__), 'fixtures', 'PMCCCallsason27Aug26.xlsx')
    df = pd.read_excel(fixture_path, sheet_name='PMCCalls', header=0, dtype=object)

    class MockMapping:
        excel2 = type('E2M', (), {'columns': type('E2C', (), {
            'inspection_from': 'Inspection Attended (From)',
            'inspection_upto': 'Inspection Attended(Upto)',
            'date_received': 'Date received',
            'qap_appl': 'QAP appl.',
            'no_of_working_days': 'No. of Days'
        })()})()
        
    class MockSession:
        mapping = MockMapping()

    # Store original methods
    orig_get_session = app.services.session_service.SessionService.get_session
    orig_get_matched = MatchingService.get_matched_records

    # Mock get_session
    app.services.session_service.SessionService.get_session = lambda sid: MockSession()

    # Mock get_matched_records
    def mock_get_matched(sid, jobs):
        records = {}
        for job in jobs:
            records[job] = [row.to_dict() for _, row in df[df['Job No.'] == job].iterrows()]
        return type('MockMatchResult', (), {'excel2_records': records})()
        
    MatchingService.get_matched_records = mock_get_matched

    yield

    # Restore original methods
    app.services.session_service.SessionService.get_session = orig_get_session
    MatchingService.get_matched_records = orig_get_matched

def test_missing_upto_date_is_treated_as_one_day(setup_mocks):
    """Test L = 10 Aug 26, M = nan evaluates to 1 day for B895."""
    # B895 has a single-day inspection on 10 Aug 26 (only From is provided)
    # as well as a 4-day inspection from 24 Aug to 27 Aug 26.
    results = InspectionRulesService.calculate_rules('fake', ['B895'], '2026-08')
    assert len(results) == 1
    job_res = results[0]
    
    # Verify the job matched
    assert job_res.job_number == 'B895'
    
    # It should have found 5 valid records in August 2026 including the single days
    assert job_res.valid_records == 5
    assert job_res.total_inspection_days == 9

def test_date_range_is_calculated_inclusively(setup_mocks):
    """Test L = 24 Aug 26, M = 27 Aug 26 evaluates to 4 days."""
    # We can check the exact evidence for B895
    results = InspectionRulesService.calculate_rules('fake', ['B895'], '2026-08')
    job_res = results[0]
    
    range_evidence = [e for e in job_res.evidence if e.status == 'VALID' and e.days == 4]
    assert len(range_evidence) == 1
    ev = range_evidence[0]
    assert '2026-08-24' in str(ev.from_date_parsed)
    assert '2026-08-27' in str(ev.upto_date_parsed)

def test_single_date_fallback_from_upto(setup_mocks):
    """If From is missing but Upto is provided, it should evaluate to 1 day."""
    # Create a synthetic test case utilizing the same mock structure
    import datetime
    
    class FakeMatchResult:
        excel2_records = {
            'SYNTH1': [{
                'Inspection Attended (From)': None,
                'Inspection Attended(Upto)': datetime.datetime(2026, 8, 15),
                'Job No.': 'SYNTH1'
            }]
        }
        
    orig_get_matched = MatchingService.get_matched_records
    MatchingService.get_matched_records = lambda sid, jobs: FakeMatchResult()
    
    try:
        results = InspectionRulesService.calculate_rules('fake', ['SYNTH1'], '2026-08')
        assert results[0].total_inspection_days == 1
        assert results[0].valid_records == 1
    finally:
        MatchingService.get_matched_records = orig_get_matched
