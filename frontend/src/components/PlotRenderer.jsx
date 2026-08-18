import Plot from "react-plotly.js";

export function PlotRenderer({ chart, className = "" }) {
  if (!chart) return null;
  if (chart.type === "image") {
    return (
      <div className={`overflow-hidden rounded-lg border border-zinc-200 bg-white dark:border-neutral-800 dark:bg-neutral-900 ${className}`}>
        {chart.image_base64 ? (
          <img alt="Pair plot" className="h-full w-full object-contain" src={`data:image/png;base64,${chart.image_base64}`} />
        ) : (
          <div className="flex h-72 items-center justify-center text-sm text-zinc-500">Pair plot needs at least two numeric columns.</div>
        )}
      </div>
    );
  }

  const figure = chart.figure || chart;
  return (
    <div className={`overflow-hidden rounded-lg border border-zinc-200 bg-white dark:border-neutral-800 dark:bg-neutral-900 ${className}`}>
      <Plot
        data={figure.data || []}
        layout={{
          autosize: true,
          height: 360,
          font: { family: "Inter, system-ui, sans-serif", color: document.documentElement.classList.contains("dark") ? "#e5e5e5" : "#27272a" },
          paper_bgcolor: "rgba(0,0,0,0)",
          plot_bgcolor: "rgba(0,0,0,0)",
          ...(figure.layout || {}),
        }}
        config={{ responsive: true, displaylogo: false, toImageButtonOptions: { format: "png", filename: "datainsight-chart" } }}
        useResizeHandler
        style={{ width: "100%", height: "100%" }}
      />
    </div>
  );
}

