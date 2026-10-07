import React from "react";
import { useNavigate, Link } from "react-router-dom";
import { useDataset } from "../../context/DatasetContext";
import { Database, UploadCloud, Play, Sparkles, AlertTriangle } from "lucide-react";

export default function NoDatasetState({ title = "No Active Dataset Selected" }) {
  const { loadSampleDataset, loading, backendError } = useDataset();
  const navigate = useNavigate();

  const handleLoadDemo = async (key) => {
    try {
      await loadSampleDataset(key);
      navigate("/dashboard");
    } catch (err) {
      console.error("Failed to load demo:", err);
    }
  };

  return (
    <div className="p-8 max-w-4xl mx-auto my-12 text-center space-y-6">
      {backendError && (
        <div className="p-4 rounded-2xl bg-rose-500/10 border border-rose-500/30 text-rose-300 text-xs text-left flex items-start gap-3 shadow-xl">
          <AlertTriangle className="w-5 h-5 text-rose-400 flex-shrink-0 mt-0.5" />
          <div className="space-y-1">
            <h4 className="font-bold text-sm text-rose-200">Backend API Server Offline (ECONNREFUSED 127.0.0.1:8000)</h4>
            <p className="text-slate-300">
              The Python FastAPI server is currently stopped. To start both the backend API and frontend UI together, open your terminal and run:
            </p>
            <code className="block p-2 rounded bg-slate-950 text-indigo-300 font-mono text-xs">
              python start_platform.py &nbsp;&nbsp;(or double-click start.bat)
            </code>
          </div>
        </div>
      )}

      <div className="w-16 h-16 rounded-2xl bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center mx-auto text-indigo-400">
        <Database className="w-8 h-8" />
      </div>

      <div className="space-y-2">
        <h2 className="text-2xl font-extrabold tracking-tight text-slate-100">{title}</h2>
        <p className="text-sm text-slate-400 max-w-lg mx-auto">
          To view analytics, forecasts, anomalies, or root causes, please select a dataset from the top header, choose a demo dataset below, or upload a file.
        </p>
      </div>

      {/* Demo Loaders */}
      <div className="pt-4 grid grid-cols-1 sm:grid-cols-3 gap-4 max-w-2xl mx-auto">
        <button
          onClick={() => handleLoadDemo("ecommerce")}
          disabled={loading}
          className="p-4 rounded-xl bg-slate-900 border border-slate-800 hover:border-indigo-500/50 text-left transition group"
        >
          <div className="flex items-center justify-between mb-2">
            <span className="text-[10px] font-extrabold px-2 py-0.5 rounded bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
              E-COMMERCE
            </span>
            <Play className="w-3.5 h-3.5 text-indigo-400 fill-indigo-400 group-hover:scale-110 transition" />
          </div>
          <h4 className="font-bold text-xs text-slate-200">Logistics & Sales</h4>
          <p className="text-[11px] text-slate-500 mt-1">4,582 orders with South delivery bottleneck.</p>
        </button>

        <button
          onClick={() => handleLoadDemo("saas")}
          disabled={loading}
          className="p-4 rounded-xl bg-slate-900 border border-slate-800 hover:border-purple-500/50 text-left transition group"
        >
          <div className="flex items-center justify-between mb-2">
            <span className="text-[10px] font-extrabold px-2 py-0.5 rounded bg-purple-500/10 text-purple-400 border border-purple-500/20">
              SAAS FUNNEL
            </span>
            <Play className="w-3.5 h-3.5 text-purple-400 fill-purple-400 group-hover:scale-110 transition" />
          </div>
          <h4 className="font-bold text-xs text-slate-200">Growth Funnel</h4>
          <p className="text-[11px] text-slate-500 mt-1">600 days spend, leads & ROI.</p>
        </button>

        <button
          onClick={() => handleLoadDemo("healthcare")}
          disabled={loading}
          className="p-4 rounded-xl bg-slate-900 border border-slate-800 hover:border-emerald-500/50 text-left transition group"
        >
          <div className="flex items-center justify-between mb-2">
            <span className="text-[10px] font-extrabold px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
              HEALTHCARE
            </span>
            <Play className="w-3.5 h-3.5 text-emerald-400 fill-emerald-400 group-hover:scale-110 transition" />
          </div>
          <h4 className="font-bold text-xs text-slate-200">Patient Flow</h4>
          <p className="text-[11px] text-slate-500 mt-1">2,428 admissions & triage.</p>
        </button>
      </div>

      <div className="pt-4">
        <Link
          to="/upload"
          className="inline-flex items-center gap-2 px-5 py-2.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white font-semibold text-xs transition shadow-lg shadow-indigo-600/20"
        >
          <UploadCloud className="w-4 h-4" /> Upload Custom Dataset
        </Link>
      </div>
    </div>
  );
}
