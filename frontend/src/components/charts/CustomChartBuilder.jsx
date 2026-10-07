import React, { useState, useEffect } from "react";
import { datasetApi } from "../../services/api";
import ChartRenderer from "./ChartRenderer";
import { BarChart2, LineChart, PieChart, ScatterChart, Plus, Loader, X, PlusCircle } from "lucide-react";

const CHART_TYPES = [
  { value: "bar",     label: "Bar Chart",     icon: BarChart2 },
  { value: "line",    label: "Line Chart",    icon: LineChart },
  { value: "donut",   label: "Donut Chart",   icon: PieChart },
  { value: "scatter", label: "Scatter Plot",  icon: ScatterChart },
  { value: "area",    label: "Area Chart",    icon: LineChart },
];

const AGGREGATIONS = [
  { value: "none",  label: "None (Raw Values)" },
  { value: "sum",   label: "Sum (Total)" },
  { value: "avg",   label: "Average" },
  { value: "count", label: "Count (Records)" },
  { value: "max",   label: "Maximum" },
  { value: "min",   label: "Minimum" },
];

export default function CustomChartBuilder({ datasetId, onAddToDashboard }) {
  const [columns, setColumns] = useState([]);
  const [xCol, setXCol] = useState("");
  const [yCol, setYCol] = useState("");
  const [chartType, setChartType] = useState("bar");
  const [aggregation, setAggregation] = useState("none");
  const [preview, setPreview] = useState(null);
  const [building, setBuilding] = useState(false);
  const [error, setError] = useState("");
  const [loadingCols, setLoadingCols] = useState(true);

  useEffect(() => {
    if (!datasetId) return;
    setLoadingCols(true);
    setError("");
    datasetApi.getColumns(datasetId)
      .then((res) => {
        const cols = res.data.columns || [];
        setColumns(cols);
        const cats = cols.filter((c) => c.is_categorical || c.is_date);
        const nums = cols.filter((c) => c.is_numeric);
        if (cats.length) setXCol(cats[0].name);
        else if (cols.length) setXCol(cols[0].name);
        if (nums.length) setYCol(nums[0].name);
        else if (cols.length > 1) setYCol(cols[1].name);
      })
      .catch((err) => {
        console.error("Column fetch error:", err);
        setError("Failed to load dataset columns. Make sure the dataset is active.");
      })
      .finally(() => setLoadingCols(false));
  }, [datasetId]);

  const numericCols = columns.filter((c) => c.is_numeric);

  const handlePreview = async () => {
    if (!xCol) return;
    setBuilding(true);
    setError("");
    setPreview(null);
    try {
      const res = await datasetApi.buildCustomChart(datasetId, {
        x_col: xCol,
        y_col: yCol || undefined,
        chart_type: chartType,
        aggregation: aggregation || "none",
      });
      setPreview(res.data);
    } catch (err) {
      setError(err.response?.data?.detail || "Chart generation failed.");
    } finally {
      setBuilding(false);
    }
  };

  const handleAddToDashboard = () => {
    if (preview && onAddToDashboard) {
      onAddToDashboard(preview);
      setPreview(null);
    }
  };

  if (loadingCols) {
    return (
      <div className="flex items-center gap-2 text-slate-500 text-xs py-4">
        <Loader className="w-4 h-4 animate-spin" /> Loading columns from active dataset...
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Column + Options Selectors */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
        {/* X Axis (Group By) */}
        <div>
          <label className="text-[10px] font-bold text-slate-400 uppercase block mb-1">
            Group / Dimension (X Axis)
          </label>
          <select
            value={xCol}
            onChange={(e) => setXCol(e.target.value)}
            className="w-full bg-slate-800 border border-slate-700 text-slate-200 text-xs rounded-lg px-2.5 py-2 outline-none hover:border-indigo-500 focus:border-indigo-500 transition cursor-pointer"
          >
            <option value="">-- Select Column --</option>
            {columns.map((c) => (
              <option key={c.name} value={c.name}>
                {c.name.replace(/_/g, " ")} ({c.type})
              </option>
            ))}
          </select>
        </div>

        {/* Y Axis (Metric / Values) */}
        <div>
          <label className="text-[10px] font-bold text-slate-400 uppercase block mb-1">
            Metric Column (Y Axis)
          </label>
          <select
            value={yCol}
            onChange={(e) => setYCol(e.target.value)}
            className="w-full bg-slate-800 border border-slate-700 text-slate-200 text-xs rounded-lg px-2.5 py-2 outline-none hover:border-indigo-500 focus:border-indigo-500 transition cursor-pointer"
          >
            <option value="">-- Optional (or select metric) --</option>
            {columns.map((c) => (
              <option key={c.name} value={c.name}>
                {c.name.replace(/_/g, " ")} ({c.type})
              </option>
            ))}
          </select>
        </div>

        {/* Aggregation */}
        <div>
          <label className="text-[10px] font-bold text-slate-400 uppercase block mb-1">
            Aggregation
          </label>
          <select
            value={aggregation}
            onChange={(e) => setAggregation(e.target.value)}
            className="w-full bg-slate-800 border border-slate-700 text-slate-200 text-xs rounded-lg px-2.5 py-2 outline-none hover:border-indigo-500 focus:border-indigo-500 transition cursor-pointer"
          >
            {AGGREGATIONS.map((a) => (
              <option key={a.value} value={a.value}>{a.label}</option>
            ))}
          </select>
        </div>

        {/* Chart Type */}
        <div>
          <label className="text-[10px] font-bold text-slate-400 uppercase block mb-1">
            Chart Type
          </label>
          <select
            value={chartType}
            onChange={(e) => setChartType(e.target.value)}
            className="w-full bg-slate-800 border border-slate-700 text-slate-200 text-xs rounded-lg px-2.5 py-2 outline-none hover:border-indigo-500 focus:border-indigo-500 transition cursor-pointer"
          >
            {CHART_TYPES.map((t) => (
              <option key={t.value} value={t.value}>{t.label}</option>
            ))}
          </select>
        </div>
      </div>

      {/* All Columns Badges */}
      {columns.length > 0 && (
        <div className="space-y-1.5">
          <span className="text-[10px] font-bold text-slate-400 uppercase block">
            Click column to select:
          </span>
          <div className="flex flex-wrap gap-1.5 max-h-36 overflow-y-auto pr-1">
            {columns.map((c) => {
              const isSelected = xCol === c.name || yCol === c.name;
              return (
                <span
                  key={c.name}
                  onClick={() => {
                    if (c.is_numeric) {
                      setYCol(c.name);
                    } else {
                      setXCol(c.name);
                    }
                  }}
                  title={`Click to select ${c.name} as ${c.is_numeric ? "Y Metric" : "X Axis"}`}
                  className={`px-2.5 py-1 rounded-md text-[11px] font-medium cursor-pointer transition border select-none ${
                    isSelected
                      ? "ring-2 ring-indigo-500 bg-indigo-500/20 text-indigo-200 border-indigo-500"
                      : c.is_numeric
                      ? "bg-emerald-500/10 border-emerald-500/30 text-emerald-400 hover:bg-emerald-500/20"
                      : c.is_date
                      ? "bg-blue-500/10 border-blue-500/30 text-blue-400 hover:bg-blue-500/20"
                      : "bg-violet-500/10 border-violet-500/30 text-violet-400 hover:bg-violet-500/20"
                  }`}
                >
                  {c.name.replace(/_/g, " ")}
                  <span className="ml-1 opacity-75">
                    {c.is_numeric ? "📊" : c.is_date ? "📅" : "🏷"}
                  </span>
                </span>
              );
            })}
          </div>
          <p className="text-[10px] text-slate-500">
            📊 numeric metric · 📅 date timeline · 🏷 category group
          </p>
        </div>
      )}

      {/* Error display */}
      {error && (
        <div className="text-xs text-rose-400 bg-rose-500/10 border border-rose-500/20 rounded-lg px-3 py-2">
          {error}
        </div>
      )}

      {/* Action Buttons */}
      <div className="flex items-center gap-3 pt-1">
        <button
          onClick={handlePreview}
          disabled={!xCol || building}
          className="px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-bold transition disabled:opacity-50 flex items-center gap-1.5"
        >
          {building ? (
            <><Loader className="w-3.5 h-3.5 animate-spin" /> Generating...</>
          ) : (
            <><Plus className="w-3.5 h-3.5" /> Preview Chart</>
          )}
        </button>
        {preview && onAddToDashboard && (
          <button
            onClick={handleAddToDashboard}
            className="px-4 py-2 rounded-lg bg-emerald-600/20 hover:bg-emerald-600/30 text-emerald-400 border border-emerald-500/30 text-xs font-bold transition flex items-center gap-1.5"
          >
            <PlusCircle className="w-3.5 h-3.5" /> Add to Dashboard
          </button>
        )}
        {preview && (
          <button
            onClick={() => setPreview(null)}
            className="p-2 rounded-lg hover:bg-slate-800 text-slate-500 transition"
          >
            <X className="w-3.5 h-3.5" />
          </button>
        )}
      </div>

      {/* Chart Preview Render */}
      {preview && (
        <div className="p-5 rounded-2xl bg-slate-950 border border-indigo-500/30">
          <div className="mb-3">
            <h4 className="text-sm font-bold text-slate-200">{preview.title}</h4>
            <p className="text-xs text-slate-400">{preview.description}</p>
          </div>
          <ChartRenderer spec={preview} />
          {preview.sql_query && (
            <pre className="mt-3 text-[10px] font-mono text-emerald-400/80 bg-slate-900 rounded p-2 overflow-x-auto">
              {preview.sql_query}
            </pre>
          )}
        </div>
      )}
    </div>
  );
}
