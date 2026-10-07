import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useDataset } from "../context/DatasetContext";
import { datasetApi } from "../services/api";
import NoDatasetState from "../components/common/NoDatasetState";
import { AlertTriangle, ShieldAlert, ArrowRight, Sparkles } from "lucide-react";

export default function AnomalyPage() {
  const { currentDataset } = useDataset();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    if (currentDataset?.id) {
      loadAnomalies();
    } else {
      setLoading(false);
    }
  }, [currentDataset]);

  const loadAnomalies = async () => {
    try {
      setLoading(true);
      const res = await datasetApi.getAnomalies(currentDataset.id, {});
      setData(res.data);
    } catch (err) {
      console.error("Anomaly error:", err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <div className="p-8 text-center text-slate-400">Executing Isolation Forest anomaly radar...</div>;

  if (!currentDataset?.id) {
    return <NoDatasetState title="No Active Dataset Selected" />;
  }

  return (
    <div className="p-8 max-w-6xl mx-auto space-y-8">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-extrabold tracking-tight">Temporal Anomaly Radar</h1>
          <p className="text-sm text-slate-400">Trained Isolation Forest & Rolling 3-Sigma thresholding on {data?.metric}.</p>
        </div>
        <div className="px-3 py-1.5 rounded-lg bg-slate-900 border border-slate-800 text-xs text-slate-300 font-semibold">
          Found {data?.total_detected} anomalies
        </div>
      </div>

      <div className="space-y-3">
        {data?.anomalies?.map((anom, i) => (
          <div key={i} className="p-5 rounded-2xl bg-slate-900 border border-slate-800 flex flex-col sm:flex-row sm:items-center justify-between gap-4 hover:border-slate-700 transition">
            <div className="space-y-1">
              <div className="flex items-center gap-2">
                <span className="font-mono text-sm font-bold text-slate-200">{anom.date}</span>
                <span className={`text-[10px] font-extrabold px-2 py-0.5 rounded-full ${
                  anom.severity === "Critical" ? "bg-rose-500/15 text-rose-400 border border-rose-500/30" :
                  anom.severity === "Medium" ? "bg-amber-500/15 text-amber-400 border border-amber-500/30" :
                  "bg-slate-800 text-slate-300"
                }`}>
                  {anom.severity} {anom.direction}
                </span>
                <span className="text-xs text-slate-400 font-mono">
                  Actual: <b className="text-slate-200">{Number(anom.actual_value).toLocaleString(undefined, { maximumFractionDigits: 2 })}</b> vs Expected: {Number(anom.expected_value).toLocaleString(undefined, { maximumFractionDigits: 2 })}
                </span>
              </div>
              <p className="text-xs text-slate-400">{anom.explanation}</p>
            </div>

            <button
              onClick={() => navigate("/root-cause")}
              className="px-4 py-2 rounded-lg bg-indigo-600/15 hover:bg-indigo-600/25 text-indigo-400 border border-indigo-500/30 text-xs font-bold flex items-center gap-1.5 self-start sm:self-auto transition"
            >
              Investigate <ArrowRight className="w-3.5 h-3.5" />
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}
