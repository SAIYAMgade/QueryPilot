import React from 'react';
import {
  Database, Terminal, Network, GitCompare, AlertCircle, FileCheck2,
  ShieldCheck, CheckCircle2, ChevronRight, Activity, Cpu, Layers
} from 'lucide-react';
import { NavTab } from '../../layouts/AppLayout';

interface OverviewViewProps {
  onNavigate: (tab: NavTab) => void;
}

export const OverviewView: React.FC<OverviewViewProps> = ({ onNavigate }) => {
  return (
    <div className="max-w-6xl mx-auto space-y-6">
      {/* Hero Welcome Card */}
      <div className="bg-gradient-to-r from-slate-900 via-slate-850 to-slate-900 border border-slate-800 rounded-xl p-6 shadow-md">
        <div className="flex items-start justify-between">
          <div>
            <div className="flex items-center gap-2 mb-2">
              <span className="px-2 py-0.5 rounded text-[10px] font-bold tracking-wider uppercase bg-sky-950 text-sky-400 border border-sky-800">
                Oracle SQL Diagnostic & Performance Workbench
              </span>
            </div>
            <h2 className="text-xl font-bold text-white tracking-tight">
              Welcome to QueryPilot
            </h2>
            <p className="text-xs text-slate-400 max-w-2xl mt-1 leading-relaxed">
              An evidence-based database engineering application designed to investigate Oracle queries,
              understand execution plans, diagnose SQL errors, compare query variants for result equivalence and latency,
              and maintain reproducible investigation case files.
            </p>
          </div>
          <div className="hidden md:flex flex-col items-end text-xs text-slate-400 font-mono">
            <span className="flex items-center gap-1.5 text-sky-400">
              <ShieldCheck className="w-4 h-4" /> Read-Only Execution Enforced
            </span>
            <span className="text-slate-500 mt-1">python-oracledb Thin Mode</span>
          </div>
        </div>

        {/* Quick KPI stats */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mt-6 pt-6 border-t border-slate-800/80">
          <div className="bg-slate-950/60 p-3 rounded-lg border border-slate-800">
            <span className="text-[11px] text-slate-400 block">Retail Demo Entities</span>
            <span className="text-lg font-bold text-slate-100 font-mono">8 Tables</span>
            <span className="text-[10px] text-slate-500 block">Customers, Orders, Items...</span>
          </div>
          <div className="bg-slate-950/60 p-3 rounded-lg border border-slate-800">
            <span className="text-[11px] text-slate-400 block">Optimizer Scenarios</span>
            <span className="text-lg font-bold text-sky-400 font-mono">8 Presets</span>
            <span className="text-[10px] text-slate-500 block">FTS, Index Scan, Joins</span>
          </div>
          <div className="bg-slate-950/60 p-3 rounded-lg border border-slate-800">
            <span className="text-[11px] text-slate-400 block">Diagnostic Knowledge</span>
            <span className="text-lg font-bold text-amber-400 font-mono">Curated KB</span>
            <span className="text-[10px] text-slate-500 block">ORA-00942, 904, 1722...</span>
          </div>
          <div className="bg-slate-950/60 p-3 rounded-lg border border-slate-800">
            <span className="text-[11px] text-slate-400 block">Investigation Workflow</span>
            <span className="text-lg font-bold text-emerald-400 font-mono">Gated</span>
            <span className="text-[10px] text-slate-500 block">Evidence required to resolve</span>
          </div>
        </div>
      </div>

      {/* 5-Minute Technical Interview Demonstration Walkthrough */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-sm">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h3 className="text-sm font-bold text-slate-200 uppercase tracking-wider flex items-center gap-2">
              <Activity className="w-4 h-4 text-sky-400" />
              5-Minute Technical Demonstration Script
            </h3>
            <p className="text-xs text-slate-400 mt-0.5">
              Structured step-by-step workflow designed for technical presentations and architecture interviews.
            </p>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-5 gap-3">
          {/* Step 1 */}
          <div
            onClick={() => onNavigate('schema')}
            className="p-3.5 bg-slate-950/60 hover:bg-slate-800/50 border border-slate-800 rounded-lg cursor-pointer transition group"
          >
            <div className="flex items-center justify-between text-xs font-mono text-sky-400 mb-1.5">
              <span>MINUTE 1</span>
              <ChevronRight className="w-3.5 h-3.5 opacity-0 group-hover:opacity-100 transition" />
            </div>
            <h4 className="text-xs font-semibold text-slate-200">Investigate Database</h4>
            <p className="text-[11px] text-slate-400 mt-1 leading-snug">
              Browse synthetic retail schema (CUSTOMERS, ORDERS), column data types, constraints, and index metadata.
            </p>
          </div>

          {/* Step 2 */}
          <div
            onClick={() => onNavigate('plans')}
            className="p-3.5 bg-slate-950/60 hover:bg-slate-800/50 border border-slate-800 rounded-lg cursor-pointer transition group"
          >
            <div className="flex items-center justify-between text-xs font-mono text-sky-400 mb-1.5">
              <span>MINUTE 2</span>
              <ChevronRight className="w-3.5 h-3.5 opacity-0 group-hover:opacity-100 transition" />
            </div>
            <h4 className="text-xs font-semibold text-slate-200">Inspect Plan</h4>
            <p className="text-[11px] text-slate-400 mt-1 leading-snug">
              Generate EXPLAIN PLAN for a reporting query. Analyze visual tree, cost, operations, and rule-based diagnostic leads.
            </p>
          </div>

          {/* Step 3 */}
          <div
            onClick={() => onNavigate('comparisons')}
            className="p-3.5 bg-slate-950/60 hover:bg-slate-800/50 border border-slate-800 rounded-lg cursor-pointer transition group"
          >
            <div className="flex items-center justify-between text-xs font-mono text-sky-400 mb-1.5">
              <span>MINUTE 3</span>
              <ChevronRight className="w-3.5 h-3.5 opacity-0 group-hover:opacity-100 transition" />
            </div>
            <h4 className="text-xs font-semibold text-slate-200">Compare Queries</h4>
            <p className="text-[11px] text-slate-400 mt-1 leading-snug">
              Execute baseline vs candidate rewrite. Run statistical benchmark iterations and multiset equivalence check.
            </p>
          </div>

          {/* Step 4 */}
          <div
            onClick={() => onNavigate('diagnostics')}
            className="p-3.5 bg-slate-950/60 hover:bg-slate-800/50 border border-slate-800 rounded-lg cursor-pointer transition group"
          >
            <div className="flex items-center justify-between text-xs font-mono text-sky-400 mb-1.5">
              <span>MINUTE 4</span>
              <ChevronRight className="w-3.5 h-3.5 opacity-0 group-hover:opacity-100 transition" />
            </div>
            <h4 className="text-xs font-semibold text-slate-200">Diagnose Errors</h4>
            <p className="text-[11px] text-slate-400 mt-1 leading-snug">
              Trigger a controlled Oracle error (e.g., ORA-00942 or ORA-01722). Inspect curated causes and resolution steps.
            </p>
          </div>

          {/* Step 5 */}
          <div
            onClick={() => onNavigate('reports')}
            className="p-3.5 bg-slate-950/60 hover:bg-slate-800/50 border border-slate-800 rounded-lg cursor-pointer transition group"
          >
            <div className="flex items-center justify-between text-xs font-mono text-sky-400 mb-1.5">
              <span>MINUTE 5</span>
              <ChevronRight className="w-3.5 h-3.5 opacity-0 group-hover:opacity-100 transition" />
            </div>
            <h4 className="text-xs font-semibold text-slate-200">Export Report</h4>
            <p className="text-[11px] text-slate-400 mt-1 leading-snug">
              Review completed investigation case file, audit timeline, plan snapshot, and export reproducible HTML report.
            </p>
          </div>
        </div>
      </div>

      {/* Core Engineering Modules Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-slate-900 border border-slate-800 rounded-lg p-4">
          <div className="flex items-center gap-2 mb-2">
            <Terminal className="w-4 h-4 text-sky-400" />
            <h4 className="text-xs font-bold text-slate-200 uppercase">Controlled SQL Workspace</h4>
          </div>
          <p className="text-xs text-slate-400 leading-relaxed">
            Multi-layer defense against destructive operations. Rejects DDL, DML, multi-statement payloads, and dangerous packages while providing live execution timing and cell-level inspection.
          </p>
        </div>

        <div className="bg-slate-900 border border-slate-800 rounded-lg p-4">
          <div className="flex items-center gap-2 mb-2">
            <Network className="w-4 h-4 text-amber-400" />
            <h4 className="text-xs font-bold text-slate-200 uppercase">Explain Plan Intelligence</h4>
          </div>
          <p className="text-xs text-slate-400 leading-relaxed">
            Extracts hierarchical plan nodes via PLAN_TABLE and DBMS_XPLAN. Differentiates estimated cost models from runtime stats and applies rule-based heuristic observations.
          </p>
        </div>

        <div className="bg-slate-900 border border-slate-800 rounded-lg p-4">
          <div className="flex items-center gap-2 mb-2">
            <FileCheck2 className="w-4 h-4 text-emerald-400" />
            <h4 className="text-xs font-bold text-slate-200 uppercase">Investigation Governance</h4>
          </div>
          <p className="text-xs text-slate-400 leading-relaxed">
            Formal investigation case tracking. Prevents marking problems as resolved without documented root cause and verified verification evidence.
          </p>
        </div>
      </div>
    </div>
  );
};
