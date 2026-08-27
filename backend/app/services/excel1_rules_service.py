import pandas as pd
from typing import List, Dict, Any, Tuple
import datetime
from dateutil import parser
from app.schemas.excel1_rules import JobCalculationResult, RecordEvidence
from app.schemas.excel1_rules import JobCalculationResult, RecordEvidence
from app.services.session_service import SessionService
from app.utils.numeric_parser import parse_numeric

from app.utils.date_parser import is_blank, parse_normalized_date

def old_is_blank(val: Any) -> bool:
    if pd.isna(val) or val is None:
        return True
    if isinstance(val, str) and val.strip() == "":
        return True
    return False

def parse_balance(val: Any) -> Tuple[bool, bool, bool, float | None]:
    """Returns (is_blank, is_invalid, is_negative, parsed_value)"""
    if is_blank(val):
        return True, False, False, None
    f_val = parse_numeric(val)
    if f_val is not None:
        return False, False, f_val < 0, f_val
    else:
        return False, True, False, None

def parse_ocs_date(val: Any) -> Tuple[bool, bool, datetime.datetime | None]:
    """Returns (is_blank, is_invalid, parsed_datetime)."""
    if is_blank(val):
        return True, False, None
        
    if isinstance(val, (datetime.datetime, datetime.date)):
        if isinstance(val, datetime.date) and not isinstance(val, datetime.datetime):
            return False, False, datetime.datetime.combine(val, datetime.time.min)
        return False, False, val
        
    s_val = str(val).strip()
    if s_val.lower() in ["bad_date", "na", "n/a", "pending", "unknown", "invalid"]:
        return False, True, None
        
    try:
        dt = pd.to_datetime(val, dayfirst=True)
        if pd.isna(dt):
            return False, True, None
        return False, False, dt.to_pydatetime()
    except (ValueError, TypeError, parser.ParserError):
        return False, True, None

def is_within_six_months(d: datetime.date, eval_month_str: str) -> bool:
    start_date, end_date = get_window_dates(eval_month_str)
    return start_date <= d <= end_date

def get_window_dates(eval_month_str: str) -> Tuple[datetime.date, datetime.date]:
    try:
        ey, em = map(int, eval_month_str.split("-"))
    except:
        return datetime.date.today(), datetime.date.today()
    
    # End date is the last day of eval month
    import calendar
    _, last_day = calendar.monthrange(ey, em)
    end_date = datetime.date(ey, em, last_day)
    
    # Start date is the 1st of the month, 5 months prior (to include eval month)
    from dateutil.relativedelta import relativedelta
    start_date = end_date.replace(day=1) - relativedelta(months=5)
    
    return start_date, end_date

class Excel1RulesService:
    @staticmethod
    def calculate_rules(session_id: str, job_numbers: List[str], evaluation_month: str) -> List[JobCalculationResult]:
        # Reuse Phase 3 matching
        session = SessionService.get_session(session_id)
        if not session.mapping or not session.mapping.excel1:
            raise ValueError("Excel 1 Mapping missing")
            
        bal_col = session.mapping.excel1.columns.balance_quantity
        ocs_col = session.mapping.excel1.columns.ocs_date
        
        from app.services.matching_service import MatchingService
        match_result = MatchingService.get_matched_records(session_id, job_numbers)
        results = []
        
        for job in job_numbers:
            records = match_result.excel1_records.get(job, [])
            
            if not records:
                results.append(JobCalculationResult(
                    job_number=job,
                    source_record_count=0,
                    eligible_record_count=0,
                    excluded_record_count=0,
                    fd=0,
                    running_orders=0,
                    ocs_done=0,
                    warnings=["No matching Excel 1 records found."],
                    status="WARNING",
                    evidence=[]
                ))
                continue
            
            job_warnings = []
            evidence_list = []
            fd_count = 0
            ro_count = 0
            ocs_done_count = 0
            eligible_count = 0
            excluded_count = 0
            
            for row_idx, row in enumerate(records):
                raw_bal = row.get(bal_col)
                raw_ocs = row.get(ocs_col)
                
                b_blank, b_inv, b_neg, b_val = parse_balance(raw_bal)
                o_blank, o_inv, o_val = parse_normalized_date(raw_ocs)
                
                notes = []
                contrib = "None"
                eligibility = "INCLUDED"
                exclusion_reason = None
                
                if b_blank:
                    notes.append("Missing Balance Quantity.")
                    job_warnings.append("Missing Balance Quantity detected.")
                elif b_inv:
                    notes.append("Invalid Balance Quantity format.")
                    job_warnings.append(f"Invalid Balance Quantity '{raw_bal}'.")
                elif b_neg:
                    notes.append("Negative Balance Quantity detected.")
                    job_warnings.append(f"Negative Balance Quantity '{raw_bal}'.")
                    
                if o_inv:
                    notes.append("Invalid OCS Date format.")
                    job_warnings.append(f"Invalid OCS Date '{raw_ocs}'.")
                elif o_blank:
                    eligibility = "BLANK_OCS"
                elif evaluation_month:
                    if not is_within_six_months(o_val, evaluation_month):
                        win_start, win_end = get_window_dates(evaluation_month)
                        is_future = (o_val.year * 12 + o_val.month) > (int(evaluation_month.split("-")[0]) * 12 + int(evaluation_month.split("-")[1]))
                        if is_future:
                            exclusion_reason = f"OCS Date {o_val.isoformat() if o_val else 'None'} is after evaluation window end ({win_end.strftime('%Y-%m-%d')})"
                        else:
                            exclusion_reason = f"OCS Date {o_val.isoformat() if o_val else 'None'} is before evaluation window start ({win_start.strftime('%Y-%m-%d')})"
                        
                        notes.append(f"Excluded — {exclusion_reason}")
                        contrib = "Excluded"
                        eligibility = "EXCLUDED"
                    
                # Apply Rules
                # Only apply if both are cleanly parsed/blank (not invalid) and not excluded
                if contrib != "Excluded" and not b_inv and not o_inv:
                    if b_val == 0 and o_blank:
                        contrib = "FD"
                        fd_count += 1
                    elif b_val == 0 and not o_blank:
                        contrib = "OCS Done"
                        ocs_done_count += 1
                    elif b_val is not None and b_val != 0:
                        contrib = "Running Order"
                        ro_count += 1
                        
                if contrib == "Excluded":
                    excluded_count += 1
                else:
                    eligible_count += 1
                    
                # Diagnostics for B269
                if job == "B269":
                    win_start, win_end = get_window_dates(evaluation_month) if evaluation_month else (None, None)
                    print(f"JOB={job}")
                    print(f"RAW_OCS={repr(raw_ocs)}")
                    print(f"PARSED_OCS={o_val.isoformat() if o_val else 'None' if o_val else 'None'}")
                    print(f"EVAL_MONTH={evaluation_month}")
                    print(f"WINDOW_START={win_start.strftime('%Y-%m-%d') if win_start else 'None'}")
                    print(f"WINDOW_END={win_end.strftime('%Y-%m-%d') if win_end else 'None'}")
                    print(f"ELIGIBLE={eligibility != 'EXCLUDED'}")
                        
                evidence_list.append(RecordEvidence(
                    balance_quantity_raw=raw_bal,
                    ocs_date_raw=raw_ocs,
                    balance_quantity_parsed=b_val,
                    ocs_date_parsed=o_val.date().isoformat() if o_val and isinstance(o_val, datetime.datetime) else (str(o_val) if o_val else None),
                    is_balance_blank=b_blank,
                    is_ocs_blank=o_blank,
                    is_balance_invalid=b_inv,
                    is_ocs_invalid=o_inv,
                    contribution=contrib,
                    notes=notes,
                    eligibility=eligibility,
                    exclusion_reason=exclusion_reason
                ))
                
            # Deduplicate warnings
            job_warnings = list(dict.fromkeys(job_warnings))
            status = "WARNING" if job_warnings else "COMPLETE"
            
            results.append(JobCalculationResult(
                job_number=job,
                source_record_count=len(records),
                eligible_record_count=eligible_count,
                excluded_record_count=excluded_count,
                fd=fd_count,
                running_orders=ro_count,
                ocs_done=ocs_done_count,
                warnings=job_warnings,
                status=status,
                evidence=evidence_list
            ))
            
        return results
