import React, { useState } from 'react';
import {
  GitCompare, Play, CheckCircle2, AlertTriangle, Clock, Hash,
  Zap, ShieldAlert, ArrowRight, Layers, FileCheck2
} from 'lucide-react';
import { CodeEditor } from '../../components/CodeEditor';
import { ComparisonResponse } from '../../types';
import { api } from '../../api/client';
import { NavTab } from '../../layouts/AppLayout';

interface ComparisonViewProps {
  onOpenInvestigation?: (data: { baselineSql: string; candidateSql: string; hypothesis?: string }) => void;
}

export const ComparisonView: React.FC<ComparisonViewProps> = ({ onOpenInvestigation }) => {
  const [baselineSql, setBaselineSql] = useState<string>(
    `-- Baseline: Date filter without index hint (Full Table Scan)
SELECT o.order_id, o.order_date, o.total_amount, c.email
FROM orders o
JOIN customers c ON o.customer_id = c.customer_id
WHERE o.order_date >= '2025-06-01'
ORDER BY o.order_date DESC
FETCH FIRST 50 ROWS ONLY`
  );

  const [candidateSql, setCandidateSql] = useState<string>(
    `-- Candidate: Indexed range scan
SELECT /*+ INDEX(o IDX_ORDERS_DATE) */ o.order_id, o.order_date, o.total_amount, c.email
FROM orders o
JOIN customers c ON o.customer_id = c.customer_id
WHERE o.order_date >= '2025-06-01'
ORDER BY o.order_date DESC
FETCH FIRST 50 ROWS ONLY`
  );

  const [hypothesis, setHypothesis] = useState<string>(
    'Utilizing IDX_ORDERS_DATE for date range filtering reduces buffer gets and execution duration.'
  );

  const [warmupRuns, setWarmupRuns] = useState(1);
  const [measuredRuns, setMeasuredRuns] = useState(3);
  const [isRunning, setIsRunning] = useState(false);
  const [comparison, setComparison] = useState<ComparisonResponse | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const handleRunComparison = async () => {
    if (!baselineSql.trim() || !candidateSql.trim() || isRunning) return;
    setIsRunning(true);
    setErrorMsg(null);
    try {
      const res = await api.runComparison({
        baseline: { sql: baselineSql, label: 'Baseline Query' },
        candidate: { sql: candidateSql, label: 'Candidate Rewrite' },
        warmup_runs: warmupRuns,
        measured_runs: measuredRuns,
        compare_equivalence: true,
        hypothesis: hypothesis
      });
      setComparison(res);
    } catch (err: any) {
      setErrorMsg(err.message || 'Comparison failed');
    } finally {
      setIsRunning(false);
    }
  };

  return (
    <div className="flex flex-col h-full space-y-3">
      {/* Configuration Bar */}
      <div className="bg-slate-900 border border-slate-800 rounded-lg p-3 text-xs space-y-2">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <span className="font-bold text-slate-200 uppercase tracking-wider flex items-center gap-1.5">
            <GitCompare className="w-4 h-4 text-sky-400" />
            Query Comparison Lab & Equivalence Checker
          </span>

          <div className="flex items-center gap-3">
            <div className="flex items-center gap-1.5 text-slate-400">
              <span>Warmup:</span>
              <input
                type="number"
                min={0}
                max={3}
                value={warmupRuns}
                onChange={e => setWarmupRuns(Number(e.target.value))}
                className="w-12 bg-slate-950 border border-slate-700 rounded px-1.5 py-0.5 text-slate-200 text-center"
              />
            </div>
            <div className="flex items-center gap-1.5 text-slate-400">
              <span>Measured Runs:</span>
              <input
                type="number"
                min={1}
                max={5}
                value={measuredRuns}
                onChange={e => setMeasuredRuns(Number(e.target.value))}
                className="w-12 bg-slate-950 border border-slate-700 rounded px-1.5 py-0.5 text-slate-200 text-center"
              />
            </div>

            <button
              onClick={handleRunComparison}
              disabled={isRunning || !baselineSql.trim() || !candidateSql.trim()}
              className="px-3.5 py-1 bg-sky-600 hover:bg-sky-500 disabled:opacity-40 text-white font-medium rounded shadow transition flex items-center gap-1.5"
            >
              <Play className={`w-3.5 h-3.5 fill-current ${isRunning ? 'animate-spin' : ''}`} />
              <span>{isRunning ? 'Comparing...' : 'Run Benchmark'}</span>
            </button>
          </div>
        </div>

        {/* Hypothesis Input */}
        <div>
          <label className="text-[11px] text-slate-400 block mb-0.5">Investigation Hypothesis</label>
          <input
            type="text"
            value={hypothesis}
            onChange={e => setHypothesis(e.target.value)}
            placeholder="Document what you expect to change and why..."
            className="w-full bg-slate-950 border border-slate-700 rounded px-2.5 py-1 text-slate-200 focus:outline-none focus:border-sky-500 text-xs"
          />
        </div>
      </div>

      {errorMsg && (
        <div className="p-3 bg-rose-950/50 border border-rose-800 rounded text-xs text-rose-200">
          {errorMsg}
        </div>
      )}

      {/* Side-by-side SQL Editors */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
        <CodeEditor
          value={baselineSql}
          onChange={setBaselineSql}
          label="Baseline SQL (Variant A)"
          minHeight="140px"
        />
        <CodeEditor
          value={candidateSql}
          onChange={setCandidateSql}
          label="Candidate SQL (Variant B)"
          minHeight="140px"
        />
      </div>

      {/* Comparison Results Card */}
      {comparison && (
        <div className="flex-1 bg-slate-900 border border-slate-800 rounded-lg p-4 overflow-auto space-y-4 text-xs">
          {/* Equivalence and Speedup Header */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-3">
            {/* Equivalence Card */}
            <div className={`p-3 rounded-lg border flex flex-col justify-between ${
              comparison.equivalence.is_equivalent
                ? 'bg-emerald-950/40 border-emerald-800 text-emerald-300'
                : 'bg-rose-950/40 border-rose-800 text-rose-300'
            }`}>
              <span className="text-[10px] uppercase font-bold tracking-wider">Result Equivalence</span>
              <div className="flex items-center gap-2 mt-1">
                {comparison.equivalence.is_equivalent ? (
                  <CheckCircle2 className="w-5 h-5 text-emerald-400" />
                ) : (
                  <AlertTriangle className="w-5 h-5 text-rose-400" />
                )}
                <span className="text-sm font-bold">{comparison.equivalence.status}</span>
              </div>
              <p className="text-[10px] mt-1 opacity-90 leading-tight">
                {comparison.equivalence.reason}
              </p>
            </div>

            {/* Baseline Median */}
            <div className="p-3 rounded-lg border border-slate-800 bg-slate-950 flex flex-col justify-between">
              <span className="text-[10px] uppercase font-bold text-slate-400">Baseline Median</span>
              <span className="text-xl font-bold font-mono text-slate-100">
                {comparison.baseline_stats.median_ms} <span className="text-xs font-normal text-slate-400">ms</span>
              </span>
              <span className="text-[10px] text-slate-500 font-mono">
                min: {comparison.baseline_stats.min_ms}ms • max: {comparison.baseline_stats.max_ms}ms
              </span>
            </div>

            {/* Candidate Median */}
            <div className="p-3 rounded-lg border border-slate-800 bg-slate-950 flex flex-col justify-between">
              <span className="text-[10px] uppercase font-bold text-slate-400">Candidate Median</span>
              <span className="text-xl font-bold font-mono text-sky-400">
                {comparison.candidate_stats.median_ms} <span className="text-xs font-normal text-slate-400">ms</span>
              </span>
              <span className="text-[10px] text-slate-500 font-mono">
                min: {comparison.candidate_stats.min_ms}ms • max: {comparison.candidate_stats.max_ms}ms
              </span>
            </div>

            {/* Speedup Factor */}
            <div className="p-3 rounded-lg border border-slate-800 bg-slate-950 flex flex-col justify-between">
              <span className="text-[10px] uppercase font-bold text-slate-400">Measured Speedup</span>
              <span className="text-xl font-bold font-mono text-emerald-400">
                {comparison.speedup_ratio ? `${comparison.speedup_ratio}x` : 'Equal'}
              </span>
              <span className="text-[10px] text-slate-500 truncate">
                {comparison.improvement_summary}
              </span>
            </div>
          </div>

          {/* Repeatable Runs Table */}
          <div className="border border-slate-800 rounded-lg overflow-hidden">
            <div className="p-2.5 bg-slate-850 border-b border-slate-800 flex items-center justify-between">
              <span className="font-semibold text-slate-200">Iteration Latency Measurements ({comparison.runs_data.length} runs)</span>
              {onOpenInvestigation && (
                <button
                  onClick={() => onOpenInvestigation({
                    baselineSql: baselineSql,
                    candidateSql: candidateSql,
                    hypothesis: hypothesis
                  })}
                  className="px-2.5 py-1 bg-sky-700 hover:bg-sky-600 text-white rounded text-xs flex items-center gap-1.5 transition"
                >
                  <FileCheck2 className="w-3.5 h-3.5" />
                  <span>Log as Investigation Case</span>
                </button>
              )}
            </div>

            <table className="w-full text-left text-xs font-mono">
              <thead className="bg-slate-950 text-slate-400 border-b border-slate-800">
                <tr>
                  <th className="py-2 px-3">Run #</th>
                  <th className="py-2 px-3">Baseline Duration (ms)</th>
                  <th className="py-2 px-3">Candidate Duration (ms)</th>
                  <th className="py-2 px-3">Row Counts</th>
                  <th className="py-2 px-3">Run Delta</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 text-slate-200">
                {comparison.runs_data.map(run => {
                  const delta = roundDec(run.baseline_duration_ms - run.candidate_duration_ms);
                  const isFaster = delta > 0;
                  return (
                    <tr key={run.run_index} className="hover:bg-slate-850">
                      <td className="py-1.5 px-3 text-slate-500">Run {run.run_index}</td>
                      <td className="py-1.5 px-3">{run.baseline_duration_ms} ms</td>
                      <td className="py-1.5 px-3 text-sky-400">{run.candidate_duration_ms} ms</td>
                      <td className="py-1.5 px-3 text-slate-400">{run.baseline_rows} vs {run.candidate_rows}</td>
                      <td className={`py-1.5 px-3 ${isFaster ? 'text-emerald-400' : 'text-slate-400'}`}>
                        {isFaster ? `-${delta} ms (faster)` : `+${Math.abs(delta)} ms`}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>

          {/* Caveat notification */}
          <div className="p-3 bg-slate-950 border border-slate-800 rounded text-slate-400 text-[11px] leading-relaxed">
            <strong className="text-slate-300">Measurement Limits & Transparency:</strong> {comparison.caveat}
          </div>
        </div>
      )}
    </div>
  );
};

function roundDec(val: number): number {
  return Math.round(val * 100) / 100;
}
