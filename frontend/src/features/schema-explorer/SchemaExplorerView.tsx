import React, { useState, useEffect } from 'react';
import {
  Database, Search, Table as TableIcon, Key, Link2, Eye,
  Layers, ArrowRight, Copy, Check, Info, FileSpreadsheet
} from 'lucide-react';
import { TableSummary, TableDetail, Relationship } from '../../types';
import { api } from '../../api/client';
import { DataGrid } from '../../components/DataGrid';

interface SchemaExplorerViewProps {
  onInsertSql?: (sql: string) => void;
}

export const SchemaExplorerView: React.FC<SchemaExplorerViewProps> = ({ onInsertSql }) => {
  const [tables, setTables] = useState<TableSummary[]>([]);
  const [selectedTableName, setSelectedTableName] = useState<string | null>(null);
  const [tableDetail, setTableDetail] = useState<TableDetail | null>(null);
  const [relationships, setRelationships] = useState<Relationship[]>([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [activeTab, setActiveTab] = useState<'columns' | 'constraints' | 'indexes' | 'preview' | 'relationships'>('columns');
  const [isLoading, setIsLoading] = useState(false);
  const [copiedCol, setCopiedCol] = useState<string | null>(null);

  useEffect(() => {
    loadTables();
    loadRelationships();
  }, []);

  const loadTables = async () => {
    try {
      const list = await api.getTables();
      setTables(list);
      if (list.length > 0 && !selectedTableName) {
        handleSelectTable(list[0].table_name);
      }
    } catch (err: any) {
      console.error(err);
    }
  };

  const loadRelationships = async () => {
    try {
      const rels = await api.getRelationships();
      setRelationships(rels);
    } catch (err: any) {
      console.error(err);
    }
  };

  const handleSelectTable = async (tableName: string) => {
    setSelectedTableName(tableName);
    setIsLoading(true);
    try {
      const detail = await api.getTableDetail(tableName);
      setTableDetail(detail);
    } catch (err: any) {
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  const copyColumn = (colName: string) => {
    navigator.clipboard.writeText(colName);
    setCopiedCol(colName);
    setTimeout(() => setCopiedCol(null), 1500);
  };

  const filteredTables = tables.filter(t =>
    t.table_name.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="flex h-full gap-4">
      {/* Left: Tables List Sidebar */}
      <div className="w-64 bg-slate-900 border border-slate-800 rounded-lg flex flex-col shrink-0 overflow-hidden text-xs">
        <div className="p-3 border-b border-slate-800 bg-slate-850">
          <div className="flex items-center justify-between mb-2">
            <span className="font-bold text-slate-200 uppercase tracking-wider text-[11px] flex items-center gap-1.5">
              <Database className="w-3.5 h-3.5 text-sky-400" />
              Tables ({tables.length})
            </span>
          </div>
          <div className="relative">
            <Search className="w-3.5 h-3.5 absolute left-2 top-2 text-slate-500" />
            <input
              type="text"
              placeholder="Search tables..."
              value={searchTerm}
              onChange={e => setSearchTerm(e.target.value)}
              className="w-full bg-slate-950 border border-slate-700 rounded pl-7 pr-2 py-1 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-sky-500"
            />
          </div>
        </div>

        <div className="flex-1 overflow-auto p-1.5 space-y-0.5">
          {filteredTables.map(t => {
            const isSelected = selectedTableName === t.table_name;
            return (
              <button
                key={t.table_name}
                onClick={() => handleSelectTable(t.table_name)}
                className={`w-full flex items-center justify-between px-3 py-2 rounded text-left transition ${
                  isSelected
                    ? 'bg-sky-950/80 text-sky-300 border border-sky-800/80 shadow-sm'
                    : 'text-slate-300 hover:bg-slate-800/60'
                }`}
              >
                <div className="flex items-center gap-2">
                  <TableIcon className={`w-3.5 h-3.5 ${isSelected ? 'text-sky-400' : 'text-slate-500'}`} />
                  <span className="font-mono text-xs font-medium">{t.table_name}</span>
                </div>
                <span className="text-[10px] text-slate-500 font-mono">
                  {t.num_rows !== null ? `~${t.num_rows} rows` : ''}
                </span>
              </button>
            );
          })}
        </div>
      </div>

      {/* Right: Table Detail Panel */}
      <div className="flex-1 bg-slate-900 border border-slate-800 rounded-lg flex flex-col overflow-hidden">
        {selectedTableName && (
          <div className="px-4 py-3 border-b border-slate-800 bg-slate-850 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded bg-sky-950 border border-sky-800 flex items-center justify-center text-sky-400 font-mono font-bold text-xs">
                ORA
              </div>
              <div>
                <h3 className="font-bold text-sm text-slate-100 font-mono flex items-center gap-2">
                  {tableDetail?.owner}.{selectedTableName}
                  {tableDetail?.is_estimated_rows && (
                    <span className="text-[10px] px-1.5 py-0.2 rounded bg-slate-800 text-slate-400 font-sans font-normal">
                      Optimizer Stats Estimated
                    </span>
                  )}
                </h3>
                <p className="text-[11px] text-slate-400">
                  {tableDetail?.columns.length} columns • {tableDetail?.indexes.length} indexes • {tableDetail?.constraints.length} constraints
                </p>
              </div>
            </div>

            {onInsertSql && (
              <button
                onClick={() => onInsertSql(`SELECT * FROM ${selectedTableName} FETCH FIRST 50 ROWS ONLY;`)}
                className="px-3 py-1 bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 rounded text-xs flex items-center gap-1.5 transition"
              >
                <FileSpreadsheet className="w-3.5 h-3.5 text-sky-400" />
                <span>Query in Workspace</span>
              </button>
            )}
          </div>
        )}

        {/* Tab Navigation */}
        <div className="flex border-b border-slate-800 bg-slate-950/60 px-4 text-xs font-medium text-slate-400">
          {[
            { id: 'columns', label: 'Columns' },
            { id: 'constraints', label: 'Constraints' },
            { id: 'indexes', label: 'Indexes' },
            { id: 'preview', label: 'Sample Data Preview' },
            { id: 'relationships', label: 'Foreign Key Graph' },
          ].map(tab => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              className={`py-2 px-3 border-b-2 transition ${
                activeTab === tab.id
                  ? 'border-sky-500 text-sky-300 font-semibold'
                  : 'border-transparent hover:text-slate-200'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {/* Tab Content */}
        <div className="flex-1 p-4 overflow-auto">
          {isLoading ? (
            <div className="p-8 text-center text-slate-500 font-mono text-xs">
              Loading Oracle data dictionary metadata...
            </div>
          ) : tableDetail ? (
            <>
              {/* Columns Tab */}
              {activeTab === 'columns' && (
                <div className="border border-slate-800 rounded-lg overflow-hidden">
                  <table className="w-full text-left text-xs border-collapse">
                    <thead className="bg-slate-950 border-b border-slate-800 text-slate-400">
                      <tr>
                        <th className="py-2 px-3 w-8">#</th>
                        <th className="py-2 px-3">Column Name</th>
                        <th className="py-2 px-3">Data Type</th>
                        <th className="py-2 px-3">Nullable</th>
                        <th className="py-2 px-3">Keys / Constraints</th>
                        <th className="py-2 px-3 text-right">Actions</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-800/60 font-mono text-slate-200">
                      {tableDetail.columns.map((c, i) => (
                        <tr key={c.name} className="hover:bg-slate-850/60">
                          <td className="py-2 px-3 text-slate-500">{i + 1}</td>
                          <td className="py-2 px-3 font-semibold text-slate-100 flex items-center gap-1.5">
                            {c.name}
                            {c.is_primary_key && <span title="Primary Key"><Key className="w-3 h-3 text-amber-400" /></span>}
                            {c.is_foreign_key && <span title={`References ${c.fk_ref_table}`}><Link2 className="w-3 h-3 text-sky-400" /></span>}
                          </td>
                          <td className="py-2 px-3 text-sky-400">{c.data_type}</td>
                          <td className="py-2 px-3 text-slate-400">{c.nullable ? 'YES' : 'NO'}</td>
                          <td className="py-2 px-3 text-slate-400">
                            {c.is_primary_key && <span className="px-1.5 py-0.5 rounded bg-amber-950/80 text-amber-300 text-[10px] mr-1">PRIMARY KEY</span>}
                            {c.is_foreign_key && <span className="px-1.5 py-0.5 rounded bg-sky-950/80 text-sky-300 text-[10px]">FK → {c.fk_ref_table}</span>}
                          </td>
                          <td className="py-2 px-3 text-right">
                            <button
                              onClick={() => copyColumn(c.name)}
                              className="px-2 py-0.5 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 text-[11px] transition"
                            >
                              {copiedCol === c.name ? <Check className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3" />}
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}

              {/* Constraints Tab */}
              {activeTab === 'constraints' && (
                <div className="space-y-2">
                  {tableDetail.constraints.map(cn => (
                    <div key={cn.constraint_name} className="p-3 bg-slate-950 border border-slate-800 rounded-lg text-xs space-y-1">
                      <div className="flex items-center justify-between">
                        <span className="font-mono font-bold text-slate-200">{cn.constraint_name}</span>
                        <span className="px-1.5 py-0.5 rounded bg-slate-800 text-sky-400 font-mono text-[10px]">
                          {cn.type_display}
                        </span>
                      </div>
                      <p className="text-slate-400 font-mono text-[11px]">
                        Columns: <strong>{cn.columns.join(', ')}</strong>
                      </p>
                      {cn.r_table_name && (
                        <p className="text-slate-400 text-[11px]">
                          References: <strong className="text-sky-300">{cn.r_table_name}</strong> ({cn.r_constraint_name})
                        </p>
                      )}
                      {cn.search_condition && (
                        <p className="text-slate-500 font-mono text-[10px]">Condition: {cn.search_condition}</p>
                      )}
                    </div>
                  ))}
                </div>
              )}

              {/* Indexes Tab */}
              {activeTab === 'indexes' && (
                <div className="space-y-2">
                  {tableDetail.indexes.map(idx => (
                    <div key={idx.index_name} className="p-3 bg-slate-950 border border-slate-800 rounded-lg text-xs space-y-1">
                      <div className="flex items-center justify-between">
                        <span className="font-mono font-bold text-slate-200">{idx.index_name}</span>
                        <span className="px-1.5 py-0.5 rounded bg-slate-800 text-amber-300 font-mono text-[10px]">
                          {idx.uniqueness}
                        </span>
                      </div>
                      <p className="text-slate-400 font-mono text-[11px]">
                        Columns: <strong>{idx.columns.join(', ')}</strong>
                      </p>
                      <p className="text-slate-500 text-[11px]">Status: {idx.status}</p>
                    </div>
                  ))}
                </div>
              )}

              {/* Sample Data Preview Tab */}
              {activeTab === 'preview' && (
                <div className="h-96">
                  <DataGrid
                    columns={tableDetail.columns.map(c => ({ name: c.name, data_type: c.data_type, nullable: c.nullable }))}
                    rows={tableDetail.preview_rows}
                  />
                </div>
              )}

              {/* Foreign Key Relationships Tab */}
              {activeTab === 'relationships' && (
                <div className="space-y-3">
                  <p className="text-xs text-slate-400">
                    Direct Foreign Key references connecting <strong className="text-slate-200">{selectedTableName}</strong> to parent or child tables:
                  </p>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                    {relationships
                      .filter(r => r.from_table === selectedTableName || r.to_table === selectedTableName)
                      .map((r, i) => (
                        <div key={i} className="p-3 bg-slate-950 border border-slate-800 rounded-lg text-xs">
                          <span className="text-[10px] font-mono text-slate-500 block mb-1">{r.constraint_name}</span>
                          <div className="flex items-center justify-between font-mono">
                            <span className={r.from_table === selectedTableName ? 'text-sky-300 font-bold' : 'text-slate-300'}>
                              {r.from_table}.{r.from_column}
                            </span>
                            <ArrowRight className="w-3.5 h-3.5 text-slate-600 mx-2" />
                            <span className={r.to_table === selectedTableName ? 'text-sky-300 font-bold' : 'text-slate-300'}>
                              {r.to_table}.{r.to_column}
                            </span>
                          </div>
                        </div>
                      ))}
                  </div>
                </div>
              )}
            </>
          ) : (
            <div className="text-slate-500 text-xs p-4">Select a table to inspect metadata.</div>
          )}
        </div>
      </div>
    </div>
  );
};
