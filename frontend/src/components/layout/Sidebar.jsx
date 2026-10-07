import React from "react";
import { NavLink } from "react-router-dom";
import { 
  LayoutDashboard, 
  UploadCloud, 
  Sparkles, 
  BarChart3, 
  AlertTriangle, 
  TrendingUp, 
  Users, 
  SearchCode, 
  Bot, 
  FileText,
  DatabaseZap
} from "lucide-react";

export default function Sidebar() {
  const navItems = [
    { section: "DATA PLATFORM" },
    { to: "/dashboard", label: "Executive Dashboard", icon: LayoutDashboard },
    { to: "/upload", label: "Upload & Ingestion", icon: UploadCloud },
    { to: "/data-prep", label: "Data Prep & Quality", icon: Sparkles },
    
    { section: "ANALYTICS & DISCOVERY" },
    { to: "/analytics", label: "Exploratory EDA", icon: BarChart3 },
    { to: "/anomalies", label: "Anomaly Radar", icon: AlertTriangle },
    { to: "/forecasting", label: "Predictive Forecast", icon: TrendingUp },
    
    { section: "BUSINESS INTELLIGENCE" },
    { to: "/customers", label: "Customer Intelligence", icon: Users },
    { to: "/root-cause", label: "Root Cause Studio", icon: SearchCode },
    { to: "/ai-analyst", label: "AI Data Analyst", icon: Bot, badge: "AI" },
    { to: "/reports", label: "Executive Reports", icon: FileText },
  ];

  return (
    <aside className="w-64 bg-slate-900 border-r border-slate-800 flex flex-col h-screen sticky top-0 select-none z-30 print:hidden print-hide">
      {/* Brand Header */}
      <div className="h-16 flex items-center px-6 gap-3 border-b border-slate-800">
        <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-indigo-600 via-indigo-500 to-purple-500 flex items-center justify-center shadow-lg shadow-indigo-500/20 text-white font-black">
          <DatabaseZap className="w-5 h-5" />
        </div>
        <div>
          <span className="font-extrabold text-lg tracking-tight bg-gradient-to-r from-white via-slate-200 to-indigo-300 bg-clip-text text-transparent">
            Insight<span className="text-indigo-400">X</span>
          </span>
          <p className="text-[10px] text-slate-400 font-medium tracking-wide">ENTERPRISE ANALYTICS</p>
        </div>
      </div>

      {/* Navigation List */}
      <div className="flex-1 overflow-y-auto px-3 py-4 space-y-1">
        {navItems.map((item, idx) => {
          if (item.section) {
            return (
              <div key={idx} className="px-3 pt-4 pb-1 text-[11px] font-semibold tracking-wider text-slate-400 uppercase">
                {item.section}
              </div>
            );
          }
          const Icon = item.icon;
          return (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) =>
                `flex items-center justify-between px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-150 ${
                  isActive
                    ? "bg-indigo-600/15 text-indigo-400 border border-indigo-500/30 shadow-sm"
                    : "text-slate-300 hover:text-white hover:bg-slate-800/60"
                }`
              }
            >
              <div className="flex items-center gap-3">
                <Icon className="w-4 h-4 flex-shrink-0" />
                <span>{item.label}</span>
              </div>
              {item.badge && (
                <span className="px-1.5 py-0.5 text-[10px] font-bold rounded-md bg-indigo-500/20 text-indigo-400 border border-indigo-500/30">
                  {item.badge}
                </span>
              )}
            </NavLink>
          );
        })}
      </div>

      {/* Footer System Status */}
      <div className="p-4 border-t border-slate-800 bg-slate-900/50">
        <div className="flex items-center gap-2 text-xs text-slate-400">
          <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
          <span>OLAP Engine: DuckDB Active</span>
        </div>
      </div>
    </aside>
  );
}
