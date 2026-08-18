import { useQuery } from "@tanstack/react-query";
import { Activity, AlertCircle, Columns3, Database, Gauge, Rows3 } from "lucide-react";

import { api } from "../api/client";
import { DataPreview } from "./DataPreview";
import { InsightsPanel } from "./InsightsPanel";
import { MetricCard } from "./MetricCard";
import { Skeleton } from "./Skeleton";

const numberFormat = new Intl.NumberFormat();

export function Dashboard({ dataset }) {
  const dashboardQuery = useQuery({ queryKey: ["dashboard"], queryFn: api.getDashboard });

  if (!dataset) return null;

  const metadata = dataset.metadata || {};
  const columns = metadata.columns || [];
  const missing = metadata.missing_cells_in_sample || 0;
  const health = metadata.health_score || 100;

  return (
    <div className="space-y-6">
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <MetricCard accent="cyan" icon={Rows3} label="Total Records" value={numberFormat.format(dataset.row_count)} />
        <MetricCard accent="emerald" icon={Columns3} label="Total Features" value={numberFormat.format(dataset.column_count)} />
        <MetricCard accent="amber" icon={AlertCircle} label="Missing Values" value={numberFormat.format(missing)} sublabel="Analyzed sample" />
        <MetricCard accent="violet" icon={Gauge} label="Dataset Health" value={`${health}%`} />
      </div>

      <div className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_360px]">
        <section className="glass-panel rounded-lg p-4">
          <div className="mb-4 flex items-center gap-2">
            <Database className="h-5 w-5 text-cyan-600" />
            <h2 className="text-sm font-semibold text-zinc-950 dark:text-white">Column Intelligence</h2>
          </div>
          <div className="grid gap-3 md:grid-cols-2">
            {columns.slice(0, 12).map((column) => (
              <article className="rounded-lg border border-zinc-200 bg-zinc-50 p-3 dark:border-neutral-800 dark:bg-neutral-950" key={column.name}>
                <div className="flex items-center justify-between gap-3">
                  <h3 className="truncate text-sm font-semibold text-zinc-900 dark:text-white" title={column.name}>
                    {column.name}
                  </h3>
                  <span className="rounded-lg bg-white px-2 py-1 text-xs font-medium text-cyan-700 dark:bg-neutral-900 dark:text-cyan-300">
                    {column.detected_type}
                  </span>
                </div>
                <div className="mt-3 grid grid-cols-3 gap-2 text-xs text-zinc-500 dark:text-neutral-400">
                  <span>{column.unique_count} unique</span>
                  <span>{Math.round((column.missing_pct || 0) * 100)}% null</span>
                  <span>{column.pandas_dtype}</span>
                </div>
              </article>
            ))}
          </div>
        </section>

        <section className="glass-panel rounded-lg p-4">
          <div className="mb-4 flex items-center gap-2">
            <Activity className="h-5 w-5 text-emerald-600" />
            <h2 className="text-sm font-semibold text-zinc-950 dark:text-white">Recent Analysis</h2>
          </div>
          {dashboardQuery.isLoading ? (
            <Skeleton className="h-48 w-full" />
          ) : (
            <div className="space-y-3">
              {dashboardQuery.data?.recent_analysis_history?.slice(0, 7).map((item) => (
                <div className="rounded-lg border border-zinc-200 p-3 dark:border-neutral-800" key={item.id}>
                  <p className="text-sm font-semibold text-zinc-900 dark:text-white">{item.title}</p>
                  <p className="mt-1 text-xs text-zinc-500 dark:text-neutral-400">{item.dataset_name}</p>
                </div>
              ))}
              {!dashboardQuery.data?.recent_analysis_history?.length ? <p className="text-sm text-zinc-500">No analysis history yet.</p> : null}
            </div>
          )}
        </section>
      </div>

      <InsightsPanel datasetId={dataset.id} />
      <DataPreview datasetId={dataset.id} />
    </div>
  );
}

