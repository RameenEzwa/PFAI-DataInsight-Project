import { useMemo, useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Loader2, Radar, SlidersHorizontal } from "lucide-react";

import { api } from "../api/client";

export function OutlierPanel({ dataset }) {
  const [method, setMethod] = useState("iqr");
  const [strategy, setStrategy] = useState("retain");
  const [persist, setPersist] = useState(false);
  const [selectedColumns, setSelectedColumns] = useState([]);
  const queryClient = useQueryClient();

  const numericColumns = useMemo(
    () => (dataset?.metadata?.columns || []).filter((column) => column.detected_type === "numeric").map((column) => column.name),
    [dataset],
  );

  const outlierMutation = useMutation({
    mutationFn: () =>
      api.detectOutliers(dataset.id, {
        method,
        strategy,
        persist,
        columns: selectedColumns.length ? selectedColumns : null,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["datasets"] });
      queryClient.invalidateQueries({ queryKey: ["preview", dataset.id] });
    },
  });

  const report = outlierMutation.data?.detection;

  return (
    <div className="grid gap-6 xl:grid-cols-[360px_minmax(0,1fr)]">
      <section className="glass-panel rounded-lg p-4">
        <div className="mb-4 flex items-center gap-2">
          <SlidersHorizontal className="h-5 w-5 text-cyan-600" />
          <h2 className="text-sm font-semibold text-zinc-950 dark:text-white">Outlier Controls</h2>
        </div>
        <label className="text-xs font-semibold uppercase tracking-wide text-zinc-500 dark:text-neutral-400">Method</label>
        <select className="select-base mt-2" value={method} onChange={(event) => setMethod(event.target.value)}>
          <option value="iqr">IQR method</option>
          <option value="zscore">Z-score method</option>
        </select>

        <label className="mt-4 block text-xs font-semibold uppercase tracking-wide text-zinc-500 dark:text-neutral-400">Strategy</label>
        <div className="mt-2 grid grid-cols-3 gap-2">
          {["retain", "cap", "remove"].map((item) => (
            <button
              className={`button-secondary px-2 ${strategy === item ? "border-cyan-400 bg-cyan-50 text-cyan-700 dark:bg-cyan-950/30" : ""}`}
              key={item}
              onClick={() => setStrategy(item)}
              type="button"
            >
              {item}
            </button>
          ))}
        </div>

        <label className="mt-4 flex items-center gap-2 text-sm text-zinc-700 dark:text-neutral-300">
          <input className="h-4 w-4 rounded border-zinc-300 text-cyan-600" checked={persist} onChange={(event) => setPersist(event.target.checked)} type="checkbox" />
          Save strategy result
        </label>

        <button className="button-primary mt-5 w-full" disabled={outlierMutation.isPending} onClick={() => outlierMutation.mutate()} type="button">
          {outlierMutation.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : <Radar className="h-4 w-4" />}
          Detect Outliers
        </button>
        {outlierMutation.error ? <p className="mt-3 text-sm text-rose-600">{outlierMutation.error.message}</p> : null}
      </section>

      <section className="glass-panel rounded-lg p-4">
        <h2 className="text-sm font-semibold text-zinc-950 dark:text-white">Numeric Features</h2>
        <div className="mt-3 flex flex-wrap gap-2">
          {numericColumns.map((column) => {
            const active = selectedColumns.includes(column);
            return (
              <button
                className={`rounded-lg border px-3 py-2 text-xs font-medium transition ${
                  active
                    ? "border-cyan-400 bg-cyan-50 text-cyan-700 dark:bg-cyan-950/30 dark:text-cyan-200"
                    : "border-zinc-200 bg-white text-zinc-600 hover:border-cyan-300 dark:border-neutral-800 dark:bg-neutral-950 dark:text-neutral-300"
                }`}
                key={column}
                onClick={() => setSelectedColumns((current) => (active ? current.filter((item) => item !== column) : [...current, column]))}
                type="button"
              >
                {column}
              </button>
            );
          })}
        </div>

        {report ? (
          <div className="mt-6">
            <div className="grid gap-3 md:grid-cols-3">
              <ResultStat label="Outlier Rows" value={report.outlier_count?.toLocaleString()} />
              <ResultStat label="Outlier Share" value={`${Math.round((report.outlier_pct || 0) * 1000) / 10}%`} />
              <ResultStat label="Columns" value={report.columns?.length} />
            </div>
            <div className="mt-4 overflow-auto">
              <table className="min-w-full text-left text-sm">
                <thead className="text-xs uppercase text-zinc-500 dark:text-neutral-400">
                  <tr>
                    <th className="px-3 py-2">Column</th>
                    <th className="px-3 py-2">Count</th>
                    <th className="px-3 py-2">Lower</th>
                    <th className="px-3 py-2">Upper</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-zinc-100 dark:divide-neutral-800">
                  {report.per_column?.map((item) => (
                    <tr key={item.column}>
                      <td className="px-3 py-2">{item.column}</td>
                      <td className="px-3 py-2">{item.count}</td>
                      <td className="px-3 py-2">{item.lower_bound?.toFixed?.(2) ?? "-"}</td>
                      <td className="px-3 py-2">{item.upper_bound?.toFixed?.(2) ?? "-"}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        ) : (
          <p className="mt-5 text-sm text-zinc-500 dark:text-neutral-400">Run detection to highlight anomalous records.</p>
        )}
      </section>
    </div>
  );
}

function ResultStat({ label, value }) {
  return (
    <div className="rounded-lg border border-zinc-200 bg-zinc-50 p-3 dark:border-neutral-800 dark:bg-neutral-950">
      <p className="text-xs font-medium uppercase tracking-wide text-zinc-500 dark:text-neutral-400">{label}</p>
      <p className="mt-2 text-xl font-semibold text-zinc-950 dark:text-white">{value}</p>
    </div>
  );
}
