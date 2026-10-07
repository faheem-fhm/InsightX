import React from "react";
import { useDataset } from "../../context/DatasetContext";
import { useTheme } from "../../context/ThemeContext";
import { Database, Sun, Moon, Sparkles } from "lucide-react";

export default function Header() {
  const { datasets, currentDataset, selectDataset, loadSampleDataset, loading } = useDataset();
  const { theme, toggleTheme } = useTheme();

  return (
    <header className="h-16 bg-slate-900/80 backdrop-blur border-b border-slate-800 flex items-center justify-between px-8 sticky top-0 z-20 print:hidden print-hide">
      <div className="flex items-center gap-4">
        {/* Active Dataset Selector */}
        <div className="flex items-center gap-2 bg-slate-800/80 border border-slate-700/60 rounded-lg px-3 py-1.5">
          <Database className="w-4 h-4 text-indigo-400" />
          <select
            value={currentDataset?.id || ""}
            onChange={(e) => {
              const selected = datasets.find(d => d.id === e.target.value);
              if (selected) selectDataset(selected);
            }}
            className="bg-transparent text-sm font-medium text-slate-200 outline-none cursor-pointer pr-2"
          >
            {datasets.map(d => (
              <option key={d.id} value={d.id} className="bg-slate-900 text-slate-200">
                {d.name} ({d.row_count?.toLocaleString()} rows)
              </option>
            ))}
            {datasets.length === 0 && (
              <option value="">No dataset selected</option>
            )}
          </select>
        </div>

        {/* Quality pill badge */}
        {currentDataset?.quality_score && (
          <div className="hidden md:flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-emerald-500/10 border border-emerald-500/20 text-emerald-400">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400"></span>
            Data Quality: {currentDataset.quality_score}/100
          </div>
        )}
      </div>

      <div className="flex items-center gap-3">
        {/* Quick Sample Loaders */}
        <div className="hidden lg:flex items-center gap-2">
          <span className="text-xs text-slate-400 font-medium">Load Demo:</span>
          <button
            onClick={() => loadSampleDataset("ecommerce")}
            disabled={loading}
            className="px-2.5 py-1 text-xs font-medium rounded-md bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 transition"
          >
            E-Commerce
          </button>
          <button
            onClick={() => loadSampleDataset("saas")}
            disabled={loading}
            className="px-2.5 py-1 text-xs font-medium rounded-md bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 transition"
          >
            SaaS Funnel
          </button>
          <button
            onClick={() => loadSampleDataset("healthcare")}
            disabled={loading}
            className="px-2.5 py-1 text-xs font-medium rounded-md bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 transition"
          >
            Healthcare
          </button>
        </div>

        {/* Theme Toggle */}
        <button
          onClick={toggleTheme}
          className="w-9 h-9 flex items-center justify-center rounded-lg bg-slate-800 hover:bg-slate-700 border border-slate-700 text-slate-300 transition"
          title="Toggle light/dark mode"
        >
          {theme === "dark" ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4 text-slate-800" />}
        </button>
      </div>
    </header>
  );
}
