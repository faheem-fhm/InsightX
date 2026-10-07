import axios from "axios";

// Use relative API base URL so Vite dev proxy (/api → http://127.0.0.1:8000) works cleanly
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "/api/v1";

const api = axios.create({
  baseURL: API_BASE_URL,
});

export const datasetApi = {
  list: () => api.get("/datasets"),
  get: (id) => api.get(`/datasets/${id}`),
  getProfile: (id) => api.get(`/datasets/${id}/profile`),
  getQuality: (id) => api.get(`/datasets/${id}/quality`),
  preprocess: (id, data) => api.post(`/datasets/${id}/preprocess`, data || {}),
  getDashboard: (id, filters) =>
    api.get(`/datasets/${id}/dashboard`, {
      params: { filters: filters ? JSON.stringify(filters) : undefined },
    }),
  getAnalytics: (id) => api.get(`/datasets/${id}/analytics`),
  getAnomalies: (id, data) => api.post(`/datasets/${id}/anomaly`, data || {}),
  getForecast: (id, data) => api.post(`/datasets/${id}/forecast`, data || {}),
  getCustomers: (id) => api.get(`/datasets/${id}/customers`),
  getChurn: (id) => api.post(`/datasets/${id}/churn`, {}),
  getRootCause: (id, data) => api.post(`/datasets/${id}/root-cause`, data || {}),

  // ── AI Analyst ─────────────────────────────────────────────────────────────
  askAI: (id, data) => api.post(`/datasets/${id}/ai/ask`, data),
  textToSql: (id, data) => api.post(`/datasets/${id}/ai/text-to-sql`, data),

  // ── RAG & Smart Prompts ───────────────────────────────────────────────────
  getSuggestedPrompts: (id) => api.get(`/datasets/${id}/ai/suggested-prompts`),
  buildRagProfile: (id) => api.post(`/datasets/${id}/ai/build-profile`),

  // ── Custom Chart Builder ──────────────────────────────────────────────────
  getColumns: (id) => api.get(`/datasets/${id}/columns`),
  buildCustomChart: (id, config) => api.post(`/datasets/${id}/ai/custom-chart`, config),

  // ── Reports & Samples ────────────────────────────────────────────────────
  getReport: (id) => api.get(`/datasets/${id}/report`),
  upload: (formData) => api.post("/datasets/upload", formData),
  loadSample: (sampleKey) => api.post("/datasets/sample", { sample_key: sampleKey }),

  // ── Target Column & ML Explainability ────────────────────────────────────
  updateTargetColumn: (id, targetCol) => api.post(`/datasets/${id}/target-column`, { target_column: targetCol }),
  getTargetExplainability: (id) => api.get(`/datasets/${id}/target-explainability`),

  // ── Delete Dataset ────────────────────────────────────────────────────────
  deleteDataset: (id) => api.delete(`/datasets/${id}`),
};

export default api;
