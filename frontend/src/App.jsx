import React from "react";
import { BrowserRouter, Routes, Route, Navigate, Outlet } from "react-router-dom";
import { DatasetProvider } from "./context/DatasetContext";
import { ThemeProvider } from "./context/ThemeContext";

import Sidebar from "./components/layout/Sidebar";
import Header from "./components/layout/Header";

import LandingPage from "./pages/LandingPage";
import UploadPage from "./pages/UploadPage";
import DataPrepPage from "./pages/DataPrepPage";
import DashboardPage from "./pages/DashboardPage";
import AnalyticsEDAPage from "./pages/AnalyticsEDAPage";
import AnomalyPage from "./pages/AnomalyPage";
import ForecastingPage from "./pages/ForecastingPage";
import CustomerIntelPage from "./pages/CustomerIntelPage";
import RootCausePage from "./pages/RootCausePage";
import AIAnalystPage from "./pages/AIAnalystPage";
import ReportsPage from "./pages/ReportsPage";

function AppLayout() {
  return (
    <div className="flex h-screen overflow-hidden bg-slate-50 dark:bg-slate-950 text-slate-900 dark:text-slate-100 transition-colors duration-200">
      <Sidebar />
      <div className="flex-1 flex flex-col min-w-0 overflow-y-auto">
        <Header />
        <main className="flex-1 pb-16">
          <Outlet />
        </main>
      </div>
    </div>
  );
}

export default function App() {
  return (
    <ThemeProvider>
      <DatasetProvider>
        <BrowserRouter>
          <Routes>
            <Route path="/" element={<LandingPage />} />
            <Route element={<AppLayout />}>
              <Route path="/dashboard" element={<DashboardPage />} />
              <Route path="/upload" element={<UploadPage />} />
              <Route path="/data-prep" element={<DataPrepPage />} />
              <Route path="/analytics" element={<AnalyticsEDAPage />} />
              <Route path="/anomalies" element={<AnomalyPage />} />
              <Route path="/forecasting" element={<ForecastingPage />} />
              <Route path="/customers" element={<CustomerIntelPage />} />
              <Route path="/root-cause" element={<RootCausePage />} />
              <Route path="/ai-analyst" element={<AIAnalystPage />} />
              <Route path="/reports" element={<ReportsPage />} />
            </Route>
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </BrowserRouter>
      </DatasetProvider>
    </ThemeProvider>
  );
}
