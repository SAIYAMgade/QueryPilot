import React, { useState } from 'react';
import {
  Network, Play, AlertCircle, Info, ShieldAlert, Cpu,
  Layers, ArrowDownRight, FileText, ChevronDown, ChevronRight
} from 'lucide-react';
import { CodeEditor } from '../../components/CodeEditor';
import { ExecutionPlanResponse, PlanOperation, DiagnosticObservation } from '../../types';
import { api } from '../../api/client';

export const ExecutionPlansView: React.FC = () => {
  const [sql, setSql] = useState<string>(
    `SELECT c.customer_id, c.first_name, o.order_id, o.order_date, o.total_amount
FROM customers c
JOIN orders o ON c.customer_id = o.customer_id
WHERE o.order_date >= '2025-06-01'
ORDER BY o.order_date DESC
FETCH FIRST 50 ROWS ONLY`
  );

  const [isExplaining, setIsExplaining] = useState(false);
  const [planResult, setPlanResult] = useState<ExecutionPlanResponse | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [viewMode, setViewMode] = useState<'tree' | 'table' | 'raw'>('tree');

  const handleExplain = async () => {
    if (!sql.trim() || isExplaining) return;
    setIsExplaining(true);
    setErrorMsg(null);
    try {
      const res = await api.explainPlan(sql);
      setPlanResult(res);
    } catch (err: any) {
      setErrorMsg(err.message || 'Failed to generate plan');
    } finally {
      setIsExplaining(false);
    }
  };

  const getSeverityBadge = (sev: DiagnosticObservation['severity']) => {
    switch (sev) {
      case 'CRITICAL':
        return 'bg-rose-950 text-rose-300 border-rose-800';
      case 'WARNING':
        return 'bg-amber-950 text-amber-300 border-amber-800';
      case 'INVESTIGATE':
        return 'bg-sky-950 text-sky-300 border-sky-800';
      case 'INFO':
      default:
        return 'bg-slate-800 text-slate-300 border-slate-700';
    }
  };

  return (
    <div className="flex flex-col h-full space-y-3">
      {/* Top Controls */}
      <div className="bg-slate-900 border border-slate-800 rounded-lg p-3 text-xs space-y-2">
        <div className="flex items-center justify-between">
          <span className="font-bold text-slate-200 uppercase tracking-wider flex items-center gap-1.5">
            <Network className="w-4 h-4 text-sky-400" />
            Oracle Cost-Based Optimizer Explain Plan
          </span>
          <button
            onClick={handleExplain}
            disabled={isExplaining || !sql.trim()}
            className="px-3 py-1 bg-sky-600 hover:bg-sky-500 disabled:opacity-40 text-white font-medium rounded shadow transition flex items-center gap-1.5"
          >
            <Play className={`w-3 h-3 fill-current ${isExplaining ? 'animate-spin' : ''}`} />
            <span>{isExplaining ? 'Computing Plan...' : 'Explain Plan'}</span>
          </button>
        </div>

        <CodeEditor
          value={sql}
          onChange={setSql}
          onExecute={handleExplain}
          label="Query to Explain"
          minHeight="110px"
        />
      </div>

      {errorMsg && (
        <div className="p-3 bg-rose-950/50 border border-rose-800 rounded text-xs text-rose-200 flex items-center gap-2">
          <AlertCircle className="w-4 h-4 text-rose-400 shrink-0" />
          <span>{errorMsg}</span>
        </div>
      )}

      {/* Plan Details Split: Visual Tree/Table & Diagnostic Leads */}
      {planResult && (
        <div className="flex-1 flex flex-col md:flex-row gap-3 min-h-0">
          {/* Left: Plan Display */}
          <div className="flex-1 bg-slate-900 border border-slate-800 rounded-lg flex flex-col overflow-hidden">
            {/* Plan Header Bar */}
            <div className="p-3 border-b border-slate-800 bg-slate-850 flex items-center justify-between text-xs">
              <div className="flex items-center gap-3">
                <span className="font-mono text-slate-300">
                  Statement ID: <strong className="text-sky-400">{planResult.statement_id}</strong>
                </span>
                {planResult.optimizer_cost !== null && (
                  <span className="px-2 py-0.5 rounded bg-slate-800 text-slate-300 font-mono text-[11px]">
                    Cost: <strong>{planResult.optimizer_cost}</strong>
                  </span>
                )}
                <span className="px-2 py-0.5 rounded bg-amber-950/60 border border-amber-800/60 text-amber-300 text-[10px] font-mono">
                  {planResult.plan_type} PLAN
                </span>
              </div>

              {/* View toggle */}
              <div className="flex items-center gap-1 bg-slate-950 p-0.5 rounded border border-slate-800 text-[11px]">
                <button
                  onClick={() => setViewMode('tree')}
                  className={`px-2 py-0.5 rounded transition ${viewMode === 'tree' ? 'bg-sky-600 text-white font-medium' : 'text-slate-400 hover:text-slate-200'}`}
                >
                  Visual Tree
                </button>
                <button
                  onClick={() => setViewMode('table')}
                  className={`px-2 py-0.5 rounded transition ${viewMode === 'table' ? 'bg-sky-600 text-white font-medium' : 'text-slate-400 hover:text-slate-200'}`}
                >
                  Operations Table
                </button>
                <button
                  onClick={() => setViewMode('raw')}
                  className={`px-2 py-0.5 rounded transition ${viewMode === 'raw' ? 'bg-sky-600 text-white font-medium' : 'text-slate-400 hover:text-slate-200'}`}
                >
                  Raw DBMS_XPLAN
                </button>
              </div>
            </div>

            {/* Contextual limitation reminder */}
            <div className="px-3 py-1.5 bg-slate-950/40 border-b border-slate-800/80 text-[11px] text-slate-400">
              {planResult.limitations_note}
            </div>

            {/* Plan Body */}
            <div className="flex-1 overflow-auto p-3">
              {viewMode === 'tree' && (
                <div className="space-y-2">
                  {planResult.operations.map(op => {
                    const indentPx = op.depth * 24;
                    return (
                      <div
                        key={op.id}
                        className="flex items-start gap-2 text-xs font-mono p-2 rounded bg-slate-950/80 border border-slate-800 hover:border-slate-700 transition"
                        style={{ marginLeft: `${indentPx}px` }}
                      >
                        <div className="px-1.5 py-0.5 rounded bg-slate-800 text-slate-400 text-[10px]">
                          Id {op.id}
                        </div>
                        <div className="flex-1 space-y-1">
                          <div className="flex items-center gap-2">
                            <span className="font-bold text-sky-300">{op.operation}</span>
                            {op.options && (
                              <span className="px-1.5 py-0.2 rounded bg-slate-800 text-amber-300 text-[10px]">
                                {op.options}
                              </span>
                            )}
                            {op.object_name && (
                              <span className="text-slate-200 font-semibold underline decoration-slate-700">
                                [{op.object_name}]
                              </span>
                            )}
                          </div>

                          <div className="flex flex-wrap items-center gap-3 text-[10px] text-slate-500">
                            {op.cost !== null && <span>Cost: <strong className="text-slate-300">{op.cost}</strong></span>}
                            {op.cardinality !== null && <span>Rows: <strong className="text-slate-300">{op.cardinality}</strong></span>}
                            {op.bytes !== null && <span>Bytes: <strong className="text-slate-300">{op.bytes}</strong></span>}
                            {op.time_sec !== null && <span>Est Time: <strong className="text-slate-300">{op.time_sec}s</strong></span>}
                          </div>

                          {op.access_predicates && (
                            <p className="text-[10px] text-emerald-400/90 truncate">
                              Access: {op.access_predicates}
                            </p>
                          )}
                          {op.filter_predicates && (
                            <p className="text-[10px] text-amber-400/90 truncate">
                              Filter: {op.filter_predicates}
                            </p>
                          )}
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}

              {viewMode === 'table' && (
                <table className="w-full text-left text-xs border-collapse">
                  <thead className="bg-slate-950 text-slate-400 border-b border-slate-800">
                    <tr>
                      <th className="py-2 px-2.5">Id</th>
                      <th className="py-2 px-3">Operation</th>
                      <th className="py-2 px-3">Object</th>
                      <th className="py-2 px-2">Cost</th>
                      <th className="py-2 px-2">Rows</th>
                      <th className="py-2 px-2">Bytes</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60 font-mono text-slate-200">
                    {planResult.operations.map(op => (
                      <tr key={op.id} className="hover:bg-slate-850">
                        <td className="py-1.5 px-2.5 text-slate-500">{op.id}</td>
                        <td className="py-1.5 px-3">
                          <span style={{ paddingLeft: `${op.depth * 12}px` }}>
                            {op.operation} {op.options || ''}
                          </span>
                        </td>
                        <td className="py-1.5 px-3 text-sky-400">{op.object_name || '-'}</td>
                        <td className="py-1.5 px-2">{op.cost ?? '-'}</td>
                        <td className="py-1.5 px-2">{op.cardinality ?? '-'}</td>
                        <td className="py-1.5 px-2">{op.bytes ?? '-'}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}

              {viewMode === 'raw' && (
                <pre className="p-3 bg-slate-950 rounded border border-slate-800 font-mono text-xs text-slate-300 overflow-auto whitespace-pre">
                  {planResult.raw_plan_text || 'No raw DBMS_XPLAN text available.'}
                </pre>
              )}
            </div>
          </div>

          {/* Right: Diagnostic Leads & Observations */}
          <div className="w-96 bg-slate-900 border border-slate-800 rounded-lg flex flex-col overflow-hidden text-xs shrink-0">
            <div className="p-3 border-b border-slate-800 bg-slate-850 flex items-center justify-between">
              <span className="font-bold text-slate-200 uppercase tracking-wider text-[11px] flex items-center gap-1.5">
                <AlertCircle className="w-3.5 h-3.5 text-amber-400" />
                Diagnostic Leads ({planResult.observations.length})
              </span>
              <span className="text-[10px] text-slate-500">Evidence-based leads</span>
            </div>

            <div className="flex-1 overflow-auto p-3 space-y-3">
              {planResult.observations.length === 0 ? (
                <div className="text-center p-6 text-slate-500">
                  No heuristic bottlenecks detected for this execution plan.
                </div>
              ) : (
                planResult.observations.map(obs => (
                  <div key={obs.id} className="p-3 bg-slate-950 border border-slate-800 rounded-lg space-y-2">
                    <div className="flex items-start justify-between gap-2">
                      <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase border ${getSeverityBadge(obs.severity)}`}>
                        {obs.severity} • {obs.confidence}
                      </span>
                    </div>

                    <h5 className="font-semibold text-slate-200 text-xs">{obs.title}</h5>

                    <p className="text-[11px] text-slate-400 leading-snug">
                      <strong>Observed:</strong> {obs.what_observed}
                    </p>

                    <p className="text-[11px] text-slate-400 leading-snug">
                      <strong>Why it matters:</strong> {obs.why_it_matters}
                    </p>

                    <div className="p-2 bg-slate-900 rounded border border-slate-800/80 text-[10px] text-sky-300 font-mono">
                      <strong>Recommended check:</strong> {obs.suggested_step}
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
