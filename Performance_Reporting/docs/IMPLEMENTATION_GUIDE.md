# Implementation Guide — OBQ Performance Reporting

**Audience:** This document is written for an AI assistant, another program, or a developer
who needs to understand and perfectly replicate the OBQ Performance Reporting system in a
new VectorBT strategy. No prior context is assumed.

---

## System Overview

The OBQ Performance Reporting system is a **self-contained Python package** that accepts:
- A portfolio equity series (NAV)
- An optional benchmark series
- An optional VBT Portfolio object
- Optional supporting data

And renders **19 interactive Plotly charts** in Jupyter Notebook, covering all dimensions of
institutional performance analysis.

**Entry Point:** `run_tearsheet()` in `tearsheet.py`
**Package Import:** `from Performance_Reporting import run_tearsheet`

---

## Complete Function Signature

```python
def run_tearsheet(
    nav: pd.Series,
    benchmark: pd.Series = None,
    long_entries = None,               # pd.DataFrame[bool] or pd.Series[bool]
    strategy_name: str = "Strategy",
    initial_capital: float = 100_000.0,
    pf = None,                         # VBT Portfolio object
    contract_specs: pd.DataFrame = None,
    ohlc: dict = None,
) -> dict:
```

### Return value
```python
{
    "equity_strategy":   pd.Series,   # nav aligned to common date range with benchmark
    "equity_benchmark":  pd.Series,   # benchmark rebased to nav's starting value
    "returns_strategy":  pd.Series,   # daily pct_change of equity_strategy
    "returns_benchmark": pd.Series,   # daily pct_change of equity_benchmark
    "metrics_strategy":  dict,        # 7 core metrics (CAGR, Sharpe, Sortino, MaxDD, Calmar, WinRate, SystemScore)
    "metrics_benchmark": dict,        # same 7 metrics for benchmark
}
```

---

## Input Requirements

### nav (required)
```
Type:    pd.Series
Index:   pd.DatetimeIndex (daily frequency, e.g. business days)
Values:  Dollar values (float), NOT returns. Start value = initial_capital.
Name:    Optional string (shown in some chart tooltips)

Example:
nav = pd.Series(
    [100000, 100500, 101200, ...],
    index=pd.date_range("1990-01-02", periods=n, freq="B"),
    name="FTT_Clenow2_P24"
)
```

### benchmark (optional)
```
Type:    pd.Series
Index:   pd.DatetimeIndex
Values:  Raw price series (any starting value; auto-rebased to nav.iloc[0])
         The function finds the common date range and rebases: bench_aligned = bench / bench[0] * nav[0]

Example:
benchmark = dl.get_pricing("Indices", symbols=["SPX"], field="close")["SPX"]
```

### long_entries (optional)
```
Type:    pd.DataFrame[bool] or pd.Series[bool]
Index:   DatetimeIndex matching nav
Purpose: Any True value on a bar → green triangle marker on the VIZ 1 equity curve

If DataFrame: long_entries.any(axis=1) → Series[bool] (True if any symbol had entry that bar)
If None:      No entry markers are shown
```

### pf (optional — required for VIZ 15, 16)
```
Type:    VectorBT Portfolio object (result of vbt.Portfolio.from_order_func() or similar)

Required attributes:
  pf.value()           → pd.DataFrame of shape (n_bars × 1) — portfolio total value
  pf.trades.records    → pd.DataFrame with columns:
                           col, size, entry_idx, entry_price, exit_idx, exit_price,
                           pnl, direction (0=Long/1=Short), status (0=Open/1=Closed)
  pf.orders.records    → pd.DataFrame with columns:
                           col, idx, size, price, fees, side (0=Buy/1=Sell)

If None: VIZ 15 (sector attribution) and VIZ 16 (trade duration) are skipped.
```

### contract_specs (optional — required for sector labels in VIZ 15)
```
Type:    pd.DataFrame
Index:   Named 'pwb_symbol' (or column 'pwb_symbol') — must match close.columns values
Columns: Must contain 'sector' (str) — sector label for each symbol

Example:
               exchange    sector        contract_size_desc
pwb_symbol
GC1            CME        Metals        100 troy oz
CL1            NYMEX      Energy        1000 barrels
ES1            CME        Indices       $50 × E-mini S&P 500
ZN1            CME        Bonds         $100,000 face value

If None: All symbols get sector label "Unknown"
If contract_specs.index.name == 'pwb_symbol': uses index directly
Otherwise: looks for 'pwb_symbol' column
```

### ohlc (optional — required for calendar-day trade durations in VIZ 16)
```
Type:    dict
Required key: 'close' → pd.DataFrame (DatetimeIndex × symbol columns)
              Same index as nav; same columns as pf columns

Usage: ohlc['close'].index is used to convert bar-index trade durations to calendar days:
       duration_days = (close_idx[exit_idx] - close_idx[entry_idx]).days

If None: Trade durations are computed as (exit_bar_number - entry_bar_number) instead of calendar days.
```

---

## Internal Architecture

### Data Flow

```
run_tearsheet(nav, benchmark, long_entries, ..., pf, contract_specs, ohlc)
    │
    ├─ Align date ranges: common = nav.index ∩ benchmark.index
    ├─ Rebase benchmark: bench_aligned = bench / bench[0] * nav[0]
    ├─ Compute daily returns: returns = equity.pct_change().dropna()
    ├─ Compute monthly returns: returns.resample('ME').apply((1+x).prod()-1) * 100
    ├─ Compute core metrics: _compute_metrics(returns, equity)
    │
    └─ Call 19 VIZ functions in order (1 through 19)
        Each function: receives pre-computed data → builds Plotly figure → calls fig.show()
```

### Helper Functions

```python
_compute_metrics(returns, equity) -> dict
    # Basic 7 metrics: CAGR, Sharpe, Sortino, MaxDD, Calmar, WinRate, SystemScore
    # Used in VIZ 1 title only

_compute_all_metrics(returns_s, equity_s, returns_b, equity_b) -> dict
    # Extended 22 metrics including CVaR, Ulcer, Lake, Omega, t-stat, IR, Capture
    # Used in VIZ 2

_manual_acf(x: np.ndarray, nlags: int) -> np.ndarray
    # Manual ACF without statsmodels
    # Returns array of length nlags (lags 1..nlags)

_extract_drawdowns(equity: pd.Series, min_dd_pct: float = -2.0) -> pd.DataFrame
    # Extract all drawdown periods with: Start, Trough, Recovery, Depth, Duration
    # Returns DataFrame sorted by depth (deepest first)
```

---

## VIZ Functions Reference

Each VIZ function is prefixed with `_viz{N}_` and is private (not exported).

| Function | Signature | Key Data Needed |
|----------|-----------|-----------------|
| `_viz1_equity_drawdown` | (equity_s, equity_b, entries, metrics, name, capital) | equity_s always; equity_b optional |
| `_viz2_extended_metrics` | (returns_s, equity_s, returns_b, equity_b, monthly_s, monthly_b, name) | returns_s always; returns_b optional |
| `_viz3_benchmark_comparison` | (equity_s, equity_b, returns_s, returns_b) | equity_b optional |
| `_viz4_capture_ratios` | (monthly_s, monthly_b) | monthly_b required; skips if None |
| `_viz5_monthly_heatmap` | (monthly_s) | always renders |
| `_viz6_intramonth_dd_heatmap` | (equity_s) | always renders |
| `_viz7_annual_table` | (returns_s, returns_b) | returns_b optional |
| `_viz8_rolling_risk_adjusted` | (returns_s, returns_b) | returns_b optional |
| `_viz9_rolling_risk_metrics` | (equity_s, equity_b, returns_s, returns_b) | equity_b optional |
| `_viz10_omega_curve` | (monthly_s, monthly_b) | monthly_b optional |
| `_viz11_distribution` | (monthly_s, monthly_b) | monthly_b optional |
| `_viz12_moments_qq` | (monthly_s) | always renders |
| `_viz13_acf` | (monthly_s) | always renders |
| `_viz14_active_returns` | (returns_s, returns_b, monthly_s, monthly_b) | returns_b optional |
| `_viz15_sector_attribution` | (pf, contract_specs, ohlc) | pf required; skips if None |
| `_viz16_trade_duration` | (pf, ohlc) | pf required; skips if None |
| `_viz17_drawdown_table` | (equity_s) | always renders |
| `_viz18_market_regime` | (returns_s, monthly_s, returns_b, equity_b) | returns_b required; skips if None |
| `_viz19_crisis_periods` | (equity_s, equity_b) | equity_b optional |

---

## Minimum Integration Pattern (for a new strategy)

```python
# ─── STEP 1: Run your VBT backtest ───────────────────────────────────────────

import vectorbt as vbt
import numpy as np
import pandas as pd
import sys
sys.path.insert(0, "/path/to/your/project")

from Performance_Reporting import run_tearsheet

# Your backtest code here...
pf = vbt.Portfolio.from_order_func(
    close_df, order_func_nb, *args,
    init_cash=100_000, cash_sharing=True, group_by=True,
    freq="D", ffill_val_price=True, update_value=True,
)

# ─── STEP 2: Extract NAV ─────────────────────────────────────────────────────

nav = pf.value()
if isinstance(nav, pd.DataFrame):
    nav = nav.iloc[:, 0]
nav.name = "My Strategy"

# ─── STEP 3: Load benchmark ───────────────────────────────────────────────────

# Using OBQ data loader:
# from PWB_tools import data_loader as dl
# benchmark = dl.get_pricing("Indices", symbols=["SPX"], field="close")["SPX"]

# Or from CSV:
benchmark = pd.read_csv("spx.csv", index_col=0, parse_dates=True)["close"]

# ─── STEP 4: Run tearsheet ────────────────────────────────────────────────────

results = run_tearsheet(
    nav=nav,
    benchmark=benchmark,
    long_entries=signals["long_entries"],    # your entry signals DataFrame
    strategy_name="My Strategy v1.0",
    initial_capital=100_000.0,
    pf=pf,
    ohlc={"close": close_df},
)
```

---

## VBT Portfolio Object — Key Fields Used

The tearsheet accesses these fields from the VBT Portfolio object:

```python
# pf.value() → equity curve
nav_series = pf.value().iloc[:, 0]

# pf.trades.records → all trade records
trades = pf.trades.records
# Columns: id, col, size, entry_idx, entry_price, entry_fees,
#          exit_idx, exit_price, exit_fees, pnl, return,
#          direction (0=Long, 1=Short), status (0=Open, 1=Closed)

# For closed trades:
closed = trades[trades['status'] == 1]
# For open trades:
open_positions = trades[trades['status'] == 0]

# pf.orders.records → all order records
orders = pf.orders.records
# Columns: id, col, idx, size, price, fees, side (0=Buy, 1=Sell)

# col → column index in close DataFrame → close.columns[col]
symbol = close_df.columns[int(trade_record['col'])]

# entry_idx / exit_idx → bar index in close DataFrame → close.index[idx]
entry_date = close_df.index[int(trade_record['entry_idx'])]
exit_date   = close_df.index[int(trade_record['exit_idx'])]
```

---

## Adding a New Visualization

To add a 20th chart to the system:

### Step 1: Write the VIZ function

```python
def _viz20_my_new_chart(param1, param2, ...):
    fig = go.Figure()
    # ... build your Plotly figure ...
    fig.update_layout(
        title="<b>My New Chart</b>",
        height=450,
        template='plotly_white'
    )
    fig.show()
    print("  Visualization 20 complete: My New Chart")
```

### Step 2: Add it to run_tearsheet()

```python
# At the bottom of the appropriate section in run_tearsheet():
_viz20_my_new_chart(param1, param2)
```

### Step 3: Update the print count

```python
# Change:
print("\nAll 19 visualizations complete!")
# To:
print("\nAll 20 visualizations complete!")
```

### Guidelines for new VIZ functions:
- Always call `fig.show()` at the end (not `fig.savefig()`)
- Always print `"  Visualization N complete: Title"` at the end
- Handle `None` inputs gracefully — skip with a print message
- Use `STRATEGY_COLOR` and `BENCHMARK_COLOR` constants
- Use `template='plotly_white'`
- Set a meaningful `height` (400–700px depending on content)

---

## Color Constants

```python
STRATEGY_COLOR  = '#1f77b4'   # matplotlib blue — strategy
BENCHMARK_COLOR = '#ff7f0e'   # matplotlib orange — benchmark

# Semantic colors used in charts:
POSITIVE_COLOR  = '#2E7D32'   # dark green (profits, positive returns)
NEGATIVE_COLOR  = '#C62828'   # dark red   (losses, negative returns)
```

---

## Crisis Periods

```python
CRISIS_PERIODS = {
    'Dot-Com Bubble Crash':    ('2000-03-24', '2002-10-09'),
    '9/11 Aftermath':          ('2001-09-10', '2001-09-21'),
    'Global Financial Crisis': ('2007-10-09', '2009-03-09'),
    'European Debt Crisis':    ('2011-05-02', '2011-10-04'),
    '2015-2016 Correction':    ('2015-08-10', '2016-02-11'),
    'Volmageddon':             ('2018-01-26', '2018-02-09'),
    'COVID Crash':             ('2020-02-20', '2020-03-23'),
    '2022 Rate Hike Selloff':  ('2022-01-03', '2022-05-16'),
}
```

To add or modify crisis periods, edit `CRISIS_PERIODS` dict directly in `tearsheet.py`.

---

## Dependencies and Fallbacks

| Library | Used For | If Missing |
|---------|----------|-----------|
| `plotly` | All 19 charts (required) | `ImportError` — must install |
| `pandas` | All data handling (required) | `ImportError` — must install |
| `numpy` | All calculations (required) | `ImportError` — must install |
| `scipy` | Q-Q plot (VIZ 12), Jarque-Bera test (VIZ 12) | Falls back to NumPy approximations; chart still renders |

scipy import is guarded:
```python
try:
    from scipy import stats as _scipy_stats
    _HAS_SCIPY = True
except ImportError:
    _HAS_SCIPY = False
```

---

## Performance Notes

- VIZ 8 and VIZ 9 use `.rolling(252).apply(lambda x: ...)` which can be slow on long series (>10 years). Use `engine='numba'` or pre-compute if needed.
- VIZ 17 (drawdown extraction) uses a Python loop over the entire equity series. For 30+ year series this runs in ~1 second.
- VIZ 16 trade duration: computing calendar days requires indexing `ohlc['close'].index[exit_idx]` for every trade — ~0.01s even for 1000 trades.
- All charts render independently; if one fails, it does not abort the others (each VIZ function has its own try/except for optional data).

---

## Full Working Example

See `examples/02_full_clenow2_example.py` for a complete working integration
with the FTT Clenow 2 P24 Universe strategy that demonstrates every feature.
