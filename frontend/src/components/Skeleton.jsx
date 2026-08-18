export function Skeleton({ className = "" }) {
  return <div className={`animate-pulse rounded-lg bg-zinc-200 dark:bg-neutral-800 ${className}`} />;
}

export function EmptyState({ title, detail, action }) {
  return (
    <div className="flex min-h-[320px] flex-col items-center justify-center rounded-lg border border-dashed border-zinc-300 bg-white p-8 text-center dark:border-neutral-700 dark:bg-neutral-900">
      <h2 className="text-lg font-semibold text-zinc-950 dark:text-white">{title}</h2>
      {detail ? <p className="mt-2 max-w-md text-sm text-zinc-500 dark:text-neutral-400">{detail}</p> : null}
      {action ? <div className="mt-5">{action}</div> : null}
    </div>
  );
}

