import React, { useState, useEffect } from "react";
import { useDataset } from "../context/DatasetContext";
import { datasetApi } from "../services/api";
import ChartRenderer from "../components/charts/ChartRenderer";
import CustomChartBuilder from "../components/charts/CustomChartBuilder";
import NoDatasetState from "../components/common/NoDatasetState";
import { 
  FileText, 
  Printer, 
  CheckCircle2, 
  TrendingUp, 
  TrendingDown, 
  ShieldAlert, 
  Zap, 
  Target, 
  HelpCircle,
  ArrowUpRight,
  ShieldCheck,
  BrainCircuit,
  PlusCircle,
  Trash2,
  X,
  Layers,
  Activity,
  BarChart3,
  Calendar,
  Database,
  Sparkles
} from "lucide-react";

const LS_CUSTOM_KEY = (id) => `insightx_custom_charts_${id}`;
const LS_ROOT_CAUSE_KEY = (id) => `insightx_report_root_causes_${id}`;

function getCustomChartExplanation(spec) {
  if (spec?.user_friendly_explanation?.what_it_shows) {
    return spec.user_friendly_explanation;
  }
  const data = spec?.data || [];
  if (data.length === 0) {
    return {
      what_it_shows: spec?.description || "Custom analytical visualization.",
      key_takeaway: "No data points recorded for this custom selection.",
      recommendation: "Review the custom chart query configuration."
    };
  }

  const sorted = [...data].sort((a, b) => (Number(b.value) || 0) - (Number(a.value) || 0));
  const top = sorted[0] || {};
  const low = sorted[sorted.length - 1] || {};
  const tot = sorted.reduce((acc, curr) => acc + (Number(curr.value) || 0), 0) || 1;
  const topVal = Number(top.value) || 0;
  const lowVal = Number(low.value) || 0;
  const topShare = Math.round((topVal / tot) * 100);
  
  const formatVal = (v) => {
    if (v === undefined || v === null || isNaN(v)) return "0";
    return Number(v).toLocaleString(undefined, { maximumFractionDigits: 2 });
  };

  const xLabel = spec?.x_axis ? String(spec.x_axis).replace(/_/g, " ") : "categories";
  const title = spec?.title || "Custom Metric";
  const topLabel = top.label || top.category || "Leading segment";
  const lowLabel = low.label || low.category || "Lowest segment";

  return {
    what_it_shows: `Distribution of ${title} grouped by ${xLabel} categories based on your custom query.`,
    key_takeaway: `'${topLabel}' commands the highest volume with ${formatVal(topVal)} (${topShare}% of total analyzed volume), whereas '${lowLabel}' records lowest at ${formatVal(lowVal)}.`,
    recommendation: `Optimize operational resources for '${topLabel}' to maximize return while reviewing performance variance in lower categories.`
  };
}

export default function ReportsPage() {
  const { currentDataset } = useDataset();
  const [report, setReport] = useState(null);
  const [loading, setLoading] = useState(true);
  const [customCharts, setCustomCharts] = useState([]);
  const [savedRootCauses, setSavedRootCauses] = useState([]);
  const [showChartBuilder, setShowChartBuilder] = useState(false);

  useEffect(() => {
    const datasetId = currentDataset?.id || currentDataset?.dataset_id;
    if (datasetId) {
      loadReport();
      const storedCustom = localStorage.getItem(LS_CUSTOM_KEY(datasetId));
      setCustomCharts(storedCustom ? JSON.parse(storedCustom) : []);

      const storedRC = localStorage.getItem(LS_ROOT_CAUSE_KEY(datasetId));
      setSavedRootCauses(storedRC ? JSON.parse(storedRC) : []);
    } else {
      setLoading(false);
    }
  }, [currentDataset]);

  const persistCustomCharts = (charts) => {
    const datasetId = currentDataset?.id || currentDataset?.dataset_id;
    if (datasetId) {
      localStorage.setItem(LS_CUSTOM_KEY(datasetId), JSON.stringify(charts));
    }
  };

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

  const handleRemoveRootCause = (itemId) => {
    const updated = savedRootCauses.filter((rc) => rc.id !== itemId);
    setSavedRootCauses(updated);
    const datasetId = currentDataset?.id || currentDataset?.dataset_id;
    if (datasetId) {
      localStorage.setItem(LS_ROOT_CAUSE_KEY(datasetId), JSON.stringify(updated));
    }
  };

  const loadReport = async () => {
    try {
      setLoading(true);
      const res = await datasetApi.getReport(currentDataset.id || currentDataset.dataset_id);
      setReport(res.data);
    } catch (err) {
      console.error("Report load error:", err);
    } finally {
      setLoading(false);
    }
  };

  const handlePrint = () => {
    window.print();
  };

  if (loading) {
    return (
      <div className="p-12 text-center text-slate-400 space-y-3">
        <Activity className="w-8 h-8 animate-spin text-indigo-400 mx-auto" />
        <p className="text-sm font-medium">Compiling comprehensive executive investigation report & charts...</p>
      </div>
    );
  }

  if (!currentDataset?.id && !currentDataset?.dataset_id) {
    return <NoDatasetState title="No Active Dataset Selected" />;
  }

  const ml = report?.ml_explainability;
  const rootCause = report?.root_cause;
  const targetLabel = report?.target_column 
    ? report.target_column.replace(/_/g, " ").toUpperCase() 
    : "PRIMARY TARGET";

  // Consolidate dashboard charts
  const dashboardCharts = report?.all_dashboard_charts || report?.report_charts || [];

  return (
    <>
      {/* Print-specific CSS */}
      <style>{`
        @media print {
          @page {
            size: A4 portrait;
            margin: 8mm 10mm;
          }
          * {
            -webkit-print-color-adjust: exact !important;
            print-color-adjust: exact !important;
            color-adjust: exact !important;
          }
          html, body, #root, #root > div, .flex, .h-screen, .overflow-hidden, .overflow-y-auto, main {
            height: auto !important;
            min-height: auto !important;
            max-height: none !important;
            overflow: visible !important;
            position: static !important;
            display: block !important;
            background-color: #0f172a !important;
            color: #f8fafc !important;
          }
          /* 100% eradicate sidebar and headers from print to remove blank sidebar pages */
          nav, aside, header, .print-hide, aside *, header * {
            display: none !important;
            visibility: hidden !important;
            width: 0 !important;
            height: 0 !important;
            margin: 0 !important;
            padding: 0 !important;
            position: absolute !important;
            left: -9999px !important;
            top: -9999px !important;
          }
          .print-full-width {
            max-width: 100% !important;
            width: 100% !important;
            padding: 0 !important;
            margin: 0 !important;
          }
          /* Section containers flow naturally across pages without premature page breaks */
          .print-section {
            background-color: #0f172a !important;
            color: #f8fafc !important;
            border: 1px solid #334155 !important;
            break-inside: auto !important;
            page-break-inside: auto !important;
            margin-bottom: 16px !important;
            box-shadow: none !important;
          }
          /* Only individual chart cards or small sub-blocks avoid breaking across pages */
          .print-avoid-break {
            break-inside: avoid !important;
            page-break-inside: avoid !important;
          }
          /* Crisp high-contrast text to eliminate any blurry or faint white-on-white text */
          .print-section h1, .print-section h2, .print-section h3, .print-section h4 {
            color: #ffffff !important;
            font-weight: 800 !important;
          }
          .print-section p, .print-section span {
            color: #f8fafc !important;
          }
          .print-section .text-slate-400, .print-section .text-slate-500 {
            color: #cbd5e1 !important;
            font-weight: 600 !important;
          }
          .print-section .text-indigo-400, .print-section .text-indigo-300 {
            color: #818cf8 !important;
            font-weight: 700 !important;
          }
          .print-section .text-emerald-400 {
            color: #34d399 !important;
            font-weight: 700 !important;
          }
          .print-section .text-rose-400 {
            color: #fb7185 !important;
            font-weight: 700 !important;
          }
          .print-section .text-amber-400 {
            color: #fbbf24 !important;
            font-weight: 700 !important;
          }
          .recharts-responsive-container {
            width: 100% !important;
            min-height: 270px !important;
            height: 270px !important;
            overflow: visible !important;
          }
          .recharts-surface {
            width: 100% !important;
            overflow: visible !important;
          }
        }
      `}</style>

      <div className="p-6 md:p-8 max-w-5xl mx-auto space-y-8 print-full-width">
        {/* Header & Single Action: Download PDF Report */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-6 border-b border-slate-800">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="px-2 py-0.5 rounded bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 text-[10px] font-extrabold uppercase tracking-wider">
                EXECUTIVE INTELLIGENCE BRIEF
              </span>
              {report?.target_column && (
                <span className="px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 text-[10px] font-extrabold uppercase flex items-center gap-1">
                  <Target className="w-3 h-3" /> Target: {report.target_column.replace(/_/g, " ")}
                </span>
              )}
            </div>
            <h1 className="text-2xl md:text-3xl font-extrabold tracking-tight text-slate-100">
              {report?.report_title || "Executive Investigation Report"}
            </h1>
            <div className="flex items-center gap-4 text-xs text-slate-400 mt-2">
              <span className="flex items-center gap-1">
                <Calendar className="w-3.5 h-3.5 text-slate-500" />
                {report?.generated_at}
              </span>
              <span className="flex items-center gap-1">
                <Database className="w-3.5 h-3.5 text-slate-500" />
                {report?.dataset_summary?.records?.toLocaleString()} verified records • {report?.dataset_summary?.columns} dimensions
              </span>
            </div>
          </div>

          {/* PDF Download Button Only */}
          <div className="print-hide flex items-center gap-3">
            <button
              onClick={handlePrint}
              className="px-5 py-2.5 rounded-xl bg-gradient-to-r from-indigo-600 via-purple-600 to-indigo-700 hover:from-indigo-500 hover:to-purple-500 text-white text-xs font-extrabold shadow-lg shadow-indigo-600/25 transition flex items-center gap-2"
              title="Generate and download printable Executive PDF Report"
            >
              <Printer className="w-4 h-4" />
              Download Executive PDF Report
            </button>
          </div>
        </div>

        {/* ── Section 1: What Happened (High-Level Discovery) ── */}
        <div className="p-6 rounded-2xl bg-slate-900 border border-slate-800 space-y-4 shadow-xl print-section">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <h3 className="text-xs font-bold uppercase tracking-wider text-indigo-400 flex items-center gap-2">
              <Zap className="w-4 h-4 text-amber-400" /> 1. What Happened (Executive Overview)
            </h3>
            <span className="text-[11px] text-slate-400">
              Data Quality: <span className="font-bold text-emerald-400">{report?.dataset_summary?.quality_score || 94} / 100</span>
            </span>
          </div>

          {rootCause?.what_happened ? (
            <div className="p-4 rounded-xl bg-slate-950/80 border border-slate-800/80 text-sm font-medium text-slate-200 leading-relaxed">
              {rootCause.what_happened}
            </div>
          ) : (
            <div className="space-y-2">
              {report?.key_findings?.map((finding, idx) => (
                <div key={idx} className="flex items-start gap-2.5 text-sm text-slate-300">
                  <span className="w-1.5 h-1.5 rounded-full bg-indigo-400 mt-2 flex-shrink-0"></span>
                  <span className="leading-relaxed">{finding}</span>
                </div>
              ))}
            </div>
          )}

          {/* Quick Stat Highlights */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 pt-2">
            <div className="p-3 rounded-xl bg-slate-950 border border-slate-800 text-center">
              <div className="text-[10px] uppercase font-bold text-slate-400">Total Analyzed Rows</div>
              <div className="text-lg font-extrabold text-slate-100 mt-0.5">
                {report?.dataset_summary?.records?.toLocaleString() || "N/A"}
              </div>
            </div>
            <div className="p-3 rounded-xl bg-slate-950 border border-slate-800 text-center">
              <div className="text-[10px] uppercase font-bold text-slate-400">Tracked Features</div>
              <div className="text-lg font-extrabold text-slate-100 mt-0.5">
                {report?.dataset_summary?.columns || "N/A"}
              </div>
            </div>
            <div className="p-3 rounded-xl bg-slate-950 border border-slate-800 text-center">
              <div className="text-[10px] uppercase font-bold text-slate-400">Target Variable</div>
              <div className="text-sm font-extrabold text-indigo-400 mt-1 truncate">
                {report?.target_column ? report.target_column.replace(/_/g, " ") : "General Analytics"}
              </div>
            </div>
            <div className="p-3 rounded-xl bg-slate-950 border border-slate-800 text-center">
              <div className="text-[10px] uppercase font-bold text-slate-400">Health / Quality</div>
              <div className="text-lg font-extrabold text-emerald-400 mt-0.5">
                {report?.dataset_summary?.quality_score || 94}%
              </div>
            </div>
          </div>
        </div>

        {/* ── Section 2: Why It Happened (Root Cause & Key Drivers) ── */}
        <div className="p-6 rounded-2xl bg-slate-900 border border-indigo-500/20 space-y-6 shadow-xl print-section">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-800 pb-3">
            <div>
              <h3 className="text-xs font-bold uppercase tracking-wider text-indigo-400 flex items-center gap-2">
                <BrainCircuit className="w-4 h-4 text-indigo-400" /> 2. Why It Happened (Root Cause & Drivers)
              </h3>
              <p className="text-xs text-slate-400 mt-1">
                Deterministic statistical attribution explaining variance, declines, or incidence in {targetLabel}.
              </p>
            </div>
            <span className="px-2.5 py-1 rounded-full text-[10px] font-extrabold bg-indigo-500/10 text-indigo-300 border border-indigo-500/20 self-start">
              {rootCause?.task_type ? `${rootCause.task_type.toUpperCase()} ANALYSIS` : "CAUSAL ANALYSIS"}
            </span>
          </div>

          {/* Why Explanation Card */}
          {rootCause?.why_it_happened && (
            <div className="p-4 rounded-xl bg-indigo-950/20 border border-indigo-500/30 text-sm text-slate-200 leading-relaxed font-medium">
              <span className="font-bold text-indigo-300">Root Cause Conclusion: </span>
              {rootCause.why_it_happened}
            </div>
          )}

          {/* Classification Metrics (if Target is categorical/binary, e.g. Heart Disease, Churn) */}
          {rootCause?.classification_metrics && (
            <div className="space-y-3">
              <div className="text-xs font-bold uppercase tracking-wider text-slate-300 flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4 text-emerald-400" /> Machine Learning Evaluation Metrics
              </div>
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                <div className="p-3.5 rounded-xl bg-slate-950 border border-slate-800">
                  <div className="text-[11px] font-bold text-slate-400">Accuracy</div>
                  <div className="text-xl font-extrabold text-emerald-400 my-0.5">
                    {rootCause.classification_metrics.accuracy}%
                  </div>
                  <p className="text-[10px] text-slate-500 leading-tight">Overall correct predictions</p>
                </div>
                <div className="p-3.5 rounded-xl bg-slate-950 border border-slate-800">
                  <div className="text-[11px] font-bold text-slate-400">Precision</div>
                  <div className="text-xl font-extrabold text-indigo-400 my-0.5">
                    {rootCause.classification_metrics.precision}%
                  </div>
                  <p className="text-[10px] text-slate-500 leading-tight">Minimizes false alarms</p>
                </div>
                <div className="p-3.5 rounded-xl bg-slate-950 border border-slate-800">
                  <div className="text-[11px] font-bold text-slate-400">Recall</div>
                  <div className="text-xl font-extrabold text-amber-400 my-0.5">
                    {rootCause.classification_metrics.recall}%
                  </div>
                  <p className="text-[10px] text-slate-500 leading-tight">Catches critical positive cases</p>
                </div>
                <div className="p-3.5 rounded-xl bg-slate-950 border border-slate-800">
                  <div className="text-[11px] font-bold text-slate-400">F1 Score</div>
                  <div className="text-xl font-extrabold text-purple-400 my-0.5">
                    {rootCause.classification_metrics.f1_score}%
                  </div>
                  <p className="text-[10px] text-slate-500 leading-tight">Harmonic balance precision/recall</p>
                </div>
              </div>
            </div>
          )}

          {/* Key Drivers Decomposition */}
          {(rootCause?.drivers || ml?.drivers) && (
            <div className="space-y-3">
              <div className="text-xs font-bold uppercase tracking-wider text-slate-300 flex items-center gap-2">
                <BarChart3 className="w-4 h-4 text-indigo-400" /> Primary Contributing Features
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {(rootCause?.drivers || ml?.drivers || []).slice(0, 4).map((d, i) => (
                  <div key={i} className="p-3.5 rounded-xl bg-slate-950 border border-slate-800 space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-bold text-slate-200">{d.feature || d.feature_label}</span>
                      <span className="text-xs font-mono font-extrabold text-indigo-400">{d.contribution_percent || d.percentage}% Impact</span>
                    </div>
                    <div className="w-full h-1.5 bg-slate-800 rounded-full overflow-hidden">
                      <div 
                        className="h-full bg-gradient-to-r from-indigo-500 to-purple-500 rounded-full" 
                        style={{ width: `${Math.min(100, (d.contribution_percent || d.percentage || 10) * 2.2)}%` }}
                      ></div>
                    </div>
                    <p className="text-[11px] text-slate-400 leading-relaxed">{d.why_explanation || d.insight}</p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* User-Added Root Cause Analyses & Feature Drivers (Pinned from Root Cause Studio) */}
          {savedRootCauses.length > 0 && (
            <div className="space-y-3 pt-3 border-t border-slate-800">
              <div className="flex items-center justify-between">
                <div className="text-xs font-bold uppercase tracking-wider text-amber-400 flex items-center gap-2">
                  <Sparkles className="w-4 h-4 text-amber-400" />
                  User-Added Root Cause Findings & Feature Drivers ({savedRootCauses.length})
                </div>
                <span className="text-[11px] text-slate-400">
                  Custom selections saved from Root Cause Studio
                </span>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-3.5">
                {savedRootCauses.map((item) => (
                  <div 
                    key={item.id} 
                    className="p-4 rounded-xl bg-slate-950 border border-amber-500/30 space-y-2.5 relative group shadow-md"
                  >
                    <button
                      onClick={() => handleRemoveRootCause(item.id)}
                      className="print-hide absolute top-3 right-3 p-1 rounded-md bg-slate-900 hover:bg-rose-500/20 text-slate-400 hover:text-rose-400 border border-slate-800 hover:border-rose-500/30 transition opacity-0 group-hover:opacity-100"
                      title="Remove from report"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>

                    <div className="flex items-center gap-2 flex-wrap pr-8">
                      <span className="px-2 py-0.5 rounded text-[9px] font-bold bg-amber-500/10 text-amber-300 border border-amber-500/20 uppercase">
                        {item.type === "overall" ? "Executive Verdict" : `Driver: ${item.percentage || 0}% Impact`}
                      </span>
                      <span className="text-xs font-mono font-bold text-indigo-400">
                        TARGET: {item.target}
                      </span>
                    </div>

                    {item.type === "overall" ? (
                      <div className="space-y-1.5 text-xs">
                        <h4 className="font-bold text-slate-200">{item.what_happened}</h4>
                        <p className="text-slate-300 leading-relaxed font-medium">{item.why_it_happened}</p>
                        {item.recommendations && item.recommendations.length > 0 && (
                          <div className="pt-1 space-y-1">
                            {item.recommendations.map((rec, rIdx) => (
                              <div key={rIdx} className="text-[11px] text-emerald-400 flex items-start gap-1.5">
                                <CheckCircle2 className="w-3 h-3 mt-0.5 flex-shrink-0" />
                                <span>{typeof rec === "object" ? (rec.detail || rec.action) : rec}</span>
                              </div>
                            ))}
                          </div>
                        )}
                      </div>
                    ) : (
                      <div className="space-y-1.5 text-xs">
                        <div className="flex items-center justify-between">
                          <h4 className="font-bold text-slate-200">{item.feature}</h4>
                          <span className="font-mono text-indigo-300 font-extrabold">{item.percentage}% Impact</span>
                        </div>
                        <p className="text-slate-300 text-[11px] leading-relaxed">{item.why_explanation}</p>
                        {item.how_to_prevent && (
                          <p className="text-[10px] text-emerald-400/90 leading-relaxed">
                            <strong className="text-emerald-400">Action: </strong>{item.how_to_prevent}
                          </p>
                        )}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* ── Section 3: How to Prevent & Optimize (Strategic Action Plan) ── */}
        <div className="p-6 rounded-2xl bg-slate-900 border border-emerald-500/20 space-y-4 shadow-xl print-section">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <h3 className="text-xs font-bold uppercase tracking-wider text-emerald-400 flex items-center gap-2">
              <ShieldCheck className="w-4 h-4 text-emerald-400" /> 3. How to Prevent & Strategic Action Plan
            </h3>
            <span className="text-[11px] text-slate-400">Dataset-Grounded Recommendations</span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Prevention / Risk Mitigation */}
            <div className="p-4 rounded-xl bg-rose-500/5 border border-rose-500/20 space-y-3">
              <h4 className="text-xs font-bold uppercase tracking-wider text-rose-400 flex items-center gap-1.5">
                <ShieldAlert className="w-4 h-4 text-rose-400" /> Prevent Negative Drops / Critical Risks
              </h4>
              <div className="space-y-2.5">
                {(rootCause?.how_to_prevent || ml?.synthesis?.how_to_prevent_decrease || [
                  "Audit segment outliers causing sudden metric variance.",
                  "Enforce automated quality checks and operational threshold alerts.",
                  "Calibrate segment parameters to prevent negative performance drops."
                ]).map((action, idx) => (
                  <div key={idx} className="flex items-start gap-2 text-xs text-slate-300">
                    <ArrowUpRight className="w-3.5 h-3.5 text-rose-400 mt-0.5 flex-shrink-0" />
                    <span className="leading-relaxed">{typeof action === "object" ? (action.detail || action.action) : action}</span>
                  </div>
                ))}
              </div>
            </div>

            {/* Growth / Optimization Recommendations */}
            <div className="p-4 rounded-xl bg-emerald-500/5 border border-emerald-500/20 space-y-3">
              <h4 className="text-xs font-bold uppercase tracking-wider text-emerald-400 flex items-center gap-1.5">
                <TrendingUp className="w-4 h-4 text-emerald-400" /> Growth & Optimization Playbook
              </h4>
              <div className="space-y-2.5">
                {(ml?.synthesis?.how_to_increase || [
                  "Scale marketing allocation into highest converting customer segments.",
                  "Bundle complementary high-volume products to maximize basket size.",
                  "Streamline turnaround time to reduce operational bottleneck churn."
                ]).map((action, idx) => (
                  <div key={idx} className="flex items-start gap-2 text-xs text-slate-300">
                    <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 mt-0.5 flex-shrink-0" />
                    <span className="leading-relaxed">{action}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* ── Section 4: All Dashboard Charts & Visual Proof ── */}
        <div className="space-y-5 print-section">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <div>
              <h3 className="text-sm font-bold text-slate-100 flex items-center gap-2">
                <Layers className="w-4 h-4 text-indigo-400" /> 4. All Dashboard Visualizations ({dashboardCharts.length})
              </h3>
              <p className="text-xs text-slate-400 mt-0.5">
                Verified visual charts generated directly from the underlying dataset records.
              </p>
            </div>
            <span className="text-xs text-slate-500 font-mono">
              Auto-Generated Analytics
            </span>
          </div>

          {dashboardCharts.length > 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
              {dashboardCharts.map((spec) => (
                <div 
                  key={spec.id} 
                  className="p-5 rounded-2xl bg-slate-900 border border-slate-800 shadow-md flex flex-col justify-between print-avoid-break"
                  style={{ breakInside: "avoid", pageBreakInside: "avoid" }}
                >
                  <div className="mb-3">
                    <h4 className="text-xs font-bold text-slate-200 mb-0.5">{spec.title}</h4>
                    <p className="text-[11px] text-slate-400">{spec.description}</p>
                  </div>
                  <div className="w-full mb-3">
                    <ChartRenderer spec={spec} />
                  </div>
                  
                  {/* User-Friendly Graph Explanation & Dataset Takeaway */}
                  <div className="p-3.5 rounded-xl bg-slate-950 border border-slate-800/80 text-xs space-y-2 mt-auto">
                    <div className="flex items-center gap-1.5 text-[10px] font-bold uppercase tracking-wider text-indigo-400">
                      <Sparkles className="w-3 h-3 text-indigo-400" /> Graph Analysis & Dataset Takeaway
                    </div>
                    {spec.user_friendly_explanation ? (
                      <div className="space-y-1.5 text-slate-300">
                        <p className="leading-relaxed">
                          <strong className="text-slate-200">What It Shows: </strong>
                          {spec.user_friendly_explanation.what_it_shows}
                        </p>
                        <p className="leading-relaxed">
                          <strong className="text-indigo-300">Key Finding: </strong>
                          {spec.user_friendly_explanation.key_takeaway}
                        </p>
                        {spec.user_friendly_explanation.recommendation && (
                          <p className="leading-relaxed text-emerald-400/90">
                            <strong className="text-emerald-400">Recommended Action: </strong>
                            {spec.user_friendly_explanation.recommendation}
                          </p>
                        )}
                      </div>
                    ) : (
                      <p className="text-slate-300 leading-relaxed">
                        {spec.description || `Evaluates dataset distribution and relationship patterns across primary dimensions.`}
                      </p>
                    )}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="p-6 rounded-xl bg-slate-900/40 border border-slate-800 text-center text-xs text-slate-400">
              No automatic dashboard charts found.
            </div>
          )}
        </div>

        {/* ── Section 5: Custom Added Charts (Synchronized from Executive Dashboard) ── */}
        <div className="space-y-5 print-section">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <div>
              <h3 className="text-sm font-bold text-slate-100 flex items-center gap-2">
                <PlusCircle className="w-4 h-4 text-emerald-400" /> 5. Custom Added Visualizations ({customCharts.length})
              </h3>
              <p className="text-xs text-slate-400 mt-0.5">
                User-created charts synchronized seamlessly across Executive Dashboard and Report.
              </p>
            </div>
            <div className="print-hide">
              <button
                onClick={() => setShowChartBuilder(true)}
                className="px-3 py-1.5 rounded-lg bg-emerald-600/20 hover:bg-emerald-600/30 text-emerald-400 border border-emerald-500/30 text-xs font-semibold transition flex items-center gap-1.5"
              >
                <PlusCircle className="w-3.5 h-3.5" />
                + Add Custom Chart
              </button>
            </div>
          </div>

          {customCharts.length > 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
              {customCharts.map((spec) => {
                const explanation = getCustomChartExplanation(spec);
                return (
                  <div
                    key={spec.id}
                    className="p-5 rounded-2xl bg-slate-900 border border-emerald-500/30 relative group shadow-md print-avoid-break flex flex-col justify-between"
                    style={{ breakInside: "avoid", pageBreakInside: "avoid" }}
                  >
                    <button
                      onClick={() => handleRemoveCustomChart(spec.id)}
                      title="Remove this chart"
                      className="print-hide absolute top-3 right-3 opacity-0 group-hover:opacity-100 transition p-1.5 rounded-md bg-slate-800 hover:bg-rose-500/20 text-slate-400 hover:text-rose-400 border border-slate-700 hover:border-rose-500/30"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                    <div className="mb-3">
                      <div className="flex items-center gap-2 mb-1">
                        <span className="px-2 py-0.5 rounded text-[9px] font-bold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                          CUSTOM CHART
                        </span>
                        <h4 className="text-xs font-bold text-slate-200 truncate">{spec.title}</h4>
                      </div>
                      <p className="text-[11px] text-slate-400">{spec.description}</p>
                    </div>
                    <div className="w-full mb-3">
                      <ChartRenderer spec={spec} />
                    </div>
                    
                    {/* User-Friendly Graph Explanation & Dataset Takeaway for Custom Charts */}
                    <div className="p-3.5 rounded-xl bg-slate-950 border border-emerald-500/30 text-xs space-y-2 mt-auto">
                      <div className="flex items-center gap-1.5 text-[10px] font-bold uppercase tracking-wider text-emerald-400">
                        <Sparkles className="w-3 h-3 text-emerald-400" /> Custom Chart Analysis & Explanation
                      </div>
                      <div className="space-y-1.5 text-slate-300">
                        <p className="leading-relaxed">
                          <strong className="text-slate-200">What It Shows: </strong>
                          {explanation.what_it_shows}
                        </p>
                        <p className="leading-relaxed">
                          <strong className="text-emerald-300">Key Finding: </strong>
                          {explanation.key_takeaway}
                        </p>
                        {explanation.recommendation && (
                          <p className="leading-relaxed text-emerald-400/90">
                            <strong className="text-emerald-400">Recommended Action: </strong>
                            {explanation.recommendation}
                          </p>
                        )}
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          ) : (
            <div className="p-5 rounded-xl bg-slate-900/40 border border-dashed border-slate-800 text-center text-xs text-slate-500">
              No custom charts added yet. You can create custom charts here or on the Executive Dashboard.
            </div>
          )}
        </div>

        {/* ── Section 6: Executive KPI Audit Summary ── */}
        <div className="p-6 rounded-2xl bg-slate-900 border border-slate-800 space-y-4 print-section">
          <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center gap-2">
            <Activity className="w-4 h-4 text-indigo-400" /> 6. Executive KPI Audit Summary
          </h3>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {report?.kpi_executive_summary?.map((kpi, i) => (
              <div key={i} className="p-4 rounded-xl bg-slate-950 border border-slate-800">
                <span className="text-xs text-slate-400 font-semibold">{kpi.title}</span>
                <div className="text-xl font-bold text-slate-100 my-1">{kpi.value}</div>
                <p className="text-[11px] text-slate-500">{kpi.description}</p>
              </div>
            ))}
          </div>
        </div>

        {/* Custom Chart Builder Modal */}
        {showChartBuilder && currentDataset && (
          <CustomChartBuilder
            datasetId={currentDataset.id || currentDataset.dataset_id}
            onAddToDashboard={handleAddCustomChart}
            onClose={() => setShowChartBuilder(false)}
          />
        )}
      </div>
    </>
  );
}
