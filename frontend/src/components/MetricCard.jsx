export function MetricCard({ icon: Icon, label, value, accent = "cyan", sublabel }) {
  const accentClasses = {
    cyan: "bg-cyan-50 text-cyan-700 dark:bg-cyan-950/40 dark:text-cyan-300",
    emerald: "bg-emerald-50 text-emerald-700 dark:bg-emerald-950/40 dark:text-emerald-300",
    amber: "bg-amber-50 text-amber-700 dark:bg-amber-950/40 dark:text-amber-300",
    rose: "bg-rose-50 text-rose-700 dark:bg-rose-950/40 dark:text-rose-300",
    violet: "bg-violet-50 text-violet-700 dark:bg-violet-950/40 dark:text-violet-300",
  };

  return (
    <section className="glass-panel rounded-lg p-4">
      <div className="flex items-center justify-between gap-3">
        <div>
          <p className="text-xs font-medium uppercase tracking-wide text-zinc-500 dark:text-neutral-400">{label}</p>
          <p className="mt-2 text-2xl font-semibold text-zinc-950 dark:text-white">{value}</p>
        </div>
        {Icon ? (
          <div className={`flex h-10 w-10 items-center justify-center rounded-lg ${accentClasses[accent]}`}>
            <Icon className="h-5 w-5" />
          </div>
        ) : null}
      </div>
      {sublabel ? <p className="mt-3 text-xs text-zinc-500 dark:text-neutral-400">{sublabel}</p> : null}
    </section>
  );
}

