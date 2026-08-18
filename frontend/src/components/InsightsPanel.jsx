import { useQuery } from "@tanstack/react-query";
import { BrainCircuit, CheckCircle2, Lightbulb, TriangleAlert } from "lucide-react";

import { api } from "../api/client";
import { Skeleton } from "./Skeleton";

const severityIcon = {
  high: TriangleAlert,
  medium: Lightbulb,
  low: CheckCircle2,
};

export function InsightsPanel({ datasetId }) {
  const insightsQuery = useQuery({
    queryKey: ["insights", datasetId],
    queryFn: () => api.getInsights(datasetId),
    enabled: Boolean(datasetId),
  });

  if (insightsQuery.isLoading) return <Skeleton className="h-72 w-full" />;
  if (insightsQuery.error) return <p className="text-sm text-rose-600">{insightsQuery.error.message}</p>;

  const data = insightsQuery.data;
  return (
    <section className="glass-panel rounded-lg p-4">
      <div className="mb-4 flex items-center gap-2">
        <BrainCircuit className="h-5 w-5 text-violet-600" />
        <h2 className="text-sm font-semibold text-zinc-950 dark:text-white">AI Analysis Assistant</h2>
      </div>
      <p className="rounded-lg bg-violet-50 p-3 text-sm leading-6 text-violet-950 dark:bg-violet-950/30 dark:text-violet-100">
        {data.executive_summary}
      </p>
      <div className="mt-4 grid gap-3 md:grid-cols-2">
        {data.insights?.slice(0, 6).map((item) => {
          const Icon = severityIcon[item.severity] || Lightbulb;
          return (
            <article className="rounded-lg border border-zinc-200 bg-white p-3 dark:border-neutral-800 dark:bg-neutral-950" key={`${item.type}-${item.title}`}>
              <div className="flex items-start gap-3">
                <Icon className="mt-0.5 h-4 w-4 shrink-0 text-cyan-600" />
                <div>
                  <h3 className="text-sm font-semibold text-zinc-900 dark:text-white">{item.title}</h3>
                  <p className="mt-1 text-sm leading-6 text-zinc-600 dark:text-neutral-400">{item.detail}</p>
                </div>
              </div>
            </article>
          );
        })}
      </div>
      <div className="mt-4">
        <h3 className="text-xs font-semibold uppercase tracking-wide text-zinc-500 dark:text-neutral-400">Recommendations</h3>
        <div className="mt-2 flex flex-wrap gap-2">
          {data.recommendations?.map((item) => (
            <span className="rounded-lg bg-emerald-50 px-3 py-2 text-xs font-medium text-emerald-800 dark:bg-emerald-950/30 dark:text-emerald-200" key={item}>
              {item}
            </span>
          ))}
        </div>
      </div>
    </section>
  );
}

