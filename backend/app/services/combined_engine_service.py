from typing import List, Dict, Any, Optional
import pandas as pd
from app.schemas.combined_rules import CombinedJobSummary, ManualInputs, SourceLineage
from app.services.excel1_rules_service import Excel1RulesService
from app.services.inspection_rules_service import InspectionRulesService
from app.services.session_service import SessionService
from app.utils.numeric_parser import parse_numeric
class CombinedEngineService:
    @staticmethod
    def calculate_combined(session_id: str, job_numbers: List[str], manual_inputs: Dict[str, ManualInputs] = None, evaluation_month: str = None) -> List[CombinedJobSummary]:
        if manual_inputs is None:
            manual_inputs = {}
            
        session = SessionService.get_session(session_id)
        if not evaluation_month:
            evaluation_month = session.evaluation_month
            
        if not session.mapping or not session.mapping.excel3:
            raise ValueError("Excel 3 Mapping missing")
            
        if getattr(session.mapping.excel3, 'workbook_file_id', None) and session.excel3_file_id:
            if session.mapping.excel3.workbook_file_id != session.excel3_file_id:
                raise ValueError(f"Stale mapping detected. Mapped workbook {session.mapping.excel3.workbook_file_id} does not match current workbook {session.excel3_file_id}.")

            
        # 1. Fetch base calculations
        e1_results = {r.job_number: r for r in Excel1RulesService.calculate_rules(session_id, job_numbers, evaluation_month)}
        e2_results = {r.job_number: r for r in InspectionRulesService.calculate_rules(session_id, job_numbers, evaluation_month)}
        
        from app.services.matching_service import normalize_job_number
        
        # 2. Fetch Excel 3 defaults for OCS Done and Others if mapped
        e3_ocs_col = session.mapping.excel3.columns.ocs_done
        e3_others_col = session.mapping.excel3.columns.others
        e3_orders_for_col = session.mapping.excel3.columns.orders_for_fd
        e3_inspection_col = session.mapping.excel3.columns.inspection
        e3_running_orders_col = session.mapping.excel3.columns.running_orders
        
        import os
        from app.config import UPLOAD_DIR
        
        # Reuse matching service to get Excel 3 row by Job Number if possible
        df3 = SessionService.get_df_cache(session_id, "excel3")
        if df3 is None or df3.empty:
            if session.excel3_file_id:
                file_path = os.path.join(UPLOAD_DIR, f"{session.excel3_file_id}.xlsx")
                if os.path.exists(file_path):
                    from app.services.excel_service import ExcelService
                    header_idx = ExcelService.detect_header_row(file_path, session.mapping.excel3.sheet)
                    df3 = pd.read_excel(file_path, sheet_name=session.mapping.excel3.sheet, header=header_idx, dtype=object)
                    df3.columns = [str(c) if pd.notna(c) and str(c).strip() != "" else f"Unnamed: {i}" for i, c in enumerate(df3.columns)]
                    # Store header_idx in df attrs so we can compute true row index
                    df3.attrs['header_idx'] = header_idx
                    SessionService.set_df_cache(session_id, "excel3", df3)
                    
        df3_dict = {}
        header_idx = df3.attrs.get('header_idx', 0) if df3 is not None else 0
        if df3 is not None and not df3.empty:
            job_col = session.mapping.excel3.columns.job_number
            df3['_norm_key'] = df3[job_col].apply(normalize_job_number)
            selected_norm = {normalize_job_number(j) for j in job_numbers}
            df3_matched = df3[df3['_norm_key'].isin(selected_norm)]
            
            for key, group in df3_matched.groupby('_norm_key'):
                df3_dict[key] = group.iloc[0]
        else:
            df3_matched = pd.DataFrame()
            job_col = None
            
        print("df3 len:", len(df3) if df3 is not None else "None", "df3_matched len:", len(df3_matched) if df3_matched is not None else "None")
        results = []
        
        for job in job_numbers:
            e1 = e1_results.get(job)
            e2 = e2_results.get(job)
            
            # Default Excel 3 values
            e3_ocs = None
            e3_others = None
            e3_expediting = None
            e3_orders_for = None
            e3_inspection = None
            e3_running_orders = None
            job_norm = None
            
            if job_col:
                job_norm = normalize_job_number(job)
                if job_norm in df3_dict:
                    row = df3_dict[job_norm]
                    
                    def build_lineage(val, col, canon):
                        if pd.isna(val): return None
                        # Excel rows are 1-indexed. row.name is 0-indexed relative to dataframe.
                        # header_idx is 0-indexed.
                        # So actual Excel row = row.name + header_idx + 2
                        true_row = row.name + header_idx + 2
                        return SourceLineage(
                            workbook=session.mapping.excel3.sheet, # Just use sheet name or session.excel3_file_id as workbook for now, we don't have filename handy here
                            sheet=session.mapping.excel3.sheet,
                            row=int(true_row),
                            column=col,
                            header=col,
                            raw_value=val
                        )
                        
                    # Parse OCS Done
                    if e3_ocs_col and e3_ocs_col in row:
                        val = parse_numeric(row[e3_ocs_col])
                        if val is not None:
                            print(f"INTEGER CONVERSION: job={job}, field=e3_ocs, raw={row[e3_ocs_col]}, parsed={val}, type={type(val)}")
                            e3_ocs = int(val)
                                
                    # Parse Others
                    if e3_others_col and e3_others_col in row:
                        val = parse_numeric(row[e3_others_col])
                        if val is not None:
                            e3_others = val

                    # Parse Orders For
                    e3_orders_for = None
                    if e3_orders_for_col and e3_orders_for_col in row:
                        val = parse_numeric(row[e3_orders_for_col])
                        if val is not None:
                            e3_orders_for = val

                    # Parse Excel 3 Inspection (Inspn)
                    e3_inspection = None
                    if e3_inspection_col and e3_inspection_col in row:
                        val = parse_numeric(row[e3_inspection_col])
                        if val is not None:
                            e3_inspection = val

                    # Parse Excel 3 Running Orders
                    e3_running_orders = None
                    if e3_running_orders_col and e3_running_orders_col in row:
                        val = parse_numeric(row[e3_running_orders_col])
                        if val is not None:
                            print(f"INTEGER CONVERSION: job={job}, field=e3_running_orders, raw={row[e3_running_orders_col]}, parsed={val}, type={type(val)}")
                            e3_running_orders = int(val)
                            
                    e3_expediting_col = getattr(session.mapping.excel3.columns, "expediting", None)
                    e3_expediting = None
                    if e3_expediting_col and e3_expediting_col in row:
                        val = parse_numeric(row[e3_expediting_col])
                        if val is not None:
                            e3_expediting = val

            # Apply manual overrides
            m_input = manual_inputs.get(job, ManualInputs())
            
            # Base variables strictly from Excel 1, or manual overrides
            fd = m_input.fd if m_input.fd is not None else (e1.fd if e1 else 0)
            ro = m_input.running_orders if m_input.running_orders is not None else (e1.running_orders if e1 else 0)
            
            lineage = {}
            
            # OCS Done is from Excel 1, or manual override
            ocs_done = m_input.ocs_done if m_input.ocs_done is not None else (e1.ocs_done if e1 else 0)
            
            # Others is now strictly from Excel 2, or manual override
            others = m_input.others if m_input.others is not None else (float(e2.total_others_contribution) if e2 and e2.total_others_contribution is not None else 0.0)
            
            # Meeting strictly manual, defaults to 0.0
            meeting = m_input.meeting if m_input.meeting is not None else 0.0
            
            # Inspection strictly from Excel 2, or manual override
            if e2 and e2.total_inspection_days is not None:
                print(f"FLOAT CONVERSION: job={job}, field=e2_inspection_days, value={e2.total_inspection_days}, type={type(e2.total_inspection_days)}")
            
            base_inspection_days = float(e2.total_inspection_days) if e2 and e2.total_inspection_days is not None else 0.0
            inspection_man_hours = base_inspection_days * 8.0
            
            inspection = m_input.inspection if m_input.inspection is not None else inspection_man_hours
            
            # Derived logic
            expediting_is_native = False
            expediting_is_overridden = False
            
            if m_input.expediting is not None:
                print(f"INTEGER CONVERSION: job={job}, field=m_input.expediting, value={m_input.expediting}, type={type(m_input.expediting)}")
                expediting = int(m_input.expediting)
                expediting_is_overridden = True
            elif ocs_done is not None:
                val = (ro + ocs_done) * 2
                print(f"INTEGER CONVERSION: job={job}, field=expediting, ro={ro}, ocs_done={ocs_done}, value={val}, type={type(val)}")
                expediting = int(val)
            else:
                expediting = None
                
                
            calculated_total = None
            if expediting is not None and inspection is not None and others is not None:
                calculated_total = float(expediting + inspection + others)
                
            # Status and Evidence
            warnings = []
            evidence = []
            
            evidence.append(f"Job: {job_norm if job_col else job}")
            evidence.append("--- SOURCE LINEAGE ---")
            
            evidence.append(f"FD: {fd}")
            if m_input.fd is not None:
                evidence.append("  Source: Manual Override")
            else:
                evidence.append(f"  Source: Excel 1 (Derived: Balance=0 & OCS=blank)")
            
            evidence.append(f"Running Orders: {ro}")
            if m_input.running_orders is not None:
                evidence.append("  Source: Manual Override")
            else:
                evidence.append(f"  Source: Excel 1 (Derived: Balance!=0)")
            
            if ocs_done is not None:
                evidence.append(f"OCS Done: {ocs_done}")
                if m_input.ocs_done is not None:
                    evidence.append("  Source: Manual Override")
                else:
                    evidence.append(f"  Source: Excel 1 (Derived: Balance=0 & OCS!=blank)")
            else:
                evidence.append("OCS Done: MISSING")
                warnings.append("OCS Done missing.")
                
            if expediting_is_overridden:
                evidence.append(f"Expediting: {expediting}")
                evidence.append("  Source: Manual Override")
            elif expediting is not None:
                evidence.append(f"Expediting: {expediting}")
                evidence.append(f"  Source: Derived Rule ({ro} + {ocs_done}) * 2")
            else:
                evidence.append("Expediting: BLOCKED")
                warnings.append("Expediting blocked.")
                

            if inspection is not None:
                evidence.append(f"Inspection Days: {base_inspection_days}")
                if m_input.inspection is not None:
                    evidence.append(f"Inspection: {inspection} (Manual Override)")
                else:
                    evidence.append(f"Inspection: {base_inspection_days} days × 8 = {inspection} man-hours")
                    evidence.append(f"  Source: Excel 2 (Filtered for {evaluation_month})")
            else:
                evidence.append("Inspection: MISSING / N/A")
                
            if others is not None:
                evidence.append(f"Others: {others}")
                if m_input.others is not None:
                    evidence.append("  Source: Manual Override")
                else:
                    evidence.append(f"  Source: Excel 2 (Filtered for {evaluation_month})")
                if others < 0:
                    warnings.append("Negative 'Others' value detected. Please verify if intentional.")
            else:
                evidence.append("Others: MISSING")
                warnings.append("Others missing. Calculated Total blocked.")
                
            evidence.append(f"Meeting: {meeting}")
            if m_input.meeting is not None:
                evidence.append("  Source: Manual Override")
            else:
                evidence.append("  Source: Default (0.0)")
                
            if calculated_total is not None:
                evidence.append(f"Calculated Total: {calculated_total}")
                status = "COMPLETE"
            else:
                evidence.append("Calculated Total: BLOCKED")
                status = "BLOCKED"
                warnings.append("Calculated Total blocked due to missing dependencies.")
                
            if status != "BLOCKED":
                status = "COMPLETE" if not warnings else "WARNING"
                
            results.append(CombinedJobSummary(
                job_number=job,
                fd=fd,
                running_orders=ro,
                ocs_done=ocs_done,
                expediting=expediting,
                native_expediting_used=expediting_is_native,
                inspection_days=base_inspection_days if e2 else None,
                inspection=inspection,
                inspection_man_hours=inspection_man_hours,
                others=others,
                meeting=meeting,
                calculated_total=calculated_total,
                status=status,
                warnings=warnings,
                evidence=evidence,
                lineage=lineage if lineage else None
            ))
            
        return results
