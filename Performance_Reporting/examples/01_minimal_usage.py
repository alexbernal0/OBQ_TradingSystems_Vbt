"""
01_minimal_usage.py
===================
Minimal OBQ Performance Reporting example.
Only requires a NAV Series (daily portfolio equity).

Renders 14 charts (those that don't require a benchmark or VBT portfolio).
Run inside a Jupyter Notebook for interactive Plotly output.
"""

import sys
import numpy as np
import pandas as pd

# ── Add project root to path ──────────────────────────────────────────────────
# Adjust this path to point to the folder containing Performance_Reporting/
sys.path.insert(0, r"C:\path\to\your\project")

from Performance_Reporting import run_tearsheet


# ── 1. Generate a synthetic NAV series ───────────────────────────────────────
# In your real strategy, this comes from: pf.value().iloc[:, 0]

np.random.seed(42)
n_days = 252 * 5          # 5 years of daily data
dates  = pd.bdate_range("2019-01-02", periods=n_days)

# Simulate a trend-following NAV: mild positive drift + fat tails
daily_returns = np.random.normal(0.0003, 0.008, n_days)        # mean 7.5%/yr, vol ~12.7%
daily_returns += np.random.choice([0, 0.02, -0.015], n_days,   # occasional jumps
                                   p=[0.97, 0.015, 0.015])

equity = pd.Series(
    100_000 * np.cumprod(1 + daily_returns),
    index=dates,
    name="Demo Strategy"
)


# ── 2. Run tearsheet ─────────────────────────────────────────────────────────
results = run_tearsheet(
    nav=equity,
    strategy_name="Demo Trend Strategy",
    initial_capital=100_000.0,
    # benchmark=None     ← omitted: skips VIZ 3, 4, 7 excess column, 8/9 bench overlay,
    #                               14 left panel, 18 regime analysis
    # pf=None            ← omitted: skips VIZ 15 (sector), 16 (trade duration)
)

# ── 3. Inspect results ────────────────────────────────────────────────────────
print("\n--- Results dict keys ---")
for k, v in results.items():
    print(f"  {k}: {type(v).__name__}")

print("\n--- Core Metrics ---")
for metric, value in results["metrics_strategy"].items():
    print(f"  {metric}: {value}")
