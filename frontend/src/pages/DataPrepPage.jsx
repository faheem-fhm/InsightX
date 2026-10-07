import React, { useState, useEffect } from "react";
import { useDataset } from "../context/DatasetContext";
import { datasetApi } from "../services/api";
import NoDatasetState from "../components/common/NoDatasetState";
import { 
  Sparkles, 
  CheckCircle2, 
  AlertTriangle, 
  Layers, 
  ShieldCheck, 
  Check, 
  ArrowRight,
  Database
} from "lucide-react";
import { Link } from "react-router-dom";

const LS_APPLIED_KEY = (id) => `insightx_prep_applied_${id}`;

export default function DataPrepPage() {
  const { currentDataset, updateDatasetQuality, fetchDatasets } = useDataset();
  const [quality, setQuality] = useState(null);
  const [profile, setProfile] = useState(null);
  const [loading, setLoading] = useState(true);
  const [applied, setApplied] = useState(false);

  const dsId = currentDataset?.id || currentDataset?.dataset_id;

  useEffect(() => {
    if (dsId) {
      const isLocallyApplied = localStorage.getItem(LS_APPLIED_KEY(dsId)) === "true";
      if (isLocallyApplied) {
        setApplied(true);
      }
      loadData();
    } else {
      setLoading(false);
    }
  }, [dsId]);

  const loadData = async () => {
    if (!dsId) return;
    try {
      setLoading(true);
      const [qRes, pRes] = await Promise.all([
        datasetApi.getQuality(dsId),
        datasetApi.getProfile(dsId)
      ]);
      setQuality(qRes.data);
      setProfile(pRes.data);

      const isLocallyApplied = localStorage.getItem(LS_APPLIED_KEY(dsId)) === "true";
      const hasAppliedActions = Boolean(
        qRes.data?.applied_actions && Object.keys(qRes.data.applied_actions).length > 0
      );
      if (isLocallyApplied || hasAppliedActions) {
        setApplied(true);
        localStorage.setItem(LS_APPLIED_KEY(dsId), "true");
      } else {
        setApplied(false);
      }

      if (qRes.data?.quality_score && updateDatasetQuality) {
        updateDatasetQuality(dsId, qRes.data.quality_score);
      }
    } catch (err) {
      console.error("Failed to load quality profile:", err);
    } finally {
      setLoading(false);
    }
  };

  const handleApplyRecommended = async () => {
    if (!dsId || applied) return;
    try {
      const res = await datasetApi.preprocess(dsId, {
        remove_duplicates: true,
        impute_missing: true,
        flag_outliers: true
      });
      setApplied(true);
      localStorage.setItem(LS_APPLIED_KEY(dsId), "true");
      if (res.data?.quality_score && updateDatasetQuality) {
        updateDatasetQuality(dsId, res.data.quality_score);
      }
      await loadData();
      if (fetchDatasets) await fetchDatasets();
    } catch (err) {
      console.error("Preprocessing failed:", err);
    }
  };

  if (loading) {
    return <div className="p-8 text-center text-slate-400">Loading dataset quality report...</div>;
  }

  if (!currentDataset?.id) {
    return <NoDatasetState title="No Active Dataset Selected" />;
  }

  return (
    <div className="p-8 max-w-6xl mx-auto space-y-8">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-extrabold tracking-tight">Data Quality & Preprocessing Workbench</h1>
          <p className="text-sm text-slate-400">Auditing {profile?.total_rows?.toLocaleString()} rows across {profile?.total_columns} columns in {currentDataset?.name}.</p>
        </div>
        <Link
          to="/dashboard"
          className="px-5 py-2.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-sm font-semibold flex items-center gap-2 self-start transition"
        >
          Go to Dashboard <ArrowRight className="w-4 h-4" />
        </Link>
      </div>

      {/* Quality Score Hero Card */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="p-6 rounded-2xl bg-slate-900 border border-slate-800 flex flex-col items-center justify-center text-center">
          <span className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-2">QUALITY SCORE</span>
          <div className="text-5xl font-black text-emerald-400 mb-2">
            {quality?.quality_score} <span className="text-xl text-slate-500 font-medium">/ 100</span>
          </div>
          <p className="text-xs text-slate-400">Production ready grade</p>
        </div>

        <div className="p-5 rounded-2xl bg-slate-900 border border-slate-800 space-y-2">
          <span className="text-xs font-bold text-slate-400">MISSING VALUES</span>
          <div className="text-2xl font-bold text-slate-200">
            {quality?.missing_cells_count} <span className="text-xs text-slate-400">({quality?.missing_cells_percentage}%)</span>
          </div>
          <p className="text-xs text-slate-400">Handled with skew-aware median/mode imputation</p>
        </div>

        <div className="p-5 rounded-2xl bg-slate-900 border border-slate-800 space-y-2">
          <span className="text-xs font-bold text-slate-400">DUPLICATE ROWS</span>
          <div className="text-2xl font-bold text-slate-200">{quality?.duplicate_rows_count}</div>
          <p className="text-xs text-slate-400">Identified and removed in clean Parquet cache</p>
        </div>

        <div className="p-5 rounded-2xl bg-slate-900 border border-slate-800 space-y-2">
          <span className="text-xs font-bold text-slate-400">OUTLIERS FLAGGED</span>
          <div className="text-2xl font-bold text-amber-400">{quality?.potential_outliers_count}</div>
          <p className="text-xs text-slate-400">Flagged via 3x IQR without destructive row drops</p>
        </div>
      </div>

      {/* Recommended Preprocessing Actions Checklist */}
      <div className="p-6 rounded-2xl bg-slate-900 border border-slate-800 space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Sparkles className="w-5 h-5 text-indigo-400" />
            <h3 className="font-bold text-base text-slate-200">Automated Remediation Actions</h3>
          </div>
          <button
            onClick={handleApplyRecommended}
            disabled={applied}
            className={`px-4 py-2 rounded-lg text-xs font-bold transition flex items-center gap-2 ${
              applied
                ? "bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 cursor-default"
                : "bg-indigo-600 hover:bg-indigo-500 text-white shadow-lg shadow-indigo-600/20 cursor-pointer"
            }`}
          >
            {applied ? <Check className="w-4 h-4" /> : null}
            {applied ? "Actions Applied" : "Apply Recommended Changes"}
          </button>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {quality?.recommended_actions?.map((act, i) => (
            <div key={i} className="p-3.5 rounded-xl bg-slate-950 border border-slate-800 flex items-start gap-3">
              <CheckCircle2 className="w-4 h-4 text-emerald-400 mt-0.5 flex-shrink-0" />
              <div>
                <div className="flex items-center gap-2">
                  <span className="text-sm font-semibold text-slate-200">{act.title}</span>
                  <span className={`text-[10px] font-bold px-1.5 py-0.5 rounded ${act.impact === "High" ? "bg-rose-500/10 text-rose-400 border border-rose-500/20" : "bg-indigo-500/10 text-indigo-400 border border-indigo-500/20"}`}>
                    {act.impact}
                  </span>
                </div>
                <p className="text-xs text-slate-400 mt-1">{act.description}</p>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Column Schema Inferred Types Table */}
      <div className="p-6 rounded-2xl bg-slate-900 border border-slate-800 space-y-4">
        <div className="flex items-center gap-2">
          <Layers className="w-5 h-5 text-indigo-400" />
          <h3 className="font-bold text-base text-slate-200">Inferred Column Dictionary</h3>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs text-slate-300">
            <thead className="bg-slate-950 text-slate-400 font-semibold border-b border-slate-800">
              <tr>
                <th className="p-3">Column Name</th>
                <th className="p-3">Safe SQL Name</th>
                <th className="p-3">Semantic Type</th>
                <th className="p-3">Distinct</th>
                <th className="p-3">Nulls</th>
                <th className="p-3">Sample Values</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {profile?.columns?.map((col, i) => (
                <tr key={i} className="hover:bg-slate-800/30 transition">
                  <td className="p-3 font-semibold text-slate-200">{col.column_name}</td>
                  <td className="p-3 font-mono text-indigo-400">{col.safe_column_name}</td>
                  <td className="p-3">
                    <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-slate-800 text-slate-300 border border-slate-700">
                      {col.detected_type}
                    </span>
                  </td>
                  <td className="p-3">{col.distinct_count}</td>
                  <td className="p-3 text-amber-400">{col.missing_count}</td>
                  <td className="p-3 text-slate-400 truncate max-w-xs">
                    {col.sample_values?.slice(0, 3).join(", ")}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
