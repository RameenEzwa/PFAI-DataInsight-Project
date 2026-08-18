import { useMemo, useState } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import { Loader2, Plus, WandSparkles } from "lucide-react";

import { api } from "../api/client";
import { PlotRenderer } from "./PlotRenderer";
import { Skeleton } from "./Skeleton";

export function VisualBuilder({ dataset }) {
  const [chartType, setChartType] = useState("histogram");
  const [x, setX] = useState("");
  const [y, setY] = useState("");

  const columns = useMemo(() => dataset?.metadata?.columns || [], [dataset]);
  const numericColumns = columns.filter((column) => column.detected_type === "numeric").map((column) => column.name);
  const chartOptions = [
    { value: "bar", label: "Bar chart" },
    { value: "line", label: "Line chart" },
    { value: "pie", label: "Pie chart" },
    { value: "scatter", label: "Scatter plot" },
    { value: "histogram", label: "Histogram" },
    { value: "box", label: "Box plot" },
    { value: "correlation", label: "Correlation heatmap" },
    { value: "pair", label: "Pair plot" },
    { value: "time_series", label: "Time series" },
  ];

  const defaultsQuery = useQuery({
    queryKey: ["visualizations", dataset?.id],
    queryFn: () => api.getVisualizations(dataset.id),
    enabled: Boolean(dataset?.id),
  });

  const chartMutation = useMutation({
    mutationFn: () =>
      api.createVisualization(dataset.id, {
        chart_type: chartType,
        x: x || null,
        y: y || null,
        color: null,
        columns: chartType === "correlation" || chartType === "pair" ? numericColumns.slice(0, 6) : null,
      }),
  });

  return (
    <div className="space-y-6">
      <section className="glass-panel rounded-lg p-4">
        <div className="mb-4 flex items-center gap-2">
          <WandSparkles className="h-5 w-5 text-cyan-600" />
          <h2 className="text-sm font-semibold text-zinc-950 dark:text-white">Interactive Visualization Builder</h2>
        </div>
        <div className="grid gap-3 md:grid-cols-4">
          <Field label="Chart">
            <select className="select-base" value={chartType} onChange={(event) => setChartType(event.target.value)}>
              {chartOptions.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </Field>
          <Field label="X Axis">
            <ColumnSelect columns={columns} value={x} onChange={setX} />
          </Field>
          <Field label="Y Axis">
            <ColumnSelect columns={columns} value={y} onChange={setY} />
          </Field>
          <div className="flex items-end">
            <button className="button-primary w-full" disabled={chartMutation.isPending} onClick={() => chartMutation.mutate()} type="button">
              {chartMutation.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : <Plus className="h-4 w-4" />}
              Create
            </button>
          </div>
        </div>
        {chartMutation.error ? <p className="mt-3 text-sm text-rose-600">{chartMutation.error.message}</p> : null}
      </section>

      {chartMutation.data ? <PlotRenderer chart={chartMutation.data} /> : null}

      <section>
        <h2 className="mb-3 text-sm font-semibold text-zinc-950 dark:text-white">Generated Chart Set</h2>
        {defaultsQuery.isLoading ? (
          <div className="grid gap-4 xl:grid-cols-2">
            <Skeleton className="h-80 w-full" />
            <Skeleton className="h-80 w-full" />
          </div>
        ) : defaultsQuery.error ? (
          <div className="rounded-lg border border-rose-200 bg-rose-50 p-4 text-sm text-rose-800 dark:border-rose-900/70 dark:bg-rose-950/30 dark:text-rose-200">
            <p className="font-semibold">Visualization request failed</p>
            <p className="mt-1">{defaultsQuery.error.message}</p>
            <button className="button-secondary mt-3" onClick={() => defaultsQuery.refetch()} type="button">
              Retry
            </button>
          </div>
        ) : (
          <div className="grid gap-4 xl:grid-cols-2">
            {defaultsQuery.data?.charts?.map((chart, index) => (
              <PlotRenderer chart={chart} key={index} />
            ))}
          </div>
        )}
      </section>
    </div>
  );
}

function Field({ label, children }) {
  return (
    <label>
      <span className="mb-2 block text-xs font-semibold uppercase tracking-wide text-zinc-500 dark:text-neutral-400">{label}</span>
      {children}
    </label>
  );
}

function ColumnSelect({ columns, value, onChange }) {
  return (
    <select className="select-base" value={value} onChange={(event) => onChange(event.target.value)}>
      <option value="">Auto</option>
      {columns.map((column) => (
        <option key={column.name} value={column.name}>
          {column.name}
        </option>
      ))}
    </select>
  );
}
