import React, { useState, useEffect } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useDataset } from "../context/DatasetContext";
import { datasetApi } from "../services/api";
import ChartRenderer from "../components/charts/ChartRenderer";
import CustomChartBuilder from "../components/charts/CustomChartBuilder";
import NoDatasetState from "../components/common/NoDatasetState";
import {
  TrendingUp,
  TrendingDown,
  AlertTriangle,
  SearchCode,
  Filter,
  ArrowRight,
  Sparkles,
  LayoutGrid,
  X,
  Check,
  BarChart2,
  PlusCircle,
} from "lucide-react";

/* ───────────── helpers ───────────── */
const LS_KEY = (id) => `insightx_visible_charts_${id}`;
const LS_CUSTOM_KEY = (id) => `insightx_custom_charts_${id}`;

export default function DashboardPage() {
  const { currentDataset } = useDataset();
  const [data, setData] = useState(null);
  const [selectedFilters, setSelectedFilters] = useState({});
  const [loading, setLoading] = useState(true);
  const [showChartManager, setShowChartManager] = useState(false);
  const [showChartBuilder, setShowChartBuilder] = useState(false);
  const [visibleChartIds, setVisibleChartIds] = useState(null);
  const [customCharts, setCustomCharts] = useState([]);
  const navigate = useNavigate();

  /* Load visible-chart & custom-charts preference from localStorage when dataset changes */
  useEffect(() => {
    if (currentDataset?.id) {
      const stored = localStorage.getItem(LS_KEY(currentDataset.id));
      setVisibleChartIds(stored ? new Set(JSON.parse(stored)) : null);

      const storedCustom = localStorage.getItem(LS_CUSTOM_KEY(currentDataset.id));
      setCustomCharts(storedCustom ? JSON.parse(storedCustom) : []);

      setSelectedFilters({});
      loadDashboard({});
    } else {
      setLoading(false);
    }
  }, [currentDataset]);

  const persistVisible = (ids) => {
    if (currentDataset?.id) {
      if (ids === null) {
        localStorage.removeItem(LS_KEY(currentDataset.id));
      } else {
        localStorage.setItem(LS_KEY(currentDataset.id), JSON.stringify([...ids]));
      }
    }
  };

  const persistCustomCharts = (charts) => {
    if (currentDataset?.id) {
      localStorage.setItem(LS_CUSTOM_KEY(currentDataset.id), JSON.stringify(charts));
    }
  };

  const loadDashboard = async (filtersToApply = selectedFilters) => {
    try {
      setLoading(true);
      const res = await datasetApi.getDashboard(currentDataset.id, filtersToApply);
      setData(res.data);
    } catch (err) {
      console.error("Dashboard error:", err);
    } finally {
      setLoading(false);
    }
  };

  const handleFilterChange = (col, val) => {
    const nextFilters = { ...selectedFilters };
    if (!val) {
      delete nextFilters[col];
    } else {
      nextFilters[col] = val;
    }
    setSelectedFilters(nextFilters);
    loadDashboard(nextFilters);
  };

  const handleResetFilters = () => {
    setSelectedFilters({});
    loadDashboard({});
  };

  /* Chart Manager: toggle a chart visible/hidden */
  const toggleChart = (chartId) => {
    const allIds = (data?.charts || []).map((c) => c.id);
    const current = visibleChartIds === null ? new Set(allIds) : new Set(visibleChartIds);
    if (current.has(chartId)) {
      current.delete(chartId);
    } else {
      current.add(chartId);
    }
    const next = current.size === allIds.length ? null : current;
    setVisibleChartIds(next);
    persistVisible(next);
  };

  const showAllCharts = () => {
    setVisibleChartIds(null);
    persistVisible(null);
  };

  /* Add custom chart to Dashboard */
  const handleAddCustomChart = (newChart) => {
    const updated = [...customCharts, { ...newChart, id: `custom_${Date.now()}` }];
    setCustomCharts(updated);
    persistCustomCharts(updated);
    setShowChartBuilder(false);
  };

  const handleRemoveCustomChart = (chartId) => {
    const updated = customCharts.filter((c) => c.id !== chartId);
    setCustomCharts(updated);
    persistCustomCharts(updated);
  };

  /* Derive visible charts */
  const allCharts = data?.charts || [];
  const visibleCharts =
    visibleChartIds === null
      ? allCharts
      : allCharts.filter((c) => visibleChartIds.has(c.id));

  if (loading && !data) {
    return (
      <div className="p-8 text-center text-slate-400">
        Loading dynamic executive dashboard...
      </div>
    );
  }

  if (!currentDataset?.id) {
    return <NoDatasetState title="No Active Dataset Selected" />;
  }

  const filtersApplied = Object.keys(selectedFilters).length > 0;

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-8">
      {/* Title & Actions */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-extrabold tracking-tight">
            Executive Performance Dashboard
          </h1>
          <p className="text-sm text-slate-400">
            Continuous business monitoring for {data?.dataset_name} (
            {data?.row_count?.toLocaleString()} active records).
          </p>
        </div>
        <div className="flex items-center gap-3 flex-wrap">
          {/* Create Custom Chart Button */}
          <button
            onClick={() => {
              setShowChartBuilder((v) => !v);
              setShowChartManager(false);
            }}
            className={`px-3.5 py-2 rounded-lg border text-xs font-bold transition flex items-center gap-1.5 ${
              showChartBuilder
                ? "bg-emerald-600/20 text-emerald-400 border-emerald-500/30"
                : "bg-emerald-600/10 text-emerald-400 border-emerald-500/20 hover:bg-emerald-600/20"
            }`}
          >
            <BarChart2 className="w-3.5 h-3.5" />
            + New Chart
          </button>

          {/* Chart Manager Button */}
          <button
            onClick={() => {
              setShowChartManager((v) => !v);
              setShowChartBuilder(false);
            }}
            className="px-3.5 py-2 rounded-lg bg-violet-600/15 text-violet-400 border border-violet-500/30 text-xs font-bold hover:bg-violet-600/25 transition flex items-center gap-2"
          >
            <LayoutGrid className="w-3.5 h-3.5" />
            Manage Charts
            {visibleChartIds !== null && (
              <span className="ml-1 bg-violet-500/30 text-violet-300 rounded px-1.5 py-0.5 text-[10px] font-bold">
                {visibleCharts.length}/{allCharts.length}
              </span>
            )}
          </button>

          <Link
            to="/ai-analyst"
            className="px-3.5 py-2 rounded-lg bg-indigo-600/15 text-indigo-400 border border-indigo-500/30 text-xs font-bold hover:bg-indigo-600/25 transition flex items-center gap-2"
          >
            <Sparkles className="w-3.5 h-3.5" /> Ask AI Analyst
          </Link>
          <Link
            to="/root-cause"
            className="px-3.5 py-2 rounded-lg bg-slate-800 text-slate-200 border border-slate-700 text-xs font-semibold hover:bg-slate-700 transition flex items-center gap-2"
          >
            <SearchCode className="w-3.5 h-3.5" /> Root Cause Studio
          </Link>
        </div>
      </div>

      {/* ───── Custom Chart Builder Panel ───── */}
      {showChartBuilder && (
        <div className="rounded-2xl border border-emerald-500/30 bg-slate-900/95 p-6 shadow-2xl">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="text-sm font-bold text-emerald-300 flex items-center gap-2">
                <BarChart2 className="w-4 h-4" /> Create New Custom Chart
              </h3>
              <p className="text-xs text-slate-400 mt-0.5">
                Pick columns from your dataset. Choose "None" aggregation to plot raw values directly without sum or average.
              </p>
            </div>
            <button
              onClick={() => setShowChartBuilder(false)}
              className="p-1.5 rounded-lg hover:bg-slate-800 text-slate-400"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
          <CustomChartBuilder
            datasetId={currentDataset.id}
            onAddToDashboard={handleAddCustomChart}
          />
        </div>
      )}

      {/* ───── Chart Manager Panel ───── */}
      {showChartManager && (
        <div className="rounded-2xl border border-violet-500/25 bg-slate-900/90 p-5 shadow-xl">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="text-sm font-bold text-violet-300 flex items-center gap-2">
                <LayoutGrid className="w-4 h-4" /> Chart Catalog
              </h3>
              <p className="text-xs text-slate-500 mt-0.5">
                Toggle charts on/off. Preferences are saved per dataset.
              </p>
            </div>
            <div className="flex items-center gap-2">
              {visibleChartIds !== null && (
                <button
                  onClick={showAllCharts}
                  className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-semibold border border-slate-700 transition"
                >
                  Show All
                </button>
              )}
              <button
                onClick={() => setShowChartManager(false)}
                className="p-1.5 rounded-lg hover:bg-slate-800 text-slate-400 transition"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
            {allCharts.map((chart) => {
              const isVisible =
                visibleChartIds === null || visibleChartIds.has(chart.id);
              return (
                <div
                  key={chart.id}
                  className={`flex items-center justify-between p-3 rounded-xl border transition cursor-pointer select-none ${
                    isVisible
                      ? "border-violet-500/40 bg-violet-500/10 hover:bg-violet-500/15"
                      : "border-slate-700 bg-slate-800/50 hover:bg-slate-800"
                  }`}
                  onClick={() => toggleChart(chart.id)}
                >
                  <div className="flex items-center gap-2.5 flex-1 min-w-0">
                    <div
                      className={`w-5 h-5 rounded flex items-center justify-center flex-shrink-0 border transition ${
                        isVisible
                          ? "bg-violet-500 border-violet-500"
                          : "border-slate-600 bg-transparent"
                      }`}
                    >
                      {isVisible && <Check className="w-3 h-3 text-white" />}
                    </div>
                    <div className="min-w-0">
                      <p className="text-xs font-semibold text-slate-200 truncate">
                        {chart.title}
                      </p>
                      <p className="text-[10px] text-slate-500 truncate capitalize">
                        {chart.chart_type} chart
                      </p>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Operational Alerts Banner */}
      {data?.alerts && data.alerts.length > 0 && (
        <div className="space-y-2">
          {data.alerts.map((alert, i) => (
            <div
              key={i}
              className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/20 flex items-center justify-between gap-4"
            >
              <div className="flex items-center gap-3">
                <AlertTriangle className="w-5 h-5 text-rose-400 flex-shrink-0" />
                <div>
                  <h4 className="text-xs font-bold text-rose-300">{alert.title}</h4>
                  <p className="text-xs text-slate-400">{alert.message}</p>
                </div>
              </div>
              <button
                onClick={() => navigate("/root-cause")}
                className="px-3.5 py-1.5 rounded-lg bg-rose-500/20 hover:bg-rose-500/30 text-rose-300 text-xs font-bold border border-rose-500/30 flex-shrink-0 transition flex items-center gap-1.5"
              >
                Investigate <ArrowRight className="w-3.5 h-3.5" />
              </button>
            </div>
          ))}
        </div>
      )}

      {/* Top Dynamic KPI Ribbon */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
        {data?.kpis?.map((kpi, i) => (
          <div
            key={i}
            className="p-5 rounded-2xl bg-slate-900 border border-slate-800 flex flex-col justify-between"
          >
            <span className="text-xs font-semibold text-slate-400">{kpi.title}</span>
            <div className="my-3">
              <div className="text-3xl font-extrabold text-slate-100">{kpi.value}</div>
            </div>
            <div className="flex items-center justify-between text-xs">
              {kpi.delta_percent !== null && (
                <div
                  className={`flex items-center gap-1 font-bold ${
                    kpi.is_positive ? "text-emerald-400" : "text-rose-400"
                  }`}
                >
                  {kpi.is_positive ? (
                    <TrendingUp className="w-3.5 h-3.5" />
                  ) : (
                    <TrendingDown className="w-3.5 h-3.5" />
                  )}
                  <span>
                    {kpi.delta_percent > 0
                      ? `+${kpi.delta_percent}%`
                      : `${kpi.delta_percent}%`}
                  </span>
                  <span className="text-slate-500 font-normal ml-1">vs prev</span>
                </div>
              )}
            </div>
          </div>
        ))}
      </div>

      {/* Dynamic Interactive Filter Strip */}
      {data?.filters && Object.keys(data.filters).length > 0 && (
        <div className="p-4 rounded-xl bg-slate-900 border border-slate-800 flex items-center gap-4 flex-wrap text-xs shadow-md overflow-x-auto">
          <div className="flex items-center gap-1.5 text-indigo-400 font-bold flex-shrink-0">
            <Filter className="w-3.5 h-3.5" /> Interactive Filters:
          </div>

          {Object.entries(data.filters).map(([col, values]) => (
            <div key={col} className="flex items-center gap-1.5 flex-shrink-0">
              <span className="text-slate-400 uppercase font-bold text-[10px]">
                {col.replace(/_/g, " ")}:
              </span>
              <select
                value={selectedFilters[col] || ""}
                onChange={(e) => handleFilterChange(col, e.target.value)}
                className="bg-slate-800 border border-slate-700 text-slate-200 font-medium rounded px-2.5 py-1 outline-none cursor-pointer hover:border-indigo-500 transition"
              >
                <option value="">All ({values.length})</option>
                {values.map((v) => (
                  <option key={v} value={v}>
                    {v}
                  </option>
                ))}
              </select>
            </div>
          ))}

          {/* Reset Filters */}
          {filtersApplied && (
            <button
              onClick={handleResetFilters}
              className="px-3 py-1 rounded bg-rose-500/10 hover:bg-rose-500/20 text-rose-400 font-semibold border border-rose-500/30 text-[11px] flex-shrink-0 transition flex items-center gap-1"
            >
              <X className="w-3 h-3" /> Reset Filters
            </button>
          )}
        </div>
      )}

      {/* ───── User's Custom Charts Section ───── */}
      {customCharts.length > 0 && (
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <h3 className="text-xs font-bold text-slate-300 uppercase tracking-wider flex items-center gap-1.5">
              <PlusCircle className="w-4 h-4 text-emerald-400" /> Custom Dashboard Charts ({customCharts.length})
            </h3>
            <button
              onClick={() => setShowChartBuilder(true)}
              className="text-xs font-semibold text-emerald-400 hover:underline"
            >
              + Create Another Chart
            </button>
          </div>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {customCharts.map((spec) => (
              <div
                key={spec.id}
                className="p-6 rounded-2xl bg-slate-900 border border-emerald-500/20 relative group shadow-lg"
              >
                <button
                  onClick={() => handleRemoveCustomChart(spec.id)}
                  title="Remove this custom chart"
                  className="absolute top-3 right-3 opacity-0 group-hover:opacity-100 transition p-1 rounded-md bg-slate-800 hover:bg-rose-500/20 text-slate-500 hover:text-rose-400 border border-slate-700 hover:border-rose-500/30"
                >
                  <X className="w-3.5 h-3.5" />
                </button>
                <div className="mb-4">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                      CUSTOM
                    </span>
                    <h3 className="text-sm font-bold text-slate-200">{spec.title}</h3>
                  </div>
                  <p className="text-xs text-slate-400">{spec.description}</p>
                </div>
                <ChartRenderer spec={spec} />
              </div>
            ))}
          </div>
        </div>
      )}

      {/* ───── Automatic Chart Grid ───── */}
      {visibleCharts.length === 0 && allCharts.length > 0 ? (
        <div className="text-center py-16 text-slate-500 border border-dashed border-slate-700 rounded-2xl">
          <LayoutGrid className="w-10 h-10 mx-auto mb-3 opacity-40" />
          <p className="font-semibold">All automatic charts are hidden.</p>
          <button
            onClick={showAllCharts}
            className="mt-3 text-violet-400 text-sm font-semibold hover:underline"
          >
            Show all charts
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {visibleCharts.map((spec) => (
            <div
              key={spec.id}
              className="p-6 rounded-2xl bg-slate-900 border border-slate-800 relative group"
            >
              <button
                onClick={() => toggleChart(spec.id)}
                title="Hide this chart"
                className="absolute top-3 right-3 opacity-0 group-hover:opacity-100 transition p-1 rounded-md bg-slate-800 hover:bg-rose-500/20 text-slate-500 hover:text-rose-400 border border-slate-700 hover:border-rose-500/30"
              >
                <X className="w-3.5 h-3.5" />
              </button>
              <div className="mb-4">
                <h3 className="text-sm font-bold text-slate-200">{spec.title}</h3>
                <p className="text-xs text-slate-400">{spec.description}</p>
              </div>
              <ChartRenderer spec={spec} />
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
