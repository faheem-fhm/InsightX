# InsightX: AI-Powered Data Analytics & Business Investigation Platform

> **Don't just show what happened. Discover why.**

InsightX is an enterprise-grade AI-powered data analytics and business investigation platform. It provides automated data profiling, robust preprocessing, dynamic dashboards, exploratory data analysis, machine learning workflows (anomaly detection, time-series forecasting, customer segmentation, churn prediction with explainability), automated root-cause investigation, and an interactive LLM Data Analyst operating under strict guardrails.

---

## Key Features

1. **Multi-Format Ingestion**: Supports CSV, XLSX, XLS, JSON, and Parquet up to 50MB with automated MIME and magic-byte validation.
2. **Data Quality Profiler**: Computes a 0–100 Data Quality Score, reports missing cells, duplicates, constant columns, and outliers.
3. **Adaptive Preprocessing**: Skewness-aware numerical imputation (Median vs Mean), Mode/'Unknown' categorical imputation, non-destructive Parquet caching.
4. **Dynamic Executive Dashboard**: Dynamic KPI cards with period-over-period delta indicators, multi-dimensional filters, automated chart selection, and threshold alerts.
5. **Exploratory Data Analysis (EDA)**: Descriptive statistics table, histogram distributions, and Pearson correlation matrices.
6. **Temporal Anomaly Radar**: Dual-engine Isolation Forest + Rolling 3-Sigma thresholding with severity classifications (Low, Medium, Critical).
7. **Time-Series Forecasting**: Chronological Holt Double Exponential Smoothing with 7, 30, and 90-day horizons, 95% uncertainty cones, and backtested MAE/RMSE/MAPE metrics.
8. **Customer Intelligence**: Standardized RFM analysis, K-Means clustering (Champions, Loyal, At Risk), and Churn Random Forest explainability waterfall.
9. **Root Cause Studio**: Multi-dimensional variance decomposition ranking driver contributions, correlated simultaneous shifts, and evidence-backed recommendations.
10. **Guardrailed AI Data Analyst**: Semantic question understanding, AST-validated Text-to-SQL queries executed on DuckDB Parquet tables, and structured chart generation.

---

## Quickstart Guide

### Prerequisites
- Python 3.11+ or 3.12+
- Node.js 18+ or 20+ LTS and npm

### 1. Run Backend
```bash
cd backend
python -m pip install -r requirements.txt
python -m app.main
```
Backend API will be accessible at: `http://localhost:8000` (API Docs at `http://localhost:8000/docs`).

### 2. Run Frontend
```bash
cd frontend
npm install
npm run dev
```
Frontend UI will be accessible at: `http://localhost:5173`.

### 3. Run with Docker Compose
```bash
docker-compose up --build
```

---

## Architecture

```
User Query / Raw File
       │
       ▼
[ Application Layer: FastAPI + Pydantic v2 ]
       │
       ├──► Storage Vault (Raw CSV/XLSX)
       ├──► Processing Engine (Polars / Pandas / Sklearn)
       ├──► Columnar Cache (Parquet)
       ├──► In-Memory OLAP (DuckDB Vectorized SQL)
       └──► AI Analyst (AST SQL Validator + Gemini LLM)
       │
       ▼
[ Presentation Layer: React 18 + Tailwind CSS + Recharts ]
```

---

## License
MIT License. Developed for advanced data engineering and enterprise business intelligence.
