import React, { useState, useEffect } from 'react';
import {
  Play, Bookmark, History, Plus, AlertCircle, CheckCircle2,
  Clock, Hash, Database, ChevronRight, X, ArrowUpRight, Zap
} from 'lucide-react';
import { CodeEditor } from '../../components/CodeEditor';
import { DataGrid } from '../../components/DataGrid';
import { QueryExecutionResponse, SavedQuery, QueryHistoryItem } from '../../types';
import { api } from '../../api/client';
import { NavTab } from '../../layouts/AppLayout';

interface WorkspaceViewProps {
  onNavigateToDiagnostics?: (errorCode?: string, errorMsg?: string, sql?: string) => void;
}

export const WorkspaceView: React.FC<WorkspaceViewProps> = ({ onNavigateToDiagnostics }) => {
  const [sql, setSql] = useState<string>(
    `SELECT c.customer_id, c.first_name || ' ' || c.last_name AS customer_name,
       o.order_id, o.order_date, p.product_name, oi.quantity, oi.unit_price, oi.line_total
FROM customers c
JOIN orders o ON c.customer_id = o.customer_id
JOIN order_items oi ON o.order_id = oi.order_id
JOIN products p ON oi.product_id = p.product_id
WHERE o.status = 'COMPLETED'
ORDER BY o.order_date DESC
FETCH FIRST 25 ROWS ONLY`
  );

  const [parameters, setParameters] = useState<Record<string, any>>({});
  const [paramInput, setParamInput] = useState<{ key: string; value: string }>({ key: '', value: '' });
  const [showParamDrawer, setShowParamDrawer] = useState(false);
  const [isExecuting, setIsExecuting] = useState(false);
  const [result, setResult] = useState<QueryExecutionResponse | null>(null);
  const [executionError, setExecutionError] = useState<string | null>(null);

  const [savedQueries, setSavedQueries] = useState<SavedQuery[]>([]);
  const [historyItems, setHistoryItems] = useState<QueryHistoryItem[]>([]);
  const [activeSideDrawer, setActiveSideDrawer] = useState<'saved' | 'history' | null>(null);

  const [newTitle, setNewTitle] = useState('');
  const [showSaveModal, setShowSaveModal] = useState(false);

  useEffect(() => {
    loadSavedQueries();
    loadHistory();
  }, []);

  const loadSavedQueries = async () => {
    try {
      const list = await api.getSavedQueries();
      setSavedQueries(list);
    } catch {
      // Ignored
    }
  };

  const loadHistory = async () => {
    try {
      const list = await api.getQueryHistory();
      setHistoryItems(list);
    } catch {
      // Ignored
    }
  };

  const handleExecute = async () => {
    if (!sql.trim() || isExecuting) return;
    setIsExecuting(true);
    setExecutionError(null);
    try {
      const res = await api.executeQuery(sql, parameters);
      setResult(res);
      loadHistory();
    } catch (err: any) {
      setExecutionError(err.message || 'Execution failed');
    } finally {
      setIsExecuting(false);
    }
  };

  const handleSelectSaved = (saved: SavedQuery) => {
    setSql(saved.sql);
    setParameters(saved.parameters || {});
    setActiveSideDrawer(null);
  };

  const handleSaveCurrent = async () => {
    if (!newTitle.trim()) return;
    try {
      await api.saveQuery({
        title: newTitle,
        sql: sql,
        parameters: parameters,
        tags: ['custom']
      });
      setNewTitle('');
      setShowSaveModal(false);
      loadSavedQueries();
    } catch (err: any) {
      alert(`Save failed: ${err.message}`);
    }
  };

  const handleAddParam = () => {
    if (!paramInput.key.trim()) return;
    setParameters(prev => ({ ...prev, [paramInput.key.trim()]: paramInput.value }));
    setParamInput({ key: '', value: '' });
  };

  const handleRemoveParam = (k: string) => {
    setParameters(prev => {
      const copy = { ...prev };
      delete copy[k];
      return copy;
    });
  };

  return (
    <div className="flex flex-col h-full space-y-3">
      {/* Workspace Top Toolbar */}
      <div className="flex flex-wrap items-center justify-between gap-2 px-3 py-2 bg-slate-900 border border-slate-800 rounded-lg text-xs">
        {/* Scenario loader dropdown */}
        <div className="flex items-center gap-2">
          <span className="text-slate-400 font-medium">Workload Scenario:</span>
          <select
            onChange={e => {
              const selected = savedQueries.find(q => q.id === e.target.value);
              if (selected) handleSelectSaved(selected);
            }}
            className="bg-slate-950 border border-slate-700 rounded px-2.5 py-1 text-slate-200 focus:outline-none focus:border-sky-500 max-w-xs"
            defaultValue=""
          >
            <option value="" disabled>Load retail workload preset...</option>
            {savedQueries.map(q => (
              <option key={q.id} value={q.id}>{q.title}</option>
            ))}
          </select>
        </div>

        {/* Action buttons */}
        <div className="flex items-center gap-2">
          <button
            onClick={() => setShowParamDrawer(!showParamDrawer)}
            className={`px-2.5 py-1 rounded border transition flex items-center gap-1.5 ${
              Object.keys(parameters).length > 0
                ? 'bg-sky-950 border-sky-800 text-sky-300'
                : 'bg-slate-800 hover:bg-slate-700 border-slate-700 text-slate-300'
            }`}
          >
            <span>Bind Params</span>
            {Object.keys(parameters).length > 0 && (
              <span className="px-1 bg-sky-600 text-white rounded text-[10px]">
                {Object.keys(parameters).length}
              </span>
            )}
          </button>

          <button
            onClick={() => setShowSaveModal(true)}
            className="px-2.5 py-1 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded border border-slate-700 transition flex items-center gap-1.5"
          >
            <Bookmark className="w-3.5 h-3.5 text-sky-400" />
            <span>Save Query</span>
          </button>

          <button
            onClick={() => setActiveSideDrawer(activeSideDrawer === 'saved' ? null : 'saved')}
            className="px-2.5 py-1 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded border border-slate-700 transition flex items-center gap-1.5"
          >
            <span>Library</span>
          </button>

          <button
            onClick={() => setActiveSideDrawer(activeSideDrawer === 'history' ? null : 'history')}
            className="px-2.5 py-1 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded border border-slate-700 transition flex items-center gap-1.5"
          >
            <History className="w-3.5 h-3.5 text-amber-400" />
            <span>History</span>
          </button>

          <button
            onClick={handleExecute}
            disabled={isExecuting || !sql.trim()}
            className="px-3.5 py-1 bg-sky-600 hover:bg-sky-500 disabled:opacity-40 text-white font-medium rounded shadow transition flex items-center gap-1.5"
          >
            <Play className={`w-3.5 h-3.5 fill-current ${isExecuting ? 'animate-spin' : ''}`} />
            <span>{isExecuting ? 'Executing...' : 'Run Query'}</span>
          </button>
        </div>
      </div>

      {/* Bind Parameter Drawer */}
      {showParamDrawer && (
        <div className="p-3 bg-slate-900 border border-slate-800 rounded-lg text-xs space-y-2">
          <div className="flex items-center justify-between">
            <span className="font-semibold text-slate-300">Oracle Bind Variables (:name)</span>
            <button onClick={() => setShowParamDrawer(false)} className="text-slate-500 hover:text-slate-300">
              <X className="w-3.5 h-3.5" />
            </button>
          </div>
          <div className="flex items-center gap-2">
            <input
              type="text"
              placeholder="Parameter Name (e.g. status)"
              value={paramInput.key}
              onChange={e => setParamInput({ ...paramInput, key: e.target.value })}
              className="bg-slate-950 border border-slate-700 rounded px-2 py-1 text-slate-200 placeholder-slate-600 w-44"
            />
            <input
              type="text"
              placeholder="Value (e.g. COMPLETED)"
              value={paramInput.value}
              onChange={e => setParamInput({ ...paramInput, value: e.target.value })}
              className="bg-slate-950 border border-slate-700 rounded px-2 py-1 text-slate-200 placeholder-slate-600 flex-1"
            />
            <button
              onClick={handleAddParam}
              className="px-3 py-1 bg-sky-700 hover:bg-sky-600 text-white rounded font-medium"
            >
              Add Bind
            </button>
          </div>

          {Object.keys(parameters).length > 0 && (
            <div className="flex flex-wrap gap-2 pt-1">
              {Object.entries(parameters).map(([k, v]) => (
                <span
                  key={k}
                  className="px-2 py-0.5 rounded bg-slate-800 text-slate-200 border border-slate-700 font-mono text-[11px] flex items-center gap-1.5"
                >
                  <strong className="text-sky-400">:{k}</strong> = {String(v)}
                  <button onClick={() => handleRemoveParam(k)} className="text-slate-500 hover:text-rose-400">
                    ×
                  </button>
                </span>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Main Workspace Split: Editor & Results */}
      <div className="flex-1 flex flex-col md:flex-row gap-3 min-h-0">
        {/* Left: SQL Editor */}
        <div className="flex-1 flex flex-col min-w-0">
          <CodeEditor
            value={sql}
            onChange={setSql}
            onExecute={handleExecute}
            label="SQL Query"
            minHeight="190px"
          />

          {/* Execution Metric Status Bar */}
          {result && (
            <div className="mt-2 px-3 py-1.5 bg-slate-900 border border-slate-800 rounded-md flex flex-wrap items-center justify-between text-[11px] text-slate-400 font-mono">
              <div className="flex items-center gap-4">
                <span className="flex items-center gap-1 text-emerald-400">
                  <CheckCircle2 className="w-3.5 h-3.5" />
                  <span>Success</span>
                </span>
                <span className="flex items-center gap-1">
                  <Clock className="w-3 h-3 text-slate-500" />
                  <span>Exec: <strong className="text-slate-200">{result.duration_ms} ms</strong></span>
                  {result.fetch_duration_ms !== undefined && (
                    <span className="text-slate-500">(fetch: {result.fetch_duration_ms} ms)</span>
                  )}
                </span>
                <span className="flex items-center gap-1">
                  <Hash className="w-3 h-3 text-slate-500" />
                  <span>Rows: <strong className="text-slate-200">{result.rows_returned}</strong></span>
                </span>
              </div>

              <div className="flex items-center gap-3">
                <span className="text-slate-500">ID: {result.query_id}</span>
                <span className="px-1.5 py-0.5 rounded bg-slate-800 text-slate-300 text-[10px]">
                  {result.environment}
                </span>
              </div>
            </div>
          )}

          {/* Error Banner with One-Click Diagnostic Routing */}
          {(executionError || (result && result.status === 'ERROR')) && (
            <div className="mt-2 p-3 bg-rose-950/50 border border-rose-800/80 rounded-md text-xs text-rose-200 space-y-2">
              <div className="flex items-start justify-between">
                <div className="flex items-start gap-2">
                  <AlertCircle className="w-4 h-4 text-rose-400 shrink-0 mt-0.5" />
                  <div>
                    <h5 className="font-semibold text-rose-300">Oracle SQL Execution Error</h5>
                    <p className="font-mono text-[11px] text-rose-200/90 mt-0.5">
                      {executionError || result?.error?.message}
                    </p>
                  </div>
                </div>

                {onNavigateToDiagnostics && (
                  <button
                    onClick={() => onNavigateToDiagnostics(
                      result?.error?.code,
                      executionError || result?.error?.message,
                      sql
                    )}
                    className="px-2.5 py-1 bg-rose-900/60 hover:bg-rose-800 border border-rose-700 rounded text-rose-200 text-xs flex items-center gap-1 transition"
                  >
                    <span>Investigate Error</span>
                    <ArrowUpRight className="w-3 h-3" />
                  </button>
                )}
              </div>
            </div>
          )}

          {/* Results Grid */}
          <div className="flex-1 mt-2 min-h-0">
            {result && result.status === 'SUCCESS' ? (
              <DataGrid
                columns={result.columns}
                rows={result.rows}
                truncated={result.truncated}
              />
            ) : (
              <div className="h-full flex items-center justify-center border border-dashed border-slate-800 rounded-lg text-slate-600 text-xs font-mono">
                Execute a permitted query to inspect rows, schema types, and timings.
              </div>
            )}
          </div>
        </div>

        {/* Right Slide-over: Saved Queries or History */}
        {activeSideDrawer && (
          <div className="w-80 bg-slate-900 border border-slate-800 rounded-lg flex flex-col shrink-0 overflow-hidden text-xs">
            <div className="p-3 border-b border-slate-800 flex items-center justify-between bg-slate-850">
              <span className="font-bold text-slate-200 uppercase tracking-wider text-[11px]">
                {activeSideDrawer === 'saved' ? 'Saved Query Library' : 'Execution History'}
              </span>
              <button onClick={() => setActiveSideDrawer(null)} className="text-slate-500 hover:text-slate-300">
                <X className="w-3.5 h-3.5" />
              </button>
            </div>

            <div className="flex-1 overflow-auto p-2 space-y-1.5 divide-y divide-slate-800/40">
              {activeSideDrawer === 'saved' ? (
                savedQueries.length === 0 ? (
                  <p className="text-slate-500 p-4 text-center">No saved queries yet.</p>
                ) : (
                  savedQueries.map(q => (
                    <div
                      key={q.id}
                      onClick={() => handleSelectSaved(q)}
                      className="p-2.5 hover:bg-slate-800/60 rounded cursor-pointer transition group"
                    >
                      <div className="flex items-center justify-between">
                        <strong className="text-slate-200 group-hover:text-sky-300 text-xs">{q.title}</strong>
                      </div>
                      {q.description && (
                        <p className="text-[11px] text-slate-400 line-clamp-1 mt-0.5">{q.description}</p>
                      )}
                      <pre className="text-[10px] text-slate-500 font-mono truncate mt-1 bg-slate-950/60 p-1 rounded">
                        {q.sql}
                      </pre>
                    </div>
                  ))
                )
              ) : historyItems.length === 0 ? (
                <p className="text-slate-500 p-4 text-center">No history recorded yet.</p>
              ) : (
                historyItems.map((h, idx) => (
                  <div
                    key={idx}
                    onClick={() => setSql(h.sql)}
                    className="p-2 hover:bg-slate-800/60 rounded cursor-pointer transition"
                  >
                    <div className="flex items-center justify-between font-mono text-[10px]">
                      <span className={h.status === 'SUCCESS' ? 'text-emerald-400' : 'text-rose-400'}>
                        {h.status}
                      </span>
                      <span className="text-slate-500">{h.duration_ms} ms • {h.rows_returned} rows</span>
                    </div>
                    <pre className="text-[11px] text-slate-300 font-mono truncate mt-1">
                      {h.sql}
                    </pre>
                  </div>
                ))
              )}
            </div>
          </div>
        )}
      </div>

      {/* Save Query Modal */}
      {showSaveModal && (
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4">
          <div className="bg-slate-900 border border-slate-700 rounded-lg p-5 w-full max-w-md space-y-4 shadow-xl">
            <h4 className="text-sm font-bold text-slate-200">Save Query to Library</h4>
            <div>
              <label className="text-xs text-slate-400 block mb-1">Title</label>
              <input
                type="text"
                value={newTitle}
                onChange={e => setNewTitle(e.target.value)}
                placeholder="e.g. Low Stock Order Report"
                className="w-full bg-slate-950 border border-slate-700 rounded px-3 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-sky-500"
              />
            </div>
            <div className="flex items-center justify-end gap-2 text-xs">
              <button
                onClick={() => setShowSaveModal(false)}
                className="px-3 py-1.5 text-slate-400 hover:text-slate-200"
              >
                Cancel
              </button>
              <button
                onClick={handleSaveCurrent}
                disabled={!newTitle.trim()}
                className="px-3.5 py-1.5 bg-sky-600 hover:bg-sky-500 text-white rounded font-medium disabled:opacity-40"
              >
                Save Query
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
