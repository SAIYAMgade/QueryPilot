import React, { useState, useEffect } from 'react';
import {
  AlertCircle, Search, CheckCircle2, BookOpen, Terminal,
  ArrowRight, ShieldAlert, Copy, Check, Lightbulb, HelpCircle
} from 'lucide-react';
import { ErrorAnalysisResponse, KnowledgeBaseEntry } from '../../types';
import { api } from '../../api/client';

interface DiagnosticsViewProps {
  initialErrorCode?: string;
  initialErrorMessage?: string;
  initialSql?: string;
}

export const DiagnosticsView: React.FC<DiagnosticsViewProps> = ({
  initialErrorCode,
  initialErrorMessage,
  initialSql
}) => {
  const [errorMessage, setErrorMessage] = useState(
    initialErrorMessage || 'ORA-00942: table or view does not exist'
  );
  const [errorCode, setErrorCode] = useState(initialErrorCode || 'ORA-00942');
  const [queryText, setQueryText] = useState(initialSql || 'SELECT * FROM customer_order WHERE status = 1');
  const [analysis, setAnalysis] = useState<ErrorAnalysisResponse | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [knowledgeBase, setKnowledgeBase] = useState<KnowledgeBaseEntry[]>([]);
  const [activeTab, setActiveTab] = useState<'analyzer' | 'knowledgeBase'>('analyzer');
  const [copiedQuery, setCopiedQuery] = useState<string | null>(null);

  useEffect(() => {
    loadKnowledgeBase();
    handleAnalyze();
  }, []);

  const loadKnowledgeBase = async () => {
    try {
      const kb = await api.getKnowledgeBase();
      setKnowledgeBase(kb);
    } catch {
      // Ignored
    }
  };

  const handleAnalyze = async () => {
    if (!errorMessage.trim() || isAnalyzing) return;
    setIsAnalyzing(true);
    try {
      const res = await api.analyzeError(errorMessage, errorCode, queryText);
      setAnalysis(res);
    } catch (err: any) {
      alert(`Analysis failed: ${err.message}`);
    } finally {
      setIsAnalyzing(false);
    }
  };

  const handleSelectPreset = (entry: KnowledgeBaseEntry) => {
    setErrorCode(entry.oracle_code);
    setErrorMessage(`${entry.oracle_code}: ${entry.official_title}`);
    setQueryText(entry.sample_problematic_sql || '');
    setActiveTab('analyzer');
    api.analyzeError(`${entry.oracle_code}: ${entry.official_title}`, entry.oracle_code, entry.sample_problematic_sql)
      .then(setAnalysis);
  };

  const copyText = (txt: string, id: string) => {
    navigator.clipboard.writeText(txt);
    setCopiedQuery(id);
    setTimeout(() => setCopiedQuery(null), 1500);
  };

  return (
    <div className="flex flex-col h-full space-y-3">
      {/* Top Header & Tabs */}
      <div className="bg-slate-900 border border-slate-800 rounded-lg p-3 flex items-center justify-between text-xs">
        <div className="flex items-center gap-2">
          <AlertCircle className="w-4 h-4 text-rose-400" />
          <span className="font-bold text-slate-200 uppercase tracking-wider">
            Oracle SQL Error Investigation & Knowledge Base
          </span>
        </div>

        <div className="flex items-center gap-1 bg-slate-950 p-0.5 rounded border border-slate-800">
          <button
            onClick={() => setActiveTab('analyzer')}
            className={`px-3 py-1 rounded transition ${activeTab === 'analyzer' ? 'bg-sky-600 text-white font-medium' : 'text-slate-400 hover:text-slate-200'}`}
          >
            Error Analyzer
          </button>
          <button
            onClick={() => setActiveTab('knowledgeBase')}
            className={`px-3 py-1 rounded transition ${activeTab === 'knowledgeBase' ? 'bg-sky-600 text-white font-medium' : 'text-slate-400 hover:text-slate-200'}`}
          >
            Curated Knowledge Base ({knowledgeBase.length})
          </button>
        </div>
      </div>

      {activeTab === 'analyzer' ? (
        <div className="flex-1 flex flex-col md:flex-row gap-3 min-h-0">
          {/* Left: Input Form */}
          <div className="w-96 bg-slate-900 border border-slate-800 rounded-lg p-4 flex flex-col gap-3 shrink-0 text-xs">
            <span className="font-semibold text-slate-200">Captured Oracle Exception</span>

            {/* Presets dropdown */}
            <div>
              <label className="text-[11px] text-slate-400 block mb-1">Common Scenarios</label>
              <select
                onChange={e => {
                  const entry = knowledgeBase.find(k => k.oracle_code === e.target.value);
                  if (entry) handleSelectPreset(entry);
                }}
                className="w-full bg-slate-950 border border-slate-700 rounded px-2.5 py-1 text-slate-200 focus:outline-none focus:border-sky-500"
                value={errorCode}
              >
                {knowledgeBase.map(k => (
                  <option key={k.oracle_code} value={k.oracle_code}>
                    {k.oracle_code} - {k.official_title}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="text-[11px] text-slate-400 block mb-1">Oracle Error Code / Message</label>
              <textarea
                value={errorMessage}
                onChange={e => setErrorMessage(e.target.value)}
                placeholder="e.g. ORA-00942: table or view does not exist"
                rows={3}
                className="w-full bg-slate-950 border border-slate-700 rounded p-2 text-slate-200 font-mono text-[11px] focus:outline-none focus:border-sky-500"
              />
            </div>

            <div>
              <label className="text-[11px] text-slate-400 block mb-1">SQL Query Context</label>
              <textarea
                value={queryText}
                onChange={e => setQueryText(e.target.value)}
                placeholder="SQL query that triggered the exception..."
                rows={4}
                className="w-full bg-slate-950 border border-slate-700 rounded p-2 text-slate-200 font-mono text-[11px] focus:outline-none focus:border-sky-500"
              />
            </div>

            <button
              onClick={handleAnalyze}
              disabled={isAnalyzing || !errorMessage.trim()}
              className="mt-2 w-full py-1.5 bg-sky-600 hover:bg-sky-500 disabled:opacity-40 text-white rounded font-medium transition"
            >
              {isAnalyzing ? 'Analyzing...' : 'Diagnose Root Cause'}
            </button>
          </div>

          {/* Right: Analysis Results */}
          <div className="flex-1 bg-slate-900 border border-slate-800 rounded-lg p-4 overflow-auto space-y-4 text-xs">
            {analysis ? (
              <>
                {/* Header Badge */}
                <div className="p-3 bg-slate-950 border border-slate-800 rounded-lg flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <span className="px-2.5 py-1 rounded bg-rose-950 border border-rose-800 text-rose-300 font-mono font-bold text-xs">
                      {analysis.oracle_error_code}
                    </span>
                    <div>
                      <h4 className="font-bold text-slate-100 text-sm">{analysis.category.replace(/_/g, ' ')}</h4>
                      <p className="text-[11px] text-slate-400 font-mono">{analysis.sanitized_message}</p>
                    </div>
                  </div>

                  <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase ${
                    analysis.is_confirmed_cause
                      ? 'bg-emerald-950 text-emerald-300 border border-emerald-800'
                      : 'bg-amber-950 text-amber-300 border border-amber-800'
                  }`}>
                    {analysis.evidence_status}
                  </span>
                </div>

                {/* Contextual position hint */}
                {analysis.position_hint && (
                  <div className="p-3 bg-amber-950/40 border border-amber-800/60 rounded-lg text-amber-200 flex items-start gap-2">
                    <Lightbulb className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
                    <div>
                      <strong>Syntax Diagnosis:</strong> {analysis.position_hint}
                    </div>
                  </div>
                )}

                {/* Plain English explanation */}
                {analysis.knowledge_base && (
                  <div className="p-3 bg-slate-950 border border-slate-800 rounded-lg space-y-1">
                    <span className="font-semibold text-slate-300 block">Plain English Explanation</span>
                    <p className="text-slate-300 leading-relaxed text-xs">
                      {analysis.knowledge_base.plain_english}
                    </p>
                    <p className="text-slate-500 text-[11px] mt-1 pt-1 border-t border-slate-800">
                      <strong>Oracle Kernel Mechanics:</strong> {analysis.knowledge_base.root_cause_analysis}
                    </p>
                  </div>
                )}

                {/* Likely causes */}
                <div className="p-3 bg-slate-950 border border-slate-800 rounded-lg space-y-1.5">
                  <span className="font-semibold text-slate-300 block">Likely Root Causes</span>
                  <ul className="space-y-1 list-disc list-inside text-slate-300">
                    {analysis.likely_causes.map((c, i) => (
                      <li key={i}>{c}</li>
                    ))}
                  </ul>
                </div>

                {/* Recommended Checks in Oracle Catalog */}
                <div className="p-3 bg-slate-950 border border-slate-800 rounded-lg space-y-2">
                  <span className="font-semibold text-slate-300 block">Recommended Verification Checks</span>
                  <div className="space-y-1.5">
                    {analysis.recommended_checks.map((chk, i) => (
                      <div key={i} className="p-2 bg-slate-900 rounded border border-slate-800 font-mono text-[11px] text-sky-300 flex items-center justify-between">
                        <span className="truncate">{chk}</span>
                        <button
                          onClick={() => copyText(chk, `chk_${i}`)}
                          className="text-slate-400 hover:text-slate-200 ml-2"
                        >
                          {copiedQuery === `chk_${i}` ? <Check className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3" />}
                        </button>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Sample problematic vs corrected SQL */}
                {analysis.knowledge_base?.sample_problematic_sql && (
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                    <div className="p-3 bg-slate-950 border border-slate-800 rounded-lg space-y-1">
                      <span className="font-semibold text-rose-400 block text-[11px]">Problematic Construct</span>
                      <pre className="p-2 bg-slate-900 rounded font-mono text-[11px] text-rose-200 overflow-x-auto whitespace-pre-wrap">
                        {analysis.knowledge_base.sample_problematic_sql}
                      </pre>
                    </div>
                    <div className="p-3 bg-slate-950 border border-slate-800 rounded-lg space-y-1">
                      <span className="font-semibold text-emerald-400 block text-[11px]">Corrected Oracle SQL</span>
                      <pre className="p-2 bg-slate-900 rounded font-mono text-[11px] text-emerald-200 overflow-x-auto whitespace-pre-wrap">
                        {analysis.knowledge_base.sample_corrected_sql}
                      </pre>
                    </div>
                  </div>
                )}
              </>
            ) : (
              <div className="text-center p-8 text-slate-500">
                Submit an Oracle exception message to run root cause analysis.
              </div>
            )}
          </div>
        </div>
      ) : (
        /* Knowledge Base Browser Tab */
        <div className="flex-1 bg-slate-900 border border-slate-800 rounded-lg p-4 overflow-auto space-y-3 text-xs">
          <p className="text-slate-400 text-xs mb-2">
            Curated diagnostic reference for representative Oracle Database error codes:
          </p>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {knowledgeBase.map(k => (
              <div
                key={k.oracle_code}
                onClick={() => handleSelectPreset(k)}
                className="p-3.5 bg-slate-950 hover:bg-slate-850 border border-slate-800 rounded-lg cursor-pointer transition space-y-2 group"
              >
                <div className="flex items-center justify-between">
                  <span className="font-mono font-bold text-sky-400 text-xs group-hover:underline">
                    {k.oracle_code}
                  </span>
                  <span className="px-1.5 py-0.5 rounded bg-slate-800 text-slate-400 text-[10px]">
                    {k.category}
                  </span>
                </div>
                <h5 className="font-semibold text-slate-200">{k.official_title}</h5>
                <p className="text-[11px] text-slate-400 line-clamp-2 leading-relaxed">
                  {k.plain_english}
                </p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
