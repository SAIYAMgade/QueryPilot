import React, { useState, useEffect } from 'react';
import {
  FileCheck2, Plus, Clock, AlertCircle, CheckCircle2, ChevronRight,
  ShieldCheck, ArrowRight, Save, Edit3, X, FileText
} from 'lucide-react';
import { Investigation, InvestigationStatus, InvestigationSeverity } from '../../types';
import { api } from '../../api/client';

interface InvestigationsViewProps {
  onViewReport?: (invId: string) => void;
  prefillData?: { baselineSql: string; candidateSql: string; hypothesis?: string } | null;
}

export const InvestigationsView: React.FC<InvestigationsViewProps> = ({ onViewReport, prefillData }) => {
  const [investigations, setInvestigations] = useState<Investigation[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [selectedInv, setSelectedInv] = useState<Investigation | null>(null);
  const [statusFilter, setStatusFilter] = useState<string>('ALL');
  const [isUpdating, setIsUpdating] = useState(false);
  const [updateError, setUpdateError] = useState<string | null>(null);

  // New Case Modal State
  const [showNewModal, setShowNewModal] = useState(false);
  const [newTitle, setNewTitle] = useState('');
  const [newDesc, setNewDesc] = useState('');
  const [newCategory, setNewCategory] = useState('PERFORMANCE');
  const [newSeverity, setNewSeverity] = useState<InvestigationSeverity>('MEDIUM');
  const [newHypothesis, setNewHypothesis] = useState('');

  // Editable fields for detail
  const [editRootCause, setEditRootCause] = useState('');
  const [editProposedFix, setEditProposedFix] = useState('');
  const [editVerification, setEditVerification] = useState('');
  const [targetStatus, setTargetStatus] = useState<InvestigationStatus>('OPEN');

  useEffect(() => {
    loadInvestigations();
  }, []);

  useEffect(() => {
    if (prefillData) {
      setNewTitle('Performance Comparison Investigation');
      setNewDesc('Investigating execution duration discrepancy between baseline and candidate rewrite.');
      setNewHypothesis(prefillData.hypothesis || '');
      setShowNewModal(true);
    }
  }, [prefillData]);

  const loadInvestigations = async () => {
    try {
      const list = await api.getInvestigations();
      setInvestigations(list);
      if (list.length > 0 && !selectedId) {
        handleSelectInvestigation(list[0].id);
      }
    } catch {
      // Ignored
    }
  };

  const handleSelectInvestigation = async (id: string) => {
    setSelectedId(id);
    setUpdateError(null);
    try {
      const inv = await api.getInvestigation(id);
      setSelectedInv(inv);
      setEditRootCause(inv.root_cause_explanation || '');
      setEditProposedFix(inv.proposed_fix || '');
      setEditVerification(inv.verification_notes || '');
      setTargetStatus(inv.status);
    } catch (err: any) {
      alert(`Failed to load investigation: ${err.message}`);
    }
  };

  const handleCreateNew = async () => {
    if (!newTitle.trim()) return;
    try {
      const created = await api.createInvestigation({
        title: newTitle,
        description: newDesc,
        category: newCategory,
        severity: newSeverity,
        initial_hypothesis: newHypothesis,
        baseline_sql: prefillData?.baselineSql
      });
      setShowNewModal(false);
      setNewTitle('');
      setNewDesc('');
      setNewHypothesis('');
      await loadInvestigations();
      handleSelectInvestigation(created.id);
    } catch (err: any) {
      alert(`Creation failed: ${err.message}`);
    }
  };

  const handleUpdate = async () => {
    if (!selectedId) return;
    setIsUpdating(true);
    setUpdateError(null);
    try {
      const updated = await api.updateInvestigation(selectedId, {
        status: targetStatus,
        root_cause_explanation: editRootCause,
        proposed_fix: editProposedFix,
        verification_notes: editVerification
      });
      setSelectedInv(updated);
      loadInvestigations();
    } catch (err: any) {
      setUpdateError(err.message || 'Update failed');
    } finally {
      setIsUpdating(false);
    }
  };

  const filteredList = investigations.filter(inv =>
    statusFilter === 'ALL' ? true : inv.status === statusFilter
  );

  const getStatusBadge = (st: InvestigationStatus) => {
    switch (st) {
      case 'RESOLVED':
        return 'bg-emerald-950 text-emerald-300 border-emerald-800';
      case 'INVESTIGATING':
        return 'bg-sky-950 text-sky-300 border-sky-800';
      case 'FIX_PROPOSED':
        return 'bg-indigo-950 text-indigo-300 border-indigo-800';
      case 'VALIDATION_REQUIRED':
        return 'bg-purple-950 text-purple-300 border-purple-800';
      case 'CLOSED_INCONCLUSIVE':
        return 'bg-slate-800 text-slate-400 border-slate-700';
      case 'OPEN':
      default:
        return 'bg-amber-950 text-amber-300 border-amber-800';
    }
  };

  return (
    <div className="flex h-full gap-4 text-xs">
      {/* Left: Case List Sidebar */}
      <div className="w-80 bg-slate-900 border border-slate-800 rounded-lg flex flex-col shrink-0 overflow-hidden">
        <div className="p-3 border-b border-slate-800 bg-slate-850 space-y-2">
          <div className="flex items-center justify-between">
            <span className="font-bold text-slate-200 uppercase tracking-wider text-[11px] flex items-center gap-1.5">
              <FileCheck2 className="w-3.5 h-3.5 text-sky-400" />
              Investigation Cases ({investigations.length})
            </span>
            <button
              onClick={() => setShowNewModal(true)}
              className="px-2 py-0.5 bg-sky-600 hover:bg-sky-500 text-white rounded text-[11px] font-medium flex items-center gap-1 transition"
            >
              <Plus className="w-3 h-3" />
              <span>New Case</span>
            </button>
          </div>

          {/* Filter */}
          <select
            value={statusFilter}
            onChange={e => setStatusFilter(e.target.value)}
            className="w-full bg-slate-950 border border-slate-700 rounded px-2 py-1 text-slate-200 text-xs focus:outline-none"
          >
            <option value="ALL">All Statuses</option>
            <option value="OPEN">Open</option>
            <option value="INVESTIGATING">Investigating</option>
            <option value="FIX_PROPOSED">Fix Proposed</option>
            <option value="VALIDATION_REQUIRED">Validation Required</option>
            <option value="RESOLVED">Resolved</option>
            <option value="CLOSED_INCONCLUSIVE">Closed Inconclusive</option>
          </select>
        </div>

        <div className="flex-1 overflow-auto p-1.5 space-y-1.5 divide-y divide-slate-800/40">
          {filteredList.map(inv => {
            const isSelected = selectedId === inv.id;
            return (
              <div
                key={inv.id}
                onClick={() => handleSelectInvestigation(inv.id)}
                className={`p-2.5 rounded cursor-pointer transition ${
                  isSelected
                    ? 'bg-sky-950/80 border border-sky-800/80 shadow-sm'
                    : 'hover:bg-slate-800/60'
                }`}
              >
                <div className="flex items-center justify-between mb-1">
                  <span className="font-mono text-[11px] text-sky-400 font-bold">{inv.id}</span>
                  <span className={`px-1.5 py-0.2 rounded text-[9px] font-bold uppercase border ${getStatusBadge(inv.status)}`}>
                    {inv.status}
                  </span>
                </div>
                <h5 className="font-semibold text-slate-200 text-xs line-clamp-1">{inv.title}</h5>
                <p className="text-[11px] text-slate-400 line-clamp-1 mt-0.5">{inv.description}</p>
              </div>
            );
          })}
        </div>
      </div>

      {/* Right: Selected Case Detail */}
      <div className="flex-1 bg-slate-900 border border-slate-800 rounded-lg flex flex-col overflow-hidden">
        {selectedInv ? (
          <>
            {/* Case Header */}
            <div className="p-4 border-b border-slate-800 bg-slate-850 flex items-start justify-between">
              <div>
                <div className="flex items-center gap-2 mb-1">
                  <span className="font-mono text-sky-400 font-bold text-xs">{selectedInv.id}</span>
                  <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase border ${getStatusBadge(selectedInv.status)}`}>
                    {selectedInv.status}
                  </span>
                  <span className="px-1.5 py-0.5 rounded bg-slate-800 text-slate-400 text-[10px] font-mono">
                    {selectedInv.category}
                  </span>
                </div>
                <h3 className="text-sm font-bold text-slate-100">{selectedInv.title}</h3>
                <p className="text-[11px] text-slate-400 mt-0.5">{selectedInv.description}</p>
              </div>

              {onViewReport && (
                <button
                  onClick={() => onViewReport(selectedInv.id)}
                  className="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 rounded text-xs flex items-center gap-1.5 transition"
                >
                  <FileText className="w-3.5 h-3.5 text-sky-400" />
                  <span>Technical Report</span>
                </button>
              )}
            </div>

            {updateError && (
              <div className="p-3 bg-rose-950/50 border-b border-rose-800 text-xs text-rose-200 flex items-center gap-2">
                <AlertCircle className="w-4 h-4 text-rose-400 shrink-0" />
                <span>{updateError}</span>
              </div>
            )}

            {/* Case Body */}
            <div className="flex-1 p-4 overflow-auto space-y-4">
              {/* Initial Hypothesis */}
              <div className="p-3 bg-slate-950 border border-slate-800 rounded-lg space-y-1">
                <span className="font-semibold text-slate-300 block">Initial Problem Hypothesis</span>
                <p className="text-slate-300 text-xs">{selectedInv.initial_hypothesis || 'No initial hypothesis specified.'}</p>
              </div>

              {/* SQL under investigation */}
              {selectedInv.baseline_sql && (
                <div className="p-3 bg-slate-950 border border-slate-800 rounded-lg space-y-1">
                  <span className="font-semibold text-slate-300 block text-[11px]">Baseline SQL Query</span>
                  <pre className="p-2 bg-slate-900 rounded font-mono text-[11px] text-sky-300 overflow-x-auto">
                    {selectedInv.baseline_sql}
                  </pre>
                </div>
              )}

              {/* Findings Form (Root Cause, Fix, Verification) */}
              <div className="p-3 bg-slate-950 border border-slate-800 rounded-lg space-y-3">
                <span className="font-semibold text-slate-200 block text-xs">Investigation Evidence & Resolution</span>

                <div>
                  <label className="text-[11px] text-slate-400 block mb-1">
                    Root Cause Analysis <strong className="text-amber-400">*</strong> (Required to resolve)
                  </label>
                  <textarea
                    value={editRootCause}
                    onChange={e => setEditRootCause(e.target.value)}
                    placeholder="Document the exact technical cause (e.g. optimizer selected FTS because date filter lacked index)..."
                    rows={2}
                    className="w-full bg-slate-900 border border-slate-700 rounded p-2 text-slate-200 text-xs focus:outline-none focus:border-sky-500"
                  />
                </div>

                <div>
                  <label className="text-[11px] text-slate-400 block mb-1">
                    Proposed or Implemented Correction <strong className="text-amber-400">*</strong>
                  </label>
                  <textarea
                    value={editProposedFix}
                    onChange={e => setEditProposedFix(e.target.value)}
                    placeholder="Describe index creation, query rewrite, or schema change..."
                    rows={2}
                    className="w-full bg-slate-900 border border-slate-700 rounded p-2 text-slate-200 text-xs focus:outline-none focus:border-sky-500"
                  />
                </div>

                <div>
                  <label className="text-[11px] text-slate-400 block mb-1">
                    Verification Notes & Benchmark Evidence <strong className="text-amber-400">*</strong>
                  </label>
                  <textarea
                    value={editVerification}
                    onChange={e => setEditVerification(e.target.value)}
                    placeholder="Record measured timing differences, plan changes, and equivalence confirmation..."
                    rows={2}
                    className="w-full bg-slate-900 border border-slate-700 rounded p-2 text-slate-200 text-xs focus:outline-none focus:border-sky-500"
                  />
                </div>

                <div className="flex flex-wrap items-center justify-between gap-3 pt-2 border-t border-slate-800">
                  <div className="flex items-center gap-2">
                    <span className="text-slate-400">Target Status:</span>
                    <select
                      value={targetStatus}
                      onChange={e => setTargetStatus(e.target.value as InvestigationStatus)}
                      className="bg-slate-900 border border-slate-700 rounded px-2.5 py-1 text-slate-200 text-xs font-medium"
                    >
                      <option value="OPEN">OPEN</option>
                      <option value="INVESTIGATING">INVESTIGATING</option>
                      <option value="FIX_PROPOSED">FIX_PROPOSED</option>
                      <option value="VALIDATION_REQUIRED">VALIDATION_REQUIRED</option>
                      <option value="RESOLVED">RESOLVED (Gated by Evidence)</option>
                      <option value="CLOSED_INCONCLUSIVE">CLOSED_INCONCLUSIVE</option>
                    </select>
                  </div>

                  <button
                    onClick={handleUpdate}
                    disabled={isUpdating}
                    className="px-3.5 py-1.5 bg-sky-600 hover:bg-sky-500 disabled:opacity-40 text-white rounded font-medium flex items-center gap-1.5 transition"
                  >
                    <Save className="w-3.5 h-3.5" />
                    <span>{isUpdating ? 'Saving...' : 'Update Case'}</span>
                  </button>
                </div>
              </div>

              {/* Investigation Timeline */}
              <div className="p-3 bg-slate-950 border border-slate-800 rounded-lg space-y-2">
                <span className="font-semibold text-slate-300 block text-xs">Timeline Audit Log ({selectedInv.timeline.length} events)</span>
                <div className="space-y-1.5">
                  {selectedInv.timeline.map((evt, i) => (
                    <div key={i} className="flex items-start gap-2.5 text-[11px] p-2 bg-slate-900 rounded border border-slate-800">
                      <Clock className="w-3.5 h-3.5 text-slate-500 mt-0.5 shrink-0" />
                      <div className="flex-1">
                        <div className="flex items-center justify-between text-slate-400">
                          <strong className="text-sky-300 font-mono text-[10px]">{evt.event_type}</strong>
                          <span className="text-[10px]">{evt.timestamp.replace('T', ' ').slice(0, 19)}</span>
                        </div>
                        <p className="text-slate-300 mt-0.5">{evt.description}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </>
        ) : (
          <div className="text-slate-500 text-xs p-6 text-center">Select an investigation to inspect details.</div>
        )}
      </div>

      {/* New Case Modal */}
      {showNewModal && (
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4">
          <div className="bg-slate-900 border border-slate-700 rounded-lg p-5 w-full max-w-lg space-y-3 shadow-xl text-xs">
            <div className="flex items-center justify-between border-b border-slate-800 pb-2">
              <h4 className="text-sm font-bold text-slate-200">Open New Investigation Case</h4>
              <button onClick={() => setShowNewModal(false)} className="text-slate-500 hover:text-slate-300">
                <X className="w-4 h-4" />
              </button>
            </div>

            <div>
              <label className="text-slate-400 block mb-1">Title</label>
              <input
                type="text"
                value={newTitle}
                onChange={e => setNewTitle(e.target.value)}
                placeholder="e.g. Latency Spike on Delayed Shipments Query"
                className="w-full bg-slate-950 border border-slate-700 rounded px-2.5 py-1.5 text-slate-200 focus:outline-none focus:border-sky-500"
              />
            </div>

            <div>
              <label className="text-slate-400 block mb-1">Description / Problem Statement</label>
              <textarea
                value={newDesc}
                onChange={e => setNewDesc(e.target.value)}
                placeholder="What is happening? Who reported the issue?"
                rows={2}
                className="w-full bg-slate-950 border border-slate-700 rounded p-2 text-slate-200 focus:outline-none focus:border-sky-500"
              />
            </div>

            <div className="grid grid-cols-2 gap-2">
              <div>
                <label className="text-slate-400 block mb-1">Category</label>
                <select
                  value={newCategory}
                  onChange={e => setNewCategory(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-700 rounded px-2 py-1 text-slate-200"
                >
                  <option value="PERFORMANCE">PERFORMANCE</option>
                  <option value="ERROR">SQL ERROR</option>
                  <option value="DATA_CORRECTNESS">DATA CORRECTNESS</option>
                  <option value="INDEX_EVALUATION">INDEX EVALUATION</option>
                </select>
              </div>

              <div>
                <label className="text-slate-400 block mb-1">Severity</label>
                <select
                  value={newSeverity}
                  onChange={e => setNewSeverity(e.target.value as InvestigationSeverity)}
                  className="w-full bg-slate-950 border border-slate-700 rounded px-2 py-1 text-slate-200"
                >
                  <option value="LOW">LOW</option>
                  <option value="MEDIUM">MEDIUM</option>
                  <option value="HIGH">HIGH</option>
                  <option value="CRITICAL">CRITICAL</option>
                </select>
              </div>
            </div>

            <div>
              <label className="text-slate-400 block mb-1">Initial Hypothesis</label>
              <textarea
                value={newHypothesis}
                onChange={e => setNewHypothesis(e.target.value)}
                placeholder="Why do you think this problem is occurring?"
                rows={2}
                className="w-full bg-slate-950 border border-slate-700 rounded p-2 text-slate-200 focus:outline-none focus:border-sky-500"
              />
            </div>

            <div className="flex items-center justify-end gap-2 pt-2 border-t border-slate-800">
              <button
                onClick={() => setShowNewModal(false)}
                className="px-3 py-1.5 text-slate-400 hover:text-slate-200"
              >
                Cancel
              </button>
              <button
                onClick={handleCreateNew}
                disabled={!newTitle.trim()}
                className="px-3.5 py-1.5 bg-sky-600 hover:bg-sky-500 disabled:opacity-40 text-white rounded font-medium"
              >
                Create Investigation
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
