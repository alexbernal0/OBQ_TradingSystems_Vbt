"""
Performance_Reporting
=====================
OBQ institutional-grade Plotly performance reporting for VectorBT strategies.

19 interactive visualizations covering:
  - Equity curve & drawdown
  - Extended metrics (CVaR, Ulcer, Lake, Omega, Sharpe t-stat, IR, Capture)
  - Benchmark comparison (4 views)
  - Up/Down capture ratios
  - Monthly + intra-month drawdown heatmaps
  - Annual performance table
  - Rolling Sharpe, Sortino, Vol, Max DD
  - Omega curve, return distribution, Q-Q plot, ACF/PACF
  - Active returns & best/worst months
  - Sector attribution (Long vs Short)
  - Trade duration analysis (4-panel)
  - Complete drawdown table with recovery
  - Market regime analysis (Bull/Bear)
  - Crisis periods (8 events)

Quick Start
-----------
    from Performance_Reporting import run_tearsheet

    run_tearsheet(
        nav=nav_series,
        benchmark=spx_series,
        long_entries=signals['long_entries'],
        strategy_name="My Strategy",
        initial_capital=100_000.0,
        pf=vbt_portfolio,          # optional — enables trade analytics + sector attribution
        contract_specs=specs_df,   # optional — enables sector mapping
        ohlc=ohlc_dict,            # optional — enables trade duration in calendar days
    )
"""

from .tearsheet import run_tearsheet, STRATEGY_COLOR, BENCHMARK_COLOR

__all__ = ["run_tearsheet", "STRATEGY_COLOR", "BENCHMARK_COLOR"]
