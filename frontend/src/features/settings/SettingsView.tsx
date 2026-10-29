import React, { useState, useEffect } from 'react';
import {
  Settings as SettingsIcon, Database, ShieldCheck, Cpu,
  RefreshCw, CheckCircle2, AlertTriangle, Terminal, KeyRound
} from 'lucide-react';
import { ConnectionInfo } from '../../types';
import { api } from '../../api/client';

export const SettingsView: React.FC = () => {
  const [conn, setConn] = useState<ConnectionInfo | null>(null);
  const [isTesting, setIsTesting] = useState(false);

  useEffect(() => {
    loadInfo();
  }, []);

  const loadInfo = async () => {
    setIsTesting(true);
    try {
      const info = await api.getConnectionStatus();
      setConn(info);
    } catch {
      // Ignored
    } finally {
      setIsTesting(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-5 text-xs">
      <div className="bg-slate-900 border border-slate-800 rounded-lg p-5 space-y-4">
        <div className="flex items-center justify-between border-b border-slate-800 pb-3">
          <div className="flex items-center gap-2">
            <Database className="w-4 h-4 text-sky-400" />
            <h3 className="font-bold text-sm text-slate-100">Oracle Database Connection & Driver</h3>
          </div>
          <button
            onClick={loadInfo}
            disabled={isTesting}
            className="px-3 py-1 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded border border-slate-700 flex items-center gap-1.5 transition"
          >
            <RefreshCw className={`w-3 h-3 ${isTesting ? 'animate-spin text-sky-400' : ''}`} />
            <span>Test Reachability</span>
          </button>
        </div>

        {/* Status card */}
        <div className={`p-3.5 rounded-lg border ${
          conn?.is_connected
            ? 'bg-emerald-950/40 border-emerald-800 text-emerald-200'
            : 'bg-amber-950/40 border-amber-800 text-amber-200'
        }`}>
          <div className="flex items-center gap-2 font-bold text-xs">
            {conn?.is_connected ? (
              <CheckCircle2 className="w-4 h-4 text-emerald-400" />
            ) : (
              <AlertTriangle className="w-4 h-4 text-amber-400" />
            )}
            <span>Status: {conn?.is_connected ? 'Connected to Live Oracle' : 'Offline Simulation Sandbox Active'}</span>
          </div>
          <p className="text-[11px] mt-1 opacity-90 leading-relaxed font-mono">
            {conn?.is_connected
              ? `Live session established to ${conn.host}:${conn.port}/${conn.service_name} using ${conn.driver}.`
              : `Oracle Database at ${conn?.host || 'localhost'}:${conn?.port || 1521}/${conn?.service_name || 'FREEPDB1'} is currently unreachable. Operating in deterministic offline sandbox mode.`
            }
          </p>
        </div>

        {/* Connection Parameters */}
        <div className="grid grid-cols-2 gap-3 font-mono">
          <div className="p-2.5 bg-slate-950 border border-slate-800 rounded">
            <span className="text-[10px] text-slate-500 block">ORACLE_HOST</span>
            <span className="text-slate-200">{conn?.host || 'localhost'}</span>
          </div>
          <div className="p-2.5 bg-slate-950 border border-slate-800 rounded">
            <span className="text-[10px] text-slate-500 block">ORACLE_PORT</span>
            <span className="text-slate-200">{conn?.port || 1521}</span>
          </div>
          <div className="p-2.5 bg-slate-950 border border-slate-800 rounded">
            <span className="text-[10px] text-slate-500 block">ORACLE_SERVICE_NAME</span>
            <span className="text-slate-200">{conn?.service_name || 'FREEPDB1'}</span>
          </div>
          <div className="p-2.5 bg-slate-950 border border-slate-800 rounded">
            <span className="text-[10px] text-slate-500 block">APPLICATION USER (Least Privilege)</span>
            <span className="text-slate-200">{conn?.user || 'qp_app_user'}</span>
          </div>
        </div>
      </div>

      {/* Safety & Execution Guardrails */}
      <div className="bg-slate-900 border border-slate-800 rounded-lg p-5 space-y-3">
        <div className="flex items-center gap-2 border-b border-slate-800 pb-2">
          <ShieldCheck className="w-4 h-4 text-emerald-400" />
          <h3 className="font-bold text-sm text-slate-100">Safety & Resource Guardrails</h3>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
          <div className="p-3 bg-slate-950 border border-slate-800 rounded">
            <span className="text-[11px] text-slate-400 block font-semibold">Max Execution Timeout</span>
            <span className="text-lg font-mono font-bold text-slate-200">30 seconds</span>
            <p className="text-[10px] text-slate-500 mt-0.5">Enforced via driver cursor call_timeout.</p>
          </div>
          <div className="p-3 bg-slate-950 border border-slate-800 rounded">
            <span className="text-[11px] text-slate-400 block font-semibold">Max Rows Returned</span>
            <span className="text-lg font-mono font-bold text-slate-200">1,000 rows</span>
            <p className="text-[10px] text-slate-500 mt-0.5">Protects browser memory and network buffers.</p>
          </div>
          <div className="p-3 bg-slate-950 border border-slate-800 rounded">
            <span className="text-[11px] text-slate-400 block font-semibold">Read-Only AST Validation</span>
            <span className="text-lg font-mono font-bold text-emerald-400">Strictly Enforced</span>
            <p className="text-[10px] text-slate-500 mt-0.5">Rejects DDL, DML, TCL, multi-statement payloads.</p>
          </div>
        </div>
      </div>

      {/* Local Oracle Setup Guide */}
      <div className="bg-slate-900 border border-slate-800 rounded-lg p-5 space-y-3">
        <div className="flex items-center gap-2 border-b border-slate-800 pb-2">
          <Terminal className="w-4 h-4 text-sky-400" />
          <h3 className="font-bold text-sm text-slate-100">Live Oracle Database 23ai Free Setup Guide</h3>
        </div>
        <p className="text-slate-400 leading-relaxed">
          To run live queries and execute actual Oracle EXPLAIN PLAN against a live database container:
        </p>
        <div className="space-y-2 font-mono text-[11px]">
          <div className="p-2.5 bg-slate-950 rounded border border-slate-800 text-slate-300">
            <span className="text-slate-500 select-none block mb-1"># 1. Start Oracle Database 23ai Free in Docker:</span>
            docker run -d --name oracle23ai -p 1521:1521 -e ORACLE_PWD=oracle_password container-registry.oracle.com/database/free:latest
          </div>
          <div className="p-2.5 bg-slate-950 rounded border border-slate-800 text-slate-300">
            <span className="text-slate-500 select-none block mb-1"># 2. Initialize schema & synthetic data:</span>
            python database/seed/generate_data.py small database/seed/seed_data.sql
          </div>
        </div>
      </div>
    </div>
  );
};
