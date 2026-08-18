import { useEffect, useMemo } from "react";
import { useQuery } from "@tanstack/react-query";
import {
  BarChart3,
  BrainCircuit,
  Brush,
  DatabaseZap,
  FileText,
  Gauge,
  LayoutDashboard,
  Radar,
} from "lucide-react";

import { api } from "./api/client";
import { CleaningPanel } from "./components/CleaningPanel";
import { Dashboard } from "./components/Dashboard";
import { DatasetSidebar } from "./components/DatasetSidebar";
import { EdaPanel } from "./components/EdaPanel";
import { EmptyState } from "./components/Skeleton";
import { InsightsPanel } from "./components/InsightsPanel";
import { OutlierPanel } from "./components/OutlierPanel";
import { ReportsPanel } from "./components/ReportsPanel";
import { ThemeToggle } from "./components/ThemeToggle";
import { UploadZone } from "./components/UploadZone";
import { VisualBuilder } from "./components/VisualBuilder";
import { useAppStore } from "./store/useAppStore";

const tabs = [
  { id: "dashboard", label: "Dashboard", icon: LayoutDashboard },
  { id: "clean", label: "Clean", icon: Brush },
  { id: "outliers", label: "Outliers", icon: Radar },
  { id: "eda", label: "EDA", icon: Gauge },
  { id: "visuals", label: "Visuals", icon: BarChart3 },
  { id: "insights", label: "Insights", icon: BrainCircuit },
  { id: "reports", label: "Reports", icon: FileText },
];

export default function App() {
  const selectedDatasetId = useAppStore((state) => state.selectedDatasetId);
  const setSelectedDatasetId = useAppStore((state) => state.setSelectedDatasetId);
  const activeTab = useAppStore((state) => state.activeTab);
  const setActiveTab = useAppStore((state) => state.setActiveTab);
  const theme = useAppStore((state) => state.theme);

  const datasetsQuery = useQuery({ queryKey: ["datasets"], queryFn: api.getDatasets });
  const datasets = datasetsQuery.data || [];
  const selectedDataset = useMemo(
    () => datasets.find((dataset) => dataset.id === selectedDatasetId) || datasets[0],
    [datasets, selectedDatasetId],
  );

  useEffect(() => {
    document.documentElement.classList.toggle("dark", theme === "dark");
  }, [theme]);

  useEffect(() => {
    if (!selectedDatasetId && datasets.length) setSelectedDatasetId(datasets[0].id);
  }, [datasets, selectedDatasetId, setSelectedDatasetId]);

  useEffect(() => {
    if (!tabs.some((tab) => tab.id === activeTab)) setActiveTab("dashboard");
  }, [activeTab, setActiveTab]);

  return (
    <div className="min-h-screen bg-zinc-50 text-zinc-900 transition-colors dark:bg-neutral-950 dark:text-neutral-100">
      <header className="sticky top-0 z-30 border-b border-zinc-200 bg-white/90 backdrop-blur dark:border-neutral-800 dark:bg-neutral-950/90">
        <div className="mx-auto flex max-w-[1600px] items-center justify-between gap-4 px-4 py-3 lg:px-6">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-cyan-600 text-white">
              <DatabaseZap className="h-5 w-5" />
            </div>
            <div>
              <h1 className="text-lg font-semibold tracking-normal text-zinc-950 dark:text-white">DataInsight Pro</h1>
              <p className="hidden text-xs text-zinc-500 dark:text-neutral-400 sm:block">Automated analytics platform</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <span className="hidden rounded-lg border border-emerald-200 bg-emerald-50 px-3 py-2 text-xs font-medium text-emerald-700 dark:border-emerald-900/70 dark:bg-emerald-950/30 dark:text-emerald-300 sm:inline-flex">
              API ready
            </span>
            <ThemeToggle />
          </div>
        </div>
      </header>

      <div className="mx-auto grid max-w-[1600px] gap-5 px-4 py-5 lg:grid-cols-[300px_minmax(0,1fr)] lg:px-6">
        <aside className="space-y-4 lg:sticky lg:top-[84px] lg:h-[calc(100vh-104px)] lg:overflow-auto">
          <UploadZone />
          <SideNavigation activeTab={activeTab} setActiveTab={setActiveTab} />
          <DatasetSidebar datasets={datasets} isLoading={datasetsQuery.isLoading} />
        </aside>

        <main className="min-w-0 space-y-5">
          {selectedDataset ? (
            <>
              <section className="glass-panel rounded-lg p-4">
                <div className="flex flex-col gap-4 xl:flex-row xl:items-center xl:justify-between">
                  <div className="min-w-0">
                    <p className="text-xs font-semibold uppercase tracking-wide text-cyan-700 dark:text-cyan-300">{selectedDataset.file_type}</p>
                    <h2 className="truncate text-2xl font-semibold tracking-normal text-zinc-950 dark:text-white">{selectedDataset.name}</h2>
                    <p className="mt-1 text-sm text-zinc-500 dark:text-neutral-400">
                      {selectedDataset.row_count?.toLocaleString()} rows / {selectedDataset.column_count} features
                    </p>
                  </div>
                </div>
              </section>

              {activeTab === "dashboard" ? <Dashboard dataset={selectedDataset} /> : null}
              {activeTab === "clean" ? <CleaningPanel dataset={selectedDataset} /> : null}
              {activeTab === "outliers" ? <OutlierPanel dataset={selectedDataset} /> : null}
              {activeTab === "eda" ? <EdaPanel dataset={selectedDataset} /> : null}
              {activeTab === "visuals" ? <VisualBuilder dataset={selectedDataset} /> : null}
              {activeTab === "insights" ? <InsightsPanel datasetId={selectedDataset.id} /> : null}
              {activeTab === "reports" ? <ReportsPanel dataset={selectedDataset} /> : null}
            </>
          ) : (
            <EmptyState title="No dataset selected" detail="Upload a CSV, Excel, JSON, SQLite, or SQL export to start analysis." />
          )}
        </main>
      </div>
    </div>
  );
}

function SideNavigation({ activeTab, setActiveTab }) {
  return (
    <section className="glass-panel rounded-lg p-2">
      <div className="px-2 py-2">
        <h2 className="text-xs font-semibold uppercase tracking-wide text-zinc-500 dark:text-neutral-400">Navigation</h2>
      </div>
      <nav className="grid gap-1">
        {tabs.map((tab) => {
          const Icon = tab.icon;
          const active = activeTab === tab.id;
          return (
            <button
              className={`flex h-11 items-center gap-3 rounded-lg px-3 text-left text-sm font-medium transition ${
                active
                  ? "bg-cyan-50 text-cyan-800 dark:bg-cyan-950/40 dark:text-cyan-200"
                  : "text-zinc-600 hover:bg-zinc-50 hover:text-zinc-950 dark:text-neutral-300 dark:hover:bg-neutral-950 dark:hover:text-white"
              }`}
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              type="button"
            >
              <Icon className="h-4 w-4" />
              {tab.label}
            </button>
          );
        })}
      </nav>
    </section>
  );
}
