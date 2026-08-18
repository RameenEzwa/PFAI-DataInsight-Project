import { Download, FileBarChart, FileSpreadsheet, FileText } from "lucide-react";

import { api } from "../api/client";

export function ReportsPanel({ dataset }) {
  const reports = [
    { title: "PDF Report", format: "pdf", type: "full", icon: FileText, accent: "text-cyan-600" },
    { title: "Excel Report", format: "xlsx", type: "full", icon: FileSpreadsheet, accent: "text-emerald-600" },
    { title: "Cleaning Report", format: "xlsx", type: "cleaning", icon: FileBarChart, accent: "text-amber-600" },
    { title: "Cleaned Data CSV", customUrl: api.cleanedCsvUrl(dataset.id), icon: FileSpreadsheet, accent: "text-rose-600" },
    { title: "Visualization Report", format: "xlsx", type: "visualization", icon: FileBarChart, accent: "text-violet-600" },
  ];

  return (
    <section className="glass-panel rounded-lg p-4">
      <div className="mb-4 flex items-center gap-2">
        <Download className="h-5 w-5 text-cyan-600" />
        <h2 className="text-sm font-semibold text-zinc-950 dark:text-white">Reporting Module</h2>
      </div>
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-5">
        {reports.map((report) => {
          const Icon = report.icon;
          return (
            <a
              className="group rounded-lg border border-zinc-200 bg-white p-4 transition hover:border-cyan-300 hover:bg-cyan-50 dark:border-neutral-800 dark:bg-neutral-950 dark:hover:border-cyan-700 dark:hover:bg-cyan-950/30"
              href={report.customUrl || api.reportUrl(dataset.id, report.format, report.type)}
              key={report.title}
              rel="noreferrer"
              target="_blank"
            >
              <Icon className={`h-6 w-6 ${report.accent}`} />
              <h3 className="mt-4 text-sm font-semibold text-zinc-950 dark:text-white">{report.title}</h3>
              <p className="mt-2 text-xs text-zinc-500 dark:text-neutral-400">{dataset.name}</p>
              <span className="mt-4 inline-flex items-center gap-2 text-sm font-semibold text-cyan-700 dark:text-cyan-300">
                Download
                <Download className="h-4 w-4 transition group-hover:translate-y-0.5" />
              </span>
            </a>
          );
        })}
      </div>
    </section>
  );
}
