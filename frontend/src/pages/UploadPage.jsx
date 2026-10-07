import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useDataset } from "../context/DatasetContext";
import { datasetApi } from "../services/api";
import { 
  UploadCloud, 
  FileSpreadsheet, 
  CheckCircle2, 
  AlertCircle, 
  ArrowRight, 
  Sparkles, 
  Play,
  FileText,
  Layers,
  Database,
  Check,
  Trash2,
  Target,
  ExternalLink
} from "lucide-react";

export default function UploadPage() {
  const [file, setFile] = useState(null);
  const [sheetName, setSheetName] = useState("");
  const [targetColumn, setTargetColumn] = useState("");
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState(null);
  const [deletingId, setDeletingId] = useState(null);
  const { datasets, currentDataset, fetchDatasets, selectDataset, loadSampleDataset, deleteDataset, loading } = useDataset();
  const navigate = useNavigate();

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
      setError(null);
    }
  };

  const handleUpload = async () => {
    if (!file) return;
    setUploading(true);
    setError(null);
    try {
      const formData = new FormData();
      formData.append("file", file);
      if (sheetName) {
        formData.append("sheet_name", sheetName);
      }
      if (targetColumn) {
        formData.append("target_column", targetColumn);
      }
      const res = await datasetApi.upload(formData);
      await fetchDatasets();
      const datasetObj = {
        ...res.data,
        id: res.data.id || res.data.dataset_id
      };
      selectDataset(datasetObj);
      setFile(null);
      setTargetColumn("");
      setSheetName("");
      navigate("/dashboard");
    } catch (err) {
      console.error("Upload error:", err);
      const msg = err.response?.data?.message || err.response?.data?.detail || err.message || "Upload failed";
      setError(msg);
    } finally {
      setUploading(false);
    }
  };

  const handleDelete = async (datasetId, e) => {
    if (e) e.stopPropagation();
    if (!window.confirm("Are you sure you want to remove this dataset? This will delete all associated reports, profiles, and queries.")) {
      return;
    }
    setDeletingId(datasetId);
    try {
      await deleteDataset(datasetId);
    } catch (err) {
      console.error("Failed to remove dataset:", err);
      alert("Failed to delete dataset. Please try again.");
    } finally {
      setDeletingId(null);
    }
  };

  const handleSelectSample = async (key) => {
    setError(null);
    try {
      const sample = await loadSampleDataset(key);
      if (sample) {
        navigate("/dashboard");
      }
    } catch (err) {
      console.error("Sample error:", err);
      const msg = err.response?.data?.message || err.response?.data?.detail || err.message || "Failed to load sample dataset";
      setError(msg);
    }
  };

  const sampleDatasets = [
    {
      key: "ecommerce",
      badge: "HIDDEN ROOT CAUSE",
      badgeColor: "bg-indigo-500/10 text-indigo-400 border-indigo-500/20",
      title: "E-Commerce Logistics & Sales",
      records: "4,582 orders",
      description: "Hidden delivery bottlenecks in South region drive complaints, cancellations, and a 49% revenue drop.",
      xlsxFile: "ecommerce_sales_with_hidden_root_cause.xlsx",
      csvFile: "ecommerce_sales_with_hidden_root_cause.csv",
      sheets: ["Orders", "Product_Catalog", "Shipping_Carriers"]
    },
    {
      key: "saas",
      badge: "MARKETING FUNNEL",
      badgeColor: "bg-purple-500/10 text-purple-400 border-purple-500/20",
      title: "B2B SaaS Growth Funnel",
      records: "600 campaign days",
      description: "Spend, impressions, CTR, leads, conversions, and ROI across 5 channels.",
      xlsxFile: "saas_marketing_funnel.xlsx",
      csvFile: "saas_marketing_funnel.csv",
      sheets: ["Campaign_Performance", "Channel_Targets"]
    },
    {
      key: "healthcare",
      badge: "CLINICAL FLOW",
      badgeColor: "bg-emerald-500/10 text-emerald-400 border-emerald-500/20",
      title: "Hospital Patient Flow",
      records: "2,428 admissions",
      description: "Emergency triage, wait times, length of stay, procedure costs, and readmissions.",
      xlsxFile: "healthcare_patient_flow.xlsx",
      csvFile: "healthcare_patient_flow.csv",
      sheets: ["Admissions", "Departments"]
    }
  ];

  const handleDownloadSample = (fileName) => {
    window.open(`/api/v1/datasets/sample/download/${fileName}`, "_blank");
  };

  return (
    <div className="p-8 max-w-6xl mx-auto space-y-8">
      <div>
        <h1 className="text-2xl font-extrabold tracking-tight">Dataset Ingestion Hub</h1>
        <p className="text-sm text-slate-400">
          Upload raw messy spreadsheets (Excel XLSX, CSV, Parquet, JSON) or explore pre-calibrated business datasets.
        </p>
      </div>

      {/* ── 1. ACTIVE & UPLOADED DATASET (PROMINENT TOP VIEW) ── */}
      {currentDataset && (
        <div className="p-6 rounded-2xl bg-gradient-to-r from-indigo-950/40 to-slate-900 border-2 border-indigo-500/40 shadow-xl space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <div className="flex items-center gap-2">
              <span className="px-2.5 py-1 rounded-full text-[10px] font-extrabold bg-indigo-500/20 text-indigo-400 border border-indigo-500/30 flex items-center gap-1.5">
                <CheckCircle2 className="w-3.5 h-3.5 text-indigo-400" /> ACTIVE DATASET
              </span>
              <span className="text-xs text-slate-400">
                {currentDataset.file_format?.toUpperCase()} · {currentDataset.row_count?.toLocaleString()} rows
              </span>
            </div>
            <div className="flex items-center gap-2">
              <button
                onClick={() => navigate("/dashboard")}
                className="px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white font-bold text-xs shadow-md shadow-indigo-600/20 transition flex items-center gap-1.5"
              >
                Explore Dashboard
                <ArrowRight className="w-3.5 h-3.5" />
              </button>
              <button
                onClick={(e) => handleDelete(currentDataset.id || currentDataset.dataset_id, e)}
                disabled={deletingId === (currentDataset.id || currentDataset.dataset_id)}
                className="px-3.5 py-2 rounded-lg bg-rose-500/10 hover:bg-rose-500/20 text-rose-400 border border-rose-500/30 text-xs font-semibold transition flex items-center gap-1.5"
                title="Remove this dataset"
              >
                <Trash2 className="w-3.5 h-3.5" />
                {deletingId === (currentDataset.id || currentDataset.dataset_id) ? "Removing..." : "Remove Dataset"}
              </button>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pt-2 border-t border-slate-800">
            <div>
              <span className="text-[11px] font-semibold text-slate-400 block mb-0.5">Dataset Name</span>
              <h3 className="text-base font-bold text-slate-100 truncate">{currentDataset.name}</h3>
            </div>
            <div>
              <span className="text-[11px] font-semibold text-slate-400 block mb-0.5">Target Column (ML Objective)</span>
              <div className="flex items-center gap-1.5">
                <Target className="w-4 h-4 text-indigo-400 flex-shrink-0" />
                <span className="text-sm font-bold text-indigo-300">
                  {currentDataset.target_column ? currentDataset.target_column.replace(/_/g, " ") : "Auto-detected by ML Engine"}
                </span>
              </div>
            </div>
            <div>
              <span className="text-[11px] font-semibold text-slate-400 block mb-0.5">Domain Context</span>
              <span className="text-sm font-medium text-slate-300 capitalize">{currentDataset.domain_type || "Generic Business"}</span>
            </div>
          </div>
        </div>
      )}

      {/* ── 2. NEW DATASET BROWSER & UPLOAD SECTION ── */}
      <div className="border-2 border-dashed border-slate-700 hover:border-indigo-500/80 bg-slate-900/50 rounded-2xl p-10 text-center transition">
        <UploadCloud className="w-12 h-12 text-indigo-400 mx-auto mb-4 animate-bounce" />
        <h3 className="text-base font-bold text-slate-200 mb-1">
          {file ? file.name : "Drag & drop your new dataset here"}
        </h3>
        <p className="text-xs text-slate-400 mb-6">Supports CSV, XLSX, XLS, JSON, and Parquet (up to 50MB)</p>

        <input
          type="file"
          id="fileUpload"
          className="hidden"
          accept=".csv,.xlsx,.xls,.json,.parquet"
          onChange={handleFileChange}
        />
        <label
          htmlFor="fileUpload"
          className="inline-block px-5 py-2.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 font-semibold text-xs border border-slate-700 cursor-pointer transition"
        >
          {file ? "Choose Another File" : "Browse Files for Upload"}
        </label>

        {/* Excel Sheet Option if XLSX selected */}
        {file && file.name.match(/\.xlsx?$/i) && (
          <div className="mt-4 max-w-xs mx-auto">
            <label className="block text-xs font-semibold text-slate-400 mb-1">Target Excel Sheet Name (Optional):</label>
            <input
              type="text"
              placeholder="e.g. Orders, Sheet1"
              value={sheetName}
              onChange={(e) => setSheetName(e.target.value)}
              className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-1.5 text-xs text-slate-200 outline-none text-center"
            />
          </div>
        )}

        {/* Target Column Option (Optional) */}
        {file && (
          <div className="mt-4 max-w-sm mx-auto">
            <label className="block text-xs font-semibold text-slate-400 mb-1">
              Target Column to Optimize / Explain (Optional):
            </label>
            <input
              type="text"
              placeholder="e.g. revenue, sales, churn, cost (Leave blank to auto-detect)"
              value={targetColumn}
              onChange={(e) => setTargetColumn(e.target.value)}
              className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-1.5 text-xs text-slate-200 outline-none text-center hover:border-indigo-500 focus:border-indigo-500 transition"
            />
            <p className="text-[10px] text-slate-500 mt-1">
              💡 If left empty, our AI & ML engine will automatically discover the best target column from your dataset!
            </p>
          </div>
        )}

        {file && (
          <div className="mt-6 flex items-center justify-center gap-3">
            <button
              onClick={handleUpload}
              disabled={uploading}
              className="px-6 py-2.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white font-bold text-sm transition shadow-lg shadow-indigo-600/20 flex items-center gap-2"
            >
              {uploading ? "Profiling & Discovering Target..." : "Process Dataset"}
              <ArrowRight className="w-4 h-4" />
            </button>
          </div>
        )}

        {error && (
          <div className="mt-4 p-3 rounded-lg bg-rose-500/10 border border-rose-500/20 text-rose-400 text-xs flex items-center justify-center gap-2">
            <AlertCircle className="w-4 h-4 flex-shrink-0" />
            <span>{error}</span>
          </div>
        )}
      </div>



      {/* Pre-Calibrated Demo Datasets */}
      <div>
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-sm font-bold uppercase tracking-wider text-slate-300 flex items-center gap-2">
            <Sparkles className="w-4 h-4 text-indigo-400" /> Pre-Calibrated Demo Datasets
          </h3>
          <span className="text-xs text-slate-500">Available in both Multi-Sheet Excel (.xlsx) and CSV</span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {sampleDatasets.map((sample) => (
            <div 
              key={sample.key}
              className="p-6 rounded-2xl bg-slate-900 border border-slate-800 hover:border-indigo-500/40 flex flex-col justify-between transition space-y-4 shadow-xl"
            >
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <span className={`text-[10px] font-extrabold px-2 py-0.5 rounded border ${sample.badgeColor}`}>
                    {sample.badge}
                  </span>
                  <span className="text-[11px] font-mono text-slate-500">{sample.records}</span>
                </div>

                <h4 className="font-bold text-base text-slate-100">{sample.title}</h4>
                <p className="text-xs text-slate-400 leading-relaxed">{sample.description}</p>

                {sample.sheets && (
                  <div className="pt-1 flex items-center gap-1.5 flex-wrap">
                    <span className="text-[10px] font-semibold text-slate-500 flex items-center gap-1">
                      <Layers className="w-3 h-3 text-indigo-400" /> Excel Sheets:
                    </span>
                    {sample.sheets.map((s) => (
                      <span key={s} className="px-1.5 py-0.5 rounded bg-slate-800 text-[10px] font-mono text-slate-300 border border-slate-700">
                        {s}
                      </span>
                    ))}
                  </div>
                )}
              </div>

              <div className="pt-4 border-t border-slate-800/80 space-y-2">
                <button
                  onClick={() => handleSelectSample(sample.key)}
                  disabled={loading}
                  className="w-full py-2.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white font-bold text-xs shadow-md shadow-indigo-600/20 transition flex items-center justify-center gap-2"
                >
                  <Play className="w-3.5 h-3.5 fill-white" />
                  {loading ? "Loading..." : "Load & Explore Dataset"}
                </button>

                <div className="grid grid-cols-2 gap-2">
                  <button
                    onClick={() => handleDownloadSample(sample.xlsxFile)}
                    className="py-1.5 px-2 rounded-lg bg-emerald-500/10 hover:bg-emerald-500/20 border border-emerald-500/30 text-emerald-400 text-[11px] font-semibold transition flex items-center justify-center gap-1.5"
                    title="Download raw Excel file with multiple sheets"
                  >
                    <FileSpreadsheet className="w-3 h-3" />
                    Excel (.xlsx)
                  </button>
                  <button
                    onClick={() => handleDownloadSample(sample.csvFile)}
                    className="py-1.5 px-2 rounded-lg bg-slate-800 hover:bg-slate-700 border border-slate-700 text-slate-300 text-[11px] font-semibold transition flex items-center justify-center gap-1.5"
                    title="Download raw CSV file"
                  >
                    <FileText className="w-3 h-3" />
                    CSV File
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
