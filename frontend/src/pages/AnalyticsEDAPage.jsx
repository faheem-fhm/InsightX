import React, { useState, useEffect } from "react";
import { useDataset } from "../context/DatasetContext";
import { datasetApi } from "../services/api";
import NoDatasetState from "../components/common/NoDatasetState";
import { BarChart3, Binary, Table } from "lucide-react";

export default function AnalyticsEDAPage() {
  const { currentDataset } = useDataset();
  const [eda, setEda] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (currentDataset?.id) {
      loadEda();
    } else {
      setLoading(false);
    }
  }, [currentDataset]);

  const loadEda = async () => {
    try {
      setLoading(true);
      const res = await datasetApi.getAnalytics(currentDataset.id);
      setEda(res.data);
    } catch (err) {
      console.error("EDA error:", err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <div className="p-8 text-center text-slate-400">Computing exploratory analytics & correlation matrices...</div>;

  if (!currentDataset?.id) {
    return <NoDatasetState title="No Active Dataset Selected" />;
  }

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-8">
      <div>
        <h1 className="text-2xl font-extrabold tracking-tight">Exploratory Data Analysis (EDA)</h1>
        <p className="text-sm text-slate-400">Statistical distributions, quartiles, and Pearson correlation coefficients.</p>
      </div>

      {/* Summary Statistics Table */}
      <div className="p-6 rounded-2xl bg-slate-900 border border-slate-800 space-y-4">
        <h3 className="text-sm font-bold text-slate-200 flex items-center gap-2">
          <Table className="w-4 h-4 text-indigo-400" /> Numerical Feature Summary Statistics
        </h3>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs text-slate-300">
            <thead className="bg-slate-950 text-slate-400 font-semibold border-b border-slate-800">
              <tr>
                <th className="p-3">Feature</th>
                <th className="p-3">Mean</th>
                <th className="p-3">Std Dev</th>
                <th className="p-3">Median</th>
                <th className="p-3">Min</th>
                <th className="p-3">Max</th>
                <th className="p-3">Q25</th>
                <th className="p-3">Q75</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 font-mono">
              {Object.entries(eda?.summary_statistics || {}).map(([col, s]) => (
                <tr key={col} className="hover:bg-slate-800/30 transition">
                  <td className="p-3 font-sans font-semibold text-slate-200">{col}</td>
                  <td className="p-3">{s.mean}</td>
                  <td className="p-3 text-slate-400">{s.std}</td>
                  <td className="p-3 text-indigo-400 font-bold">{s.median}</td>
                  <td className="p-3">{s.min}</td>
                  <td className="p-3">{s.max}</td>
                  <td className="p-3 text-slate-400">{s.q25}</td>
                  <td className="p-3 text-slate-400">{s.q75}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Correlation Matrix Heatmap List */}
      <div className="p-6 rounded-2xl bg-slate-900 border border-slate-800 space-y-4">
        <h3 className="text-sm font-bold text-slate-200 flex items-center gap-2">
          <Binary className="w-4 h-4 text-purple-400" /> Linear Correlation Matrix (Pearson r)
        </h3>
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-3">
          {eda?.correlations?.filter(c => c.x !== c.y).slice(0, 16).map((c, i) => (
            <div key={i} className="p-3 rounded-xl bg-slate-950 border border-slate-800 flex items-center justify-between text-xs">
              <span className="text-slate-400 font-medium truncate mr-2">{c.x} × {c.y}</span>
              <span className={`font-mono font-bold px-2 py-0.5 rounded ${
                c.correlation > 0.4 ? "bg-emerald-500/20 text-emerald-400" :
                c.correlation < -0.4 ? "bg-rose-500/20 text-rose-400" : "bg-slate-800 text-slate-300"
              }`}>
                {c.correlation > 0 ? `+${c.correlation}` : c.correlation}
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
