import { useEffect, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { ChevronLeft, ChevronRight, Table2 } from "lucide-react";

import { api } from "../api/client";
import { Skeleton } from "./Skeleton";

export function DataPreview({ datasetId }) {
  const [offset, setOffset] = useState(0);
  const [pageSize, setPageSize] = useState(100);

  useEffect(() => {
    setOffset(0);
  }, [datasetId]);

  const previewQuery = useQuery({
    queryKey: ["preview", datasetId, pageSize, offset],
    queryFn: () => api.getPreview(datasetId, pageSize, offset),
    enabled: Boolean(datasetId),
    placeholderData: (previous) => previous,
  });

  if (previewQuery.isLoading && !previewQuery.data) return <Skeleton className="h-80 w-full" />;
  if (previewQuery.error) return <p className="text-sm text-rose-600">{previewQuery.error.message}</p>;

  const preview = previewQuery.data;
  if (!preview?.columns?.length) return null;

  return (
    <section className="glass-panel rounded-lg">
      <div className="flex flex-col gap-3 border-b border-zinc-200 p-4 dark:border-neutral-800 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex items-center gap-2">
          <Table2 className="h-4 w-4 text-cyan-600" />
          <h2 className="text-sm font-semibold text-zinc-950 dark:text-white">Dataset Preview</h2>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <span className="text-xs text-zinc-500 dark:text-neutral-400">
            {preview.offset + 1}-{Math.min(preview.offset + preview.total_preview_rows, preview.total_rows)} of {preview.total_rows?.toLocaleString()} rows
          </span>
          <select
            className="h-9 rounded-lg border border-zinc-200 bg-white px-2 text-xs text-zinc-700 dark:border-neutral-700 dark:bg-neutral-950 dark:text-neutral-200"
            value={pageSize}
            onChange={(event) => {
              setPageSize(Number(event.target.value));
              setOffset(0);
            }}
          >
            <option value={50}>50</option>
            <option value={100}>100</option>
            <option value={250}>250</option>
            <option value={500}>500</option>
          </select>
          <button
            className="button-secondary h-9 w-9 px-0"
            disabled={!preview.has_previous || previewQuery.isFetching}
            onClick={() => setOffset((current) => Math.max(0, current - pageSize))}
            title="Previous rows"
            type="button"
          >
            <ChevronLeft className="h-4 w-4" />
          </button>
          <button
            className="button-secondary h-9 w-9 px-0"
            disabled={!preview.has_next || previewQuery.isFetching}
            onClick={() => setOffset((current) => current + pageSize)}
            title="Next rows"
            type="button"
          >
            <ChevronRight className="h-4 w-4" />
          </button>
        </div>
      </div>
      <div className="overflow-auto">
        <table className="min-w-full text-left text-sm">
          <thead className="bg-zinc-50 text-xs uppercase text-zinc-500 dark:bg-neutral-950 dark:text-neutral-400">
            <tr>
              {preview.columns.map((column) => (
                <th className="whitespace-nowrap px-4 py-3 font-semibold" key={column}>
                  {column}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-zinc-100 dark:divide-neutral-800">
            {preview.rows.map((row, index) => (
              <tr className="hover:bg-zinc-50 dark:hover:bg-neutral-950" key={`${index}-${preview.columns[0]}`}>
                {preview.columns.map((column) => (
                  <td className="max-w-[220px] truncate px-4 py-3 text-zinc-700 dark:text-neutral-300" key={column} title={String(row[column] ?? "")}>
                    {row[column] === null || row[column] === undefined ? <span className="text-zinc-400">null</span> : String(row[column])}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}
