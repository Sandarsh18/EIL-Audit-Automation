import pandas as pd
from typing import List, Dict, Any, Tuple, Optional
import datetime
import calendar
from dateutil.relativedelta import relativedelta
from app.schemas.inspection_rules import InspectionJobResult, InspectionRecordResult
from app.services.session_service import SessionService
from app.utils.numeric_parser import parse_numeric
from dateutil import parser

from app.utils.date_parser import is_blank, parse_normalized_date

def old_is_blank(val: Any) -> bool:
    if pd.isna(val) or val is None:
        return True
    if isinstance(val, str) and val.strip() == "":
        return True
    return False

def parse_date(val: Any):
    return parse_normalized_date(val)

class InspectionRulesService:
    @staticmethod
    def calculate_rules(session_id: str, job_numbers: List[str], evaluation_month: str) -> List[InspectionJobResult]:
        session = SessionService.get_session(session_id)
        if not session.mapping or not session.mapping.excel2:
            raise ValueError("Excel 2 Mapping missing")
            
        from_col = session.mapping.excel2.columns.inspection_from
        upto_col = session.mapping.excel2.columns.inspection_upto
        date_recv_col = getattr(session.mapping.excel2.columns, "date_received", None)
        qap_col = getattr(session.mapping.excel2.columns, "qap_appl", None)
        working_days_col = getattr(session.mapping.excel2.columns, "no_of_working_days", None)
        
        from app.services.matching_service import MatchingService
        match_result = MatchingService.get_matched_records(session_id, job_numbers)
        results = []
        
        # Pre-calculate calendar window
        eval_year = eval_month = None
        start_date = end_date = None
        if evaluation_month:
            try:
                ey, em = map(int, evaluation_month.split("-"))
                eval_year, eval_month = ey, em
                _, last_day = calendar.monthrange(ey, em)
                end_date = datetime.date(ey, em, last_day)
                start_date = end_date.replace(day=1) - relativedelta(months=5) # 5 months prior + eval month = 6 months
            except ValueError:
                pass
        
        
        # Extract sample keys to verify working_days_col actually exists
        sample_keys = []
        for job_records in match_result.excel2_records.values():
            if job_records:
                sample_keys = list(job_records[0].keys())
                break
                
        # If mapping provided a column but it's not in the file, fallback
        if working_days_col and working_days_col not in sample_keys:
            working_days_col = None
            
        # Auto-detect working_days_col if missing
        if not working_days_col:
            for k in sample_keys:
                k_norm = k.strip().upper()
                if k_norm in ["NO. OF DAYS", "NUMBER OF WORKING DAYS", "WORKING DAYS", "NUMBER OF DAYS", "NO OF DAYS"]:
                    working_days_col = k
                    break
        for job in job_numbers:
            records = match_result.excel2_records.get(job, [])
            
            if not records:
                results.append(InspectionJobResult(
                    job_number=job,
                    evaluation_month_str=evaluation_month,
                    records_analyzed=0,
                    valid_records=0,
                    invalid_records=0,
                    total_inspection_days=0,
                    total_others_contribution=0.0,
                    warnings=["No matching Excel 2 records found."],
                    status="WARNING",
                    evidence=[]
                ))
                continue
            
            if not evaluation_month or start_date is None or end_date is None:
                results.append(InspectionJobResult(
                    job_number=job,
                    evaluation_month_str=None,
                    records_analyzed=len(records),
                    valid_records=0,
                    invalid_records=0,
                    total_inspection_days=0,
                    total_others_contribution=0.0,
                    warnings=["Evaluation month is required to calculate rules."],
                    status="ERROR",
                    evidence=[]
                ))
                continue
                
            job_warnings = []
            evidence_list = []
            valid_count = 0
            invalid_count = 0
            total_days = 0
            total_others = 0.0
            
            for row_idx, row in enumerate(records):
                raw_from = row.get(from_col)
                raw_upto = row.get(upto_col)
                raw_days = raw_wdays = row.get(working_days_col) if working_days_col else None
                raw_recv = row.get(date_recv_col) if date_recv_col else None
                raw_qap = row.get(qap_col) if qap_col else None
                
                f_blank, f_inv, f_dt = parse_date(raw_from)
                u_blank, u_inv, u_dt = parse_date(raw_upto)
                r_blank, r_inv, r_dt = parse_date(raw_recv)
                
                notes = []
                record_days = None
                status = "INVALID"
                diagnostic_match = None
                excluded_reason = None
                others_contribution = None
                others_source = None
                
                # --- Others Calculation ---
                if r_blank:
                    notes.append("Date Received is blank; ignored for Others calculation.")
                elif r_inv:
                    notes.append("Invalid Date Received format; ignored for Others calculation.")
                else:
                    rd = r_dt
                    if start_date <= rd <= end_date:
                        # Use robust parse_numeric instead of float()
                        q_val = parse_numeric(raw_qap)
                        w_val = parse_numeric(raw_wdays)
                        
                        q_present = q_val is not None
                        w_present = w_val is not None
                            
                        if q_present:
                            others_contribution = q_val
                            others_source = "QAP Appl."
                        elif w_present:
                            others_contribution = w_val
                            others_source = "Working Days"
                            
                        if others_contribution is not None:
                            total_others += others_contribution
                            
                        if job == "C028":
                            print("\n===== C028 ACCEPTANCE =====")
                            print("Evaluation Month:")
                            print(evaluation_month)
                            print("\nWindow Start:")
                            print(start_date)
                            print("\nWindow End:")
                            print(end_date)
                            print("\nExcel 2 Source Records:")
                            print(len(records))
                            print("\nDATE RECEIVED Raw:")
                            print(repr(raw_recv))
                            print("\nDATE RECEIVED Parsed:")
                            print(rd)
                            print("\nQAP APPL Raw:")
                            print(repr(raw_qap))
                            print("\nQAP APPL Parsed:")
                            print(q_val)
                            print("\nWORKING DAYS Raw:")
                            print(repr(raw_wdays))
                            print("\nWORKING DAYS Parsed:")
                            print(w_val)
                            print("\nOthers Source:")
                            print(others_source)
                            print("\nOthers Contribution:")
                            print(others_contribution)
                            print("\nCombined Others:")
                            print(total_others)
                            print("===========================\n")
                    else:
                        excluded_reason = "Older than six-month window"
                        notes.append(f"Excluded for Others: Date Received {rd} outside 6-month window ({start_date} to {end_date}); ignored for Others calculation.")

                # --- Inspection Days Calculation ---
                if f_blank and u_blank:
                    notes.append("Inspection dates missing.")
                elif f_inv and not f_blank:
                    notes.append("Invalid inspection From date format.")
                elif u_inv and not u_blank:
                    notes.append("Invalid inspection Upto date format.")
                else:
                    # Treat missing Upto as From, and missing From as Upto
                    if f_blank and not u_blank and not u_inv:
                        f_dt = u_dt
                        notes.append("Inspection From missing, using Upto date.")
                        f_blank = False
                    elif u_blank and not f_blank and not f_inv:
                        u_dt = f_dt
                        notes.append("Inspection Upto missing, using From date.")
                        u_blank = False

                    if f_blank or u_blank or f_inv or u_inv:
                        pass # handled above
                    else:
                        if f_dt > u_dt:
                            notes.append("Inspection Upto is earlier than Inspection From.")
                        else:
                            delta = (u_dt - f_dt).days + 1
                            record_days = delta
                            status = "VALID"
                            
                            # Apply Evaluation Month Filter FIRST
                            if f_dt.year == eval_year and f_dt.month == eval_month and u_dt.year == eval_year and u_dt.month == eval_month:
                                valid_count += 1
                                total_days += record_days
                            else:
                                status = "EXCLUDED"
                                if f_dt.year != eval_year or u_dt.year != eval_year:
                                    excluded_reason = f"Wrong year (Expected {eval_year})"
                                else:
                                    excluded_reason = f"Wrong month (Expected {eval_month})"

                        if raw_days is not None and not pd.isna(raw_days):
                            try:
                                src_d = int(float(raw_days))
                                if src_d == record_days:
                                    diagnostic_match = True
                                else:
                                    diagnostic_match = False
                                    notes.append(f"Calculated days ({record_days}) differs from source No. of Days ({src_d}).")
                            except (ValueError, TypeError):
                                pass

                if status == "INVALID":
                    invalid_count += 1
                    
                evidence_list.append(InspectionRecordResult(
                    source_row=row.get("_row_index", row_idx + 2),
                    date_field_used=date_recv_col if date_recv_col else "Date Received",
                    from_date_raw=raw_from,
                    upto_date_raw=raw_upto,
                    from_date_parsed=f_dt.isoformat() if f_dt else None,
                    upto_date_parsed=u_dt.isoformat() if u_dt else None,
                    days=record_days,
                    status=status,
                    warnings=notes,
                    source_no_of_days=raw_days,
                    diagnostic_match=diagnostic_match,
                    excluded_reason=excluded_reason,
                    date_received_raw=raw_recv,
                    date_received_parsed=r_dt.isoformat() if r_dt else None,
                    qap_appl_raw=raw_qap,
                    working_days_raw=raw_wdays,
                    others_selected_source=others_source,
                    others_contribution=others_contribution
                ))
                
            job_warnings = list(dict.fromkeys(job_warnings))
            final_status = "WARNING" if job_warnings else "COMPLETE"
                
            results.append(InspectionJobResult(
                job_number=job,
                evaluation_month_str=evaluation_month,
                records_analyzed=len(records),
                valid_records=valid_count,
                invalid_records=invalid_count,
                total_inspection_days=total_days,
                total_others_contribution=total_others,
                status=final_status,
                warnings=job_warnings,
                evidence=evidence_list
            ))
            
        return results
