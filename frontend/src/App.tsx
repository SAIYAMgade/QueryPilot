import React, { useState } from 'react';
import { AppLayout, NavTab } from './layouts/AppLayout';
import { OverviewView } from './features/overview/OverviewView';
import { WorkspaceView } from './features/workspace/WorkspaceView';
import { SchemaExplorerView } from './features/schema-explorer/SchemaExplorerView';
import { ExecutionPlansView } from './features/execution-plans/ExecutionPlansView';
import { ComparisonView } from './features/comparisons/ComparisonView';
import { DiagnosticsView } from './features/diagnostics/DiagnosticsView';
import { InvestigationsView } from './features/investigations/InvestigationsView';
import { ReportsView } from './features/reports/ReportsView';
import { SettingsView } from './features/settings/SettingsView';

export const App: React.FC = () => {
  const [currentTab, setCurrentTab] = useState<NavTab>('overview');

  // Cross-view state sharing
  const [diagPrefill, setDiagPrefill] = useState<{ code?: string; msg?: string; sql?: string } | null>(null);
  const [invPrefill, setInvPrefill] = useState<{ baselineSql: string; candidateSql: string; hypothesis?: string } | null>(null);
  const [reportTargetId, setReportTargetId] = useState<string | null>(null);

  const handleNavigateToDiagnostics = (code?: string, msg?: string, sql?: string) => {
    setDiagPrefill({ code, msg, sql });
    setCurrentTab('diagnostics');
  };

  const handleOpenInvestigationFromComparison = (data: { baselineSql: string; candidateSql: string; hypothesis?: string }) => {
    setInvPrefill(data);
    setCurrentTab('investigations');
  };

  const handleViewReport = (invId: string) => {
    setReportTargetId(invId);
    setCurrentTab('reports');
  };

  return (
    <AppLayout currentTab={currentTab} onTabChange={setCurrentTab}>
      {currentTab === 'overview' && (
        <OverviewView onNavigate={setCurrentTab} />
      )}

      {currentTab === 'workspace' && (
        <WorkspaceView
          onNavigateToDiagnostics={handleNavigateToDiagnostics}
        />
      )}

      {currentTab === 'schema' && (
        <SchemaExplorerView
          onInsertSql={(query) => {
            setCurrentTab('workspace');
          }}
        />
      )}

      {currentTab === 'plans' && (
        <ExecutionPlansView />
      )}

      {currentTab === 'comparisons' && (
        <ComparisonView
          onOpenInvestigation={handleOpenInvestigationFromComparison}
        />
      )}

      {currentTab === 'diagnostics' && (
        <DiagnosticsView
          initialErrorCode={diagPrefill?.code}
          initialErrorMessage={diagPrefill?.msg}
          initialSql={diagPrefill?.sql}
        />
      )}

      {currentTab === 'investigations' && (
        <InvestigationsView
          onViewReport={handleViewReport}
          prefillData={invPrefill}
        />
      )}

      {currentTab === 'reports' && (
        <ReportsView initialInvestigationId={reportTargetId} />
      )}

      {currentTab === 'settings' && (
        <SettingsView />
      )}
    </AppLayout>
  );
};

export default App;
