import React, { useState, useEffect } from 'react';
import {
  FileText, Download, CheckCircle2, AlertCircle, FileCheck2, ExternalLink
} from 'lucide-react';
import { Investigation } from '../../types';
import { api } from '../../api/client';

interface ReportsViewProps {
  initialInvestigationId?: string | null;
}

export const ReportsView: React.FC<ReportsViewProps> = ({ initialInvestigationId }) => {
  const [investigations, setInvestigations] = useState<Investigation[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(initialInvestigationId || null);
  const [htmlReport, setHtmlReport] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    loadList();
  }, []);

  useEffect(() => {
    if (selectedId) {
      loadReport(selectedId);
    }
  }, [selectedId]);

  const loadList = async () => {
    try {
      const list = await api.getInvestigations();
      setInvestigations(list);
      if (list.length > 0 && !selectedId) {
        setSelectedId(list[0].id);
      }
    } catch {
      // Ignored
    }
  };

  const loadReport = async (invId: string) => {
    setIsLoading(true);
    try {
      const rep = await api.generateReport(invId);
      setHtmlReport(rep.html_content);
    } catch (err: any) {
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleDownloadHtml = () => {
    if (!selectedId) return;
    window.open(`/api/reports/${selectedId}/export/html`, '_blank');
  };

  return (
    <div className="flex h-full gap-4 text-xs">
      {/* Case Selector Sidebar */}
      <div className="w-72 bg-slate-900 border border-slate-800 rounded-lg flex flex-col shrink-0 overflow-hidden">
        <div className="p-3 border-b border-slate-800 bg-slate-850">
          <span className="font-bold text-slate-200 uppercase tracking-wider text-[11px] flex items-center gap-1.5">
            <FileText className="w-3.5 h-3.5 text-sky-400" />
            Investigation Reports
          </span>
        </div>

        <div className="flex-1 overflow-auto p-1.5 space-y-1 divide-y divide-slate-800/40">
          {investigations.map(inv => {
            const isSelected = selectedId === inv.id;
            return (
              <div
                key={inv.id}
                onClick={() => setSelectedId(inv.id)}
                className={`p-2.5 rounded cursor-pointer transition ${
                  isSelected
                    ? 'bg-sky-950/80 border border-sky-800/80 text-sky-300'
                    : 'text-slate-300 hover:bg-slate-800/60'
                }`}
              >
                <div className="flex items-center justify-between mb-0.5">
                  <span className="font-mono text-[10px] font-bold">{inv.id}</span>
                  <span className="text-[9px] uppercase px-1 rounded bg-slate-800 text-slate-400">
                    {inv.status}
                  </span>
                </div>
                <h5 className="font-semibold text-xs line-clamp-1">{inv.title}</h5>
              </div>
            );
          })}
        </div>
      </div>

      {/* Report Preview */}
      <div className="flex-1 bg-slate-900 border border-slate-800 rounded-lg flex flex-col overflow-hidden">
        <div className="p-3 border-b border-slate-800 bg-slate-850 flex items-center justify-between">
          <span className="font-mono text-slate-300 font-medium">
            Case: <strong className="text-sky-400">{selectedId}</strong>
          </span>

          <div className="flex items-center gap-2">
            <button
              onClick={handleDownloadHtml}
              disabled={!selectedId}
              className="px-3 py-1 bg-sky-600 hover:bg-sky-500 disabled:opacity-40 text-white rounded font-medium flex items-center gap-1.5 transition"
            >
              <Download className="w-3.5 h-3.5" />
              <span>Download HTML Report</span>
            </button>
          </div>
        </div>

        <div className="flex-1 p-4 overflow-auto bg-slate-950">
          {isLoading ? (
            <div className="p-8 text-center text-slate-500 font-mono">
              Generating report preview...
            </div>
          ) : htmlReport ? (
            <div className="max-w-4xl mx-auto bg-slate-900 border border-slate-800 rounded-lg p-6 shadow-sm">
              <iframe
                srcDoc={htmlReport}
                title="Investigation Report"
                className="w-full h-[650px] border-0 rounded bg-slate-900"
              />
            </div>
          ) : (
            <div className="p-8 text-center text-slate-500 font-mono">
              Select an investigation case to view its technical report.
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
