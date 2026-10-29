import React, { useState, useMemo } from 'react';
import { ArrowUpDown, ArrowUp, ArrowDown, Search, Download, Copy, AlertTriangle } from 'lucide-react';
import { QueryResultColumn } from '../types';

interface DataGridProps {
  columns: QueryResultColumn[];
  rows: Record<string, any>[];
  truncated?: boolean;
  maxRows?: number;
}

export const DataGrid: React.FC<DataGridProps> = ({ columns, rows, truncated, maxRows }) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [sortCol, setSortCol] = useState<string | null>(null);
  const [sortDir, setSortDir] = useState<'asc' | 'desc'>('asc');
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(25);
  const [copiedCell, setCopiedCell] = useState<string | null>(null);

  const handleSort = (colName: string) => {
    if (sortCol === colName) {
      if (sortDir === 'asc') setSortDir('desc');
      else {
        setSortCol(null);
        setSortDir('asc');
      }
    } else {
      setSortCol(colName);
      setSortDir('asc');
    }
    setPage(1);
  };

  const filteredRows = useMemo(() => {
    if (!searchTerm.trim()) return rows;
    const term = searchTerm.toLowerCase();
    return rows.filter(row =>
      Object.values(row).some(val =>
        val !== null && val !== undefined && String(val).toLowerCase().includes(term)
      )
    );
  }, [rows, searchTerm]);

  const sortedRows = useMemo(() => {
    if (!sortCol) return filteredRows;
    return [...filteredRows].sort((a, b) => {
      const valA = a[sortCol];
      const valB = b[sortCol];
      if (valA === valB) return 0;
      if (valA === null || valA === undefined) return 1;
      if (valB === null || valB === undefined) return -1;
      if (typeof valA === 'number' && typeof valB === 'number') {
        return sortDir === 'asc' ? valA - valB : valB - valA;
      }
      return sortDir === 'asc'
        ? String(valA).localeCompare(String(valB))
        : String(valB).localeCompare(String(valA));
    });
  }, [filteredRows, sortCol, sortDir]);

  const totalPages = Math.ceil(sortedRows.length / pageSize) || 1;
  const paginatedRows = sortedRows.slice((page - 1) * pageSize, page * pageSize);

  const copyCell = (text: string, id: string) => {
    navigator.clipboard.writeText(text);
    setCopiedCell(id);
    setTimeout(() => setCopiedCell(null), 1500);
  };

  const exportCsv = () => {
    if (rows.length === 0) return;
    const colKeys = columns.map(c => c.name);
    const csvLines = [
      colKeys.join(','),
      ...rows.map(r => colKeys.map(k => `"${String(r[k] ?? '').replace(/"/g, '""')}"`).join(','))
    ];
    const blob = new Blob([csvLines.join('\n')], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `query_result_${Date.now()}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  };

  if (columns.length === 0) {
    return (
      <div className="p-8 text-center text-slate-500 font-mono text-sm border border-slate-800 rounded bg-slate-900/50">
        No columns returned. Query executed or no result set available.
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full bg-slate-900 border border-slate-800 rounded-lg overflow-hidden shadow-sm">
      {/* Truncation notification */}
      {truncated && (
        <div className="bg-amber-950/60 border-b border-amber-800/60 px-3 py-1.5 flex items-center justify-between text-xs text-amber-200">
          <div className="flex items-center gap-1.5">
            <AlertTriangle className="w-3.5 h-3.5 text-amber-400" />
            <span>Output truncated by safety limit ({maxRows || 1000} rows fetched). Refine query filter or increase bounds.</span>
          </div>
        </div>
      )}

      {/* Grid Toolbar */}
      <div className="flex items-center justify-between px-3 py-2 border-b border-slate-800 bg-slate-850/60 text-xs">
        <div className="flex items-center gap-2">
          <div className="relative">
            <Search className="w-3.5 h-3.5 absolute left-2 top-2 text-slate-500" />
            <input
              type="text"
              placeholder="Filter results..."
              value={searchTerm}
              onChange={e => { setSearchTerm(e.target.value); setPage(1); }}
              className="bg-slate-900 border border-slate-700 rounded pl-7 pr-2 py-1 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-sky-500 w-48"
            />
          </div>
          <span className="text-slate-400">
            Showing <strong className="text-slate-200">{filteredRows.length}</strong> of <strong className="text-slate-200">{rows.length}</strong> rows
          </span>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={exportCsv}
            className="flex items-center gap-1.5 px-2.5 py-1 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded text-xs border border-slate-700 transition"
            title="Export CSV"
          >
            <Download className="w-3 h-3 text-sky-400" />
            <span>CSV</span>
          </button>
        </div>
      </div>

      {/* Scrollable Data Table */}
      <div className="flex-1 overflow-auto">
        <table className="w-full text-left text-xs border-collapse">
          <thead className="bg-slate-950/90 sticky top-0 z-10 border-b border-slate-800 select-none">
            <tr>
              <th className="py-2 px-2.5 w-10 text-slate-500 font-mono text-[11px] border-r border-slate-800/80">#</th>
              {columns.map(col => (
                <th
                  key={col.name}
                  onClick={() => handleSort(col.name)}
                  className="py-2 px-3 font-semibold text-slate-300 hover:text-sky-300 cursor-pointer border-r border-slate-800/60 whitespace-nowrap group"
                >
                  <div className="flex items-center justify-between gap-1.5">
                    <span className="font-mono tracking-tight">{col.name}</span>
                    <span className="text-slate-600 group-hover:text-slate-400">
                      {sortCol === col.name ? (
                        sortDir === 'asc' ? <ArrowUp className="w-3 h-3 text-sky-400" /> : <ArrowDown className="w-3 h-3 text-sky-400" />
                      ) : (
                        <ArrowUpDown className="w-3 h-3 opacity-40 group-hover:opacity-100" />
                      )}
                    </span>
                  </div>
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/50 font-mono text-slate-200">
            {paginatedRows.length === 0 ? (
              <tr>
                <td colSpan={columns.length + 1} className="py-8 text-center text-slate-500">
                  {searchTerm ? 'No rows match filter criteria.' : 'Query returned 0 rows.'}
                </td>
              </tr>
            ) : (
              paginatedRows.map((row, rIdx) => {
                const absoluteIdx = (page - 1) * pageSize + rIdx + 1;
                return (
                  <tr key={rIdx} className="hover:bg-slate-800/40 transition-colors">
                    <td className="py-1.5 px-2.5 text-slate-500 text-[11px] bg-slate-950/40 border-r border-slate-800/60 select-none">
                      {absoluteIdx}
                    </td>
                    {columns.map(col => {
                      const val = row[col.name];
                      const cellId = `${rIdx}_${col.name}`;
                      const isNull = val === null || val === undefined;
                      const displayVal = isNull ? 'NULL' : String(val);

                      return (
                        <td
                          key={col.name}
                          onClick={() => !isNull && copyCell(displayVal, cellId)}
                          className={`py-1.5 px-3 border-r border-slate-800/40 whitespace-nowrap max-w-xs truncate cursor-pointer group/cell relative ${
                            isNull ? 'text-slate-500 italic' : ''
                          }`}
                          title={displayVal}
                        >
                          <span className={isNull ? 'px-1 rounded bg-slate-800/60 text-[10px]' : ''}>
                            {displayVal}
                          </span>
                          {!isNull && (
                            <span className="hidden group-hover/cell:inline-block absolute right-1 top-1.5 bg-slate-800 text-slate-300 p-0.5 rounded shadow">
                              <Copy className="w-2.5 h-2.5" />
                            </span>
                          )}
                          {copiedCell === cellId && (
                            <span className="absolute right-1 top-1 bg-sky-600 text-white text-[10px] px-1 rounded shadow">
                              Copied!
                            </span>
                          )}
                        </td>
                      );
                    })}
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>

      {/* Pagination Bar */}
      <div className="flex items-center justify-between px-3 py-1.5 border-t border-slate-800 bg-slate-850/60 text-xs text-slate-400">
        <div className="flex items-center gap-2">
          <span>Rows per page:</span>
          <select
            value={pageSize}
            onChange={e => { setPageSize(Number(e.target.value)); setPage(1); }}
            className="bg-slate-900 border border-slate-700 rounded px-1.5 py-0.5 text-slate-200 focus:outline-none"
          >
            <option value={10}>10</option>
            <option value={25}>25</option>
            <option value={50}>50</option>
            <option value={100}>100</option>
          </select>
        </div>

        <div className="flex items-center gap-2">
          <span>
            Page <strong className="text-slate-200">{page}</strong> of <strong className="text-slate-200">{totalPages}</strong>
          </span>
          <div className="flex items-center gap-1">
            <button
              disabled={page <= 1}
              onClick={() => setPage(p => Math.max(1, p - 1))}
              className="px-2 py-0.5 bg-slate-800 hover:bg-slate-700 disabled:opacity-40 disabled:hover:bg-slate-800 rounded border border-slate-700 text-slate-300"
            >
              Prev
            </button>
            <button
              disabled={page >= totalPages}
              onClick={() => setPage(p => Math.min(totalPages, p + 1))}
              className="px-2 py-0.5 bg-slate-800 hover:bg-slate-700 disabled:opacity-40 disabled:hover:bg-slate-800 rounded border border-slate-700 text-slate-300"
            >
              Next
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
