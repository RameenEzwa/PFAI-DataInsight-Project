import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Database, FileSpreadsheet, Trash2 } from "lucide-react";

import { api } from "../api/client";
import { useAppStore } from "../store/useAppStore";

const numberFormat = new Intl.NumberFormat();

export function DatasetSidebar({ datasets = [], isLoading }) {
  const selectedDatasetId = useAppStore((state) => state.selectedDatasetId);
  const setSelectedDatasetId = useAppStore((state) => state.setSelectedDatasetId);
  const queryClient = useQueryClient();

  const deleteMutation = useMutation({
    mutationFn: api.deleteDataset,
    onSuccess: (_, deletedId) => {
      if (selectedDatasetId === deletedId) setSelectedDatasetId(null);
      queryClient.setQueryData(["datasets"], (current = []) => current.filter((dataset) => dataset.id !== deletedId));
      queryClient.invalidateQueries({ queryKey: ["datasets"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard"] });
    },
  });

  return (
    <section className="glass-panel rounded-lg">
      <div className="flex items-center gap-2 border-b border-zinc-200 p-4 dark:border-neutral-800">
        <Database className="h-4 w-4 text-cyan-600" />
        <h2 className="text-sm font-semibold text-zinc-950 dark:text-white">Datasets</h2>
      </div>
      <div className="max-h-[420px] space-y-2 overflow-auto p-2">
        {isLoading ? (
          <p className="p-3 text-sm text-zinc-500">Loading datasets...</p>
        ) : datasets.length ? (
          datasets.map((dataset) => {
            const selected = dataset.id === selectedDatasetId;
            return (
              <div
                className={`group flex items-start gap-3 rounded-lg border p-3 transition ${
                  selected
                    ? "border-cyan-400 bg-cyan-50 dark:border-cyan-700 dark:bg-cyan-950/40"
                    : "border-transparent hover:border-zinc-200 hover:bg-zinc-50 dark:hover:border-neutral-800 dark:hover:bg-neutral-950"
                }`}
                key={dataset.id}
              >
                <button className="flex min-w-0 flex-1 items-start gap-3 text-left" onClick={() => setSelectedDatasetId(dataset.id)} type="button">
                  <span className="mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-white text-cyan-700 shadow-sm dark:bg-neutral-900 dark:text-cyan-300">
                    <FileSpreadsheet className="h-4 w-4" />
                  </span>
                  <span className="min-w-0">
                    <span className="block truncate text-sm font-semibold text-zinc-900 dark:text-white">{dataset.name}</span>
                    <span className="mt-1 block text-xs text-zinc-500 dark:text-neutral-400">
                      {numberFormat.format(dataset.row_count)} rows / {dataset.column_count} cols
                    </span>
                  </span>
                </button>
                <button
                  className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg text-zinc-400 hover:bg-rose-50 hover:text-rose-600 dark:hover:bg-rose-950/30"
                  disabled={deleteMutation.isPending && deleteMutation.variables === dataset.id}
                  onClick={(event) => {
                    event.stopPropagation();
                    deleteMutation.mutate(dataset.id);
                  }}
                  title="Delete dataset"
                  type="button"
                >
                  <Trash2 className="h-4 w-4" />
                </button>
              </div>
            );
          })
        ) : (
          <p className="p-3 text-sm text-zinc-500 dark:text-neutral-400">No datasets yet.</p>
        )}
        {deleteMutation.error ? <p className="px-3 pb-3 text-xs text-rose-600">{deleteMutation.error.message}</p> : null}
      </div>
    </section>
  );
}
