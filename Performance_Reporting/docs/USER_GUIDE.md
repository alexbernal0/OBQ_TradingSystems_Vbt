# User Guide — OBQ Performance Reporting

Complete step-by-step guide for integrating the 19-chart tearsheet into any VectorBT backtest.

---

## Table of Contents

1. [Installation](#1-installation)
2. [Minimal Usage — nav only](#2-minimal-usage)
3. [Standard Usage — with Benchmark](#3-standard-usage-with-benchmark)
4. [Full VBT Integration — all 19 charts](#4-full-vbt-integration)
5. [Input Data Reference](#5-input-data-reference)
6. [Chart-by-Chart Guide](#6-chart-by-chart-guide)
7. [Customization](#7-customization)
8. [Saving Charts](#8-saving-charts)
9. [Troubleshooting](#9-troubleshooting)

---

## 1. Installation

```bash
pip install plotly pandas numpy scipy
```

Copy the `Performance_Reporting/` folder into your project root (same level as your strategy files), then import:

```python
import sys
sys.path.insert(0, "/path/to/your/project")
from Performance_Reporting import run_tearsheet
```

Or if installed as a package:
```python
from Performance_Reporting import run_tearsheet
```

---

## 2. Minimal Usage

The only required input is a **nav Series** (daily portfolio equity in dollars):

```python
import pandas as pd
from Performance_Reporting import run_tearsheet

# nav must be a pd.Series with a DatetimeIndex
nav = pd.Series(
    data=[100_000, 101_200, 99_800, ...],
    index=pd.date_range("2020-01-01", periods=len(data), freq="D"),
    name="My Strategy"
)

results = run_tearsheet(
    nav=nav,
    strategy_name="My First Strategy",
    initial_capital=100_000.0,
)
```

This renders **all charts that don't require a benchmark or VBT portfolio** (charts 1, 2 partial,
5, 6, 7, 8 partial, 9 partial, 10, 11, 12, 13, 14 partial, 17).

---

## 3. Standard Usage — with Benchmark

Add a benchmark for the full comparative analysis:

```python
import pandas as pd
from Performance_Reporting import run_tearsheet

# Load benchmark (raw price series — auto-rebased to match nav start value)
spx = pd.read_csv("spx.csv", index_col=0, parse_dates=True)["close"]

results = run_tearsheet(
    nav=nav,
    benchmark=spx,
    long_entries=signals["long_entries"],  # pd.DataFrame[bool] or pd.Series[bool]
    strategy_name="My Strategy vs SPX",
    initial_capital=100_000.0,
)
```

### What the benchmark enables:
- VIZ 2: Up/Down Capture, Information Ratio, Tracking Error columns
- VIZ 3: All 4 benchmark comparison panels
- VIZ 4: Up/Down Capture chart
- VIZ 7: Excess return column in annual table
- VIZ 8-9: Benchmark rolling overlay lines
- VIZ 14: Monthly active returns bar chart (left panel)
- VIZ 18: Market regime analysis (Bull/Bear via benchmark 200-SMA)
- VIZ 19: Benchmark line in each crisis panel

---

## 4. Full VBT Integration — all 19 charts

To enable the 3 trade-analytics charts (sector attribution, trade duration, drawdown detail),
pass the VBT portfolio object plus supporting data:

```python
import vectorbt as vbt
from Performance_Reporting import run_tearsheet

# --- Your VBT backtest ---
pf = vbt.Portfolio.from_order_func(
    close, order_func_nb, ...,
    init_cash=100_000, cash_sharing=True, group_by=True,
    freq="D", ffill_val_price=True, update_value=True,
)
nav = pf.value().iloc[:, 0]

# --- Run tearsheet ---
results = run_tearsheet(
    nav=nav,
    benchmark=spx,
    long_entries=signals["long_entries"],
    strategy_name="FTT Clenow 2 — P24 Universe",
    initial_capital=100_000.0,
    # --- VBT extras ---
    pf=pf,                                 # enables VIZ 15, 16, 17
    contract_specs=CONTRACT_SPECS_DF,      # enables sector mapping in VIZ 15
    ohlc={"close": close_df},              # enables calendar-day durations in VIZ 16
)
```

### contract_specs requirements:
A `pd.DataFrame` with:
- Index named `pwb_symbol` (or a column named `pwb_symbol`) containing the ticker symbols that match `close.columns`
- A column named `sector` with string sector labels

Example:
```
              exchange    sector    contract_size_desc
pwb_symbol
GC1           CME       Metals    100 troy oz
CL1           NYMEX     Energy    1000 barrels
ES1           CME       Indices   $50 × E-mini S&P 500
```

### ohlc requirements:
A `dict` with at minimum:
```python
ohlc = {"close": pd.DataFrame}  # wide format: DatetimeIndex × symbol columns
```

---

## 5. Input Data Reference

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `nav` | `pd.Series` | **Yes** | Daily portfolio equity in $ with `DatetimeIndex` |
| `benchmark` | `pd.Series` | No | Raw benchmark price (auto-rebased); None = skip all benchmark charts |
| `long_entries` | `pd.DataFrame` or `pd.Series` (bool) | No | Entry signals; any True per bar → triangle marker on equity curve |
| `strategy_name` | `str` | No | Shown in all chart titles; default `"Strategy"` |
| `initial_capital` | `float` | No | Horizontal guide line on equity curve; default `100_000.0` |
| `pf` | VBT Portfolio | No | Required for VIZ 15 (sector attribution), 16 (trade duration), partial 17 (drawdown cross-check) |
| `contract_specs` | `pd.DataFrame` | No | Required for sector labels in VIZ 15 |
| `ohlc` | `dict` | No | Required for calendar-day trade duration in VIZ 16; must have `"close"` key |

### nav format requirements:
```python
nav = pd.Series(
    data=[100000.0, 101234.5, ...],           # dollar values, NOT returns
    index=pd.DatetimeIndex(["2020-01-02", "2020-01-03", ...]),
    name="strategy_name"
)
nav.index.freq = "D"   # recommended but not required
```

---

## 6. Chart-by-Chart Guide

### VIZ 1 — Equity Curve + Drawdown
- **Top panel**: Portfolio equity vs. benchmark, with initial capital guide line
- **Green triangles**: Bars where any `long_entries` signal was True
- **Bottom panel**: Drawdown from peak (%) — filled red area
- **Title subtitle**: CAGR, Sharpe, Max DD, Win Rate, SystemScore (Sharpe × Calmar)

### VIZ 2 — Extended Metrics Table
Full institutional metrics in 4 sections:

| Section | Metrics |
|---------|---------|
| RETURNS | CAGR, Annual Vol, Sharpe, Sortino, Calmar, Win Rate |
| RISK | Max DD, CVaR 95%, CVaR 99%, Ulcer Index, Pain Index, Lake Ratio |
| ADVANCED | Omega Ratio, Serenity Ratio, Pain Ratio, Sharpe t-stat, 95% CI, Haircut Sharpe |
| VS BENCHMARK | Information Ratio, Tracking Error, Up Capture, Down Capture |

### VIZ 3 — Benchmark Comparison 2×2
Four views of strategy vs benchmark:
1. Cumulative returns (linear scale)
2. Cumulative returns (log scale — reveals compounding)
3. Volatility-matched benchmark comparison
4. Cumulative alpha (strategy minus benchmark equity)

### VIZ 4 — Up/Down Capture Ratios
- **Left bar chart**: Up Capture % and Down Capture % as bars with 100% reference line
- **Right line chart**: Rolling 24-month capture ratios over time
- **Annotation**: Overall capture ratio (Up ÷ Down); ideal = high Up, low Down

### VIZ 5 — Monthly Returns Heatmap
- Standard month × year heatmap with RdYlGn colorscale
- Values shown as bold text inside each cell
- YTD column on the right

### VIZ 6 — Intra-Month Max Drawdown Heatmap
- For each calendar month: worst peak-to-trough decline within that month
- Red colorscale (darker = worse)
- Reveals **intra-month volatility** hidden in monthly return figures

### VIZ 7 — Annual Performance Table
Model / Benchmark / Excess return per year. Negative returns shown in red.

### VIZ 8 — Rolling Sharpe & Sortino
252-day rolling window. Values below 0 = trailing-year risk-adjusted return is negative.

### VIZ 9 — Rolling Vol & Max DD
252-day rolling annualized volatility and max drawdown. Shows regime changes in risk.

### VIZ 10 — Omega Ratio Curve
- X-axis: monthly return threshold swept −5% to +5%
- Y-axis: Omega ratio at that threshold
- **Red dashed line at Omega = 1** (breakeven) — where the curve crosses this is the "gain/loss equilibrium" threshold
- Higher curve = more gains relative to losses at any threshold level

### VIZ 11 — Distribution & Box Plots
Histogram (overlaid strategy vs benchmark) + box plots showing IQR, median, whiskers, outliers.

### VIZ 12 — Distribution Moments + Q-Q
- **Left table**: 15 statistics including skewness, excess kurtosis, Jarque-Bera test, VaR and CVaR at 95%/99%
- **Right Q-Q plot**: Monthly returns vs Normal distribution. Points on the red line = perfectly normal. Fat tails appear as S-curve.

### VIZ 13 — ACF / PACF
- **Left (ACF)**: Autocorrelation of monthly returns at lags 1–24 months
- **Right (PACF)**: Partial autocorrelation — removes indirect effects
- **Red dashed bands**: ±1.96/√n (95% significance bounds)
- Green bars = statistically significant autocorrelation. Significant lag-1 ACF can indicate **momentum persistence**.

### VIZ 14 — Active Returns & Best/Worst
- **Left**: Monthly active return bars (green = outperformed, red = underperformed)
- **Right**: Strategy's top 5 and bottom 5 months, with benchmark overlay for context

### VIZ 15 — Sector Attribution *(requires pf + contract_specs)*
- **Left**: P&L by sector with Long (green) and Short (red) bars grouped side by side
- **Right**: Total P&L per sector (green = profitable, red = losing)
- Title shows total closed P&L and number of trades

### VIZ 16 — Trade Duration Analysis *(requires pf)*
4-panel analysis:
1. **Duration histogram** — win (green) vs loss (red) distributions
2. **Average duration** bars — avg/median win vs loss days
3. **Win rate by duration bucket** — 0–7d, 8–30d, 31–90d, 91–180d, 181–365d, >365d
4. **Scatter** — every trade plotted (duration × P&L), color-coded win/loss

### VIZ 17 — Complete Drawdown Table
All drawdown periods ≥ 2% depth, sorted deepest first:
- Start date, Trough date, Recovery date (or "Ongoing")
- Depth (%), Drawdown duration (days), Recovery duration (days), Total duration

### VIZ 18 — Market Regime *(requires benchmark)*
Bull = benchmark > 200-day SMA; Bear = below 200-day SMA.
4 panels:
1. Monthly return box plots by regime (strategy + benchmark)
2. Annualized return by regime (green/red bars)
3. Win rate by regime vs 50% line
4. Cumulative return with Bear periods shaded red

### VIZ 19 — Crisis Periods
8 historical crises, normalized to 1.0 at start:
Dot-Com, 9/11, GFC, Euro Debt, 2015 Correction, Volmageddon, COVID, 2022 Rate Hike.

---

## 7. Customization

### Change colors:
```python
from Performance_Reporting import tearsheet
tearsheet.STRATEGY_COLOR  = "#00BCD4"   # teal
tearsheet.BENCHMARK_COLOR = "#FF5722"   # deep orange
```

### Add/remove crisis periods:
```python
tearsheet.CRISIS_PERIODS["Your Crisis"] = ("2023-03-01", "2023-05-15")
del tearsheet.CRISIS_PERIODS["Volmageddon"]
```

### Call individual charts:
```python
from Performance_Reporting.tearsheet import (
    _viz12_moments_qq, _viz17_drawdown_table, _viz10_omega_curve
)
_viz12_moments_qq(monthly_returns)
_viz17_drawdown_table(equity_series)
_viz10_omega_curve(monthly_strategy, monthly_benchmark)
```

---

## 8. Saving Charts

`run_tearsheet()` does **not** save files. To save individual charts:

```python
# In tearsheet.py, modify a viz function to return fig:
def _viz1_equity_drawdown(...):
    fig = ...
    fig.show()
    return fig   # add this line

# Or use Plotly's write functions after the run:
import plotly.io as pio
pio.write_html(fig, "tearsheet_viz1.html")
pio.write_image(fig, "tearsheet_viz1.png", width=1400, height=700)
```

---

## 9. Troubleshooting

| Problem | Cause | Fix |
|---------|-------|-----|
| `VIZ 15 skipped: no portfolio object` | `pf=None` | Pass `pf=vbt_portfolio` |
| `VIZ 15 skipped: no closed trades` | All trades still open | Run backtest to a later end date |
| `VIZ 16 skipped: ...` | `pf=None` or all trades open | Same as above |
| `Import OK` but charts blank | Not in Jupyter | Call `fig.show()` needs a notebook or browser |
| `KeyError: 'sector'` | contract_specs missing sector column | Add `sector` column to your contract_specs DataFrame |
| `ValueError: index not monotonic` | nav has duplicate dates | `nav = nav[~nav.index.duplicated()]` |
| Charts don't align with benchmark | Date range mismatch | Pass raw benchmark (before rebasing); function auto-aligns |
| scipy warning | scipy not installed | `pip install scipy` for Q-Q and Jarque-Bera |
