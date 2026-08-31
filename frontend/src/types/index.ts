export interface Session {
  session_id: string;
  excel1_file_id?: string;
  excel2_file_id?: string;
  excel3_file_id?: string;
  created_at: string;
}

export interface ColumnMetadata {
  name: string;
  index: number;
  data_type: string;
  canonical?: string;
}

export interface SheetMetadata {
  sheet_name: string;
  row_count: number;
  column_count: number;
  columns: ColumnMetadata[];
  preview: Record<string, any>[];
}

export interface SheetSummary {
  name: string;
  is_candidate: boolean;
  schema_type: string;
  row_count: number;
  columns: string[];
}

export interface WorkbookMetadata {
  file_id: string;
  workbook_type: string;
  filename: string;
  size: number;
  sheets: string[];
  sheet_summaries?: SheetSummary[];
}

export interface Excel1Mapping {
  sheet: string;
  columns: {
    job_number: string;
    balance_quantity: string;
    ocs_date: string;
  }
}

export interface Excel2Mapping {
  sheet: string;
  columns: {
    job_number: string;
    inspection_from: string;
    inspection_upto: string;
  }
}

export interface Excel3Mapping {
  sheet: string;
  columns: {
    job_number: string;
    running_orders: string;
    orders_for: string;
    ocs_done: string;
    expediting: string;
    inspection: string;
    others: string;
    total: string;
  }
}

export interface MappingConfiguration {
  excel1: Excel1Mapping;
  excel2: Excel2Mapping;
  excel3: Excel3Mapping;
}

export interface TypeWarning {
  logical_field: string;
  source_column: string;
  expected_type: string;
  detected_type: string;
  message: string;
}

export interface ValidationResult {
  valid: boolean;
  warnings: TypeWarning[];
}

export interface JobNumberOption {
  original_value: string;
  normalized_key: string;
  excel1_count: number;
  excel2_count: number;
  excel3_count: number;
  excel1_found: boolean;
  excel2_found: boolean;
  excel3_found: boolean;
  intersection_status: string;
}

export interface JobNumberSummary {
  options: JobNumberOption[];
  total_valid_job_numbers: number;
  blank_job_numbers: number;
}

export interface MatchRequest {
  job_numbers: string[];
}

export interface MatchResult {
  job_numbers: string[];
  excel1_records: Record<string, Record<string, any>[]>;
  excel2_records: Record<string, Record<string, any>[]>;
  excel3_records: Record<string, Record<string, any>[]>;
}

export interface RecordEvidence {
  balance_quantity_raw: any;
  ocs_date_raw: any;
  balance_quantity_parsed: number | null;
  ocs_date_parsed: string | null;
  is_balance_blank: boolean;
  is_ocs_blank: boolean;
  is_balance_invalid: boolean;
  is_ocs_invalid: boolean;
  contribution: string;
  notes: string[];
  eligibility: string;
  exclusion_reason?: string | null;
}

export interface JobCalculationResult {
  job_number: string;
  source_record_count: number;
  eligible_record_count: number;
  excluded_record_count: number;
  fd: number;
  running_orders: number;
  warnings: string[];
  status: 'COMPLETE' | 'WARNING' | 'ERROR';
  evidence: RecordEvidence[];
}

export interface InspectionRecordResult {
  from_date_raw: any;
  upto_date_raw: any;
  from_date_parsed: string | null;
  upto_date_parsed: string | null;
  days: number | null;
  status: string;
  warnings: string[];
  source_no_of_days: any | null;
  diagnostic_match: boolean | null;
}

export interface InspectionJobResult {
  job_number: string;
  evaluation_month_str?: string;
  records_analyzed: number;
  valid_records: number;
  invalid_records: number;
  total_inspection_days: number;
  status: 'COMPLETE' | 'WARNING' | 'ERROR';
  warnings: string[];
  evidence: InspectionRecordResult[];
}

export interface ManualInputs {
  fd: number | null;
  running_orders: number | null;
  ocs_done: number | null;
  expediting: number | null;
  inspection: number | null;
  others: number | null;
}

export interface CombinedCalculationRequest {
  job_numbers: string[];
  evaluation_month: string;
  manual_inputs?: Record<string, ManualInputs>;
}

export interface SourceLineage {
  workbook: string;
  sheet: string;
  row: number | null;
  column: string | null;
  header: string;
  raw_value: any;
}

export interface CombinedJobSummary {
  job_number: string;
  fd: number;
  running_orders: number;
  ocs_done: number | null;
  expediting: number | null;
  native_expediting_used: boolean;
  inspection: number | null;
  others: number | null;
  meeting?: number | null;
  calculated_total: number | null;
  status: 'COMPLETE' | 'WARNING' | 'BLOCKED';
  warnings: string[];
  evidence: string[];
  lineage?: Record<string, SourceLineage>;
}

export interface ChangePlanCell {
  session_id: string;
  job_number: string;
  sheet_name: string;
  row_index: number;
  column_index: number;
  cell_address: string;
  logical_field: string;
  old_value: any;
  old_formula?: string | null;
  new_value: any;
  new_formula?: string | null;
  action: string;
  reason: string;
  source: string;
  approval_status: string;
  is_formula: boolean;
  formula_overwrite_approved: boolean;
}

export interface ChangePlan {
  cells_to_modify: ChangePlanCell[];
  cells_unchanged: number;
  blocked_jobs: string[];
  approved_jobs_included: number;
  formula_overwrites: number;
}

export interface OutputMetadata {
  status: string;
  filename: string;
  output_path: string;
  output_id: string;
  original_sha256: string;
  original_unchanged: boolean;
  jobs_processed: number;
  jobs_blocked: number;
  cells_modified: number;
  unexpected_changes: number;
  formula_changes: number;
  unexpected_formula_changes: number;
  sheets_changed: string[];
}

export interface ManualOverride {
  field: string;
  source_value: number | null;
  override_value: number | null;
  reason: string | null;
  timestamp: string;
  active: boolean;
}

export interface OverrideRequest {
  field: 'ocs_done' | 'others' | 'expediting' | 'meeting';
  value: number | null;
  reason: string | null;
}

export interface ApprovalRequest {
  acknowledge_warnings: boolean;
}

export interface JobReviewResult extends Omit<CombinedJobSummary, 'status'> {
  status: 'DRAFT' | 'WARNING' | 'BLOCKED' | 'APPROVED' | 'DELETED';
  overrides: Record<string, ManualOverride>;
}

export interface CustomColumnData {
  heading: string;
  data: Record<string, any>;
}

export interface OutputGenerateRequest {
  job_numbers: string[];
  custom_columns?: CustomColumnData[];
}
