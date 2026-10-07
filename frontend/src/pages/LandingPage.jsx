import React, { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useDataset } from "../context/DatasetContext";
import { 
  DatabaseZap, 
  ArrowRight, 
  CheckCircle2, 
  ShieldCheck, 
  Bot, 
  TrendingUp, 
  TrendingDown, 
  AlertTriangle,
  Play,
  UploadCloud,
  Layers,
  HeartPulse,
  ShoppingCart,
  Rocket,
  SearchCode
} from "lucide-react";

export default function LandingPage() {
  const { currentDataset, datasets, loadSampleDataset, loading } = useDataset();
  const navigate = useNavigate();
  const [activeStep, setActiveStep] = useState(0);

  // User always starts from the UI on landing; no auto-redirection hijacking.
  const handleStartDemo = async (key) => {
    await loadSampleDataset(key);
    navigate("/dashboard");
  };

  const flowSteps = [
    {
      id: 0,
      step: "1. INGESTION",
      title: "Upload & Detect",
      desc: "Instant file drag & drop with automated schema inference and column profiling.",
      color: "text-indigo-400",
      borderColor: "border-indigo-500",
      preview: {
        badge: "Auto-Profiled Schema",
        title: "Deterministic Ingestion Engine",
        instruction: "Step 1: Upload your raw CSV or multi-sheet Excel file. InsightX auto-identifies dates, numerical metrics, categories, and candidate target objectives.",
        actionLabel: "Upload Custom File",
        actionLink: "/upload"
      }
    },
    {
      id: 1,
      step: "2. CLEANING",
      title: "Clean & Audit",
      desc: "Smart missing-value imputation, duplicate removal, and quality audit scoring.",
      color: "text-emerald-400",
      borderColor: "border-emerald-500",
      preview: {
        badge: "Data Health Score: 96/100",
        title: "Non-Destructive Cleaning Pipeline",
        instruction: "Step 2: Automated data health scoring (0-100), duplicate deduplication, and outlier identification while preserving zero raw data loss.",
        actionLabel: "View Quality Audit",
        actionLink: "/upload"
      }
    },
    {
      id: 2,
      step: "3. ROOT CAUSE",
      title: "Explain Why Metrics Shift",
      desc: "Discovers why sales drop or disease rates increase using explainable ML drivers.",
      color: "text-amber-400",
      borderColor: "border-amber-500",
      preview: {
        badge: "Explainable Attribution",
        title: "Why, What & How to Prevent",
        instruction: "Step 3: Root Cause Studio evaluates key drivers with ML metrics (Accuracy, Precision, Recall, F1) to show exactly what caused the change and how to mitigate it.",
        actionLabel: "Open Root Cause Studio",
        actionLink: "/root-cause"
      }
    },
    {
      id: 3,
      step: "4. AI ANALYST",
      title: "Plain English Q&A",
      desc: "Ask any business question. Generates validated SQL queries and targeted charts.",
      color: "text-purple-400",
      borderColor: "border-purple-500",
      preview: {
        badge: "Read-Only DuckDB Engine",
        title: "Grounded AI Data Intelligence",
        instruction: "Step 4: Interrogate your numbers in natural language. Receive direct statistical answers with relevant charts only when requested.",
        actionLabel: "Chat with AI Analyst",
        actionLink: "/ai-analyst"
      }
    }
  ];

  return (
    <div className="h-screen max-h-screen bg-slate-950 text-slate-100 flex flex-col justify-between overflow-hidden">
      {/* Top Navbar - Sleek & Compact */}
      <header className="h-14 border-b border-slate-800/80 flex items-center justify-between px-6 md:px-10 max-w-7xl w-full mx-auto flex-shrink-0">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-tr from-indigo-600 via-indigo-500 to-purple-500 flex items-center justify-center shadow-md shadow-indigo-500/20 text-white font-black">
            <DatabaseZap className="w-4 h-4" />
          </div>
          <span className="font-extrabold text-base tracking-tight bg-gradient-to-r from-white to-slate-300 bg-clip-text text-transparent">
            Insight<span className="text-indigo-400">X</span>
          </span>
        </div>
        <div className="flex items-center gap-3">
          <Link
            to="/upload"
            className="px-3 py-1.5 rounded-lg bg-slate-900 hover:bg-slate-800 text-slate-300 text-xs font-semibold border border-slate-800 transition flex items-center gap-1.5"
          >
            <UploadCloud className="w-3.5 h-3.5" /> Upload File
          </Link>
          <Link
            to="/dashboard"
            className="px-3.5 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white font-bold text-xs transition shadow-md shadow-indigo-600/20 flex items-center gap-1.5"
          >
            Launch Platform <ArrowRight className="w-3.5 h-3.5" />
          </Link>
        </div>
      </header>

      {/* Main Content - Engineered for Perfect Fit (Zero Viewport Cut-off) */}
      <main className="max-w-5xl w-full mx-auto px-6 py-4 flex-1 flex flex-col justify-center space-y-5 min-h-0">
        {/* Hero Title & Subtitle */}
        <div className="text-center space-y-2">
          <h1 className="text-3xl md:text-4xl font-extrabold tracking-tight leading-tight">
            Don't just show what happened.{" "}
            <span className="bg-gradient-to-r from-indigo-400 via-purple-400 to-pink-400 bg-clip-text text-transparent">
              Discover why.
            </span>
          </h1>
          <p className="text-xs md:text-sm text-slate-400 leading-relaxed max-w-2xl mx-auto">
            InsightX turns spreadsheets into executive dashboards, pinpoints hidden root causes, and explains performance changes with interactive machine learning and AI.
          </p>
        </div>

        {/* Active Dataset Quick Resume (if user previously tested/uploaded a dataset) */}
        {currentDataset && (
          <div className="flex items-center justify-center">
            <div className="inline-flex items-center gap-3 px-3.5 py-1.5 rounded-xl bg-indigo-950/70 border border-indigo-500/30 text-xs shadow-md">
              <span className="text-slate-300 flex items-center gap-1.5">
                <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
                Active Dataset: <strong className="text-indigo-200">{currentDataset.name}</strong>
              </span>
              <Link
                to="/dashboard"
                className="px-3 py-1 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white font-bold text-xs transition flex items-center gap-1 shadow-sm"
              >
                Continue to Dashboard <ArrowRight className="w-3 h-3" />
              </Link>
            </div>
          </div>
        )}

        {/* 1-Click Interactive Scenario Launchers */}
        <div className="flex flex-col items-center gap-2">
          <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 flex items-center gap-1">
            <Play className="w-3 h-3 text-indigo-400 fill-indigo-400" />
            Select a Scenario to Explore:
          </span>
          <div className="flex flex-wrap items-center justify-center gap-2.5">
            <button
              onClick={() => handleStartDemo("ecommerce")}
              disabled={loading}
              className="px-3.5 py-2 rounded-xl bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-500 hover:to-purple-500 text-white font-bold text-xs shadow-md shadow-indigo-500/20 transition flex items-center gap-2 cursor-pointer"
            >
              <ShoppingCart className="w-3.5 h-3.5" />
              <span>E-Commerce Demo <span className="opacity-80 font-normal">(Why Sales Drop)</span></span>
            </button>
            <button
              onClick={() => handleStartDemo("healthcare")}
              disabled={loading}
              className="px-3.5 py-2 rounded-xl bg-slate-900 hover:bg-slate-800 text-rose-300 border border-rose-500/30 font-bold text-xs transition flex items-center gap-2 cursor-pointer"
            >
              <HeartPulse className="w-3.5 h-3.5 text-rose-400" />
              <span>Heart Clinical Demo <span className="opacity-80 font-normal">(Disease Drivers & Prevention)</span></span>
            </button>
            <button
              onClick={() => handleStartDemo("saas")}
              disabled={loading}
              className="px-3.5 py-2 rounded-xl bg-slate-900 hover:bg-slate-800 text-emerald-300 border border-emerald-500/30 font-bold text-xs transition flex items-center gap-2 cursor-pointer"
            >
              <Rocket className="w-3.5 h-3.5 text-emerald-400" />
              <span>SaaS Funnel Demo <span className="opacity-80 font-normal">(Churn Prevention)</span></span>
            </button>
            <Link
              to="/upload"
              className="px-3.5 py-2 rounded-xl bg-slate-900 hover:bg-slate-800 text-slate-300 border border-slate-700 font-semibold text-xs transition flex items-center gap-2"
            >
              <UploadCloud className="w-3.5 h-3.5 text-slate-400" />
              Upload Custom File
            </Link>
          </div>
        </div>

        {/* Interactive Platform Data Flow Section */}
        <div className="rounded-2xl bg-slate-900/90 border border-slate-800 p-4 shadow-xl space-y-3">
          <div className="flex items-center justify-between">
            <h3 className="text-[11px] font-bold text-indigo-400 uppercase tracking-wider flex items-center gap-1.5">
              <Layers className="w-3.5 h-3.5" /> Interactive Platform Workflow
            </h3>
            <span className="text-[10px] text-slate-400">Click any step to preview instruction</span>
          </div>

          {/* 4 Interactive Flow Cards */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-2.5">
            {flowSteps.map((step) => {
              const isSelected = activeStep === step.id;
              return (
                <button
                  key={step.id}
                  onClick={() => setActiveStep(step.id)}
                  className={`p-3 rounded-xl text-left transition-all duration-150 cursor-pointer ${
                    isSelected
                      ? `bg-slate-950 border-2 ${step.borderColor} shadow-md ring-1 ring-indigo-500/20`
                      : "bg-slate-950/60 border border-slate-800/80 hover:border-slate-700 opacity-80 hover:opacity-100"
                  }`}
                >
                  <div className="flex items-center justify-between mb-1">
                    <span className={`text-[10px] font-bold ${step.color}`}>{step.step}</span>
                    {isSelected && <span className="w-1.5 h-1.5 rounded-full bg-indigo-400"></span>}
                  </div>
                  <h4 className="text-xs font-bold text-slate-200 mb-0.5">{step.title}</h4>
                  <p className="text-[10px] text-slate-400 leading-snug">{step.desc}</p>
                </button>
              );
            })}
          </div>

          {/* Interactive Live Step Preview Card */}
          <div className="p-3.5 rounded-xl bg-slate-950 border border-slate-800 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <div className="space-y-1">
              <div className="flex items-center gap-2">
                <span className="px-2 py-0.5 rounded text-[9px] font-extrabold bg-indigo-500/15 text-indigo-300 border border-indigo-500/25">
                  {flowSteps[activeStep].preview.badge}
                </span>
                <h4 className="text-xs font-bold text-slate-200">
                  {flowSteps[activeStep].preview.title}
                </h4>
              </div>
              <p className="text-xs text-slate-300 leading-relaxed max-w-2xl">
                {flowSteps[activeStep].preview.instruction}
              </p>
            </div>
            <Link
              to={flowSteps[activeStep].preview.actionLink}
              className="px-3.5 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-bold border border-slate-700 transition flex items-center gap-1.5 flex-shrink-0 self-start sm:self-center"
            >
              <span>{flowSteps[activeStep].preview.actionLabel}</span>
              <ArrowRight className="w-3 h-3" />
            </Link>
          </div>
        </div>
      </main>

      {/* Footer - Compact */}
      <footer className="h-10 border-t border-slate-800/60 flex items-center justify-between px-6 md:px-10 max-w-7xl w-full mx-auto text-[11px] text-slate-500 flex-shrink-0">
        <span>InsightX Analytics Engine</span>
        <span>Deterministic BI & Root Cause AI</span>
      </footer>
    </div>
  );
}
