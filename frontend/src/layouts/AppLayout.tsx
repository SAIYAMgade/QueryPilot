import React, { useState, useEffect } from 'react';
import {
  Database, Terminal, Compass, Network, GitCompare, AlertCircle,
  FileCheck2, FileText, Settings as SettingsIcon, Radio, RefreshCw, ChevronRight, CheckCircle2, AlertTriangle
} from 'lucide-react';
import { ConnectionInfo } from '../types';
import { api } from '../api/client';

export type NavTab =
  | 'overview'
  | 'workspace'
  | 'schema'
  | 'plans'
  | 'comparisons'
  | 'diagnostics'
  | 'investigations'
  | 'reports'
  | 'settings';

interface AppLayoutProps {
  currentTab: NavTab;
  onTabChange: (tab: NavTab) => void;
  children: React.ReactNode;
}

export const AppLayout: React.FC<AppLayoutProps> = ({ currentTab, onTabChange, children }) => {
  const [connInfo, setConnInfo] = useState<ConnectionInfo | null>(null);
  const [isCheckingConn, setIsCheckingConn] = useState(false);

  const fetchConnection = async () => {
    setIsCheckingConn(true);
    try {
      const info = await api.getConnectionStatus();
      setConnInfo(info);
    } catch {
      // Offline fallback
      setConnInfo({
        host: 'localhost',
        port: 1521,
        service_name: 'FREEPDB1',
        user: 'qp_app_user',
        driver: 'python-oracledb (Thin Mode)',
        is_connected: false,
        error_detail: 'API connection offline or unreachable',
        environment: 'Offline Simulation Sandbox'
      });
    } finally {
      setIsCheckingConn(false);
    }
  };

  useEffect(() => {
    fetchConnection();
    const interval = setInterval(fetchConnection, 30000);
    return () => clearInterval(interval);
  }, []);

  const navItems: { id: NavTab; label: string; icon: React.ReactNode }[] = [
    { id: 'overview', label: 'Overview', icon: <Compass className="w-4 h-4" /> },
    { id: 'workspace', label: 'SQL Workspace', icon: <Terminal className="w-4 h-4" /> },
    { id: 'schema', label: 'Schema Explorer', icon: <Database className="w-4 h-4" /> },
    { id: 'plans', label: 'Execution Plans', icon: <Network className="w-4 h-4" /> },
    { id: 'comparisons', label: 'Query Comparisons', icon: <GitCompare className="w-4 h-4" /> },
    { id: 'diagnostics', label: 'Error Diagnostics', icon: <AlertCircle className="w-4 h-4" /> },
    { id: 'investigations', label: 'Investigations', icon: <FileCheck2 className="w-4 h-4" /> },
    { id: 'reports', label: 'Technical Reports', icon: <FileText className="w-4 h-4" /> },
    { id: 'settings', label: 'Settings & Config', icon: <SettingsIcon className="w-4 h-4" /> },
  ];

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-slate-950 text-slate-100">
      {/* Sidebar Navigation */}
      <aside className="w-64 bg-slate-900 border-r border-slate-800 flex flex-col justify-between shrink-0 select-none">
        <div>
          {/* Brand header */}
          <div className="p-4 border-b border-slate-800 flex items-center justify-between">
            <div className="flex items-center gap-2.5">
              <div className="w-8 h-8 rounded-lg bg-sky-600/20 border border-sky-500/40 flex items-center justify-center text-sky-400 font-bold">
                QP
              </div>
              <div>
                <h1 className="font-bold text-sm tracking-tight text-white flex items-center gap-1.5">
                  QueryPilot
                  <span className="text-[10px] px-1.5 py-0.2 bg-slate-800 text-sky-400 rounded border border-slate-700 font-mono">v1.0</span>
                </h1>
                <p className="text-[11px] text-slate-400">Oracle SQL Diagnostics</p>
              </div>
            </div>
          </div>

          {/* Nav links */}
          <nav className="p-2 space-y-0.5">
            {navItems.map(item => {
              const active = currentTab === item.id;
              return (
                <button
                  key={item.id}
                  onClick={() => onTabChange(item.id)}
                  className={`w-full flex items-center gap-3 px-3 py-2 rounded-md text-xs font-medium transition ${
                    active
                      ? 'bg-sky-950/70 text-sky-300 border border-sky-800/60 shadow-sm'
                      : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
                  }`}
                >
                  <span className={active ? 'text-sky-400' : 'text-slate-500'}>{item.icon}</span>
                  <span>{item.label}</span>
                </button>
              );
            })}
          </nav>
        </div>

        {/* Database Connection Status in Sidebar */}
        <div className="p-3 border-t border-slate-800 bg-slate-950/60 text-xs">
          <div className="flex items-center justify-between mb-1.5">
            <span className="text-[11px] text-slate-400 font-medium uppercase tracking-wider">Environment</span>
            <button
              onClick={fetchConnection}
              disabled={isCheckingConn}
              className="text-slate-500 hover:text-slate-300 transition"
              title="Refresh Connection Status"
            >
              <RefreshCw className={`w-3 h-3 ${isCheckingConn ? 'animate-spin text-sky-400' : ''}`} />
            </button>
          </div>

          {connInfo?.is_connected ? (
            <div className="p-2 rounded bg-emerald-950/50 border border-emerald-800/50 text-emerald-300">
              <div className="flex items-center gap-1.5 font-semibold text-[11px]">
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                <span>Live Oracle Connected</span>
              </div>
              <p className="text-[10px] text-emerald-400/80 font-mono mt-0.5 truncate">
                {connInfo.host}:{connInfo.port}/{connInfo.service_name}
              </p>
            </div>
          ) : (
            <div
              onClick={() => onTabChange('settings')}
              className="p-2 rounded bg-amber-950/50 border border-amber-800/50 text-amber-200 cursor-pointer hover:border-amber-700 transition"
              title="Click to view connection settings"
            >
              <div className="flex items-center gap-1.5 font-semibold text-[11px]">
                <AlertTriangle className="w-3.5 h-3.5 text-amber-400" />
                <span>Offline Sandbox Active</span>
              </div>
              <p className="text-[10px] text-amber-300/80 font-mono mt-0.5 truncate">
                Retail Demo Schema • In-Memory
              </p>
            </div>
          )}
        </div>
      </aside>

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col overflow-hidden bg-slate-950">
        {/* Top Navbar */}
        <header className="h-12 border-b border-slate-800 bg-slate-900/90 px-4 flex items-center justify-between shrink-0">
          <div className="flex items-center gap-2 text-xs text-slate-400">
            <span className="font-semibold text-slate-200 capitalize">{currentTab.replace('-', ' ')}</span>
            <ChevronRight className="w-3.5 h-3.5 text-slate-600" />
            <span className="text-slate-500 font-mono text-[11px]">
              {connInfo?.environment || 'QueryPilot Engine'}
            </span>
          </div>

          <div className="flex items-center gap-3 text-xs">
            {/* Live Indicator Pill */}
            <div className="flex items-center gap-2 px-2.5 py-1 bg-slate-800/80 rounded-full border border-slate-700 text-[11px]">
              <span className={`w-2 h-2 rounded-full ${connInfo?.is_connected ? 'bg-emerald-400 animate-pulse' : 'bg-amber-400'}`} />
              <span className="text-slate-300 font-mono">
                {connInfo?.is_connected ? 'Oracle Live' : 'Offline Sandbox'}
              </span>
            </div>

            <span className="text-slate-500 font-mono text-[11px]">
              User: <strong className="text-slate-300">{connInfo?.user || 'QP_APP_USER'}</strong>
            </span>
          </div>
        </header>

        {/* Prominent Environment Notice Banner when Offline */}
        {connInfo && !connInfo.is_connected && (
          <div className="bg-amber-950/40 border-b border-amber-800/40 px-4 py-1.5 flex items-center justify-between text-xs text-amber-200">
            <div className="flex items-center gap-2">
              <span className="w-1.5 h-1.5 rounded-full bg-amber-400" />
              <span>
                <strong>Offline Simulation Sandbox:</strong> Live Oracle DB is unreachable at <code className="bg-slate-900 px-1 py-0.5 rounded text-[11px]">{connInfo.host}:{connInfo.port}/{connInfo.service_name}</code>. Operating in offline demo mode using deterministic retail data.
              </span>
            </div>
            <button
              onClick={() => onTabChange('settings')}
              className="text-[11px] underline hover:text-white transition"
            >
              Configure Oracle Connection →
            </button>
          </div>
        )}

        {/* View Content */}
        <main className="flex-1 overflow-auto p-4">
          {children}
        </main>
      </div>
    </div>
  );
};
