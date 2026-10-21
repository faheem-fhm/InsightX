import React from "react";
import { useDataset } from "../../context/DatasetContext";
import { useTheme } from "../../context/ThemeContext";
import { Database, Sun, Moon, Menu, X, DatabaseZap } from "lucide-react";

export default function Header({ mobileMenuOpen, setMobileMenuOpen }) {
  const { datasets, currentDataset, selectDataset, loadSampleDataset, loading } = useDataset();
  const { theme, toggleTheme } = useTheme();

  return (
    <header className="h-16 glass-panel border-b border-white/10 flex items-center justify-between px-4 sm:px-6 lg:px-8 sticky top-0 z-20 print:hidden flex-shrink-0">
      <div className="flex items-center gap-3">
        {/* Mobile Hamburger Button */}
        {setMobileMenuOpen && (
          <button
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            className="md:hidden p-2 rounded-xl glass-btn text-slate-300 hover:text-white"
            aria-label="Toggle navigation menu"
          >
            {mobileMenuOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
          </button>
        )}

        {/* Mobile Brand Logo */}
        <div className="flex md:hidden items-center gap-2">
          <div className="w-7 h-7 rounded-lg bg-gradient-to-tr from-[#00F2FE] via-[#6366F1] to-[#9B51E0] flex items-center justify-center text-[#070B19] font-bold">
            <DatabaseZap className="w-4 h-4 text-[#070B19]" />
          </div>
          <span className="font-extrabold text-sm tracking-tight">
            <span className="text-[#00F2FE]">Insight</span>
            <span className="text-[#9B51E0]">X</span>
          </span>
        </div>

        {/* Active Dataset Selector */}
        <div className="flex items-center gap-2 glass-input rounded-xl px-3 py-1.5 max-w-[200px] sm:max-w-xs md:max-w-sm">
          <Database className="w-4 h-4 text-[#00F2FE] flex-shrink-0" />
          <select
            value={currentDataset?.id || ""}
            onChange={(e) => {
              const selected = datasets.find(d => d.id === e.target.value);
              if (selected) selectDataset(selected);
            }}
            className="bg-transparent text-xs sm:text-sm font-medium text-slate-200 outline-none cursor-pointer pr-1 w-full truncate"
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

        {/* Quality score pill */}
        {currentDataset?.quality_score && (
          <div className="hidden lg:flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-emerald-500/10 border border-emerald-500/25 text-emerald-400 shadow-sm backdrop-blur-md">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span>
            Data Quality: {currentDataset.quality_score}/100
          </div>
        )}
      </div>

      <div className="flex items-center gap-2 sm:gap-3">
        {/* Quick Sample Loaders */}
        <div className="hidden xl:flex items-center gap-2">
          <span className="text-xs text-slate-400 font-medium">Demo:</span>
          <button
            onClick={() => loadSampleDataset("ecommerce")}
            disabled={loading}
            className="px-2.5 py-1 text-xs font-medium rounded-lg glass-btn text-slate-300 hover:text-white"
          >
            E-Commerce
          </button>
          <button
            onClick={() => loadSampleDataset("saas")}
            disabled={loading}
            className="px-2.5 py-1 text-xs font-medium rounded-lg glass-btn text-slate-300 hover:text-white"
          >
            SaaS Funnel
          </button>
          <button
            onClick={() => loadSampleDataset("healthcare")}
            disabled={loading}
            className="px-2.5 py-1 text-xs font-medium rounded-lg glass-btn text-slate-300 hover:text-white"
          >
            Healthcare
          </button>
        </div>

        {/* Theme Toggle */}
        <button
          onClick={toggleTheme}
          className="w-9 h-9 flex items-center justify-center rounded-xl glass-btn text-slate-300 hover:text-white"
          title="Toggle light/dark mode"
        >
          {theme === "dark" ? <Sun className="w-4 h-4 text-amber-300" /> : <Moon className="w-4 h-4 text-slate-700" />}
        </button>
      </div>
    </header>
  );
}
