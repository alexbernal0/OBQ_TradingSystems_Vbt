# Performance Reporting — OBQ VectorBT Framework

Institutional-grade, fully interactive performance reporting for VectorBT backtests.
**19 Plotly visualizations** covering every dimension of systematic strategy analysis.

---

## Quick Start

```python
from Performance_Reporting import run_tearsheet

results = run_tearsheet(
    nav=nav_series,               # pd.Series — daily portfolio equity ($)
    benchmark=spx_series,         # pd.Series — benchmark price (raw, auto-rebased)
    long_entries=signals['long_entries'],  # pd.DataFrame bool — entry signals
    strategy_name="My Strategy",
    initial_capital=100_000.0,
    pf=vbt_portfolio,             # optional: VBT Portfolio object
    contract_specs=specs_df,      # optional: DataFrame with 'sector' column
    ohlc=ohlc_dict,               # optional: dict with 'close' key
)
```

All 19 charts render inline in Jupyter via `fig.show()`.

---

## 19 Visualizations at a Glance

| # | Section | Chart | New Metrics Shown |
|---|---------|-------|-------------------|
| 1 | Overview | Equity Curve + Drawdown Underwater | CAGR, Sharpe, Max DD, Win Rate |
| 2 | Overview | **Extended Metrics Table** | CVaR, Ulcer, Lake, Omega, Sharpe t-stat + CI, IR, Capture |
| 3 | Benchmark | Benchmark Comparison 2×2 | Normal / Log / Vol-matched / Alpha |
| 4 | Benchmark | **Up/Down Capture Ratios** | Up Capture %, Down Capture %, Capture Ratio |
| 5 | Calendar | Monthly Returns Heatmap | RdYlGn color-coded month × year |
| 6 | Calendar | **Intra-Month Max DD Heatmap** | Worst peak-to-trough within each month |
| 7 | Calendar | Annual Performance Table | Model vs Benchmark vs Excess by year |
| 8 | Rolling | Rolling 252-Day Sharpe & Sortino | Strategy vs Benchmark |
| 9 | Rolling | Rolling 252-Day Vol & Max DD | Strategy vs Benchmark |
| 10 | Distribution | **Omega Ratio Curve** | Omega(threshold) swept −5% to +5% |
| 11 | Distribution | Return Distribution & Boxes | Histogram + box plot overlay |
| 12 | Distribution | **Distribution Moments + Q-Q** | Skew, Kurtosis, JB test, VaR/CVaR table |
| 13 | Distribution | **ACF / PACF** | Return autocorrelation lags 1–24 months |
| 14 | Active | Monthly Active Returns & Best/Worst | Monthly active bar chart, green/red |
| 15 | Attribution | **Sector Attribution** | P&L by sector, Long vs Short split |
| 16 | Trade Analytics | **Trade Duration Analysis** | 4-panel: histogram, avg, win-rate by bucket, scatter |
| 17 | Drawdown | **Complete Drawdown Table** | All drawdowns ≥ 2% with recovery dates |
| 18 | Regime | **Market Regime Performance** | Bull/Bear via 200-SMA, box plots + shading |
| 19 | Crisis | Crisis Periods (8 events) | Normalized returns during 8 historical crises |

> Charts 2, 4, 6, 10, 12, 13, 15, 16, 17, 18 are **new** relative to standard tearsheets.

---

## Files in This Folder

```
Performance_Reporting/
├── __init__.py                   — Package entry point (import run_tearsheet here)
├── tearsheet.py                  — Complete 19-chart implementation (~750 lines)
├── README.md                     — This file
│
├── docs/
│   ├── USER_GUIDE.md             — Step-by-step integration guide
│   ├── METRICS_REFERENCE.md      — Every metric: formula, range, interpretation
│   ├── GLOSSARY.md               — Full terms glossary (metrics + VBT + trading)
│   └── IMPLEMENTATION_GUIDE.md   — Complete spec for AI/program integration
│
└── examples/
    ├── README.md                 — Example descriptions
    ├── 01_minimal_usage.py       — Simplest possible integration (nav only)
    └── 02_full_clenow2_example.py — Full FTT Clenow 2 integration with all features
```

---

## Dependencies

```
plotly >= 5.0
pandas >= 1.3
numpy >= 1.21
scipy       # optional — enables Q-Q plot and Jarque-Bera test
```

Install: `pip install plotly pandas numpy scipy`

---

## Return Value

`run_tearsheet()` returns a `dict`:

```python
{
    "equity_strategy":   pd.Series,   # rebased to common date range
    "equity_benchmark":  pd.Series,   # rebased to strategy start value
    "returns_strategy":  pd.Series,   # daily pct returns
    "returns_benchmark": pd.Series,   # daily pct returns
    "metrics_strategy":  dict,        # 7 core metrics
    "metrics_benchmark": dict,        # 7 core metrics for benchmark
}
```

---

## Design Principles

- **Zero side effects** — `run_tearsheet()` only renders charts; it never saves files or modifies state.
- **Graceful degradation** — charts requiring `pf`, `contract_specs`, or `ohlc` skip cleanly with a message if those args are `None`.
- **Benchmark optional** — every benchmark-dependent chart skips if no benchmark is provided.
- **No statsmodels dependency** — ACF and PACF are implemented manually with NumPy.
- **scipy optional** — Q-Q and Jarque-Bera fall back to NumPy approximations if scipy is absent.
