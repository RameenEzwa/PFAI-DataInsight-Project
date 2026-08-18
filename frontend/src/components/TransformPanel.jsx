import { useMemo, useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Loader2, PlusCircle, Workflow } from "lucide-react";

import { api } from "../api/client";

export function TransformPanel({ dataset }) {
  const [operationType, setOperationType] = useState("normalize");
  const [selectedColumns, setSelectedColumns] = useState([]);
  const [targetColumn, setTargetColumn] = useState("");
  const [separator, setSeparator] = useState(" ");
  const [formula, setFormula] = useState("");
  const queryClient = useQueryClient();

  const columns = useMemo(() => dataset?.metadata?.columns || [], [dataset]);
  const transformMutation = useMutation({
    mutationFn: () =>
      api.transformDataset(dataset.id, {
        persist: true,
        operations: [
          {
            type: operationType,
            columns: selectedColumns,
            target_column: targetColumn || null,
            separator,
            formula: formula || null,
          },
        ],
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["datasets"] });
      queryClient.invalidateQueries({ queryKey: ["preview", dataset.id] });
    },
  });

  return (
    <div className="grid gap-6 xl:grid-cols-[360px_minmax(0,1fr)]">
      <section className="glass-panel rounded-lg p-4">
        <div className="mb-4 flex items-center gap-2">
          <Workflow className="h-5 w-5 text-cyan-600" />
          <h2 className="text-sm font-semibold text-zinc-950 dark:text-white">Data Transformation</h2>
        </div>
        <label className="text-xs font-semibold uppercase tracking-wide text-zinc-500 dark:text-neutral-400">Operation</label>
        <select className="select-base mt-2" value={operationType} onChange={(event) => setOperationType(event.target.value)}>
          <option value="normalize">Normalization</option>
          <option value="standardize">Standardization</option>
          <option value="encode">Encode categorical</option>
          <option value="scale_minmax">Feature scaling</option>
          <option value="merge_columns">Merge columns</option>
          <option value="split_column">Split column</option>
          <option value="date_parts">Date processing</option>
          <option value="calculated_column">Calculated column</option>
        </select>

        <label className="mt-4 block text-xs font-semibold uppercase tracking-wide text-zinc-500 dark:text-neutral-400">Target Column</label>
        <input className="input-base mt-2" value={targetColumn} onChange={(event) => setTargetColumn(event.target.value)} placeholder="new_column" />

        <label className="mt-4 block text-xs font-semibold uppercase tracking-wide text-zinc-500 dark:text-neutral-400">Separator</label>
        <input className="input-base mt-2" value={separator} onChange={(event) => setSeparator(event.target.value)} />

        <label className="mt-4 block text-xs font-semibold uppercase tracking-wide text-zinc-500 dark:text-neutral-400">Formula</label>
        <input className="input-base mt-2" value={formula} onChange={(event) => setFormula(event.target.value)} placeholder="daily_usage_hours / num_platforms_used" />

        <button
          className="button-primary mt-5 w-full"
          disabled={transformMutation.isPending || !selectedColumns.length}
          onClick={() => transformMutation.mutate()}
          type="button"
        >
          {transformMutation.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : <PlusCircle className="h-4 w-4" />}
          Apply
        </button>
        {transformMutation.error ? <p className="mt-3 text-sm text-rose-600">{transformMutation.error.message}</p> : null}
      </section>

      <section className="glass-panel rounded-lg p-4">
        <h2 className="text-sm font-semibold text-zinc-950 dark:text-white">Columns</h2>
        <div className="mt-3 flex flex-wrap gap-2">
          {columns.map((column) => {
            const active = selectedColumns.includes(column.name);
            return (
              <button
                className={`rounded-lg border px-3 py-2 text-xs font-medium transition ${
                  active
                    ? "border-cyan-400 bg-cyan-50 text-cyan-700 dark:bg-cyan-950/30 dark:text-cyan-200"
                    : "border-zinc-200 bg-white text-zinc-600 hover:border-cyan-300 dark:border-neutral-800 dark:bg-neutral-950 dark:text-neutral-300"
                }`}
                key={column.name}
                onClick={() =>
                  setSelectedColumns((current) => (active ? current.filter((item) => item !== column.name) : [...current, column.name]))
                }
                type="button"
              >
                {column.name}
              </button>
            );
          })}
        </div>

        {transformMutation.data ? (
          <div className="mt-6">
            <h3 className="text-xs font-semibold uppercase tracking-wide text-zinc-500 dark:text-neutral-400">Result</h3>
            <div className="mt-3 grid gap-3 md:grid-cols-3">
              <Result label="Rows" value={transformMutation.data.rows?.toLocaleString()} />
              <Result label="Columns" value={transformMutation.data.columns?.toLocaleString()} />
              <Result label="New Columns" value={transformMutation.data.new_columns?.length || 0} />
            </div>
            <div className="mt-4 rounded-lg border border-zinc-200 bg-zinc-50 p-3 dark:border-neutral-800 dark:bg-neutral-950">
              <pre className="max-h-72 overflow-auto text-xs text-zinc-700 dark:text-neutral-300">{JSON.stringify(transformMutation.data.operations, null, 2)}</pre>
            </div>
          </div>
        ) : (
          <p className="mt-5 text-sm text-zinc-500 dark:text-neutral-400">Select columns and apply a transformation to create a saved processed dataset.</p>
        )}
      </section>
    </div>
  );
}

function Result({ label, value }) {
  return (
    <div className="rounded-lg border border-zinc-200 bg-zinc-50 p-3 dark:border-neutral-800 dark:bg-neutral-950">
      <p className="text-xs font-medium uppercase tracking-wide text-zinc-500 dark:text-neutral-400">{label}</p>
      <p className="mt-2 text-xl font-semibold text-zinc-950 dark:text-white">{value}</p>
    </div>
  );
}

