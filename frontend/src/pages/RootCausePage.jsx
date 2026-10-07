import React, { useState, useEffect } from "react";
import { useDataset } from "../context/DatasetContext";
import { datasetApi } from "../services/api";
import NoDatasetState from "../components/common/NoDatasetState";
import { 
  SearchCode, 
  AlertTriangle, 
  ArrowDownRight, 
  Layers, 
  CheckCircle2, 
  ShieldAlert, 
  Target, 
  BrainCircuit, 
  TrendingUp, 
  TrendingDown, 
  Sparkles,
  HelpCircle,
  ShieldCheck,
  Zap,
  Activity,
  ChevronDown,
  PlusCircle
} from "lucide-react";

const LS_ROOT_CAUSE_KEY = (id) => `insightx_report_root_causes_${id}`;

export default function RootCausePage() {
  const { currentDataset } = useDataset();
  const [investigation, setInvestigation] = useState(null);
  const [selectedTarget, setSelectedTarget] = useState("");
  const [availableTargets, setAvailableTargets] = useState([]);
  const [loading, setLoading] = useState(true);
  const [savedReportItems, setSavedReportItems] = useState([]);

  useEffect(() => {
    const datasetId = currentDataset?.id || currentDataset?.dataset_id;
    if (datasetId) {
      const stored = localStorage.getItem(LS_ROOT_CAUSE_KEY(datasetId));
      setSavedReportItems(stored ? JSON.parse(stored) : []);

      // Fetch profile to guarantee all dataset columns are available in the target selector
      datasetApi.getProfile(datasetId).then((pRes) => {
        if (pRes.data?.columns?.length) {
          const cols = pRes.data.columns.map((c) => c.safe_column_name || c.column_name);
          setAvailableTargets(cols);
        }
      }).catch((err) => console.error("Profile columns fetch error:", err));

      loadInvestigation(selectedTarget);
    } else {
      setLoading(false);
    }
  }, [currentDataset]);

  const persistReportItems = (items) => {
    const datasetId = currentDataset?.id || currentDataset?.dataset_id;
    if (datasetId) {
      localStorage.setItem(LS_ROOT_CAUSE_KEY(datasetId), JSON.stringify(items));
    }
  };

  const isItemInReport = (itemId) => {
    return savedReportItems.some((it) => it.id === itemId);
  };

  const toggleReportItem = (item) => {
    let updated;
    if (isItemInReport(item.id)) {
      updated = savedReportItems.filter((it) => it.id !== item.id);
    } else {
      updated = [...savedReportItems, { ...item, added_at: new Date().toLocaleTimeString() }];
    }
    setSavedReportItems(updated);
    persistReportItems(updated);
  };

  const loadInvestigation = async (targetOverride) => {
    try {
      setLoading(true);
      const datasetId = currentDataset.id || currentDataset.dataset_id;
      const payload = targetOverride ? { target_metric: targetOverride } : {};
      const res = await datasetApi.getRootCause(datasetId, payload);
      setInvestigation(res.data);
      if (res.data?.available_targets && res.data.available_targets.length > 0) {
        setAvailableTargets(res.data.available_targets);
      }
      if (res.data?.target_metric && !targetOverride) {
        setSelectedTarget(res.data.target_metric);
      }
    } catch (err) {
      console.error("Root Cause error:", err);
    } finally {
      setLoading(false);
    }
  };

  const handleTargetChange = (newTarget) => {
    setSelectedTarget(newTarget);
    loadInvestigation(newTarget);
  };

  if (loading && !investigation) {
    return (
      <div className="p-12 text-center text-slate-400 space-y-3">
        <Activity className="w-8 h-8 text-indigo-400 animate-spin mx-auto" />
        <p className="font-semibold text-sm">Investigating root cause & computing feature drivers...</p>
      </div>
    );
  }

  if (!currentDataset?.id && !currentDataset?.dataset_id) {
    return <NoDatasetState title="No Active Dataset Selected" />;
  }

  const isClass = investigation?.problem_type === "classification";
  const metrics = investigation?.classification_metrics;
  const targetLabel = investigation?.target_title || selectedTarget || currentDataset?.target_column || "Primary Target Metric";

  // Build complete unique list of all columns in dataset for user target selection
  const allTargetOptions = Array.from(
    new Set([
      investigation?.target_metric,
      selectedTarget,
      ...availableTargets
    ].filter(Boolean))
  );

  return (
    <div className="p-6 md:p-8 max-w-6xl mx-auto space-y-8">
      {/* Header & Target Selector */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-800">
        <div>
          <h1 className="text-2xl font-extrabold tracking-tight flex items-center gap-2.5 text-slate-100">
            <SearchCode className="w-7 h-7 text-indigo-400" />
            Root Cause Investigation Studio
          </h1>
          <p className="text-xs md:text-sm text-slate-400 mt-1">
            Empirical causal discovery: discover <strong className="text-slate-200">what</strong> happened, <strong className="text-slate-200">why</strong> it dropped or increased, and <strong className="text-slate-200">how to prevent</strong> it based on your dataset.
          </p>
        </div>

        {/* Target Column Selector */}
        <div className="flex items-center gap-3 flex-wrap">
          <div className="flex items-center gap-2 bg-slate-900 border border-slate-700/80 px-3 py-1.5 rounded-xl">
            <Target className="w-3.5 h-3.5 text-indigo-400" />
            <span className="text-xs text-slate-400 font-semibold">Target Column:</span>
            <select
              value={selectedTarget || investigation?.target_metric || ""}
              onChange={(e) => handleTargetChange(e.target.value)}
              className="bg-slate-950 text-indigo-300 text-xs font-bold border border-slate-800 rounded-lg px-2.5 py-1.5 outline-none cursor-pointer hover:border-indigo-500/50"
            >
              {allTargetOptions.map((col) => (
                <option key={col} value={col}>
                  {col.replace(/_/g, " ").toUpperCase()}
                </option>
              ))}
            </select>
          </div>

          <span className={`px-2.5 py-1 rounded-full text-xs font-bold ${isClass ? "bg-purple-500/10 text-purple-400 border border-purple-500/20" : "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"}`}>
            {isClass ? "Classification Model" : "Regression Decomposition"}
          </span>
        </div>
      </div>

      {/* ── 1. WHAT HAPPENED & WHY IT HAPPENED HERO ── */}
      {(() => {
        const overallId = `rc_overall_${selectedTarget || investigation?.target_metric || "default"}`;
        const overallItem = {
          id: overallId,
          type: "overall",
          target: targetLabel,
          title: `Executive Verdict: ${targetLabel}`,
          what_happened: investigation?.what_happened || investigation?.narrative_finding,
          why_it_happened: investigation?.why_it_happened || investigation?.driver_explanation,
          recommendations: (
            investigation?.recommendations && investigation.recommendations.length > 0
              ? investigation.recommendations
              : (investigation?.how_to_prevent || []).map(r => ({ detail: typeof r === "object" ? (r.detail || r.action) : r }))
          ).slice(0, 3)
        };
        const inReport = isItemInReport(overallId);
        const recordCount = investigation?.total_records 
          || (typeof investigation?.baseline_daily === "number" && investigation?.baseline_daily > 100 ? investigation.baseline_daily : null)
          || currentDataset?.row_count 
          || "analyzed";

        return (
          <div className="p-6 rounded-2xl bg-gradient-to-r from-slate-900 via-slate-900 to-indigo-950/40 border-2 border-indigo-500/30 space-y-4 shadow-xl">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
              <div className="flex items-center gap-2 text-xs font-bold text-indigo-400 uppercase tracking-wider">
                <Sparkles className="w-4 h-4 text-indigo-400" />
                Executive Root Cause Verdict
              </div>
              <div className="flex items-center gap-3">
                <span className="text-xs text-slate-400">
                  Based on {typeof recordCount === "number" ? recordCount.toLocaleString() : recordCount} dataset records
                </span>
                <button
                  onClick={() => toggleReportItem(overallItem)}
                  className={`px-3 py-1.5 rounded-lg text-xs font-bold flex items-center gap-1.5 transition ${
                    inReport
                      ? "bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 hover:bg-emerald-500/30"
                      : "bg-indigo-600/30 text-indigo-200 border border-indigo-500/40 hover:bg-indigo-600/50"
                  }`}
                  title={inReport ? "Remove overall verdict from report" : "Add overall verdict to report"}
                >
                  {inReport ? (
                    <>
                      <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                      In Report (Click to Remove)
                    </>
                  ) : (
                    <>
                      <PlusCircle className="w-3.5 h-3.5 text-indigo-300" />
                      + Add Verdict to Report
                    </>
                  )}
                </button>
              </div>
            </div>

            <div>
              <span className="text-xs font-bold uppercase tracking-wider text-rose-400 block mb-1">
                1. What Happened
              </span>
              <h2 className="text-xl font-bold text-slate-100 leading-snug">
                {investigation?.what_happened || investigation?.narrative_finding || `Analysis completed for ${targetLabel} across historical observations.`}
              </h2>
            </div>

            <div className="p-4 rounded-xl bg-slate-950/80 border border-slate-800 space-y-1.5">
              <span className="text-xs font-bold uppercase tracking-wider text-amber-400 block">
                2. Why It Happened (Underlying Root Causes)
              </span>
              <p className="text-sm text-slate-300 leading-relaxed font-medium">
                {investigation?.why_it_happened || investigation?.driver_explanation || `Primary variance in ${targetLabel} is statistically driven by operational bottlenecks and cohort shifts.`}
              </p>
            </div>

            {investigation?.causality_disclaimer && (
              <div className="text-[11px] text-slate-500 italic">
                *{investigation.causality_disclaimer}
              </div>
            )}
          </div>
        );
      })()}

      {/* ── 2. CLASSIFICATION EVALUATION METRICS (IMAGE 3) ── */}
      {isClass && metrics && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-bold text-slate-200 flex items-center gap-2">
              <BrainCircuit className="w-4 h-4 text-purple-400" />
              Machine Learning Classification Metrics
            </h3>
            <span className="text-xs text-slate-500">
              Evaluated on predictive attribution for {targetLabel}
            </span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {/* Accuracy */}
            <div className="p-5 rounded-2xl bg-slate-900 border border-slate-800 hover:border-indigo-500/40 transition">
              <div className="flex items-center justify-between mb-1">
                <span className="text-xs font-bold text-slate-400">Accuracy</span>
                <span className="text-[10px] px-2 py-0.5 rounded bg-indigo-500/10 text-indigo-400 font-mono font-bold">
                  Overall
                </span>
              </div>
              <div className="text-3xl font-extrabold text-slate-100 my-1 font-mono">
                {metrics.accuracy}%
              </div>
              <p className="text-xs text-slate-400 leading-relaxed">
                {metrics.accuracy_desc}
              </p>
            </div>

            {/* Precision */}
            <div className="p-5 rounded-2xl bg-slate-900 border border-slate-800 hover:border-emerald-500/40 transition">
              <div className="flex items-center justify-between mb-1">
                <span className="text-xs font-bold text-slate-400">Precision</span>
                <span className="text-[10px] px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 font-mono font-bold">
                  Min False Positives
                </span>
              </div>
              <div className="text-3xl font-extrabold text-emerald-400 my-1 font-mono">
                {metrics.precision}%
              </div>
              <p className="text-xs text-slate-400 leading-relaxed">
                {metrics.precision_desc}
              </p>
            </div>

            {/* Recall */}
            <div className="p-5 rounded-2xl bg-slate-900 border border-slate-800 hover:border-rose-500/40 transition">
              <div className="flex items-center justify-between mb-1">
                <span className="text-xs font-bold text-slate-400">Recall</span>
                <span className="text-[10px] px-2 py-0.5 rounded bg-rose-500/10 text-rose-400 font-mono font-bold">
                  Min False Negatives
                </span>
              </div>
              <div className="text-3xl font-extrabold text-rose-400 my-1 font-mono">
                {metrics.recall}%
              </div>
              <p className="text-xs text-slate-400 leading-relaxed">
                {metrics.recall_desc}
              </p>
            </div>

            {/* F1 Score */}
            <div className="p-5 rounded-2xl bg-slate-900 border border-slate-800 hover:border-purple-500/40 transition">
              <div className="flex items-center justify-between mb-1">
                <span className="text-xs font-bold text-slate-400">F1 Score</span>
                <span className="text-[10px] px-2 py-0.5 rounded bg-purple-500/10 text-purple-400 font-mono font-bold">
                  Balanced
                </span>
              </div>
              <div className="text-3xl font-extrabold text-purple-400 my-1 font-mono">
                {metrics.f1_score}%
              </div>
              <p className="text-xs text-slate-400 leading-relaxed">
                {metrics.f1_desc}
              </p>
            </div>
          </div>
        </div>
      )}

      {/* ── 3. KEY DRIVERS DECOMPOSITION (FEATURE INFLUENCE) ── */}
      {investigation?.key_drivers && investigation.key_drivers.length > 0 && (
        <div className="p-6 rounded-2xl bg-slate-900 border border-slate-800 space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-bold text-slate-200 flex items-center gap-2">
              <Zap className="w-4 h-4 text-amber-400" />
              Key Feature Drivers (Influence Breakdown)
            </h3>
            <span className="text-xs text-slate-500">Relative contribution to {targetLabel}</span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {investigation.key_drivers.map((driver, idx) => {
              const driverId = `rc_driver_${selectedTarget || investigation?.target_metric || "default"}_${driver.feature || idx}`;
              const driverItem = {
                id: driverId,
                type: "driver",
                target: targetLabel,
                feature: driver.feature_label || driver.feature,
                percentage: driver.percentage,
                why_explanation: driver.why_explanation,
                how_to_prevent: driver.how_to_prevent
              };
              const inReport = isItemInReport(driverId);

              return (
                <div key={idx} className="p-4 rounded-xl bg-slate-950 border border-slate-800 space-y-2 flex flex-col justify-between">
                  <div>
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-bold text-slate-200">{driver.feature_label || driver.feature}</span>
                      <span className="text-xs font-mono font-extrabold text-indigo-400">{driver.percentage}% Impact</span>
                    </div>
                    <div className="w-full h-1.5 bg-slate-800 rounded-full overflow-hidden my-2">
                      <div 
                        className="h-full bg-gradient-to-r from-indigo-500 to-purple-500 rounded-full" 
                        style={{ width: `${Math.min(100, (driver.percentage || 10) * 2.2)}%` }}
                      ></div>
                    </div>
                    <p className="text-[11px] text-slate-400 leading-relaxed">{driver.why_explanation}</p>
                    {driver.how_to_prevent && (
                      <p className="text-[10px] text-emerald-400/90 mt-1 leading-relaxed">
                        <strong className="text-emerald-400">Action: </strong>{driver.how_to_prevent}
                      </p>
                    )}
                  </div>
                  <div className="pt-2 border-t border-slate-800/80 flex items-center justify-between mt-2">
                    <span className="text-[10px] text-slate-500 font-mono">Driver #{idx + 1}</span>
                    <button
                      onClick={() => toggleReportItem(driverItem)}
                      className={`text-[10px] font-bold px-2.5 py-1 rounded-md flex items-center gap-1 transition ${
                        inReport
                          ? "bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 hover:bg-emerald-500/30"
                          : "bg-slate-800 text-indigo-300 border border-slate-700 hover:border-indigo-500/50 hover:bg-indigo-950/40"
                      }`}
                      title={inReport ? "Remove driver from report" : "Add driver to report"}
                    >
                      {inReport ? (
                        <>
                          <CheckCircle2 className="w-3 h-3 text-emerald-400" />
                          In Report (Remove)
                        </>
                      ) : (
                        <>
                          <PlusCircle className="w-3 h-3 text-indigo-400" />
                          + Add to Report
                        </>
                      )}
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* ── 4. HOW TO PREVENT & MITIGATE (ACTION PLAN) ── */}
      <div className="p-6 rounded-2xl bg-slate-900 border border-emerald-500/25 space-y-4 shadow-lg">
        <div className="flex items-center justify-between border-b border-slate-800 pb-3">
          <h3 className="text-xs font-bold uppercase tracking-wider text-emerald-400 flex items-center gap-2">
            <ShieldCheck className="w-4 h-4 text-emerald-400" /> 3. How to Prevent & Mitigate (Action Plan)
          </h3>
          <span className="text-[11px] text-slate-400">Derived from underlying dataset patterns</span>
        </div>

        <div className="space-y-3">
          {(
            (investigation?.recommendations && investigation.recommendations.length > 0)
              ? investigation.recommendations
              : (investigation?.how_to_prevent || []).map(r => ({ detail: r }))
          ).map((rec, i) => (
            <div key={i} className="p-3.5 rounded-xl bg-slate-950 border border-slate-800 flex items-start gap-3">
              <CheckCircle2 className="w-4 h-4 text-emerald-400 mt-0.5 flex-shrink-0" />
              <div className="space-y-0.5">
                {rec.action && (
                  <h4 className="text-xs font-bold text-slate-100">{rec.action}</h4>
                )}
                <p className="text-xs text-slate-300 font-medium leading-relaxed">{rec.detail || rec}</p>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* ── 5. DIMENSIONAL BREAKDOWN (WITHOUT FORCED DOLLAR SYMBOLS) ── */}
      {investigation?.dimensional_breakdowns && investigation.dimensional_breakdowns.length > 0 && (
        <div className="p-6 rounded-2xl bg-slate-900 border border-slate-800 space-y-4">
          <h3 className="text-sm font-bold text-slate-200 flex items-center gap-2">
            <Layers className="w-4 h-4 text-indigo-400" /> Dimensional Segment Breakdown
          </h3>
          {investigation.dimensional_breakdowns.slice(0, 2).map((dim, idx) => (
            <div key={idx} className="space-y-2 pt-2">
              <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400">{dim.dimension_title} Breakdown</h4>
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs text-slate-300">
                  <thead className="bg-slate-950 text-slate-400 font-semibold border-b border-slate-800">
                    <tr>
                      <th className="p-2.5">Segment Name</th>
                      <th className="p-2.5">Baseline Scope</th>
                      <th className="p-2.5">{isClass ? "Target Positive Cases" : "Crisis Scope"}</th>
                      <th className="p-2.5">Variance</th>
                      <th className="p-2.5">% Shift</th>
                      <th className="p-2.5">Contribution %</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60 font-mono">
                    {dim.items.map((it, i) => (
                      <tr key={i} className="hover:bg-slate-800/30 transition">
                        <td className="p-2.5 font-sans font-semibold text-slate-200">{it.name}</td>
                        <td className="p-2.5">{Number(it.baseline_daily || 0).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</td>
                        <td className="p-2.5">{Number(it.crisis_daily || 0).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</td>
                        <td className={`p-2.5 font-bold ${it.delta < 0 ? "text-rose-400" : "text-emerald-400"}`}>
                          {it.delta > 0 ? `+${Number(it.delta).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}` : Number(it.delta || 0).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                        </td>
                        <td className="p-2.5">{it.pct_change}%</td>
                        <td className="p-2.5 text-indigo-400 font-bold">{it.contribution_percentage}%</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
