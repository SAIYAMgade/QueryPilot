import {
  ConnectionInfo, QueryExecutionResponse, QueryHistoryItem, SavedQuery,
  TableSummary, TableDetail, Relationship, ExecutionPlanResponse,
  ComparisonResponse, ErrorAnalysisResponse, KnowledgeBaseEntry,
  Investigation
} from '../types';

const API_BASE = '/api';

async function request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const res = await fetch(`${API_BASE}${endpoint}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
  });

  if (!res.ok) {
    const errorData = await res.json().catch(() => ({ message: res.statusText }));
    throw new Error(errorData.message || errorData.detail || 'Request failed');
  }

  return res.json();
}

export const api = {
  getConnectionStatus: () => request<ConnectionInfo>('/connection/status'),
  
  // SQL Workspace
  executeQuery: (sql: string, parameters: Record<string, any> = {}, max_rows?: number, timeout_sec?: number) =>
    request<QueryExecutionResponse>('/query/execute', {
      method: 'POST',
      body: JSON.stringify({ sql, parameters, max_rows, timeout_sec }),
    }),
  getQueryHistory: () => request<QueryHistoryItem[]>('/query/history'),
  getSavedQueries: () => request<SavedQuery[]>('/query/saved'),
  saveQuery: (data: { title: string; sql: string; description?: string; tags?: string[]; parameters?: Record<string, any> }) =>
    request<SavedQuery>('/query/saved', {
      method: 'POST',
      body: JSON.stringify(data),
    }),
  deleteSavedQuery: (id: string) =>
    request<{ deleted: boolean; id: string }>(`/query/saved/${id}`, {
      method: 'DELETE',
    }),

  // Schema Explorer
  getTables: () => request<TableSummary[]>('/schema/tables'),
  getTableDetail: (tableName: string) => request<TableDetail>(`/schema/table/${tableName}`),
  getRelationships: () => request<Relationship[]>('/schema/relationships'),

  // Execution Plans
  explainPlan: (sql: string) =>
    request<ExecutionPlanResponse>('/plan/explain', {
      method: 'POST',
      body: JSON.stringify({ sql }),
    }),

  // Comparison Lab
  runComparison: (payload: {
    baseline: { sql: string; label?: string; parameters?: Record<string, any> };
    candidate: { sql: string; label?: string; parameters?: Record<string, any> };
    warmup_runs?: number;
    measured_runs?: number;
    compare_equivalence?: boolean;
    hypothesis?: string;
  }) =>
    request<ComparisonResponse>('/comparison/run', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),

  // Diagnostics
  analyzeError: (errorMessage: string, errorCode?: string, queryText?: string) =>
    request<ErrorAnalysisResponse>('/diagnostics/analyze-error', {
      method: 'POST',
      body: JSON.stringify({ error_message: errorMessage, error_code: errorCode, query_text: queryText }),
    }),
  getKnowledgeBase: () => request<KnowledgeBaseEntry[]>('/diagnostics/knowledge-base'),

  // Investigations
  getInvestigations: () => request<Investigation[]>('/investigations'),
  getInvestigation: (id: string) => request<Investigation>(`/investigations/${id}`),
  createInvestigation: (data: {
    title: string;
    description: string;
    category?: string;
    severity?: string;
    initial_hypothesis?: string;
    baseline_sql?: string;
  }) =>
    request<Investigation>('/investigations', {
      method: 'POST',
      body: JSON.stringify(data),
    }),
  updateInvestigation: (id: string, data: Partial<Investigation>) =>
    request<Investigation>(`/investigations/${id}`, {
      method: 'PATCH',
      body: JSON.stringify(data),
    }),

  // Reports
  generateReport: (investigationId: string) =>
    request<{ report_id: string; html_content: string }>(`/reports/generate`, {
      method: 'POST',
      body: JSON.stringify({ investigation_id: investigationId }),
    }),
};
