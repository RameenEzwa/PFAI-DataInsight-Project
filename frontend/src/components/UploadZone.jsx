import { useRef, useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { FileUp, Loader2, UploadCloud } from "lucide-react";

import { api } from "../api/client";
import { useAppStore } from "../store/useAppStore";

export function UploadZone() {
  const inputRef = useRef(null);
  const [isDragging, setIsDragging] = useState(false);
  const queryClient = useQueryClient();
  const setSelectedDatasetId = useAppStore((state) => state.setSelectedDatasetId);

  const uploadMutation = useMutation({
    mutationFn: api.uploadDataset,
    onSuccess: (dataset) => {
      setSelectedDatasetId(dataset.id);
      queryClient.invalidateQueries({ queryKey: ["datasets"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard"] });
    },
  });

  const handleFiles = (files) => {
    const file = files?.[0];
    if (file) uploadMutation.mutate(file);
  };

  const busy = uploadMutation.isPending;

  return (
    <section className="glass-panel rounded-lg p-4">
      <button
        className={`flex min-h-40 w-full flex-col items-center justify-center rounded-lg border border-dashed p-4 text-center transition ${
          isDragging
            ? "border-cyan-500 bg-cyan-50 text-cyan-700 dark:bg-cyan-950/30 dark:text-cyan-200"
            : "border-zinc-300 bg-zinc-50 text-zinc-600 hover:border-cyan-400 dark:border-neutral-700 dark:bg-neutral-950 dark:text-neutral-300"
        }`}
        onClick={() => inputRef.current?.click()}
        onDragLeave={() => setIsDragging(false)}
        onDragOver={(event) => {
          event.preventDefault();
          setIsDragging(true);
        }}
        onDrop={(event) => {
          event.preventDefault();
          setIsDragging(false);
          handleFiles(event.dataTransfer.files);
        }}
        type="button"
      >
        {busy ? <Loader2 className="mb-3 h-7 w-7 animate-spin" /> : <UploadCloud className="mb-3 h-7 w-7" />}
        <span className="text-sm font-semibold">Upload dataset</span>
        <span className="mt-1 text-xs text-zinc-500 dark:text-neutral-500">CSV, XLSX, JSON, SQLite, SQL</span>
      </button>
      <input
        ref={inputRef}
        className="hidden"
        type="file"
        accept=".csv,.xlsx,.xls,.json,.jsonl,.db,.sqlite,.sql"
        onChange={(event) => handleFiles(event.target.files)}
      />
      {uploadMutation.error ? <p className="mt-3 text-xs text-rose-600">{uploadMutation.error.message}</p> : null}
      <div className="mt-3">
        <button className="button-primary" disabled={busy} onClick={() => inputRef.current?.click()} type="button">
          <FileUp className="h-4 w-4" />
          Browse
        </button>
      </div>
    </section>
  );
}
