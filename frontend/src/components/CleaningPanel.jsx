import { useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Check, Download, Eraser, Loader2, RefreshCw, Sparkles, Wand2 } from "lucide-react";

import { api } from "../api/client";
import { Skeleton } from "./Skeleton";

export function CleaningPanel({ dataset }) {
  const [strategy, setStrategy] = useState("smart");
  const [selectedColumns, setSelectedColumns] = useState([]);
  const [dropDuplicates, setDropDuplicates] = useState(true);
  const [standardizeNulls, setStandardizeNulls] = useState(true);
  const [constantValue, setConstantValue] = useState("");
  const queryClient = useQueryClient();
  const columns = useMemo(() => dataset?.metadata?.columns || [], [dataset]);
  const missingColumns = useMemo(
    () => new Set(Object.keys(qualityDataFromCache(queryClient, dataset?.id)?.missing_by_column || {})),
    [dataset?.id, queryClient],
  );

  const qualityQuery = useQuery({
    queryKey: ["quality", dataset?.id],
    queryFn: () => api.getQuality(dataset.id),
    enabled: Boolean(dataset?.id),
    placeholderData: (previous) => previous,
  });

  const cleanMutation = useMutation({
    mutationFn: (payload) => api.cleanDataset(dataset.id, payload),
    onSuccess: (report) => {
      queryClient.setQueryData(["quality", dataset.id], report.after);
      queryClient.invalidateQueries({ queryKey: ["datasets"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard"] });
      queryClient.invalidateQueries({ queryKey: ["preview", dataset.id] });
    },
  });

  if (qualityQuery.isLoading) return <Skeleton className="h-96 w-full" />;
  if (qualityQuery.error) return <p className="text-sm text-rose-600">{qualityQuery.error.message}</p>;

  const quality = cleanMutation.data?.after || qualityQuery.data;
  const before = cleanMutation.data?.before;
  const missingByColumn = quality?.missing_by_column || {};
  const missingColumnNames = Object.keys(missingByColumn);

  const runManualClean = () => {
    cleanMutation.mutate({
      mode: "manual",
      persist: true,
      actions: {
        standardize_nulls: standardizeNulls,
        drop_duplicates: dropDuplicates,
        handle_missing: {
          strategy,
          columns: selectedColumns.length ? selectedColumns : undefined,
          value: strategy === "constant" ? constantValue : undefined,
        },
      },
    });
  };

  return (
    <div className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_360px]">
      <section className="glass-panel rounded-lg p-4">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div className="flex items-center gap-2">
            <Eraser className="h-5 w-5 text-cyan-600" />
            <h2 className="text-sm font-semibold text-zinc-950 dark:text-white">Automated Data Cleaning</h2>
          </div>
          <div className="flex gap-2">
            <button className="button-secondary" onClick={() => qualityQuery.refetch()} type="button">
              <RefreshCw className="h-4 w-4" />
              Scan
            </button>
            <a className="button-secondary" href={api.cleanedCsvUrl(dataset.id)} rel="noreferrer" target="_blank">
              <Download className="h-4 w-4" />
              CSV
            </a>
            <button
              className="button-primary"
              disabled={cleanMutation.isPending}
              onClick={() => cleanMutation.mutate({ mode: "auto", persist: true })}
              type="button"
            >
              {cleanMutation.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : <Sparkles className="h-4 w-4" />}
              Auto Clean
            </button>
          </div>
        </div>

        <div className="mt-5 grid gap-3 md:grid-cols-2 xl:grid-cols-5">
          <QualityStat label="Total Rows" value={quality.row_count?.toLocaleString()} />
          <QualityStat label="Analyzed Rows" value={(quality.sampled_rows || quality.row_count)?.toLocaleString()} />
          <QualityStat label="Missing In Analysis" value={quality.missing_total?.toLocaleString()} />
          <QualityStat label="Duplicates In Analysis" value={quality.duplicate_rows?.toLocaleString()} />
          <QualityStat label="Issues" value={(quality.suggestions?.length || 0).toLocaleString()} />
        </div>

        {before ? (
          <div className="mt-5 rounded-lg border border-emerald-200 bg-emerald-50 p-4 text-sm text-emerald-900 dark:border-emerald-900/60 dark:bg-emerald-950/30 dark:text-emerald-100">
            <p className="font-semibold">Before / After</p>
            <p className="mt-1">
              Missing values {before.missing_total?.toLocaleString()}
              {" -> "}
              {quality.missing_total?.toLocaleString()}, duplicates {before.duplicate_rows?.toLocaleString()}
              {" -> "}
              {quality.duplicate_rows?.toLocaleString()}.
            </p>
          </div>
        ) : null}

        <div className="mt-5 rounded-lg border border-zinc-200 bg-zinc-50 p-4 dark:border-neutral-800 dark:bg-neutral-950">
          <div className="flex items-center gap-2">
            <Wand2 className="h-4 w-4 text-cyan-600" />
            <h3 className="text-sm font-semibold text-zinc-950 dark:text-white">Manual Missing Value Fix</h3>
          </div>
          <div className="mt-4 grid gap-3 md:grid-cols-[1fr_1fr_auto]">
            <label>
              <span className="mb-2 block text-xs font-semibold uppercase tracking-wide text-zinc-500 dark:text-neutral-400">Fill Strategy</span>
              <select className="select-base" value={strategy} onChange={(event) => setStrategy(event.target.value)}>
                <option value="smart">Smart fill</option>
                <option value="mean">Mean for numeric, mode otherwise</option>
                <option value="median">Median for numeric, mode otherwise</option>
                <option value="mode">Mode</option>
                <option value="zero">Zero</option>
                <option value="constant">Custom value</option>
                <option value="drop_rows">Remove rows with missing values</option>
              </select>
            </label>
            <label>
              <span className="mb-2 block text-xs font-semibold uppercase tracking-wide text-zinc-500 dark:text-neutral-400">Custom Value</span>
              <input
                className="input-base"
                disabled={strategy !== "constant"}
                onChange={(event) => setConstantValue(event.target.value)}
                placeholder="Unknown"
                value={constantValue}
              />
            </label>
            <div className="flex items-end">
              <button className="button-primary w-full" disabled={cleanMutation.isPending} onClick={runManualClean} type="button">
                {cleanMutation.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : <Check className="h-4 w-4" />}
                Apply
              </button>
            </div>
          </div>
          <div className="mt-4 flex flex-wrap gap-3">
            <label className="flex items-center gap-2 text-sm text-zinc-700 dark:text-neutral-300">
              <input className="h-4 w-4 rounded border-zinc-300 text-cyan-600" checked={standardizeNulls} onChange={(event) => setStandardizeNulls(event.target.checked)} type="checkbox" />
              Convert null-like text
            </label>
            <label className="flex items-center gap-2 text-sm text-zinc-700 dark:text-neutral-300">
              <input className="h-4 w-4 rounded border-zinc-300 text-cyan-600" checked={dropDuplicates} onChange={(event) => setDropDuplicates(event.target.checked)} type="checkbox" />
              Remove duplicates
            </label>
          </div>
          <p className="mt-3 text-xs text-zinc-500 dark:text-neutral-400">No selected columns means the fix applies to every column with missing values.</p>
          <div className="mt-3 flex flex-wrap gap-2">
            {columns.map((column) => {
              const active = selectedColumns.includes(column.name);
              const hasMissing = missingColumnNames.includes(column.name) || missingColumns.has(column.name);
              return (
                <button
                  className={`rounded-lg border px-3 py-2 text-xs font-medium transition ${
                    active
                      ? "border-cyan-400 bg-cyan-50 text-cyan-700 dark:bg-cyan-950/30 dark:text-cyan-200"
                      : hasMissing
                        ? "border-amber-300 bg-amber-50 text-amber-800 dark:border-amber-900 dark:bg-amber-950/30 dark:text-amber-200"
                        : "border-zinc-200 bg-white text-zinc-600 hover:border-cyan-300 dark:border-neutral-800 dark:bg-neutral-900 dark:text-neutral-300"
                  }`}
                  key={column.name}
                  onClick={() => setSelectedColumns((current) => (active ? current.filter((item) => item !== column.name) : [...current, column.name]))}
                  type="button"
                >
                  {column.name}
                </button>
              );
            })}
          </div>
        </div>

        <div className="mt-5">
          <h3 className="text-xs font-semibold uppercase tracking-wide text-zinc-500 dark:text-neutral-400">Suggestions</h3>
          <div className="mt-3 grid gap-3">
            {quality.suggestions?.length ? (
              quality.suggestions.map((suggestion) => (
                <article className="rounded-lg border border-zinc-200 bg-white p-3 dark:border-neutral-800 dark:bg-neutral-950" key={suggestion.id}>
                  <div className="flex items-start gap-3">
                    <Check className="mt-0.5 h-4 w-4 text-emerald-600" />
                    <div>
                      <p className="text-sm font-semibold text-zinc-900 dark:text-white">{suggestion.issue?.replaceAll("_", " ")}</p>
                      <p className="mt-1 text-sm text-zinc-600 dark:text-neutral-400">{suggestion.recommendation}</p>
                    </div>
                  </div>
                </article>
              ))
            ) : (
              <p className="rounded-lg border border-zinc-200 p-4 text-sm text-zinc-500 dark:border-neutral-800 dark:text-neutral-400">
                No cleaning suggestions for the analyzed sample.
              </p>
            )}
          </div>
        </div>
      </section>

      <section className="glass-panel rounded-lg p-4">
        <h2 className="text-sm font-semibold text-zinc-950 dark:text-white">Issue Breakdown</h2>
        <div className="mt-4 space-y-3">
          {Object.entries(quality.missing_by_column || {})
            .slice(0, 12)
            .map(([column, count]) => (
              <div key={column}>
                <div className="mb-1 flex justify-between gap-3 text-xs text-zinc-500 dark:text-neutral-400">
                  <span className="truncate">{column}</span>
                  <span>{count}</span>
                </div>
                <div className="h-2 rounded-full bg-zinc-100 dark:bg-neutral-800">
                  <div className="h-2 rounded-full bg-amber-500" style={{ width: `${Math.min(100, (count / Math.max(quality.sampled_rows || quality.row_count, 1)) * 100)}%` }} />
                </div>
              </div>
            ))}
          {!Object.keys(quality.missing_by_column || {}).length ? <p className="text-sm text-zinc-500">No missing columns.</p> : null}
        </div>
      </section>
    </div>
  );
}

function qualityDataFromCache(queryClient, datasetId) {
  if (!datasetId) return null;
  return queryClient.getQueryData(["quality", datasetId]);
}

function QualityStat({ label, value }) {
  return (
    <div className="rounded-lg border border-zinc-200 bg-zinc-50 p-3 dark:border-neutral-800 dark:bg-neutral-950">
      <p className="text-xs font-medium uppercase tracking-wide text-zinc-500 dark:text-neutral-400">{label}</p>
      <p className="mt-2 text-xl font-semibold text-zinc-950 dark:text-white">{value ?? 0}</p>
    </div>
  );
}
