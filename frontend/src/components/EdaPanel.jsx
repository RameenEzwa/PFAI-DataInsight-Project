import { useQuery } from "@tanstack/react-query";
import { BarChart3, Sigma } from "lucide-react";

import { api } from "../api/client";
import { Skeleton } from "./Skeleton";

export function EdaPanel({ dataset }) {
  const edaQuery = useQuery({
    queryKey: ["eda", dataset?.id],
    queryFn: () => api.getEda(dataset.id),
    enabled: Boolean(dataset?.id),
  });

  if (edaQuery.isLoading) return <Skeleton className="h-96 w-full" />;
  if (edaQuery.error) return <p className="text-sm text-rose-600">{edaQuery.error.message}</p>;

  const eda = edaQuery.data;
  const matrix = eda.correlation_matrix || { columns: [], values: [] };

  return (
    <div className="space-y-6">
      <section className="glass-panel rounded-lg p-4">
        <div className="mb-4 flex items-center gap-2">
          <Sigma className="h-5 w-5 text-cyan-600" />
          <h2 className="text-sm font-semibold text-zinc-950 dark:text-white">Statistical Summary</h2>
        </div>
        <div className="overflow-auto">
          <table className="min-w-full text-left text-sm">
            <thead className="bg-zinc-50 text-xs uppercase text-zinc-500 dark:bg-neutral-950 dark:text-neutral-400">
              <tr>
                <th className="px-3 py-3">Feature</th>
                <th className="px-3 py-3">Mean</th>
                <th className="px-3 py-3">Median</th>
                <th className="px-3 py-3">Std</th>
                <th className="px-3 py-3">Variance</th>
                <th className="px-3 py-3">Skew</th>
                <th className="px-3 py-3">Kurtosis</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-zinc-100 dark:divide-neutral-800">
              {eda.column_statistics
                ?.filter((item) => item.mean !== undefined)
                .slice(0, 40)
                .map((item) => (
                  <tr key={item.column}>
                    <td className="px-3 py-3 font-medium text-zinc-900 dark:text-white">{item.column}</td>
                    <td className="px-3 py-3">{format(item.mean)}</td>
                    <td className="px-3 py-3">{format(item.median)}</td>
                    <td className="px-3 py-3">{format(item.standard_deviation)}</td>
                    <td className="px-3 py-3">{format(item.variance)}</td>
                    <td className="px-3 py-3">{format(item.skewness)}</td>
                    <td className="px-3 py-3">{format(item.kurtosis)}</td>
                  </tr>
                ))}
            </tbody>
          </table>
        </div>
      </section>

      <div className="grid gap-6 xl:grid-cols-2">
        <section className="glass-panel rounded-lg p-4">
          <div className="mb-4 flex items-center gap-2">
            <BarChart3 className="h-5 w-5 text-emerald-600" />
            <h2 className="text-sm font-semibold text-zinc-950 dark:text-white">Strong Correlations</h2>
          </div>
          <div className="space-y-3">
            {eda.strong_correlations?.length ? (
              eda.strong_correlations.slice(0, 10).map((item) => (
                <div className="rounded-lg border border-zinc-200 p-3 dark:border-neutral-800" key={`${item.feature_a}-${item.feature_b}`}>
                  <div className="flex items-center justify-between gap-4">
                    <p className="truncate text-sm font-semibold text-zinc-900 dark:text-white">
                      {item.feature_a} / {item.feature_b}
                    </p>
                    <span className="text-sm font-semibold text-cyan-700 dark:text-cyan-300">{item.correlation.toFixed(2)}</span>
                  </div>
                  <div className="mt-2 h-2 rounded-full bg-zinc-100 dark:bg-neutral-800">
                    <div className="h-2 rounded-full bg-cyan-500" style={{ width: `${Math.min(100, Math.abs(item.correlation) * 100)}%` }} />
                  </div>
                </div>
              ))
            ) : (
              <p className="text-sm text-zinc-500">No strong correlations above the threshold.</p>
            )}
          </div>
        </section>

        <section className="glass-panel rounded-lg p-4">
          <h2 className="mb-4 text-sm font-semibold text-zinc-950 dark:text-white">Correlation Matrix</h2>
          {matrix.columns.length ? (
            <div className="overflow-auto">
              <div className="grid min-w-[520px]" style={{ gridTemplateColumns: `130px repeat(${matrix.columns.length}, minmax(70px, 1fr))` }}>
                <div />
                {matrix.columns.map((column) => (
                  <div className="truncate px-2 py-2 text-xs font-semibold text-zinc-500" key={column} title={column}>
                    {column}
                  </div>
                ))}
                {matrix.values.map((row, rowIndex) => (
                  <>
                    <div className="truncate px-2 py-2 text-xs font-semibold text-zinc-500" key={`${matrix.columns[rowIndex]}-label`}>
                      {matrix.columns[rowIndex]}
                    </div>
                    {row.map((value, columnIndex) => (
                      <div
                        className="m-0.5 rounded px-2 py-2 text-center text-xs font-medium"
                        key={`${rowIndex}-${columnIndex}`}
                        style={{
                          backgroundColor: heatColor(value),
                          color: Math.abs(value || 0) > 0.55 ? "white" : undefined,
                        }}
                      >
                        {Number(value).toFixed(2)}
                      </div>
                    ))}
                  </>
                ))}
              </div>
            </div>
          ) : (
            <p className="text-sm text-zinc-500">Correlation needs at least two numeric columns.</p>
          )}
        </section>
      </div>
    </div>
  );
}

function format(value) {
  if (value === null || value === undefined || Number.isNaN(value)) return "-";
  return Number(value).toLocaleString(undefined, { maximumFractionDigits: 3 });
}

function heatColor(value) {
  const intensity = Math.min(1, Math.abs(value || 0));
  if (value >= 0) return `rgba(8, 145, 178, ${0.12 + intensity * 0.78})`;
  return `rgba(225, 29, 72, ${0.12 + intensity * 0.68})`;
}

