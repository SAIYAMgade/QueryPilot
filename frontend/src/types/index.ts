export interface ConnectionInfo {
  host: string;
  port: number;
  service_name: string;
  user: string;
  driver: string;
  is_connected: boolean;
  error_detail: string | null;
  environment: string;
}

export interface QueryResultColumn {
  name: string;
  data_type: string;
  nullable?: boolean;
}

export interface QueryExecutionResponse {
  query_id: string;
  sql: string;
  status: 'SUCCESS' | 'ERROR';
  duration_ms: number;
  fetch_duration_ms?: number;
  rows_returned: number;
  truncated: boolean;
  columns: QueryResultColumn[];
  rows: Record<string, any>[];
  error?: {
    code?: string;
    message: string;
    offset?: number;
    category?: string;
  };
  environment: string;
  executed_at: string;
}

export interface SavedQuery {
  id: string;
  title: string;
  description: string;
  sql: string;
  parameters: Record<string, any>;
  tags: string[];
  investigation_id?: string | null;
  created_at: string;
  updated_at: string;
}

export interface QueryHistoryItem {
  id: string;
  sql: string;
  status: string;
  duration_ms: number;
  rows_returned: number;
  truncated: boolean;
  error_summary?: string;
  environment: string;
  executed_at: string;
}

export interface TableSummary {
  owner: string;
  table_name: string;
  num_rows: number | null;
  is_estimated_rows: boolean;
  column_count: number;
  last_analyzed: string | null;
}

export interface ColumnMetadata {
  name: string;
  data_type: string;
  nullable: boolean;
  data_length?: number;
  data_precision?: number;
  data_scale?: number;
  column_id?: number;
  is_primary_key: boolean;
  is_foreign_key: boolean;
  fk_ref_table?: string;
  fk_ref_column?: string;
  num_distinct?: number;
  density?: number;
  histogram?: string;
}

export interface IndexMetadata {
  index_name: string;
  uniqueness: string;
  columns: string[];
  status: string;
  index_type?: string;
  distinct_keys?: number;
}

export interface ConstraintMetadata {
  constraint_name: string;
  constraint_type: string;
  type_display: string;
  search_condition?: string;
  r_constraint_name?: string;
  r_table_name?: string;
  columns: string[];
}

export interface TableDetail {
  owner: string;
  table_name: string;
  num_rows: number | null;
  is_estimated_rows: boolean;
  last_analyzed: string | null;
  columns: ColumnMetadata[];
  indexes: IndexMetadata[];
  constraints: ConstraintMetadata[];
  preview_rows: Record<string, any>[];
}

export interface Relationship {
  constraint_name: string;
  from_table: string;
  from_column: string;
  to_table: string;
  to_column: string;
}

export interface PlanOperation {
  id: number;
  parent_id?: number | null;
  operation: string;
  options?: string | null;
  object_name?: string | null;
  object_type?: string | null;
  cost?: number | null;
  cardinality?: number | null;
  bytes?: number | null;
  cpu_cost?: number | null;
  io_cost?: number | null;
  time_sec?: number | null;
  access_predicates?: string | null;
  filter_predicates?: string | null;
  depth: number;
  children?: PlanOperation[];
}

export interface DiagnosticObservation {
  id: string;
  category: string;
  severity: 'INFO' | 'INVESTIGATE' | 'WARNING' | 'CRITICAL';
  title: string;
  what_observed: string;
  where_observed: string;
  why_it_matters: string;
  evidence_needed: string;
  suggested_step: string;
  confidence: 'EVIDENCED' | 'HYPOTHESIS' | 'HEURISTIC';
}

export interface ExecutionPlanResponse {
  query_id: string;
  statement_id: string;
  plan_type: string;
  is_actual: boolean;
  operations: PlanOperation[];
  observations: DiagnosticObservation[];
  raw_plan_text: string;
  optimizer_cost?: number | null;
  limitations_note: string;
  generated_at: string;
}

export interface EquivalenceResult {
  is_equivalent: boolean;
  status: 'EQUIVALENT' | 'DIFFERENT' | 'INCONCLUSIVE';
  reason: string;
  row_count_baseline: number;
  row_count_candidate: number;
  column_match: boolean;
  columns_baseline: string[];
  columns_candidate: string[];
  diff_summary?: string;
  sample_discrepancy?: Record<string, any>;
}

export interface RunMeasurement {
  run_index: number;
  baseline_duration_ms: number;
  candidate_duration_ms: number;
  baseline_rows: number;
  candidate_rows: number;
}

export interface VariantStatistics {
  label: string;
  runs: number;
  median_ms: number;
  min_ms: number;
  max_ms: number;
  iqr_ms: number;
  successful_runs: number;
  failed_runs: number;
  rows: number;
  optimizer_cost?: number | null;
}

export interface ComparisonResponse {
  comparison_id: string;
  hypothesis?: string;
  equivalence: EquivalenceResult;
  baseline_stats: VariantStatistics;
  candidate_stats: VariantStatistics;
  runs_data: RunMeasurement[];
  speedup_ratio?: number;
  improvement_summary: string;
  caveat: string;
  environment: string;
  created_at: string;
}

export interface KnowledgeBaseEntry {
  oracle_code: string;
  category: string;
  official_title: string;
  plain_english: string;
  common_scenarios: string[];
  root_cause_analysis: string;
  recommended_checks: string[];
  resolution_steps: string[];
  sample_problematic_sql?: string;
  sample_corrected_sql?: string;
}

export interface ErrorAnalysisResponse {
  analysis_id: string;
  oracle_error_code: string;
  category: string;
  sanitized_message: string;
  likely_causes: string[];
  recommended_checks: string[];
  knowledge_base?: KnowledgeBaseEntry;
  position_hint?: string;
  is_confirmed_cause: boolean;
  evidence_status: 'CONFIRMED' | 'HYPOTHESIS';
  analyzed_at: string;
}

export type InvestigationStatus = 'OPEN' | 'INVESTIGATING' | 'FIX_PROPOSED' | 'VALIDATION_REQUIRED' | 'RESOLVED' | 'CLOSED_INCONCLUSIVE';
export type InvestigationSeverity = 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';

export interface TimelineEvent {
  event_id: string;
  event_type: string;
  description: string;
  timestamp: string;
  metadata?: Record<string, any>;
}

export interface Investigation {
  id: string;
  title: string;
  description: string;
  category: string;
  severity: InvestigationSeverity;
  status: InvestigationStatus;
  initial_hypothesis?: string;
  baseline_query_id?: string;
  baseline_sql?: string;
  candidate_sql?: string;
  related_error_code?: string;
  root_cause_explanation?: string;
  proposed_fix?: string;
  verification_notes?: string;
  timeline: TimelineEvent[];
  created_at: string;
  updated_at: string;
  resolved_at?: string;
}
