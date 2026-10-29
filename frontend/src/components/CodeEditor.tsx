import React, { useRef } from 'react';
import { Play, Copy, RotateCcw, Sparkles } from 'lucide-react';

interface CodeEditorProps {
  value: string;
  onChange: (val: string) => void;
  onExecute?: () => void;
  readOnly?: boolean;
  minHeight?: string;
  placeholder?: string;
  label?: string;
}

export const CodeEditor: React.FC<CodeEditorProps> = ({
  value,
  onChange,
  onExecute,
  readOnly = false,
  minHeight = '180px',
  placeholder = 'SELECT * FROM table_name...',
  label
}) => {
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const lines = value.split('\n');
  const lineCount = Math.max(lines.length, 1);

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    // Ctrl+Enter or Cmd+Enter executes query
    if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
      e.preventDefault();
      if (onExecute) onExecute();
    }
    // Tab key inserts 2 spaces
    if (e.key === 'Tab') {
      e.preventDefault();
      const textarea = textareaRef.current;
      if (!textarea) return;
      const start = textarea.selectionStart;
      const end = textarea.selectionEnd;
      const newValue = value.substring(0, start) + '  ' + value.substring(end);
      onChange(newValue);
      setTimeout(() => {
        textarea.selectionStart = textarea.selectionEnd = start + 2;
      }, 0);
    }
  };

  const handleCopy = () => {
    navigator.clipboard.writeText(value);
  };

  const handleClear = () => {
    onChange('');
    if (textareaRef.current) textareaRef.current.focus();
  };

  const handleFormat = () => {
    // Clean, readable SQL formatting: uppercase major SQL clauses and align indentations
    const clauses = [
      'SELECT', 'FROM', 'WHERE', 'JOIN', 'INNER JOIN', 'LEFT JOIN', 'RIGHT JOIN',
      'ON', 'GROUP BY', 'HAVING', 'ORDER BY', 'FETCH FIRST', 'ROWS ONLY', 'UNION ALL', 'WITH'
    ];
    let formatted = value;
    for (const kw of clauses) {
      const reg = new RegExp(`\\b${kw}\\b`, 'gi');
      formatted = formatted.replace(reg, kw);
    }
    onChange(formatted.trim());
  };

  return (
    <div className="flex flex-col border border-slate-800 rounded-lg overflow-hidden bg-slate-900 shadow-sm">
      {/* Editor Header Bar */}
      <div className="flex items-center justify-between px-3 py-1.5 bg-slate-850/80 border-b border-slate-800 text-xs">
        <div className="flex items-center gap-2">
          {label && <span className="font-semibold text-slate-300">{label}</span>}
          <span className="text-[11px] text-slate-500 font-mono">
            {lineCount} {lineCount === 1 ? 'line' : 'lines'} • {value.length} chars
          </span>
        </div>

        <div className="flex items-center gap-1.5">
          <button
            onClick={handleFormat}
            disabled={readOnly || !value.trim()}
            className="flex items-center gap-1 px-2 py-0.5 text-slate-400 hover:text-slate-200 disabled:opacity-30 rounded hover:bg-slate-800 transition"
            title="Format SQL Keywords"
          >
            <Sparkles className="w-3 h-3 text-amber-400" />
            <span>Format</span>
          </button>
          <button
            onClick={handleCopy}
            disabled={!value.trim()}
            className="flex items-center gap-1 px-2 py-0.5 text-slate-400 hover:text-slate-200 disabled:opacity-30 rounded hover:bg-slate-800 transition"
            title="Copy SQL"
          >
            <Copy className="w-3 h-3 text-sky-400" />
            <span>Copy</span>
          </button>
          {!readOnly && (
            <button
              onClick={handleClear}
              disabled={!value.trim()}
              className="flex items-center gap-1 px-2 py-0.5 text-slate-400 hover:text-slate-200 disabled:opacity-30 rounded hover:bg-slate-800 transition"
              title="Clear Editor"
            >
              <RotateCcw className="w-3 h-3 text-rose-400" />
              <span>Clear</span>
            </button>
          )}
          {onExecute && (
            <button
              onClick={onExecute}
              disabled={!value.trim()}
              className="flex items-center gap-1 px-2.5 py-0.5 bg-sky-600 hover:bg-sky-500 text-white font-medium rounded text-xs shadow transition disabled:opacity-40"
              title="Execute Query (Ctrl + Enter)"
            >
              <Play className="w-3 h-3 fill-current" />
              <span>Run (Ctrl+↵)</span>
            </button>
          )}
        </div>
      </div>

      {/* Editor Body with Line Numbers */}
      <div className="flex relative font-mono text-xs overflow-auto" style={{ minHeight }}>
        {/* Line numbers gutter */}
        <div className="select-none py-2.5 px-2 bg-slate-950/60 text-slate-600 text-right w-10 border-r border-slate-800/80 leading-5">
          {Array.from({ length: lineCount }).map((_, i) => (
            <div key={i}>{i + 1}</div>
          ))}
        </div>

        {/* Textarea */}
        <textarea
          ref={textareaRef}
          value={value}
          onChange={e => onChange(e.target.value)}
          onKeyDown={handleKeyDown}
          readOnly={readOnly}
          placeholder={placeholder}
          spellCheck={false}
          className="flex-1 p-2.5 bg-transparent text-slate-200 placeholder-slate-600 focus:outline-none resize-none leading-5 tracking-tight font-mono selection:bg-sky-500/30"
          style={{ minHeight }}
        />
      </div>
    </div>
  );
};
