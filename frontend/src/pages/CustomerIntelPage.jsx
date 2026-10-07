import React, { useState, useEffect } from "react";
import { useDataset } from "../context/DatasetContext";
import { datasetApi } from "../services/api";
import NoDatasetState from "../components/common/NoDatasetState";
import { 
  Users, 
  UserCheck, 
  ShieldAlert, 
  BarChart2, 
  Sparkles, 
  CheckCircle2, 
  TrendingUp, 
  Layers, 
  Activity, 
  Award,
  AlertTriangle,
  ArrowRight
} from "lucide-react";

export default function CustomerIntelPage() {
  const { currentDataset } = useDataset();
  const [rfm, setRfm] = useState(null);
  const [churn, setChurn] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const datasetId = currentDataset?.id || currentDataset?.dataset_id;
    if (datasetId) {
      loadIntel();
    } else {
      setLoading(false);
    }
  }, [currentDataset]);

  const loadIntel = async () => {
    try {
      setLoading(true);
      const datasetId = currentDataset.id || currentDataset.dataset_id;
      const [rRes, cRes] = await Promise.all([
        datasetApi.getCustomers(datasetId),
        datasetApi.getChurn(datasetId)
      ]);
      setRfm(rRes.data);
      setChurn(cRes.data);
    } catch (err) {
      console.error("Customer Intel error:", err);
    } finally {
      setLoading(false);
    }
  };

  if (loading && !rfm) {
    return (
      <div className="p-12 text-center text-slate-400 space-y-3">
        <Activity className="w-8 h-8 text-indigo-400 animate-spin mx-auto" />
        <p className="font-semibold text-sm">Computing RFM segmentation & behavioral intelligence...</p>
      </div>
    );
  }

  if (!currentDataset?.id && !currentDataset?.dataset_id) {
    return <NoDatasetState title="No Active Dataset Selected" />;
  }

  const entityLabel = rfm?.entity_label || "Customer";

  return (
    <div className="p-6 md:p-8 max-w-6xl mx-auto space-y-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-800">
        <div>
          <h1 className="text-2xl font-extrabold tracking-tight flex items-center gap-2.5 text-slate-100">
            <Users className="w-7 h-7 text-indigo-400" />
            {rfm?.studio_title || `${entityLabel} Intelligence & Lifecycle Studio`}
          </h1>
          <p className="text-xs md:text-sm text-slate-400 mt-1">
            {rfm?.studio_subtitle || "Deterministic RFM (Recency, Frequency, Value) behavioral clustering and attrition risk attribution."}
          </p>
        </div>

        <div className="flex items-center gap-2">
          <span className="px-3 py-1 rounded-full text-xs font-bold bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 flex items-center gap-1.5">
            <UserCheck className="w-3.5 h-3.5" />
            {rfm?.total_customers?.toLocaleString()} {entityLabel.endsWith("s") ? entityLabel : (entityLabel.endsWith("y") ? entityLabel.slice(0, -1) + "ies" : entityLabel + "s")} Analyzed
          </span>
          {rfm?.retention_rate !== undefined && (
            <span className="px-3 py-1 rounded-full text-xs font-bold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
              {rfm.retention_rate}% {rfm?.retention_label || "Health Retention"}
            </span>
          )}
        </div>
      </div>

      {/* ── 1. SEGMENTS SUMMARY GRID (WITHOUT FORCED DOLLAR SIGNS) ── */}
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
            <Layers className="w-4 h-4 text-indigo-400" /> Behavioral Cohorts & Lifecycle Distribution
          </h3>
          <span className="text-[11px] text-slate-500">Tracked Metric: {rfm?.monetary_column || "Volume"}</span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {rfm?.segments?.map((seg, i) => {
            const isTop = i === 0;
            const isSecond = i === 1;
            const isThird = i === 2;
            const isLow = i === 3;

            return (
              <div 
                key={i} 
                className={`p-5 rounded-2xl bg-slate-900 border transition flex flex-col justify-between space-y-3 ${
                  isTop 
                    ? "border-emerald-500/40 shadow-lg shadow-emerald-500/5" 
                    : isLow 
                    ? "border-rose-500/40 shadow-lg shadow-rose-500/5" 
                    : isSecond 
                    ? "border-indigo-500/40" 
                    : "border-amber-500/40"
                }`}
              >
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <span className={`text-[10px] font-extrabold uppercase px-2 py-0.5 rounded border ${
                      isTop 
                        ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/20" 
                        : isLow 
                        ? "bg-rose-500/10 text-rose-400 border-rose-500/20" 
                        : isSecond 
                        ? "bg-indigo-500/10 text-indigo-400 border-indigo-500/20" 
                        : "bg-amber-500/10 text-amber-400 border-amber-500/20"
                    }`}>
                      {seg.segment}
                    </span>
                    <span className="text-xs font-mono font-bold text-slate-400">{seg.percentage}%</span>
                  </div>

                  <div className="text-2xl font-extrabold text-slate-100 my-1 font-mono">
                    {seg.customer_count?.toLocaleString()}
                  </div>

                  <div className="space-y-1 text-[11px] text-slate-400 pt-1">
                    {rfm?.has_dates ? (
                      <div className="flex justify-between">
                        <span>Avg Recency:</span>
                        <span className="font-mono text-slate-300 font-semibold">{seg.avg_recency_days} days</span>
                      </div>
                    ) : (
                      <div className="flex justify-between">
                        <span>Cohort Records:</span>
                        <span className="font-mono text-slate-300 font-semibold">{seg.customer_count?.toLocaleString()}</span>
                      </div>
                    )}
                    <div className="flex justify-between">
                      <span>Avg {rfm?.monetary_column || "Value"}:</span>
                      <span className="font-mono text-slate-300 font-semibold">
                        {Number(seg.avg_monetary || 0).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                      </span>
                    </div>
                  </div>
                </div>

                <div className="pt-3 border-t border-slate-800/80">
                  <span className="text-[10px] font-bold text-indigo-300 uppercase block mb-1">Recommended Action:</span>
                  <p className="text-[11px] text-slate-400 leading-snug">{seg.work_action}</p>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* ── 2. STRATEGIC WORK PLAYBOOK (ACTION ITEMS BASED ON DATASET) ── */}
      <div className="p-6 rounded-2xl bg-slate-900 border border-slate-800 space-y-4 shadow-xl">
        <div className="flex items-center justify-between border-b border-slate-800 pb-3">
          <div>
            <h3 className="text-sm font-bold text-slate-200 flex items-center gap-2">
              <Sparkles className="w-4 h-4 text-indigo-400" /> Operational Playbook (What Teams Should Work On)
            </h3>
            <p className="text-xs text-slate-400 mt-0.5">
              Targeted workflows based on {entityLabel.toLowerCase()} cohort patterns
            </p>
          </div>
          <span className="text-xs text-slate-500 font-mono">Cohort Optimization</span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {rfm?.segments?.map((seg, idx) => (
            <div key={idx} className="p-4 rounded-xl bg-slate-950 border border-slate-800 space-y-2">
              <div className="flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4 text-emerald-400 flex-shrink-0" />
                <h4 className="text-xs font-bold text-slate-200">
                  {seg.segment}: <span className="text-indigo-400">{seg.work_action}</span>
                </h4>
              </div>
              <p className="text-xs text-slate-400 leading-relaxed pl-6">
                {seg.playbook}
              </p>
            </div>
          ))}
        </div>
      </div>

      {/* ── 3. CHURN & RISK EXPLAINABILITY (SHAP PROXY) ── */}
      {churn?.supported && (
        <div className="p-6 rounded-2xl bg-slate-900 border border-indigo-500/25 space-y-6 shadow-xl">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-800 pb-4">
            <div>
              <h3 className="text-sm font-bold text-slate-100 flex items-center gap-2">
                <ShieldAlert className="w-4 h-4 text-rose-400" />
                Predictive Risk & Attrition Drivers: <span className="text-indigo-400">{churn.target_metric}</span>
              </h3>
              <p className="text-xs text-slate-400 mt-1">
                Trained Random Forest Classifier to identify which features trigger churn or drop-off.
              </p>
            </div>

            {churn.evaluation_metrics && (
              <div className="flex items-center gap-2 flex-wrap text-xs font-mono">
                <span className="px-2.5 py-1 rounded-lg bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-bold">
                  Acc: {churn.evaluation_metrics.accuracy}%
                </span>
                <span className="px-2.5 py-1 rounded-lg bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 font-bold">
                  Prec: {churn.evaluation_metrics.precision}%
                </span>
                <span className="px-2.5 py-1 rounded-lg bg-amber-500/10 text-amber-400 border border-amber-500/20 font-bold">
                  Rec: {churn.evaluation_metrics.recall}%
                </span>
                <span className="px-2.5 py-1 rounded-lg bg-purple-500/10 text-purple-400 border border-purple-500/20 font-bold">
                  F1: {churn.evaluation_metrics.f1_score}%
                </span>
              </div>
            )}
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {churn.feature_contributions?.map((f, i) => (
              <div key={i} className="p-3.5 rounded-xl bg-slate-950 border border-slate-800 space-y-2">
                <div className="flex items-center justify-between text-xs">
                  <span className="font-bold text-slate-200">{f.feature_label || f.feature}</span>
                  <div className="flex items-center gap-2">
                    <span className="font-mono text-indigo-400 font-extrabold">{f.percentage}% Impact</span>
                    <span className={`text-[9px] font-extrabold px-1.5 py-0.2 rounded border ${
                      f.impact.includes("High") 
                        ? "bg-rose-500/10 text-rose-400 border-rose-500/20" 
                        : "bg-indigo-500/10 text-indigo-400 border-indigo-500/20"
                    }`}>
                      {f.impact}
                    </span>
                  </div>
                </div>
                <div className="w-full h-1.5 bg-slate-800 rounded-full overflow-hidden">
                  <div 
                    className="h-full bg-gradient-to-r from-indigo-500 to-rose-500 rounded-full" 
                    style={{ width: `${Math.min(100, f.percentage * 2.2)}%` }}
                  ></div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* ── 4. TOP ACCOUNTS / ENTITIES PREVIEW TABLE ── */}
      {rfm?.top_entities && rfm.top_entities.length > 0 && (
        <div className="p-6 rounded-2xl bg-slate-900 border border-slate-800 space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-bold text-slate-200 flex items-center gap-2">
              <Award className="w-4 h-4 text-amber-400" />
              Key High-Value Accounts & Cohort Alignment
            </h3>
            <span className="text-xs text-slate-500 font-mono">Top Accounts by Value</span>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs text-slate-300">
              <thead className="bg-slate-950 text-slate-400 font-semibold border-b border-slate-800">
                <tr>
                  <th className="p-2.5">Entity / Account</th>
                  <th className="p-2.5">Cohort Segment</th>
                  <th className="p-2.5">Total Activity / Frequency</th>
                  <th className="p-2.5">Aggregate Value ({rfm.monetary_column})</th>
                  <th className="p-2.5">Recency (Days Ago)</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 font-mono">
                {rfm.top_entities.map((e, idx) => (
                  <tr key={idx} className="hover:bg-slate-800/30 transition">
                    <td className="p-2.5 font-sans font-semibold text-slate-200">{e.entity_name}</td>
                    <td className="p-2.5">
                      <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
                        {e.segment}
                      </span>
                    </td>
                    <td className="p-2.5">{e.frequency} transactions</td>
                    <td className="p-2.5 font-bold text-slate-100">
                      {Number(e.total_value).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                    </td>
                    <td className="p-2.5 text-slate-400">{e.recency_days} days</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
