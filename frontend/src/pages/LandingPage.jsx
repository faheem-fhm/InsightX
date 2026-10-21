import React, { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useDataset } from "../context/DatasetContext";
import { 
  DatabaseZap, 
  ArrowRight, 
  CheckCircle2, 
  ShieldCheck, 
  TrendingUp, 
  TrendingDown, 
  AlertTriangle,
  Play,
  UploadCloud,
  Layers,
  HeartPulse,
  ShoppingCart,
  Rocket,
  SearchCode,
  Activity,
  Sparkles
} from "lucide-react";

export default function LandingPage() {
  const { currentDataset, loadSampleDataset, loading } = useDataset();
  const navigate = useNavigate();
  const [activeStep, setActiveStep] = useState(0);

  const handleStartDemo = async (key) => {
    await loadSampleDataset(key);
    navigate("/dashboard");
  };

  const flowSteps = [
    {
      id: 0,
      step: "01. INGESTION",
      title: "Deterministic Ingestion",
      desc: "Fast drag & drop file profiling with automated schema typing and data quality scoring.",
      color: "text-indigo-400",
      borderColor: "border-indigo-500/60",
      badgeColor: "bg-indigo-500/15 text-indigo-300 border-indigo-500/30",
      preview: {
        badge: "Verified Schema Profiler",
        title: "Automated Ingestion Pipeline",
        instruction: "Step 1: Upload raw CSV or multi-sheet Excel files. The engine profiles data types, timestamps, numeric distributions, and automatically isolates primary business drivers.",
        actionLabel: "Upload Custom File",
        actionLink: "/upload"
      }
    },
    {
      id: 1,
      step: "02. CLEANING",
      title: "Quality Audit & Cleaning",
      desc: "Deterministic imputation, deduplication, and health scoring with zero raw data loss.",
      color: "text-emerald-400",
      borderColor: "border-emerald-500/60",
      badgeColor: "bg-emerald-500/15 text-emerald-300 border-emerald-500/30",
      preview: {
        badge: "Data Health Score: 98/100",
        title: "Non-Destructive Cleaning Engine",
        instruction: "Step 2: Inspect missing values, anomalies, and schema distributions with automated audit scoring (0-100) while keeping all raw historical rows intact.",
        actionLabel: "View Quality Audit",
        actionLink: "/upload"
      }
    },
    {
      id: 2,
      step: "03. ROOT CAUSE",
      title: "Root Cause Investigation",
      desc: "Statistically discover what happened, why metrics dropped, and exact mitigation actions.",
      color: "text-amber-400",
      borderColor: "border-amber-500/60",
      badgeColor: "bg-amber-500/15 text-amber-300 border-amber-500/30",
      preview: {
        badge: "Explainable Attribution",
        title: "Causal Driver Discovery",
        instruction: "Step 3: Root Cause Studio evaluates key drivers with verified statistical metrics (Accuracy, Precision, Recall, F1) to isolate performance bottlenecks and mitigation steps.",
        actionLabel: "Open Root Cause Studio",
        actionLink: "/root-cause"
      }
    },
    {
      id: 3,
      step: "04. ANALYST STUDIO",
      title: "Natural Language Analyst",
      desc: "Interrogate data in plain English with in-memory DuckDB queries and targeted charts.",
      color: "text-purple-400",
      borderColor: "border-purple-500/60",
      badgeColor: "bg-purple-500/15 text-purple-300 border-purple-500/30",
      preview: {
        badge: "Grounded In-Memory OLAP",
        title: "Direct Data Intelligence",
        instruction: "Step 4: Ask business questions and receive verified calculations derived strictly from your dataset records, generating visual charts whenever requested.",
        actionLabel: "Open Analyst Studio",
        actionLink: "/ai-analyst"
      }
    }
  ];

  return (
    <div className="min-h-screen text-slate-100 flex flex-col justify-between overflow-x-hidden">
      {/* Top Glass Navbar */}
      <header className="h-16 glass-panel border-b border-white/10 sticky top-0 z-30 w-full">
        <div className="max-w-7xl mx-auto h-full flex items-center justify-between px-4 sm:px-6 lg:px-8">
          <div className="flex items-center gap-2.5">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-[#00F2FE] via-[#6366F1] to-[#9B51E0] flex items-center justify-center shadow-lg shadow-[#00F2FE]/25 text-[#070B19] font-black">
              <DatabaseZap className="w-5 h-5 text-[#070B19]" />
            </div>
            <div>
              <span className="font-extrabold text-lg tracking-tight">
                <span className="text-[#00F2FE]">Insight</span>
                <span className="text-[#9B51E0]">X</span>
              </span>
            </div>
          </div>

          <div className="flex items-center gap-2.5 sm:gap-3">
            <Link
              to="/upload"
              className="px-3.5 py-2 rounded-xl glass-btn text-[#A5B4FC] hover:text-white text-xs font-semibold flex items-center gap-1.5"
            >
              <UploadCloud className="w-3.5 h-3.5 text-[#00F2FE]" />
              <span>Upload Dataset</span>
            </Link>
            <Link
              to="/dashboard"
              className="px-4 py-2 rounded-xl glass-btn-primary font-bold text-xs flex items-center gap-1.5"
            >
              <span>Launch Studio</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          </div>
        </div>
      </header>

      {/* Main Hero & Interactive Flow */}
      <main className="max-w-6xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8 md:py-12 flex-1 flex flex-col justify-center space-y-8">
        {/* Hero Section */}
        <div className="text-center space-y-3 max-w-3xl mx-auto">
          <div className="inline-flex items-center gap-2 px-3.5 py-1 rounded-full glass-card border border-[#00F2FE]/30 text-[11px] font-semibold text-[#00F2FE] mb-2 shadow-sm shadow-[#00F2FE]/10">
            <Activity className="w-3 h-3 text-[#00F2FE] animate-pulse" />
            Next-Gen Enterprise Analytics & Root Cause Engine
          </div>
          <h1 className="text-3xl sm:text-4xl md:text-5xl font-extrabold tracking-tight leading-tight text-white">
            Don't just show what happened.{" "}
            <span className="bg-gradient-to-r from-[#00F2FE] via-[#A5B4FC] to-[#9B51E0] bg-clip-text text-transparent">
              Discover why.
            </span>
          </h1>
          <p className="text-sm sm:text-base text-slate-400 leading-relaxed max-w-2xl mx-auto">
            InsightX turns multi-sheet spreadsheets and raw tables into executive intelligence, isolates causal drivers, and produces verified analytical insights with in-memory DuckDB OLAP.
          </p>
        </div>

        {/* Active Dataset Quick Resume Banner */}
        {currentDataset && (
          <div className="flex items-center justify-center">
            <div className="glass-card inline-flex items-center gap-3 px-4 py-2 rounded-2xl border border-indigo-500/30 text-xs shadow-xl">
              <span className="text-slate-300 flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
                Active Dataset: <strong className="text-indigo-200">{currentDataset.name}</strong>
              </span>
              <Link
                to="/dashboard"
                className="px-3 py-1.5 rounded-xl glass-btn-primary text-white font-bold text-xs flex items-center gap-1"
              >
                Go to Dashboard <ArrowRight className="w-3 h-3" />
              </Link>
            </div>
          </div>
        )}

        {/* Interactive Scenario Launchers */}
        <div className="space-y-3">
          <div className="flex items-center justify-center gap-1 text-[11px] font-bold uppercase tracking-wider text-slate-400">
            <Play className="w-3.5 h-3.5 text-indigo-400 fill-indigo-400" />
            Instant Interactive Demo Scenarios
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
            <button
              onClick={() => handleStartDemo("ecommerce")}
              disabled={loading}
              className="p-4 rounded-2xl glass-card text-left group hover:border-indigo-500/50"
            >
              <div className="w-8 h-8 rounded-xl bg-indigo-500/20 text-indigo-400 flex items-center justify-center mb-2.5">
                <ShoppingCart className="w-4 h-4" />
              </div>
              <h4 className="text-sm font-bold text-slate-100 group-hover:text-indigo-300 transition">E-Commerce Intelligence</h4>
              <p className="text-[11px] text-slate-400 mt-1">4,582 orders with South shipping bottleneck.</p>
            </button>

            <button
              onClick={() => handleStartDemo("healthcare")}
              disabled={loading}
              className="p-4 rounded-2xl glass-card text-left group hover:border-rose-500/50"
            >
              <div className="w-8 h-8 rounded-xl bg-rose-500/20 text-rose-400 flex items-center justify-center mb-2.5">
                <HeartPulse className="w-4 h-4" />
              </div>
              <h4 className="text-sm font-bold text-slate-100 group-hover:text-rose-300 transition">Heart Clinical Discovery</h4>
              <p className="text-[11px] text-slate-400 mt-1">Disease attribution and triage optimization.</p>
            </button>

            <button
              onClick={() => handleStartDemo("saas")}
              disabled={loading}
              className="p-4 rounded-2xl glass-card text-left group hover:border-emerald-500/50"
            >
              <div className="w-8 h-8 rounded-xl bg-emerald-500/20 text-emerald-400 flex items-center justify-center mb-2.5">
                <Rocket className="w-4 h-4" />
              </div>
              <h4 className="text-sm font-bold text-slate-100 group-hover:text-emerald-300 transition">SaaS Funnel Analytics</h4>
              <p className="text-[11px] text-slate-400 mt-1">Acquisition drop-off & retention drivers.</p>
            </button>

            <Link
              to="/upload"
              className="p-4 rounded-2xl glass-card text-left group hover:border-purple-500/50 flex flex-col justify-between"
            >
              <div>
                <div className="w-8 h-8 rounded-xl bg-purple-500/20 text-purple-400 flex items-center justify-center mb-2.5">
                  <UploadCloud className="w-4 h-4" />
                </div>
                <h4 className="text-sm font-bold text-slate-100 group-hover:text-purple-300 transition">Upload Custom File</h4>
                <p className="text-[11px] text-slate-400 mt-1">Drop CSV or multi-sheet Excel directly.</p>
              </div>
            </Link>
          </div>
        </div>

        {/* Interactive Platform Flow Section */}
        <div className="glass-panel rounded-3xl p-5 sm:p-7 space-y-4 shadow-2xl">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-white/10 pb-3">
            <h3 className="text-xs font-bold text-indigo-400 uppercase tracking-wider flex items-center gap-2">
              <Layers className="w-4 h-4" /> End-to-End Enterprise Data Flow
            </h3>
            <span className="text-[11px] text-slate-400">Click any step to inspect technical pipeline</span>
          </div>

          {/* 4 Interactive Flow Cards */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
            {flowSteps.map((step) => {
              const isSelected = activeStep === step.id;
              return (
                <button
                  key={step.id}
                  onClick={() => setActiveStep(step.id)}
                  className={`p-4 rounded-2xl text-left transition-all duration-200 cursor-pointer ${
                    isSelected
                      ? `glass-panel border-2 ${step.borderColor} shadow-lg ring-1 ring-white/15 scale-[1.02]`
                      : "glass-card opacity-75 hover:opacity-100"
                  }`}
                >
                  <div className="flex items-center justify-between mb-1.5">
                    <span className={`text-[10px] font-extrabold ${step.color}`}>{step.step}</span>
                    {isSelected && <span className="w-2 h-2 rounded-full bg-indigo-400 animate-pulse"></span>}
                  </div>
                  <h4 className="text-xs font-bold text-slate-100 mb-1">{step.title}</h4>
                  <p className="text-[11px] text-slate-400 leading-snug">{step.desc}</p>
                </button>
              );
            })}
          </div>

          {/* Live Pipeline Preview Card */}
          <div className="p-4 sm:p-5 rounded-2xl glass-card border border-white/10 flex flex-col md:flex-row md:items-center justify-between gap-4">
            <div className="space-y-1.5">
              <div className="flex items-center gap-2 flex-wrap">
                <span className={`px-2.5 py-0.5 rounded-full text-[10px] font-bold border ${flowSteps[activeStep].badgeColor}`}>
                  {flowSteps[activeStep].preview.badge}
                </span>
                <h4 className="text-sm font-bold text-slate-100">
                  {flowSteps[activeStep].preview.title}
                </h4>
              </div>
              <p className="text-xs sm:text-sm text-slate-300 leading-relaxed max-w-3xl">
                {flowSteps[activeStep].preview.instruction}
              </p>
            </div>
            <Link
              to={flowSteps[activeStep].preview.actionLink}
              className="px-4 py-2 rounded-xl glass-btn text-white text-xs font-bold flex items-center gap-1.5 flex-shrink-0 self-start md:self-center hover:scale-105 transition"
            >
              <span>{flowSteps[activeStep].preview.actionLabel}</span>
              <ArrowRight className="w-3.5 h-3.5 text-indigo-400" />
            </Link>
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="h-14 glass-panel border-t border-white/10 flex items-center justify-between px-4 sm:px-6 lg:px-8 text-xs text-slate-400 flex-shrink-0">
        <span className="font-medium">InsightX Enterprise Platform</span>
        <span className="font-mono text-[11px] text-slate-500">Deterministic In-Memory OLAP</span>
      </footer>
    </div>
  );
}
