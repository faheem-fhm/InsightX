# InsightX: Technical Interview Preparation & Architecture Deep-Dive

This document provides architectural rationale, algorithmic derivations, and interview-grade Q&As for the technical systems powering InsightX.

---

## 1. System Architecture & Data Engineering

### Q1: Why did you decouple analytical compute (DuckDB/Parquet) from the transactional application database (PostgreSQL)?
**Answer:**
Relational databases like PostgreSQL are row-oriented (OLTP) optimized for transactional integrity (`ACID`), single-record lookups, and concurrent inserts/updates. Analytical aggregations (`SUM`, `AVG`, `GROUP BY` across millions of rows) require scanning entire tables row-by-row into memory.
Columnar engines like **DuckDB** and formats like **Apache Parquet** store values column-by-column with dictionary encoding and vectorization (SIMD). When calculating `SUM(revenue)`, DuckDB reads only the `revenue` byte stream from disk using memory-mapping, skipping all other columns entirely. This achieves sub-10ms aggregation speeds without choking PostgreSQL connections or exhausting application memory.

### Q2: How does InsightX enforce the rule that the LLM must never calculate numbers?
**Answer:**
Large Language Models are probabilistic token predictors, not mathematical engines. Prompting an LLM to compute arithmetic or aggregate large data arrays causes hallucinations.
InsightX enforces a strict 4-stage pipeline:
1. **Natural Language Intent Parsing**: The LLM extracts the user's analytical objective (e.g. "top 10 products by profit").
2. **Schema-Constrained SQL Generation**: The LLM outputs a SQL query against verified column definitions.
3. **AST SQL Validation**: An Abstract Syntax Tree parser (`sqlparse`) validates that the statement is strictly read-only (`SELECT`, CTEs) and blocks mutating DDL/DML.
4. **Deterministic Execution & Grounding**: DuckDB runs the SQL on verified Parquet data. The actual computed numbers are then injected into the response template:
   - **Finding**: What happened.
   - **Evidence**: Actual computed metrics.
   - **Explanation**: Associated drivers.
   - **Recommendation**: Operational next steps.

---

## 2. Data Quality & Preprocessing

### Q3: How is the Data Quality Score calculated?
**Answer:**
$$\text{Score} = 100 - (\text{NullPenalty} + \text{DuplicatePenalty} + \text{ConstantColPenalty} + \text{OutlierPenalty} + \text{InvalidValuesPenalty})$$
- Missing values: penalized proportionally up to 25 points.
- Duplicate rows: penalized up to 20 points.
- Constant columns (zero variance): 5 points per column.
- Outlier density: penalized up to 15 points based on $3 \times \text{IQR}$ frequency.
- Impossible values (e.g. negative prices/ages): 10 points.

### Q4: Why use skewness-aware imputation instead of simple mean imputation?
**Answer:**
If a feature is normally distributed ($\text{Skewness} \approx 0$), the mean is the minimum variance unbiased estimator. However, financial and operational metrics (revenue, wait times, contract values) exhibit heavy right-skew ($\text{Skewness} > 1.0$). Imputing with the mean pulls typical values toward extreme outliers.
InsightX checks sample skewness:
$$\text{Skewness} = \frac{n}{(n-1)(n-2)} \sum \left(\frac{x_i - \bar{x}}{s}\right)^3$$
If $|\text{Skewness}| > 1.0$, the **Median** is imputed. Otherwise, the **Mean** is imputed.

---

## 3. Machine Learning & Investigation

### Q5: How does Isolation Forest detect anomalies compared to statistical 3-Sigma?
**Answer:**
- **Rolling 3-Sigma**: Assumes values follow a Gaussian distribution and evaluates each point unidimensionally against a moving window:
  $$\mu_t \pm 2.5 \cdot \sigma_t$$
  It is fast for univariate temporal anomalies but sensitive to non-normal distributions and misses multivariate interactions.
- **Isolation Forest**: An ensemble of randomized decision trees. Anomalies are isolated near the root of the tree with short average path lengths:
  $$s(x, n) = 2^{-\frac{E(h(x))}{c(n)}}$$
  InsightX blends both methods: Rolling 3-Sigma establishes the expected baseline band, while Isolation Forest scores the multivariate severity.

### Q6: How does the Root Cause Engine differentiate correlation from causation?
**Answer:**
Observational data alone cannot prove causality without randomized controlled trials (A/B tests) or instrumental variables. Therefore, InsightX explicitly guards against false causal claims:
1. Performs dimensional variance decomposition:
   $$\Delta \text{Metric}_{\text{dim}} = \text{Daily}_{\text{crisis}} - \text{Daily}_{\text{baseline}}$$
   and computes each segment's contribution percentage to the total variance.
2. Identifies simultaneous metric shifts (e.g. delivery delays $+73\%$, complaints $+164\%$).
3. Badges the output with a **Causality Disclaimer**:
   *"Metrics are statistically associated. Root causes reflect empirical correlations rather than randomized trial causation."*
   Findings are phrased using *"likely contributor"* or *"associated with"*.

### Q7: How are K-Means RFM clusters labeled with business-friendly segment names?
**Answer:**
Recency, Frequency, and Monetary (RFM) values are standardized with `StandardScaler`. K-Means is fitted with $k=4$. The centroids of the resulting clusters are sorted:
- The cluster with highest Monetary and Frequency $\rightarrow$ **"Champions"**.
- Second highest $\rightarrow$ **"Loyal Customers"**.
- Clusters with elevated Recency (long time since last purchase) $\rightarrow$ **"At Risk / Inactive"**.
- Remaining cluster $\rightarrow$ **"Potential Loyalists"**.

---

## 4. Web & Security Engineering

### Q8: How does InsightX prevent SQL Injection in Text-to-SQL?
**Answer:**
1. **Token AST Validation**: Generated SQL is tokenized into syntax trees. Prohibited operations (`DROP`, `DELETE`, `UPDATE`, `INSERT`, `ALTER`, `TRUNCATE`, `EXEC`) are blocked before execution.
2. **Read-Only Scope**: Queries must start with `SELECT` or `WITH`.
3. **Semicolon Stacking Prevention**: Multiple statements within a single string are rejected.
4. **Isolated Parquet Tables**: Queries run against in-memory DuckDB views of Parquet data, physically isolated from the application's PostgreSQL transactional database.

### Q9: How is Light & Dark theme accessibility guaranteed across charts?
**Answer:**
Charts use semantic design tokens:
- Primary Metric (Revenue/Volume) $\rightarrow$ Indigo/Blue palette (`#6366f1`).
- Efficiency/Positive Change $\rightarrow$ Emerald Green (`#10b981`).
- Operational Risk/Cancellations $\rightarrow$ Rose Red (`#ef4444`).
- Alerts/Warning $\rightarrow$ Amber (`#f59e0b`).
Background grids use subtle neutral strokes (`#1e293b`), ensuring contrast ratios comply with WCAG 2.1 AA standards across both light and dark modes.
