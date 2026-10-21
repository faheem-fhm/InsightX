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
  DatabaseZap,
  X
} from "lucide-react";

export default function Sidebar({ mobileMenuOpen, setMobileMenuOpen }) {
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
    { to: "/ai-analyst", label: "Data Analyst Studio", icon: Bot },
    { to: "/reports", label: "Executive Reports", icon: FileText },
  ];

  const handleNavClick = () => {
    if (setMobileMenuOpen) {
      setMobileMenuOpen(false);
    }
  };

  const navContent = (
    <div className="flex flex-col h-full select-none">
      {/* Brand Header */}
      <div className="h-16 flex items-center justify-between px-6 border-b border-white/10 flex-shrink-0">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-[#00F2FE] via-[#6366F1] to-[#9B51E0] flex items-center justify-center shadow-lg shadow-[#00F2FE]/20 text-[#070B19] font-black">
            <DatabaseZap className="w-5 h-5 text-[#070B19]" />
          </div>
          <div>
            <span className="font-extrabold text-lg tracking-tight">
              <span className="text-[#00F2FE]">Insight</span>
              <span className="text-[#9B51E0]">X</span>
            </span>
            <p className="text-[10px] text-[#A5B4FC]/70 font-medium tracking-wider uppercase">Enterprise Analytics</p>
          </div>
        </div>
        {/* Mobile Close Button */}
        {setMobileMenuOpen && (
          <button
            onClick={() => setMobileMenuOpen(false)}
            className="md:hidden p-1.5 rounded-lg text-[#A5B4FC] hover:text-white hover:bg-white/10 transition"
            aria-label="Close menu"
          >
            <X className="w-5 h-5" />
          </button>
        )}
      </div>

      {/* Navigation List */}
      <div className="flex-1 overflow-y-auto px-3 py-4 space-y-1">
        {navItems.map((item, idx) => {
          if (item.section) {
            return (
              <div key={idx} className="px-3 pt-4 pb-1 text-[10px] font-bold tracking-wider text-[#A5B4FC]/60 uppercase">
                {item.section}
              </div>
            );
          }
          const Icon = item.icon;
          return (
            <NavLink
              key={item.to}
              to={item.to}
              onClick={handleNavClick}
              className={({ isActive }) =>
                `flex items-center justify-between px-3 py-2.5 rounded-xl text-sm font-medium transition-all duration-200 ${
                  isActive
                    ? "bg-[#00F2FE]/15 text-[#00F2FE] border border-[#00F2FE]/30 shadow-sm backdrop-blur-md font-semibold"
                    : "text-[#A5B4FC] hover:text-white hover:bg-white/[0.06] border border-transparent"
                }`
              }
            >
              <div className="flex items-center gap-3">
                <Icon className="w-4 h-4 flex-shrink-0" />
                <span>{item.label}</span>
              </div>
            </NavLink>
          );
        })}
      </div>

      {/* Footer System Status */}
      <div className="p-4 border-t border-white/10 bg-black/20 flex-shrink-0">
        <div className="flex items-center gap-2 text-xs text-slate-400">
          <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse shadow-sm shadow-emerald-400/50"></span>
          <span className="font-mono text-[11px]">OLAP Engine: DuckDB Active</span>
        </div>
      </div>
    </div>
  );

  return (
    <>
      {/* Desktop Static Glass Sidebar */}
      <aside className="hidden md:flex w-64 glass-panel border-r border-white/10 flex-col h-screen sticky top-0 z-30 print:hidden flex-shrink-0">
        {navContent}
      </aside>

      {/* Mobile Drawer Overlay */}
      {mobileMenuOpen && (
        <div 
          className="fixed inset-0 bg-black/70 backdrop-blur-md z-40 md:hidden animate-in fade-in duration-200"
          onClick={() => setMobileMenuOpen(false)}
        />
      )}

      {/* Mobile Slide-over Glass Drawer */}
      <aside 
        className={`fixed inset-y-0 left-0 w-72 glass-panel border-r border-white/15 z-50 md:hidden shadow-2xl transition-transform duration-300 ease-in-out ${
          mobileMenuOpen ? "translate-x-0" : "-translate-x-full"
        }`}
      >
        {navContent}
      </aside>
    </>
  );
}
