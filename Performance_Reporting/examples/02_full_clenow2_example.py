"""
02_full_clenow2_example.py
===========================
Full OBQ Performance Reporting example using the FTT Clenow 2 P24 Universe strategy.
Demonstrates ALL 19 charts with all optional parameters passed.

This is the exact integration used in PWB_FFT_Clenow2.ipynb.
Run inside a Jupyter Notebook for interactive Plotly output.

Pipeline:
  1. Load pre-built Clenow 2 artifacts (or run the full backtest)
  2. Call run_tearsheet() with all parameters
  3. Inspect the returned results dict

Prerequisites:
  - D:/Master Data Backup 2025/PapersWBacktest/PWBBacktest_Data/p24_cache/ (parquet files)
  - All pwb_strategies/clenow2_*.py modules
  - Performance_Reporting/ package in sys.path
"""

import sys
import importlib

# ── Paths ─────────────────────────────────────────────────────────────────────
PROJECT_ROOT = r"D:\Master Data Backup 2025\PapersWBacktest"
sys.path.insert(0, PROJECT_ROOT)

# ── Imports ───────────────────────────────────────────────────────────────────
import warnings
warnings.filterwarnings("ignore")

import numpy as np
import pandas as pd

import pwb_strategies.clenow2_config    as _cfg
import pwb_strategies.clenow2_data      as _data
import pwb_strategies.clenow2_signals   as _sigs
import pwb_strategies.clenow2_portfolio as _port
import pwb_strategies.clenow2_report    as _rep

from Performance_Reporting import run_tearsheet


# ── Step 1: Configure ─────────────────────────────────────────────────────────
params = _cfg.PARAMS.copy()
# Override any params here if needed:
# params["atr_multiplier"] = 3.0
# params["leverage"] = 5

print("Config loaded.")
print(f"  Strategy params: {params}")


# ── Step 2: Load Data ─────────────────────────────────────────────────────────
print("\nLoading P24 universe data...")
ohlc      = _data.load_p24_universe(params)
benchmark = _data.load_benchmark(params)

close = ohlc["close"]
print(f"  Universe: {len(close.columns)} symbols × {len(close):,} bars")
print(f"  Date range: {close.index[0].date()} → {close.index[-1].date()}")


# ── Step 3: Indicators ────────────────────────────────────────────────────────
print("\nComputing indicators...")
indicators = _sigs.compute_indicators(ohlc, params)


# ── Step 4: Signals ───────────────────────────────────────────────────────────
print("Computing signals...")
signals = _sigs.compute_signals(ohlc, indicators, params)
print(f"  Long entries: {signals['long_entries'].sum().sum():,.0f}")
print(f"  Short entries: {signals['short_entries'].sum().sum():,.0f}")


# ── Step 5: Backtest ──────────────────────────────────────────────────────────
print("\nRunning VBT backtest...")
pf = _port.run_backtest(ohlc, signals, params)
print(f"  Final NAV: ${pf.value().iloc[-1, 0]:,.0f}")


# ── Step 6: Extract NAV ───────────────────────────────────────────────────────
nav = _rep.extract_nav(pf)
print(f"\nNAV extracted: {len(nav):,} bars, "
      f"${nav.iloc[0]:,.0f} → ${nav.iloc[-1]:,.0f}")


# ── Step 7: Contract Specs ────────────────────────────────────────────────────
specs = _cfg.CONTRACT_SPECS
print(f"\nContract specs: {len(specs)} instruments across "
      f"{specs['sector'].nunique()} sectors")


# ── Step 8: Run Full 19-Chart Tearsheet ───────────────────────────────────────
print("\n" + "=" * 70)
print("  OBQ PERFORMANCE REPORT — FTT Clenow 2 P24 Universe")
print("=" * 70)

results = run_tearsheet(
    nav=nav,
    benchmark=benchmark,
    long_entries=signals["long_entries"],
    strategy_name="FTT Clenow 2 — P24 Universe",
    initial_capital=params.get("init_cash", 100_000.0),

    # ── VBT extras — enables VIZ 15 (sector attribution) + VIZ 16 (trade duration)
    pf=pf,
    contract_specs=specs if not specs.empty else None,
    ohlc=ohlc,
)

print("\n" + "=" * 70)
print("  All 19 visualizations complete!")
print("=" * 70)


# ── Step 9: Inspect Results ───────────────────────────────────────────────────
print("\n--- Core Performance Metrics ---")
m = results["metrics_strategy"]
print(f"  CAGR:         {m['CAGR']:.2f}%")
print(f"  Sharpe:       {m['Sharpe Ratio']:.3f}")
print(f"  Sortino:      {m['Sortino Ratio']:.3f}")
print(f"  Max Drawdown: {m['Max Drawdown']:.2f}%")
print(f"  Calmar:       {m['Calmar Ratio']:.3f}")
print(f"  Monthly WR:   {m['Win Rate']:.1f}%")
print(f"  SystemScore:  {m['SystemScore']:.2f}")

if results["metrics_benchmark"]:
    print("\n--- Benchmark Metrics ---")
    b = results["metrics_benchmark"]
    print(f"  CAGR:         {b['CAGR']:.2f}%")
    print(f"  Sharpe:       {b['Sharpe Ratio']:.3f}")
    print(f"  Max Drawdown: {b['Max Drawdown']:.2f}%")

print("\n--- Final NAV ---")
print(f"  Strategy:  ${results['equity_strategy'].iloc[-1]:,.0f}")
if results["equity_benchmark"] is not None:
    print(f"  Benchmark: ${results['equity_benchmark'].iloc[-1]:,.0f}")
    alpha = results['equity_strategy'].iloc[-1] - results['equity_benchmark'].iloc[-1]
    print(f"  Alpha $:   ${alpha:,.0f}")

# ── Optional: Current positions and last trading activity ────────────────────
print("\n--- Current Portfolio Positions ---")
pos_df = _rep.build_position_summary(
    pf, ohlc, indicators, params,
    contract_specs=specs if not specs.empty else None
)
if pos_df.empty:
    print("  No open positions.")
else:
    from IPython.display import display
    print(f"  {len(pos_df)} open position(s) as of {ohlc['close'].index[-1].date()}")
    display(pos_df)

print("\n--- Last Trading Activity ---")
act_df, act_date = _rep.build_last_activity(pf, ohlc)
if act_df.empty:
    print("  No order history.")
else:
    from IPython.display import display
    print(f"  {len(act_df)} trade(s) on {act_date}")
    display(act_df)
