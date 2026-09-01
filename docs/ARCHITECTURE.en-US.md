# Project Architecture — Cross-Correlation Analysis in Financial Time Series

## 1. Overview

This document describes the software architecture adopted for the project on cross-correlation analysis in financial time series, as well as the architectural concerns (CoCs) that guided the design decisions, aligned with the methodological scope defined in the research.

The object of study is the **Mini Ibovespa Index futures contract (WIN)**, with intraday data collected between June 2025 and June 2026, considering exclusively trading days. The analysis does not compare distinct assets against each other; instead, it investigates the **correlation of a reference day ($d_n$) against the previous days of the same series** ($d_{n-1}, d_{n-2}, \dots, d_1$), forming a lag matrix that is subsequently represented as a heatmap and integrated into an **already existing dashboard**.

The system is organized as a **layered pipeline (layered pipeline / pipes-and-filters)**, in which data flows unidirectionally from acquisition at the source (MetaTrader 5) to the integration of correlation results into the dashboard. Each layer has a single responsibility, communicates only with adjacent layers through well-defined contracts (interfaces/schemas), and can be tested and evolved in isolation.

This architectural style was chosen for three main reasons:

1. **Separation of concerns**: acquisition, cleaning, storage, statistical analysis, and presentation are distinct concerns, with different rates of change and different quality requirements.
2. **Extensibility**: the data source (MT5) is treated as an implementation detail isolated behind an interface, allowing eventual replacement by another broker or data provider without impacting the remaining layers (Dependency Inversion Principle). Likewise, the correlation method is treated as a pluggable component, since the research plans to investigate multiple techniques (CCF, Pearson, Spearman, DCCA/MF-DCCA).
3. **Scientific reproducibility**: a pipeline with explicit stages and persisted intermediate data facilitates auditing, versioning, and repetition of experiments — a central requirement for a project of academic and documentary nature.

## 2. Layered View

```
┌─────────────────────────────────────────────────┐
│  Presentation Layer (Dashboard)                  │
│  - Integration with the existing dashboard       │
│  - Day-by-day correlation heatmap                │
│  - Graphical overlay of lagged series             │
├─────────────────────────────────────────────────┤
│  Analysis Layer (Correlation Engine)              │
│  - CCF (Cross-Correlation Function)              │
│  - Pearson / Spearman                            │
│  - DCCA / ρDCCA / MF-DCCA (candidate methods)    │
│  - Significance and stability testing            │
├─────────────────────────────────────────────────┤
│  Storage Layer (Data Store)                       │
│  - Series-specific dataset (candles)             │
│  - Pair/lag structure (d_i, d_k)                 │
├─────────────────────────────────────────────────┤
│  Preprocessing Layer (ETL/Cleaning)               │
│  - Chronological ordering, date/time handling    │
│  - Backfill / gap imputation                     │
│  - Filtering by trading days                     │
├─────────────────────────────────────────────────┤
│  Acquisition Layer (Data Acquisition)             │
│  - Integration with MetaTrader 5 (WIN, intraday) │
└─────────────────────────────────────────────────┘
```

### 2.1 Acquisition Layer (Data Acquisition)

Responsible for obtaining the intraday price history (candle structure, OHLC) of the WIN futures contract directly from the MetaTrader 5 terminal, via the official Python API, over the period from June 2025 to June 2026. This layer exposes an abstract data acquisition interface, of which the MT5 client is one concrete implementation — this isolates the rest of the system from source-specific particularities (return format, broker server time zone, request limits), even though switching brokers is not a requirement of the current research.

### 2.2 Preprocessing Layer (ETL/Cleaning)

Responsible for preparing the extracted dataset for statistical analysis: chronological ordering of records, handling of date and time information, gap filling via backfill and equivalent operational imputation mechanisms (preserving the datatype originally returned by the MT5 client package), and filtering to include exclusively the trading days of the analyzed period. The result is a series structured from candles (OHLC), ready to be organized into day pairs in the next stage.

### 2.3 Storage Layer (Data Store)

Responsible for persisting the series-specific dataset, already cleaned and chronologically organized. This layer also structures the **lag pairs** defined in the methodology: for each reference day $d_i$, the set $\mathcal{P}_i = (v_{i,k})$ of pairs $(d_i, d_k)$ against the previous days $d_k$ is maintained, forming the base upon which the correlation matrix will be computed. A typed and efficient format (e.g., Parquet or SQLite) serves as a stable boundary between preprocessing and analysis, allowing calculations to be re-run without the need to recapture the data.

### 2.4 Analysis Layer (Correlation Engine)

Responsible for the statistical computation of the correlation between the reference day and each of the previous days in the series, within the same intraday window. This layer is designed to support multiple correlation methods, as anticipated in the methodology:

- **CCF (Cross-Correlation Function)**: measure of association between the two series at different time lags, the methodological core of the research;
- **Pearson**: strength and direction of the linear relationship, suitable for data with bivariate normal distribution;
- **Spearman**: monotonic relationship based on ranks, more robust to outliers;
- **DCCA / ρDCCA / MF-DCCA**: candidate methods for assessing long-range dependence and multifractal properties in non-stationary series.

In addition to computing the coefficients, this layer is responsible for statistical validation procedures — significance testing, comparison across lags, and stability analysis of results across different time windows — so that the identification of correlations does not rely exclusively on visual inspection.

### 2.5 Presentation Layer (Dashboard)

Responsible for integrating the analysis results into an **already existing dashboard**, expanded with the new correlation feature. This includes generating the correlational heatmap (the $d_i \times d_k$ matrix), simultaneously displaying time series with graphical overlay, and making numerical and graphical results available for comparative observation of trends, variations, and lags.

## 3. Architectural Concerns (CoCs)

Concerns are the preoccupations that guide and constrain architectural decisions, in the sense defined by ISO/IEC/IEEE 42010. For this project, the following concerns were identified:

### 3.1 Functional Concerns

| Concern | Description |
|---|---|
| Data acquisition | Reliable retrieval of the WIN intraday history via MT5, for the Jun/2025–Jun/2026 period |
| Temporal consistency | Chronological ordering, date/time handling, and filtering by trading days |
| Lag structuring | Organize the dataset into pairs $(d_i, d_k)$ for each reference day, following the $\mathcal{P}_i$ model |
| Correlation calculation | Support multiple methods (CCF, Pearson, Spearman, DCCA/MF-DCCA) over the day pairs |
| Statistical validation | Apply significance tests and stability analysis across time windows |
| Dashboard integration | Make numerical results and the heatmap available in the existing dashboard |

### 3.2 Non-Functional Concerns (Quality Attributes)

| Concern | Description | Architectural impact |
|---|---|---|
| **Reproducibility** | The same input and parameters must produce the same output, essential for documentary/academic validation | Explicit pipeline stages, persisted intermediate data, parameters (period, correlation method, window) versioned in a configuration file |
| **Methodological extensibility** | The research plans to compare different correlation methods (CCF, Pearson, Spearman, DCCA, MF-DCCA) | Analysis Layer designed with a pluggable per-method interface, allowing techniques to be added/compared without changing the other layers |
| **Testability** | Each layer must be testable in isolation | Clear separation between acquisition, processing, pair structuring, and analysis; use of synthetic/mocked data in tests |
| **Data integrity** | Handling of gaps and missing values without altering the original datatype returned by MT5 | Preprocessing layer dedicated to backfill/imputation and preservation of data types |
| **Combinatorial scalability** | The number of pairs $(d_i, d_k)$ grows quadratically with sample size ($n$ days) | Storage structure optimized for pair-based queries; vectorized computation in the analysis layer |
| **Integration with an existing system** | The dashboard already exists and will be expanded, not replaced | Presentation layer decoupled via a data contract (API/schema) consumed by the dashboard, minimizing coupling with its current implementation |
| **Traceability/Auditability** | Each run must record sufficient metadata for academic auditing | Acquisition metadata and the applied correlation method stored alongside the processed dataset |

### 3.3 Assumptions and Constraints

The following assumptions, already stated in the research methodology, directly guide the architectural decisions:

- **Analyzed asset**: Mini Ibovespa Index futures contract (WIN), the sole instrument under study
- **Period**: June 2025 to June 2026, trading days only
- **Granularity**: intraday data, structured as candles (OHLC)
- **Correlation unit**: day against day (not asset against asset) — each pair $(d_i, d_k)$ is one observation
- **Reference sample size**: $n=10$ days, as illustrated in the methodology example (parameterizable)
- **Missing data handling**: backfill and equivalent imputation mechanisms, preserving the original datatype
- **Candidate correlation methods**: CCF (methodological core), Pearson, Spearman, DCCA/ρDCCA and MF-DCCA
- **Validation**: not exclusively visual — includes significance testing, comparison across lags, and stability across windows
- **Presentation channel**: an already existing dashboard, to be expanded (building a new dashboard from scratch is out of scope)

## 4. Release 1 Scope

The first release covers the **Acquisition**, **Preprocessing**, and **Storage** layers (including the structuring of lag pairs), with the goal of producing the series-specific dataset — organized according to the $\mathcal{P}_i = (v_{i,k})$ model — ready to be consumed by the Analysis layer in a subsequent release, which will include computing the correlation coefficients and generating the heatmap to be integrated into the dashboard.

## 5. Release 2 Scope

The second release implements the **Analysis** layer: given the sealed-day dataset, it computes the correlation matrix $\mathbf{V} = [v_{i,j}]$ between daily series, with $v_{i,j} = \mathrm{corr}(d_i, d_j)$ for $j < i$, and persists the coefficients, the pairwise p-value, and a stability measure across sub-windows. Each day's series is the **close log-return** over a parametrized **uniform intraday window**. Methods are pluggable (`CorrelationMethod`); this release ships **Pearson** and **Spearman** — CCF with lag sweep, ρDCCA, and MF-DCCA follow through the same interface. Visualization produces the **heatmap** (upper triangle of $\mathbf{V}$). Dashboard integration remains out of scope. See `docs/adr/0004-camada-de-analise-correlacao-cruzada.md`.