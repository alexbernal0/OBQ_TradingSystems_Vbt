"""
QGSI_Performance_Reporting/tearsheet.py
========================================
Plotly-based comprehensive performance reporting — institutional grade.
19 interactive visualizations for strategy vs benchmark analysis.

Visualizations
--------------
Section 1 — Overview
  1.  Equity Curve + Drawdown Underwater
  2.  Extended Performance Metrics Table (CVaR, Ulcer, Lake, Omega, t-stat, IR)

Section 2 — Benchmark Analysis
  3.  Benchmark Comparison 2x2 Grid
  4.  Up / Down Capture Ratios

Section 3 — Calendar Performance
  5.  Monthly Returns Heatmap
  6.  Intra-Month Max Drawdown Heatmap
  7.  Annual Performance Table

Section 4 — Rolling Risk
  8.  Rolling Sharpe & Sortino (1x2)
  9.  Rolling Volatility & Max Drawdown (1x2)

Section 5 — Return Distribution
  10. Omega Ratio Curve
  11. Return Distribution & Quantile Boxes
  12. Distribution Moments + Q-Q Plot
  13. Return Autocorrelation ACF / PACF

Section 6 — Active Returns & Attribution
  14. Monthly Active Returns & Best/Worst Analysis
  15. Sector Attribution by Long / Short

Section 7 — Trade Analytics
  16. Trade Duration Analysis

Section 8 — Drawdown Deep Dive
  17. Complete Drawdown Table with Recovery

Section 9 — Regime & Crisis
  18. Performance by Market Regime
  19. Crisis Periods Analysis (2x4 Grid)
"""

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

try:
    from scipy import stats as _scipy_stats
    _HAS_SCIPY = True
except ImportError:
    _HAS_SCIPY = False

STRATEGY_COLOR  = '#1f77b4'   # blue
BENCHMARK_COLOR = '#ff7f0e'   # orange

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


# ─── PUBLIC ENTRY POINT ───────────────────────────────────────────────────────

def run_tearsheet(
    nav: pd.Series,
    benchmark: pd.Series = None,
    long_entries=None,
    strategy_name: str = "Strategy",
    initial_capital: float = 100_000.0,
    pf=None,
    contract_specs=None,
    ohlc: dict = None,
) -> dict:
    """
    Run all 19 QGSI performance visualizations.

    Parameters
    ----------
    nav            : pd.Series — portfolio equity curve (daily dollar values).
    benchmark      : pd.Series — benchmark price series (raw; rebased to nav start).
    long_entries   : pd.DataFrame or pd.Series (bool) — entry signals.
    strategy_name  : str — displayed in chart titles.
    initial_capital: float — horizontal guide line on equity curve.
    pf             : VBT Portfolio object (for trade analytics + sector attribution).
    contract_specs : pd.DataFrame with sector column (for sector attribution).
    ohlc           : dict with 'close' key (for symbol names / bar index).

    Returns
    -------
    dict with keys: equity_strategy, equity_benchmark,
                    returns_strategy, returns_benchmark,
                    metrics_strategy, metrics_benchmark
    """
    # ── Align equity curves ───────────────────────────────────────────────────
    equity_strategy = nav.copy()

    if benchmark is not None:
        common = equity_strategy.index.intersection(benchmark.index)
        equity_strategy  = equity_strategy.loc[common]
        bench_raw        = benchmark.loc[common]
        equity_benchmark = bench_raw / bench_raw.iloc[0] * equity_strategy.iloc[0]
    else:
        equity_benchmark = None

    returns_strategy  = equity_strategy.pct_change().dropna()
    returns_benchmark = (
        equity_benchmark.pct_change().dropna() if equity_benchmark is not None else None
    )

    # ── Monthly returns ───────────────────────────────────────────────────────
    monthly_returns_strat = (
        returns_strategy.resample('ME').apply(lambda x: (1 + x).prod() - 1) * 100
    )
    monthly_returns_bench = (
        returns_benchmark.resample('ME').apply(lambda x: (1 + x).prod() - 1) * 100
        if returns_benchmark is not None else None
    )

    # ── Metrics ───────────────────────────────────────────────────────────────
    metrics_strategy  = _compute_metrics(returns_strategy,  equity_strategy)
    metrics_benchmark = (
        _compute_metrics(returns_benchmark, equity_benchmark)
        if returns_benchmark is not None else {}
    )

    # ── Entry signal (any symbol per bar) ─────────────────────────────────────
    if long_entries is not None:
        if isinstance(long_entries, pd.DataFrame):
            breakout_signal = long_entries.any(axis=1).reindex(equity_strategy.index).fillna(False)
        else:
            breakout_signal = long_entries.reindex(equity_strategy.index).fillna(False)
    else:
        breakout_signal = pd.Series(False, index=equity_strategy.index)

    # ── Run all 19 charts ─────────────────────────────────────────────────────
    print(f"\nCreating comprehensive visualizations for: {strategy_name}")

    # Section 1 — Overview
    _viz1_equity_drawdown(
        equity_strategy, equity_benchmark, breakout_signal,
        metrics_strategy, strategy_name, initial_capital
    )
    _viz2_extended_metrics(
        returns_strategy, equity_strategy,
        returns_benchmark, equity_benchmark,
        monthly_returns_strat, monthly_returns_bench,
        strategy_name
    )

    # Section 2 — Benchmark Analysis
    _viz3_benchmark_comparison(
        equity_strategy, equity_benchmark, returns_strategy, returns_benchmark
    )
    _viz4_capture_ratios(monthly_returns_strat, monthly_returns_bench)

    # Section 3 — Calendar Performance
    _viz5_monthly_heatmap(monthly_returns_strat)
    _viz6_intramonth_dd_heatmap(equity_strategy)
    _viz7_annual_table(returns_strategy, returns_benchmark)

    # Section 4 — Rolling Risk
    _viz8_rolling_risk_adjusted(returns_strategy, returns_benchmark)
    _viz9_rolling_risk_metrics(
        equity_strategy, equity_benchmark, returns_strategy, returns_benchmark
    )

    # Section 5 — Return Distribution
    _viz10_omega_curve(monthly_returns_strat, monthly_returns_bench)
    _viz11_distribution(monthly_returns_strat, monthly_returns_bench)
    _viz12_moments_qq(monthly_returns_strat)
    _viz13_acf(monthly_returns_strat)

    # Section 6 — Active Returns & Attribution
    _viz14_active_returns(
        returns_strategy, returns_benchmark,
        monthly_returns_strat, monthly_returns_bench
    )
    _viz15_sector_attribution(pf, contract_specs, ohlc)

    # Section 7 — Trade Analytics
    _viz16_trade_duration(pf, ohlc)

    # Section 8 — Drawdown Deep Dive
    _viz17_drawdown_table(equity_strategy)

    # Section 9 — Regime & Crisis
    _viz18_market_regime(returns_strategy, monthly_returns_strat,
                         returns_benchmark, equity_benchmark)
    _viz19_crisis_periods(equity_strategy, equity_benchmark)

    print("\nAll 19 visualizations complete!")

    return {
        "equity_strategy":   equity_strategy,
        "equity_benchmark":  equity_benchmark,
        "returns_strategy":  returns_strategy,
        "returns_benchmark": returns_benchmark,
        "metrics_strategy":  metrics_strategy,
        "metrics_benchmark": metrics_benchmark,
    }


# ─── METRICS HELPERS ──────────────────────────────────────────────────────────

def _compute_metrics(returns: pd.Series, equity: pd.Series) -> dict:
    """Basic 7 metrics used in VIZ 1 title bar."""
    n_years  = len(returns) / 252
    cagr     = ((equity.iloc[-1] / equity.iloc[0]) ** (1 / n_years) - 1) * 100 if n_years > 0 else 0.0
    sharpe   = returns.mean() / returns.std() * np.sqrt(252) if returns.std() != 0 else 0.0
    downside = returns[returns < 0].std()
    sortino  = returns.mean() / downside * np.sqrt(252) if downside != 0 else 0.0
    rolling_max = equity.cummax()
    dd          = (equity - rolling_max) / rolling_max
    max_dd      = dd.min() * 100
    calmar      = (cagr / abs(max_dd)) if max_dd != 0 else 0.0
    monthly     = returns.resample('ME').apply(lambda x: (1 + x).prod() - 1)
    win_rate    = (monthly > 0).sum() / len(monthly) * 100 if len(monthly) > 0 else 0.0
    system_score = round(sharpe * calmar, 2) if calmar != 0 else 0.0
    return {
        "CAGR":          round(cagr,     2),
        "Sharpe Ratio":  round(sharpe,   2),
        "Sortino Ratio": round(sortino,  2),
        "Max Drawdown":  round(max_dd,   2),
        "Calmar Ratio":  round(calmar,   2),
        "Win Rate":      round(win_rate, 2),
        "SystemScore":   system_score,
    }


def _compute_all_metrics(returns: pd.Series, equity: pd.Series,
                          returns_b: pd.Series = None,
                          equity_b: pd.Series = None) -> dict:
    """Extended metrics for VIZ 2 table."""
    n_obs   = len(returns)
    n_years = n_obs / 252
    cagr    = ((equity.iloc[-1] / equity.iloc[0]) ** (1 / n_years) - 1) * 100 if n_years > 0 else 0.0
    ann_vol = returns.std() * np.sqrt(252) * 100
    sharpe  = returns.mean() / returns.std() * np.sqrt(252) if returns.std() != 0 else 0.0
    downside = returns[returns < 0].std()
    sortino  = returns.mean() / downside * np.sqrt(252) if downside != 0 else 0.0

    rolling_max  = equity.cummax()
    dd_series    = (equity - rolling_max) / rolling_max
    max_dd       = dd_series.min() * 100
    calmar       = (cagr / abs(max_dd)) if max_dd != 0 else 0.0

    monthly  = returns.resample('ME').apply(lambda x: (1 + x).prod() - 1)
    win_rate = (monthly > 0).sum() / len(monthly) * 100 if len(monthly) > 0 else 0.0

    # CVaR (Expected Shortfall)
    cvar_95 = returns[returns <= returns.quantile(0.05)].mean() * 100
    cvar_99 = returns[returns <= returns.quantile(0.01)].mean() * 100

    # Ulcer Index (sqrt of mean squared drawdown %)
    dd_pct   = dd_series * 100
    ulcer    = np.sqrt((dd_pct ** 2).mean())

    # Pain Index (mean absolute drawdown %)
    pain_idx = dd_pct.abs().mean()

    # Serenity Ratio = CAGR / Ulcer Index
    serenity = cagr / ulcer if ulcer > 0 else np.nan

    # Pain Ratio = CAGR / Pain Index
    pain_ratio = cagr / pain_idx if pain_idx > 0 else np.nan

    # Lake Ratio = 1 - mean(nav / nav.cummax())
    lake_ratio = 1.0 - (equity / rolling_max).mean()

    # Omega Ratio (threshold = 0)
    r = returns.values
    gains  = np.sum(np.maximum(r, 0))
    losses = np.sum(np.maximum(-r, 0))
    omega  = gains / losses if losses > 0 else np.nan

    # Sharpe t-statistic + CI + Haircut
    sr_se = np.sqrt((1 + 0.5 * sharpe ** 2) / n_obs) if n_obs > 1 else np.nan
    sr_t  = sharpe / sr_se if (sr_se and sr_se > 0) else np.nan
    sr_ci_lo = sharpe - 1.96 * sr_se if sr_se else np.nan
    sr_ci_hi = sharpe + 1.96 * sr_se if sr_se else np.nan
    haircut_sr = sr_ci_lo  # lower bound of 95% CI

    # vs Benchmark
    info_ratio  = np.nan
    tracking_er = np.nan
    up_capture  = np.nan
    down_capture = np.nan

    if returns_b is not None and len(returns_b) > 10:
        common = returns.index.intersection(returns_b.index)
        rs = returns.loc[common]
        rb = returns_b.loc[common]
        active = rs - rb
        tracking_er = active.std() * np.sqrt(252) * 100
        info_ratio  = active.mean() * 252 / (active.std() * np.sqrt(252)) if active.std() > 0 else np.nan

        # Monthly up/down capture
        ms = (rs.resample('ME').apply(lambda x: (1 + x).prod() - 1))
        mb = (rb.resample('ME').apply(lambda x: (1 + x).prod() - 1))
        cm = ms.index.intersection(mb.index)
        ms, mb = ms.loc[cm], mb.loc[cm]

        up_mask = mb > 0
        dn_mask = mb < 0
        n_up = up_mask.sum()
        n_dn = dn_mask.sum()
        if n_up > 0:
            s_up_ann = (1 + ms[up_mask]).prod() ** (12 / n_up) - 1
            b_up_ann = (1 + mb[up_mask]).prod() ** (12 / n_up) - 1
            up_capture = s_up_ann / b_up_ann * 100 if b_up_ann != 0 else np.nan
        if n_dn > 0:
            s_dn_ann = (1 + ms[dn_mask]).prod() ** (12 / n_dn) - 1
            b_dn_ann = (1 + mb[dn_mask]).prod() ** (12 / n_dn) - 1
            down_capture = s_dn_ann / b_dn_ann * 100 if b_dn_ann != 0 else np.nan

    return {
        "CAGR (%)":               round(cagr,       2),
        "Annual Vol (%)":         round(ann_vol,     2),
        "Sharpe Ratio":           round(sharpe,      3),
        "Sortino Ratio":          round(sortino,     3),
        "Calmar Ratio":           round(calmar,      3),
        "Win Rate (Monthly %)":   round(win_rate,    1),
        "Max Drawdown (%)":       round(max_dd,      2),
        "CVaR 95% (daily %)":     round(cvar_95,     3),
        "CVaR 99% (daily %)":     round(cvar_99,     3),
        "Ulcer Index":            round(ulcer,       3),
        "Pain Index":             round(pain_idx,    3),
        "Serenity Ratio":         round(serenity,    3) if not np.isnan(serenity) else "—",
        "Pain Ratio":             round(pain_ratio,  3) if not np.isnan(pain_ratio) else "—",
        "Lake Ratio":             round(lake_ratio,  4),
        "Omega Ratio":            round(omega,       3) if not np.isnan(omega) else "—",
        "Sharpe t-stat":          round(sr_t,        2) if not np.isnan(sr_t) else "—",
        "Sharpe 95% CI":          f"[{sr_ci_lo:.2f}, {sr_ci_hi:.2f}]" if not np.isnan(sr_ci_lo) else "—",
        "Haircut Sharpe":         round(haircut_sr,  3) if not np.isnan(haircut_sr) else "—",
        "Info Ratio":             round(info_ratio,  3) if not np.isnan(info_ratio) else "—",
        "Tracking Error (%)":     round(tracking_er, 2) if not np.isnan(tracking_er) else "—",
        "Up Capture (%)":         round(up_capture,  1) if not np.isnan(up_capture) else "—",
        "Down Capture (%)":       round(down_capture,1) if not np.isnan(down_capture) else "—",
    }


def _manual_acf(x: np.ndarray, nlags: int = 24) -> np.ndarray:
    """Compute autocorrelation function without statsmodels."""
    x = x - x.mean()
    n = len(x)
    c0 = np.dot(x, x) / n
    acfs = []
    for lag in range(1, nlags + 1):
        if lag >= n:
            acfs.append(np.nan)
        else:
            ck = np.dot(x[:-lag], x[lag:]) / n
            acfs.append(ck / c0 if c0 != 0 else 0.0)
    return np.array(acfs)


def _extract_drawdowns(equity: pd.Series, min_dd_pct: float = -2.0) -> pd.DataFrame:
    """Extract all completed (and current) drawdown periods >= min_dd_pct."""
    rolling_max = equity.cummax()
    dd_pct      = (equity - rolling_max) / rolling_max * 100

    rows         = []
    in_dd        = False
    start_date   = None
    peak_val     = None
    trough_val   = None
    trough_date  = None

    dates  = equity.index
    values = equity.values

    for i, (date, val) in enumerate(zip(dates, values)):
        if not in_dd:
            if dd_pct.iloc[i] < 0:
                in_dd      = True
                start_date = date
                peak_val   = rolling_max.iloc[i]
                trough_val = val
                trough_date = date
        else:
            if val < trough_val:
                trough_val  = val
                trough_date = date
            if dd_pct.iloc[i] >= -0.001:   # recovered
                depth = (trough_val - peak_val) / peak_val * 100
                if depth <= min_dd_pct:
                    rows.append({
                        "Start":                  start_date.date(),
                        "Trough":                 trough_date.date(),
                        "Recovery":               date.date(),
                        "Depth (%)":              round(depth, 2),
                        "Drawdown (days)":        (trough_date - start_date).days,
                        "Recovery (days)":        (date - trough_date).days,
                        "Total (days)":           (date - start_date).days,
                    })
                in_dd = False
                start_date = trough_date = peak_val = trough_val = None

    # Ongoing drawdown at end of series
    if in_dd and start_date is not None:
        depth = (trough_val - peak_val) / peak_val * 100
        if depth <= min_dd_pct:
            rows.append({
                "Start":             start_date.date(),
                "Trough":            trough_date.date(),
                "Recovery":          "Ongoing",
                "Depth (%)":         round(depth, 2),
                "Drawdown (days)":   (trough_date - start_date).days,
                "Recovery (days)":   "—",
                "Total (days)":      "—",
            })

    if not rows:
        return pd.DataFrame()
    df = pd.DataFrame(rows)
    return df.sort_values("Depth (%)").reset_index(drop=True)


# ─── VIZ 1: Equity Curve + Drawdown ──────────────────────────────────────────

def _viz1_equity_drawdown(equity_strategy, equity_benchmark, breakout_signal,
                           metrics_strategy, strategy_name, initial_capital):
    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.03,
        row_heights=[0.8, 0.2],
        subplot_titles=(f'{strategy_name} - Equity Curve', 'Drawdown Underwater')
    )

    fig.add_trace(
        go.Scatter(
            x=equity_strategy.index, y=equity_strategy.values,
            name='Portfolio Value',
            line=dict(color=STRATEGY_COLOR, width=2),
            hovertemplate='<b>Date</b>: %{x}<br><b>Value</b>: $%{y:,.2f}<extra></extra>'
        ),
        row=1, col=1
    )

    if equity_benchmark is not None:
        fig.add_trace(
            go.Scatter(
                x=equity_benchmark.index, y=equity_benchmark.values,
                name='Benchmark (SPX)',
                line=dict(color=BENCHMARK_COLOR, width=2, dash='dash'),
                hovertemplate='<b>Date</b>: %{x}<br><b>Benchmark</b>: $%{y:,.2f}<extra></extra>'
            ),
            row=1, col=1
        )

    fig.add_hline(
        y=initial_capital, line_dash="dash", line_color="gray",
        annotation_text="Initial Capital", row=1, col=1
    )

    entry_dates = breakout_signal[breakout_signal].index
    if len(entry_dates) > 0:
        entry_prices = equity_strategy.reindex(entry_dates)
        fig.add_trace(
            go.Scatter(
                x=entry_dates, y=entry_prices.values,
                mode='markers', name='Long Entry',
                marker=dict(symbol='triangle-up', size=6, color='green'),
                hovertemplate='<b>Entry</b><br>Date: %{x}<br>Value: $%{y:,.2f}<extra></extra>'
            ),
            row=1, col=1
        )

    rolling_max  = equity_strategy.cummax()
    drawdown_pct = ((equity_strategy - rolling_max) / rolling_max) * 100
    fig.add_trace(
        go.Scatter(
            x=drawdown_pct.index, y=drawdown_pct.values,
            name='Drawdown %', fill='tozeroy',
            line=dict(color='#E45756', width=1),
            hovertemplate='<b>Date</b>: %{x}<br><b>Drawdown</b>: %{y:.2f}%<extra></extra>'
        ),
        row=2, col=1
    )

    fig.update_xaxes(title_text="Date", row=2, col=1)
    fig.update_yaxes(title_text="Portfolio Value ($)", row=1, col=1)
    fig.update_yaxes(title_text="Drawdown (%)", row=2, col=1)

    m = metrics_strategy
    fig.update_layout(
        title=(
            f"<b>{strategy_name} - Performance</b><br>"
            f"<sub>CAGR: {m['CAGR']:.2f}% | Sharpe: {m['Sharpe Ratio']:.2f} | "
            f"Max DD: {m['Max Drawdown']:.2f}% | "
            f"Win Rate: {m['Win Rate']:.2f}% | SystemScore: {m.get('SystemScore', 0):.2f}</sub>"
        ),
        height=700, showlegend=True, hovermode='x unified', template='plotly_white'
    )
    fig.show()
    print("  Visualization 1 complete: Equity Curve + Drawdown")


# ─── VIZ 2: Extended Metrics Table ───────────────────────────────────────────

def _viz2_extended_metrics(returns_s, equity_s, returns_b, equity_b,
                            monthly_s, monthly_b, strategy_name):
    all_m  = _compute_all_metrics(returns_s, equity_s, returns_b, equity_b)
    bench_m = (
        _compute_all_metrics(returns_b, equity_b)
        if returns_b is not None else {}
    )

    section_groups = [
        ("RETURNS",  ["CAGR (%)", "Annual Vol (%)", "Sharpe Ratio", "Sortino Ratio",
                       "Calmar Ratio", "Win Rate (Monthly %)"]),
        ("RISK",     ["Max Drawdown (%)", "CVaR 95% (daily %)", "CVaR 99% (daily %)",
                       "Ulcer Index", "Pain Index", "Lake Ratio"]),
        ("ADVANCED", ["Omega Ratio", "Serenity Ratio", "Pain Ratio",
                       "Sharpe t-stat", "Sharpe 95% CI", "Haircut Sharpe"]),
        ("VS BENCHMARK", ["Info Ratio", "Tracking Error (%)",
                           "Up Capture (%)", "Down Capture (%)"]),
    ]

    metric_names  = []
    strat_vals    = []
    bench_vals    = []
    row_colors_s  = []
    row_colors_b  = []

    for section, keys in section_groups:
        # Section header row
        metric_names.append(f"── {section} ──")
        strat_vals.append("")
        bench_vals.append("")
        row_colors_s.append("#2c3e50")
        row_colors_b.append("#2c3e50")

        for k in keys:
            v_s = all_m.get(k, "—")
            v_b = bench_m.get(k, "—") if bench_m else "—"
            metric_names.append(k)
            strat_vals.append(str(v_s))
            bench_vals.append(str(v_b))

            # Color numeric cells
            def _color(v):
                try:
                    fv = float(str(v).replace("%", "").replace(",", ""))
                    if k in ["Max Drawdown (%)", "CVaR 95% (daily %)", "CVaR 99% (daily %)",
                              "Ulcer Index", "Pain Index", "Lake Ratio", "Down Capture (%)"]:
                        return "#fde8e8" if fv < 0 else "white"
                    return "white"
                except Exception:
                    return "white"

            row_colors_s.append(_color(v_s))
            row_colors_b.append(_color(v_b))

    header_vals = ["<b>Metric</b>", f"<b>{strategy_name}</b>"]
    cell_vals   = [metric_names, strat_vals]
    cell_colors = [
        ["#34495e" if "──" in n else "white" for n in metric_names],
        row_colors_s,
    ]
    font_colors_list = [
        ["white" if "──" in n else "black" for n in metric_names],
        ["white" if s == "" else "black" for s in strat_vals],
    ]

    if returns_b is not None:
        header_vals.append("<b>Benchmark</b>")
        cell_vals.append(bench_vals)
        cell_colors.append(row_colors_b)
        font_colors_list.append(
            ["white" if b == "" else "black" for b in bench_vals]
        )

    fig = go.Figure(data=[go.Table(
        columnwidth=[220, 120, 120],
        header=dict(
            values=header_vals,
            fill_color="#1f2d3d",
            align='center',
            font=dict(size=12, family='Arial', color='white')
        ),
        cells=dict(
            values=cell_vals,
            fill_color=cell_colors,
            align=['left', 'center', 'center'],
            font=dict(size=11, family='Arial', color=font_colors_list),
            height=26
        )
    )])

    n_rows = len(metric_names)
    fig.update_layout(
        title=f"<b>Extended Performance Metrics — {strategy_name}</b>",
        height=max(500, n_rows * 26 + 100),
        margin=dict(l=10, r=10, t=50, b=10),
        template='plotly_white'
    )
    fig.show()
    print("  Visualization 2 complete: Extended Metrics Table")


# ─── VIZ 3: Benchmark Comparison 2x2 ─────────────────────────────────────────

def _viz3_benchmark_comparison(equity_strategy, equity_benchmark,
                                returns_strategy, returns_benchmark):
    cum_returns_strat = (1 + returns_strategy).cumprod()

    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=(
            'Cumulative Returns vs Benchmark',
            'Cumulative Returns (Log Scale)',
            'Volatility Matched Returns',
            'Cumulative Alpha (Strategy - Benchmark)'
        ),
        vertical_spacing=0.12,
        horizontal_spacing=0.1
    )

    fig.add_trace(
        go.Scatter(x=cum_returns_strat.index, y=cum_returns_strat.values,
                   name='Strategy', line=dict(color=STRATEGY_COLOR, width=2)),
        row=1, col=1
    )
    fig.add_trace(
        go.Scatter(x=cum_returns_strat.index, y=cum_returns_strat.values,
                   name='Strategy', line=dict(color=STRATEGY_COLOR, width=2),
                   showlegend=False),
        row=1, col=2
    )
    fig.update_yaxes(type="log", row=1, col=2)

    if returns_benchmark is not None:
        cum_returns_bench = (1 + returns_benchmark).cumprod()

        fig.add_trace(
            go.Scatter(x=cum_returns_bench.index, y=cum_returns_bench.values,
                       name='Benchmark', line=dict(color=BENCHMARK_COLOR, width=2)),
            row=1, col=1
        )
        fig.add_trace(
            go.Scatter(x=cum_returns_bench.index, y=cum_returns_bench.values,
                       name='Benchmark', line=dict(color=BENCHMARK_COLOR, width=2),
                       showlegend=False),
            row=1, col=2
        )

        vol_strat = returns_strategy.std()
        vol_bench = returns_benchmark.std()
        vol_adj   = vol_strat / vol_bench if vol_bench != 0 else 1.0
        cum_bench_adj = (1 + returns_benchmark * vol_adj).cumprod()

        fig.add_trace(
            go.Scatter(x=cum_returns_strat.index, y=cum_returns_strat.values,
                       name='Strategy', line=dict(color=STRATEGY_COLOR, width=2),
                       showlegend=False),
            row=2, col=1
        )
        fig.add_trace(
            go.Scatter(x=cum_bench_adj.index, y=cum_bench_adj.values,
                       name='Benchmark (Vol Matched)',
                       line=dict(color=BENCHMARK_COLOR, width=2, dash='dash'),
                       showlegend=False),
            row=2, col=1
        )

        excess_equity = equity_strategy - equity_benchmark.reindex(equity_strategy.index)
        fill_color = (
            'rgba(0,200,0,0.15)' if excess_equity.iloc[-1] > 0 else 'rgba(200,0,0,0.15)'
        )
        fig.add_trace(
            go.Scatter(
                x=excess_equity.index, y=excess_equity.values,
                name='Alpha', fill='tozeroy',
                line=dict(color='green' if excess_equity.iloc[-1] > 0 else 'red', width=2),
                fillcolor=fill_color, showlegend=False
            ),
            row=2, col=2
        )
        fig.add_hline(y=0, line_dash="dash", line_color="gray", row=2, col=2)

        vol_s_ann = vol_strat * 100 * np.sqrt(252)
        vol_b_ann = vol_bench * 100 * np.sqrt(252)
        sub = (
            f"Strategy Vol: {vol_s_ann:.2f}% | Benchmark Vol: {vol_b_ann:.2f}% | "
            f"Final Excess: ${excess_equity.iloc[-1]:,.0f}"
        )
    else:
        sub = "No benchmark provided"

    fig.update_layout(
        title=f"<b>Benchmark Comparison Analysis</b><br><sub>{sub}</sub>",
        height=800, showlegend=True, template='plotly_white'
    )
    fig.show()
    print("  Visualization 3 complete: Benchmark Comparison 2x2")


# ─── VIZ 4: Up / Down Capture Ratios ─────────────────────────────────────────

def _viz4_capture_ratios(monthly_returns_strat, monthly_returns_bench):
    if monthly_returns_bench is None:
        print("  Visualization 4 skipped: no benchmark for capture ratios")
        return

    common = monthly_returns_strat.index.intersection(monthly_returns_bench.index)
    ms = monthly_returns_strat.loc[common] / 100
    mb = monthly_returns_bench.loc[common] / 100

    up_mask = mb > 0
    dn_mask = mb < 0
    n_up = up_mask.sum()
    n_dn = dn_mask.sum()

    def _annualize(r_vec, n):
        return (1 + r_vec).prod() ** (12 / n) - 1 if n > 0 else np.nan

    s_up_ann = _annualize(ms[up_mask], n_up) if n_up > 0 else np.nan
    b_up_ann = _annualize(mb[up_mask], n_up) if n_up > 0 else np.nan
    s_dn_ann = _annualize(ms[dn_mask], n_dn) if n_dn > 0 else np.nan
    b_dn_ann = _annualize(mb[dn_mask], n_dn) if n_dn > 0 else np.nan

    up_cap  = s_up_ann / b_up_ann * 100 if (b_up_ann and b_up_ann != 0) else np.nan
    dn_cap  = s_dn_ann / b_dn_ann * 100 if (b_dn_ann and b_dn_ann != 0) else np.nan
    cap_rat = up_cap / dn_cap if (dn_cap and dn_cap != 0) else np.nan

    # Rolling 24-month capture
    roll_up  = []
    roll_dn  = []
    roll_idx = []
    w = 24
    for i in range(w, len(ms) + 1):
        ms_w = ms.iloc[i - w:i]
        mb_w = mb.iloc[i - w:i]
        u_m = mb_w > 0
        d_m = mb_w < 0
        n_u = u_m.sum()
        n_d = d_m.sum()
        su = _annualize(ms_w[u_m], n_u)
        bu = _annualize(mb_w[u_m], n_u)
        sd = _annualize(ms_w[d_m], n_d)
        bd = _annualize(mb_w[d_m], n_d)
        roll_up.append(su / bu * 100 if (bu and bu != 0) else np.nan)
        roll_dn.append(sd / bd * 100 if (bd and bd != 0) else np.nan)
        roll_idx.append(ms.index[i - 1])

    fig = make_subplots(
        rows=1, cols=2,
        subplot_titles=(
            'Up / Down Capture Summary',
            'Rolling 24-Month Capture Ratios'
        ),
        horizontal_spacing=0.12,
        column_widths=[0.4, 0.6]
    )

    # Summary bars
    labels = ['Up Capture', 'Down Capture']
    vals   = [
        round(up_cap, 1) if not np.isnan(up_cap) else 0,
        round(dn_cap, 1) if not np.isnan(dn_cap) else 0,
    ]
    colors = [
        '#2E7D32' if vals[0] >= 100 else '#C62828',
        '#2E7D32' if vals[1] <= 100 else '#C62828',
    ]
    fig.add_trace(
        go.Bar(
            x=labels, y=vals, marker_color=colors,
            text=[f"{v:.1f}%" for v in vals],
            textposition='outside',
            hovertemplate='%{x}: %{y:.1f}%<extra></extra>'
        ),
        row=1, col=1
    )
    fig.add_hline(y=100, line_dash="dash", line_color="black",
                  annotation_text="100%", row=1, col=1)
    fig.update_yaxes(title_text="Capture (%)", range=[0, max(vals) * 1.3 + 10], row=1, col=1)

    cap_ratio_str = f"{cap_rat:.2f}" if not np.isnan(cap_rat) else "—"
    fig.add_annotation(
        text=f"<b>Capture Ratio: {cap_ratio_str}</b><br>"
             f"Up months: {n_up} | Down months: {n_dn}",
        x=0.5, y=0.05, xref="x1 domain", yref="y1 domain",
        showarrow=False, font=dict(size=11),
        bgcolor="rgba(255,255,255,0.8)", bordercolor="gray", borderwidth=1
    )

    # Rolling lines
    if roll_idx:
        fig.add_trace(
            go.Scatter(x=roll_idx, y=roll_up, name='Up Capture',
                       line=dict(color='#2E7D32', width=2)),
            row=1, col=2
        )
        fig.add_trace(
            go.Scatter(x=roll_idx, y=roll_dn, name='Down Capture',
                       line=dict(color='#C62828', width=2, dash='dash')),
            row=1, col=2
        )
        fig.add_hline(y=100, line_dash="dot", line_color="black",
                      annotation_text="100%", row=1, col=2)
        fig.update_yaxes(title_text="Capture (%)", row=1, col=2)

    up_str = f"{up_cap:.1f}" if not np.isnan(up_cap) else "—"
    dn_str = f"{dn_cap:.1f}" if not np.isnan(dn_cap) else "—"
    fig.update_layout(
        title=f"<b>Up/Down Capture Ratios</b><br>"
              f"<sub>Up: {up_str}% | Down: {dn_str}% | Ratio: {cap_ratio_str}</sub>",
        height=450, showlegend=True, template='plotly_white'
    )
    fig.show()
    print("  Visualization 4 complete: Up/Down Capture Ratios")


# ─── VIZ 5: Monthly Returns Heatmap ──────────────────────────────────────────

def _viz5_monthly_heatmap(monthly_returns_strat):
    monthly_pivot = pd.DataFrame({
        'Year':   monthly_returns_strat.index.year,
        'Month':  monthly_returns_strat.index.month,
        'Return': monthly_returns_strat.values
    })
    heatmap_data = monthly_pivot.pivot(index='Year', columns='Month', values='Return')

    ytd_returns = []
    for year in heatmap_data.index:
        year_data = monthly_returns_strat[monthly_returns_strat.index.year == year]
        ytd = ((1 + year_data / 100).prod() - 1) * 100
        ytd_returns.append(ytd)
    heatmap_data['YTD'] = ytd_returns

    month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                   'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec', 'YTD']

    fig = go.Figure(data=go.Heatmap(
        z=heatmap_data.values,
        x=month_names,
        y=heatmap_data.index,
        colorscale='RdYlGn',
        zmid=0,
        text=[
            [f'<b>{val:.2f}%</b>' if not np.isnan(val) else ''
             for val in row]
            for row in heatmap_data.values
        ],
        texttemplate='%{text}',
        textfont={"size": 11, "family": "Arial Black"},
        showscale=False,
        hovertemplate='<b>%{y} %{x}</b><br>Return: %{z:.2f}%<extra></extra>'
    ))

    fig.update_layout(
        title="<b>Monthly Returns Heatmap (%)</b>",
        xaxis_title="Month", yaxis_title="Year",
        height=max(400, len(heatmap_data) * 25),
        template='plotly_white'
    )
    fig.show()
    print("  Visualization 5 complete: Monthly Returns Heatmap")


# ─── VIZ 6: Intra-Month Max Drawdown Heatmap ─────────────────────────────────

def _viz6_intramonth_dd_heatmap(equity_strategy):
    # For each calendar month, compute the worst intra-month drawdown (%)
    dd_map = {}
    grouped = equity_strategy.groupby([equity_strategy.index.year, equity_strategy.index.month])
    for (year, month), grp in grouped:
        if len(grp) < 2:
            dd_map[(year, month)] = np.nan
            continue
        rolling_peak = grp.cummax()
        worst_dd = ((grp - rolling_peak) / rolling_peak * 100).min()
        dd_map[(year, month)] = worst_dd

    years  = sorted(set(k[0] for k in dd_map))
    months = list(range(1, 13))

    z_data = []
    for year in years:
        row = [dd_map.get((year, m), np.nan) for m in months]
        z_data.append(row)

    month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                   'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

    text_data = [
        [f'{v:.1f}%' if not np.isnan(v) else '' for v in row]
        for row in z_data
    ]

    fig = go.Figure(data=go.Heatmap(
        z=z_data,
        x=month_names,
        y=years,
        colorscale='Reds_r',   # deeper red = worse drawdown
        zmid=-5,
        zmax=0,
        text=text_data,
        texttemplate='%{text}',
        textfont={"size": 9, "family": "Arial"},
        colorbar=dict(title="DD %"),
        hovertemplate='<b>%{y} %{x}</b><br>Intra-Month Max DD: %{z:.2f}%<extra></extra>'
    ))

    fig.update_layout(
        title="<b>Intra-Month Maximum Drawdown Heatmap (%)</b>"
              "<br><sub>Worst peak-to-trough within each calendar month</sub>",
        xaxis_title="Month", yaxis_title="Year",
        height=max(400, len(years) * 25),
        template='plotly_white'
    )
    fig.show()
    print("  Visualization 6 complete: Intra-Month Max Drawdown Heatmap")


# ─── VIZ 7: Annual Performance Table ─────────────────────────────────────────

def _viz7_annual_table(returns_strategy, returns_benchmark):
    annual_strat = (
        returns_strategy.resample('YE').apply(lambda x: (1 + x).prod() - 1) * 100
    )
    years = [str(y) for y in annual_strat.index.year]

    header_vals = ['<b>Return (%)</b>'] + [f'<b>{y}</b>' for y in years]
    cell_vals   = [['Model']]
    cell_colors = [['lightgray']]
    font_colors = [['black']]

    if returns_benchmark is not None:
        annual_bench  = (
            returns_benchmark.resample('YE').apply(lambda x: (1 + x).prod() - 1) * 100
        )
        annual_excess = annual_strat - annual_bench
        cell_vals[0]   = ['Model', 'Benchmark', 'Excess']
        cell_colors[0] = ['lightgray', 'lightgray', 'lightgray']
        font_colors[0] = ['black', 'black', 'black']
    else:
        annual_bench  = None
        annual_excess = None

    for i in range(len(years)):
        s = annual_strat.values[i]
        if annual_bench is not None:
            b = annual_bench.values[i]
            e = annual_excess.values[i]
            cell_vals.append([f'{s:.2f}', f'{b:.2f}', f'{e:.2f}'])
            cell_colors.append([
                'white' if s >= 0 else '#ffcccc',
                'white' if b >= 0 else '#ffcccc',
                'white' if e >= 0 else '#ffcccc',
            ])
            font_colors.append([
                'black' if s >= 0 else 'red',
                'black' if b >= 0 else 'red',
                'black' if e >= 0 else 'red',
            ])
        else:
            cell_vals.append([f'{s:.2f}'])
            cell_colors.append(['white' if s >= 0 else '#ffcccc'])
            font_colors.append(['black' if s >= 0 else 'red'])

    fig = go.Figure(data=[go.Table(
        header=dict(
            values=header_vals,
            fill_color='lightgray',
            align='center',
            font=dict(size=11, family='Arial', color='black')
        ),
        cells=dict(
            values=cell_vals,
            fill_color=cell_colors,
            align='center',
            font=dict(size=10, family='Arial', color=font_colors),
            height=25
        )
    )])

    fig.update_layout(
        title="<b>Performance by Calendar Year (%)</b>",
        height=200, margin=dict(l=0, r=0, t=40, b=0)
    )
    fig.show()
    print("  Visualization 7 complete: Annual Performance Table")


# ─── VIZ 8: Rolling Sharpe & Sortino ─────────────────────────────────────────

def _viz8_rolling_risk_adjusted(returns_strategy, returns_benchmark):
    rolling_window = 252

    rolling_sharpe_strat = returns_strategy.rolling(rolling_window).apply(
        lambda x: x.mean() / x.std() * np.sqrt(252) if x.std() != 0 else 0
    )
    rolling_sortino_strat = returns_strategy.rolling(rolling_window).apply(
        lambda x: (x.mean() / x[x < 0].std() * np.sqrt(252)
                   if (x < 0).any() and x[x < 0].std() != 0 else 0)
    )

    fig = make_subplots(
        rows=1, cols=2,
        subplot_titles=('Rolling 252-Day Sharpe Ratio', 'Rolling 252-Day Sortino Ratio'),
        horizontal_spacing=0.1
    )

    fig.add_trace(
        go.Scatter(x=rolling_sharpe_strat.index, y=rolling_sharpe_strat.values,
                   name='Strategy', line=dict(color=STRATEGY_COLOR, width=2)),
        row=1, col=1
    )
    fig.add_trace(
        go.Scatter(x=rolling_sortino_strat.index, y=rolling_sortino_strat.values,
                   name='Strategy', line=dict(color=STRATEGY_COLOR, width=2),
                   showlegend=False),
        row=1, col=2
    )

    if returns_benchmark is not None:
        rolling_sharpe_bench = returns_benchmark.rolling(rolling_window).apply(
            lambda x: x.mean() / x.std() * np.sqrt(252) if x.std() != 0 else 0
        )
        rolling_sortino_bench = returns_benchmark.rolling(rolling_window).apply(
            lambda x: (x.mean() / x[x < 0].std() * np.sqrt(252)
                       if (x < 0).any() and x[x < 0].std() != 0 else 0)
        )
        fig.add_trace(
            go.Scatter(x=rolling_sharpe_bench.index, y=rolling_sharpe_bench.values,
                       name='Benchmark', line=dict(color=BENCHMARK_COLOR, width=2, dash='dash')),
            row=1, col=1
        )
        fig.add_trace(
            go.Scatter(x=rolling_sortino_bench.index, y=rolling_sortino_bench.values,
                       name='Benchmark', line=dict(color=BENCHMARK_COLOR, width=2, dash='dash'),
                       showlegend=False),
            row=1, col=2
        )

    for col_n in [1, 2]:
        fig.add_hline(y=0, line_dash="dot", line_color="gray", row=1, col=col_n)

    fig.update_layout(
        title="<b>Rolling Risk-Adjusted Returns</b>",
        height=400, showlegend=True, template='plotly_white',
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1)
    )
    fig.show()
    print("  Visualization 8 complete: Rolling Sharpe & Sortino")


# ─── VIZ 9: Rolling Volatility & Max DD ──────────────────────────────────────

def _viz9_rolling_risk_metrics(equity_strategy, equity_benchmark,
                                returns_strategy, returns_benchmark):
    rolling_window = 252

    rolling_vol_strat = returns_strategy.rolling(rolling_window).std() * np.sqrt(252) * 100
    rolling_dd_strat  = equity_strategy.rolling(rolling_window).apply(
        lambda x: ((x - x.max()) / x.max()).min() * 100
    )

    fig = make_subplots(
        rows=1, cols=2,
        subplot_titles=('Rolling 252-Day Volatility (%)', 'Rolling 252-Day Max Drawdown (%)'),
        horizontal_spacing=0.1
    )

    fig.add_trace(
        go.Scatter(x=rolling_vol_strat.index, y=rolling_vol_strat.values,
                   name='Strategy', line=dict(color=STRATEGY_COLOR, width=2)),
        row=1, col=1
    )
    fig.add_trace(
        go.Scatter(x=rolling_dd_strat.index, y=rolling_dd_strat.values,
                   name='Strategy', line=dict(color=STRATEGY_COLOR, width=2),
                   showlegend=False),
        row=1, col=2
    )

    if equity_benchmark is not None and returns_benchmark is not None:
        rolling_vol_bench = returns_benchmark.rolling(rolling_window).std() * np.sqrt(252) * 100
        rolling_dd_bench  = equity_benchmark.rolling(rolling_window).apply(
            lambda x: ((x - x.max()) / x.max()).min() * 100
        )
        fig.add_trace(
            go.Scatter(x=rolling_vol_bench.index, y=rolling_vol_bench.values,
                       name='Benchmark', line=dict(color=BENCHMARK_COLOR, width=2, dash='dash')),
            row=1, col=1
        )
        fig.add_trace(
            go.Scatter(x=rolling_dd_bench.index, y=rolling_dd_bench.values,
                       name='Benchmark', line=dict(color=BENCHMARK_COLOR, width=2, dash='dash'),
                       showlegend=False),
            row=1, col=2
        )

    fig.update_layout(
        title="<b>Rolling Risk Metrics</b>",
        height=400, showlegend=True, template='plotly_white',
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1)
    )
    fig.show()
    print("  Visualization 9 complete: Rolling Volatility & Max DD")


# ─── VIZ 10: Omega Ratio Curve ────────────────────────────────────────────────

def _viz10_omega_curve(monthly_returns_strat, monthly_returns_bench):
    # Sweep monthly threshold from -5% to +5%
    thresholds = np.linspace(-5, 5, 200)
    r_s = monthly_returns_strat.values / 100  # fractions

    def _omega(r_arr, thresh_arr):
        omegas = []
        for t in thresh_arr:
            gains  = np.sum(np.maximum(r_arr - t, 0))
            losses = np.sum(np.maximum(t - r_arr, 0))
            omegas.append(gains / losses if losses > 0 else np.nan)
        return np.array(omegas)

    omegas_s = _omega(r_s, thresholds / 100)

    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=thresholds, y=omegas_s,
            name='Strategy',
            line=dict(color=STRATEGY_COLOR, width=2),
            hovertemplate='Threshold: %{x:.2f}%<br>Omega: %{y:.3f}<extra></extra>'
        )
    )

    if monthly_returns_bench is not None:
        r_b = monthly_returns_bench.values / 100
        omegas_b = _omega(r_b, thresholds / 100)
        fig.add_trace(
            go.Scatter(
                x=thresholds, y=omegas_b,
                name='Benchmark',
                line=dict(color=BENCHMARK_COLOR, width=2, dash='dash'),
                hovertemplate='Threshold: %{x:.2f}%<br>Omega: %{y:.3f}<extra></extra>'
            )
        )

    # Mark Omega = 1 line
    fig.add_hline(y=1.0, line_dash="dash", line_color="red",
                  annotation_text="Omega = 1 (breakeven)")
    fig.add_vline(x=0.0, line_dash="dot", line_color="gray",
                  annotation_text="0% threshold")

    # Clip y-axis for readability
    valid_s = omegas_s[~np.isnan(omegas_s) & np.isfinite(omegas_s)]
    y_max   = min(float(np.percentile(valid_s, 95)) * 1.2, 20) if len(valid_s) > 0 else 5

    omega_at_zero = omegas_s[np.argmin(np.abs(thresholds))]
    omega_str = f"{omega_at_zero:.3f}" if not np.isnan(omega_at_zero) else "—"

    fig.update_layout(
        title=f"<b>Omega Ratio Curve</b>"
              f"<br><sub>Omega @ 0% threshold (strategy): {omega_str}</sub>",
        xaxis_title="Monthly Return Threshold (%)",
        yaxis_title="Omega Ratio",
        yaxis=dict(range=[0, y_max]),
        height=450, showlegend=True, template='plotly_white',
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1)
    )
    fig.show()
    print("  Visualization 10 complete: Omega Ratio Curve")


# ─── VIZ 11: Return Distribution & Quantile Boxes ────────────────────────────

def _viz11_distribution(monthly_returns_strat, monthly_returns_bench):
    fig = make_subplots(
        rows=1, cols=2,
        subplot_titles=('Distribution of Monthly Returns', 'Returns Quantiles (Box)'),
        horizontal_spacing=0.1
    )

    fig.add_trace(
        go.Histogram(x=monthly_returns_strat.values, nbinsx=30, name='Strategy',
                     marker=dict(color=STRATEGY_COLOR, opacity=0.6)),
        row=1, col=1
    )
    fig.add_vline(x=monthly_returns_strat.mean(), line_dash="dash",
                  line_color=STRATEGY_COLOR, annotation_text="Strategy Mean", row=1, col=1)

    fig.add_trace(
        go.Box(y=monthly_returns_strat.values, name='Strategy',
               marker=dict(color=STRATEGY_COLOR)),
        row=1, col=2
    )

    if monthly_returns_bench is not None:
        fig.add_trace(
            go.Histogram(x=monthly_returns_bench.values, nbinsx=30, name='Benchmark',
                         marker=dict(color=BENCHMARK_COLOR, opacity=0.6)),
            row=1, col=1
        )
        fig.add_vline(x=monthly_returns_bench.mean(), line_dash="dot",
                      line_color=BENCHMARK_COLOR, annotation_text="Benchmark Mean", row=1, col=1)
        fig.add_trace(
            go.Box(y=monthly_returns_bench.values, name='Benchmark',
                   marker=dict(color=BENCHMARK_COLOR)),
            row=1, col=2
        )

    fig.update_layout(
        title="<b>Return Distribution Analysis</b>",
        height=400, showlegend=True, template='plotly_white',
        barmode='overlay',
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1)
    )
    fig.show()
    print("  Visualization 11 complete: Distribution & Quantile Boxes")


# ─── VIZ 12: Distribution Moments + Q-Q Plot ─────────────────────────────────

def _viz12_moments_qq(monthly_returns_strat):
    r = monthly_returns_strat.dropna().values
    n = len(r)

    mean_r  = float(np.mean(r))
    std_r   = float(np.std(r, ddof=1))
    skew_r  = float(((r - mean_r) ** 3).mean() / std_r ** 3) if std_r > 0 else 0.0
    kurt_r  = float(((r - mean_r) ** 4).mean() / std_r ** 4 - 3) if std_r > 0 else 0.0  # excess

    # Jarque-Bera
    if _HAS_SCIPY:
        jb_stat, jb_p = _scipy_stats.jarque_bera(r)
    else:
        jb_stat = n / 6 * (skew_r ** 2 + kurt_r ** 2 / 4)
        # approximate p-value via chi2 with 2 dof
        jb_p = float(np.exp(-jb_stat / 2)) if jb_stat < 30 else 0.0

    var_95  = float(np.percentile(r, 5))
    var_99  = float(np.percentile(r, 1))
    cvar_95 = float(r[r <= var_95].mean()) if (r <= var_95).any() else var_95
    cvar_99 = float(r[r <= var_99].mean()) if (r <= var_99).any() else var_99

    # Q-Q data
    sorted_r = np.sort(r)
    theoretical_quantiles = np.array([
        _scipy_stats.norm.ppf((i + 0.5) / n) for i in range(n)
    ]) if _HAS_SCIPY else (np.arange(n) - n / 2) / (n / 2) * std_r
    empirical_line = mean_r + std_r * theoretical_quantiles

    # Metrics table data
    metric_rows = [
        ["Mean (monthly %)",          f"{mean_r:.3f}%"],
        ["Std Dev (monthly %)",        f"{std_r:.3f}%"],
        ["Skewness",                   f"{skew_r:.3f}"],
        ["Excess Kurtosis",            f"{kurt_r:.3f}"],
        ["Jarque-Bera Stat",           f"{jb_stat:.2f}"],
        ["Jarque-Bera p-value",        f"{jb_p:.4f}"],
        ["Normal Distribution",        "Yes" if jb_p > 0.05 else "No (p<0.05)"],
        ["VaR 95% (monthly %)",        f"{var_95:.3f}%"],
        ["VaR 99% (monthly %)",        f"{var_99:.3f}%"],
        ["CVaR 95% (monthly %)",       f"{cvar_95:.3f}%"],
        ["CVaR 99% (monthly %)",       f"{cvar_99:.3f}%"],
        ["1st Percentile",             f"{np.percentile(r, 1):.3f}%"],
        ["5th Percentile",             f"{np.percentile(r, 5):.3f}%"],
        ["95th Percentile",            f"{np.percentile(r, 95):.3f}%"],
        ["99th Percentile",            f"{np.percentile(r, 99):.3f}%"],
    ]

    row_colors = []
    for lbl, _ in metric_rows:
        if "Kurtosis" in lbl and kurt_r > 3:
            row_colors.append("#fde8e8")
        elif "Skewness" in lbl and abs(skew_r) > 1:
            row_colors.append("#fff3cd")
        elif "Normal" in lbl:
            row_colors.append("#d4edda" if jb_p > 0.05 else "#fde8e8")
        else:
            row_colors.append("white")

    fig = make_subplots(
        rows=1, cols=2,
        subplot_titles=('Distribution Moments & Risk Statistics', 'Q-Q Plot vs Normal'),
        horizontal_spacing=0.12,
        column_widths=[0.45, 0.55]
    )

    fig.add_trace(
        go.Table(
            header=dict(
                values=["<b>Statistic</b>", "<b>Value</b>"],
                fill_color="#1f2d3d",
                font=dict(color="white", size=11),
                align="left"
            ),
            cells=dict(
                values=[[row[0] for row in metric_rows],
                        [row[1] for row in metric_rows]],
                fill_color=[row_colors, row_colors],
                font=dict(size=10),
                align=["left", "center"],
                height=24
            )
        ),
        row=1, col=1
    )

    # Q-Q scatter
    fig.add_trace(
        go.Scatter(
            x=theoretical_quantiles, y=sorted_r,
            mode='markers', name='Monthly Returns',
            marker=dict(color=STRATEGY_COLOR, size=5, opacity=0.7),
            hovertemplate='Theoretical: %{x:.2f}<br>Empirical: %{y:.2f}%<extra></extra>'
        ),
        row=1, col=2
    )
    fig.add_trace(
        go.Scatter(
            x=theoretical_quantiles, y=empirical_line,
            mode='lines', name='Normal',
            line=dict(color='red', width=2, dash='dash'),
            showlegend=True
        ),
        row=1, col=2
    )
    fig.update_xaxes(title_text="Theoretical Normal Quantiles", row=1, col=2)
    fig.update_yaxes(title_text="Empirical Quantiles (%)", row=1, col=2)

    normality = "Normal" if jb_p > 0.05 else f"Non-Normal (p={jb_p:.4f})"
    fig.update_layout(
        title=f"<b>Distribution Moments & Q-Q Plot</b>"
              f"<br><sub>Skew: {skew_r:.3f} | Excess Kurt: {kurt_r:.3f} | "
              f"JB: {normality}</sub>",
        height=520, showlegend=True, template='plotly_white'
    )
    fig.show()
    print("  Visualization 12 complete: Distribution Moments + Q-Q Plot")


# ─── VIZ 13: Return Autocorrelation ACF / PACF ───────────────────────────────

def _viz13_acf(monthly_returns_strat):
    r    = monthly_returns_strat.dropna().values
    n    = len(r)
    nlags = min(24, n // 3)

    acf_vals = _manual_acf(r, nlags)

    # PACF via Yule-Walker (manual)
    def _pacf_yw(x, nlags):
        x = x - x.mean()
        n = len(x)
        pacf_vals = []
        for k in range(1, nlags + 1):
            if k >= n:
                pacf_vals.append(np.nan)
                continue
            # Build correlation matrix for Yule-Walker
            r_vec = np.array([np.corrcoef(x[:-j], x[j:])[0, 1] if j < n else 0
                               for j in range(1, k + 1)])
            R = np.array([[np.corrcoef(x[:-abs(i-j)], x[abs(i-j):])[0, 1]
                           if abs(i-j) < n else float(i == j)
                           for j in range(k)]
                          for i in range(k)])
            try:
                phi = np.linalg.solve(R, r_vec)
                pacf_vals.append(float(phi[-1]))
            except np.linalg.LinAlgError:
                pacf_vals.append(np.nan)
        return np.array(pacf_vals)

    pacf_vals = _pacf_yw(r, nlags)
    lags      = np.arange(1, nlags + 1)
    ci        = 1.96 / np.sqrt(n)   # 95% confidence interval

    fig = make_subplots(
        rows=1, cols=2,
        subplot_titles=(
            f'Autocorrelation Function (ACF) — {nlags} Lags',
            f'Partial Autocorrelation (PACF) — {nlags} Lags'
        ),
        horizontal_spacing=0.12
    )

    # ACF bars
    acf_colors = ['#2E7D32' if abs(v) > ci else STRATEGY_COLOR for v in acf_vals]
    fig.add_trace(
        go.Bar(
            x=lags, y=acf_vals,
            name='ACF',
            marker_color=acf_colors,
            hovertemplate='Lag %{x}: ACF = %{y:.3f}<extra></extra>'
        ),
        row=1, col=1
    )
    fig.add_hline(y=ci,  line_dash="dash", line_color="red",
                  annotation_text="+95% CI", row=1, col=1)
    fig.add_hline(y=-ci, line_dash="dash", line_color="red",
                  annotation_text="-95% CI", row=1, col=1)
    fig.add_hline(y=0, line_color="black", line_width=1, row=1, col=1)
    fig.update_xaxes(title_text="Lag (months)", row=1, col=1)
    fig.update_yaxes(title_text="Autocorrelation", row=1, col=1)

    # PACF bars
    pacf_colors = ['#2E7D32' if abs(v) > ci else STRATEGY_COLOR
                   for v in pacf_vals if not np.isnan(v)]
    pacf_colors += ['gray'] * (len(lags) - len(pacf_colors))
    fig.add_trace(
        go.Bar(
            x=lags, y=pacf_vals,
            name='PACF',
            marker_color=pacf_colors,
            hovertemplate='Lag %{x}: PACF = %{y:.3f}<extra></extra>'
        ),
        row=1, col=2
    )
    fig.add_hline(y=ci,  line_dash="dash", line_color="red", row=1, col=2)
    fig.add_hline(y=-ci, line_dash="dash", line_color="red", row=1, col=2)
    fig.add_hline(y=0, line_color="black", line_width=1, row=1, col=2)
    fig.update_xaxes(title_text="Lag (months)", row=1, col=2)
    fig.update_yaxes(title_text="Partial Autocorrelation", row=1, col=2)

    sig_lags = lags[np.abs(acf_vals) > ci]
    sig_str  = ", ".join(str(l) for l in sig_lags) if len(sig_lags) > 0 else "None"
    fig.update_layout(
        title=f"<b>Return Autocorrelation (ACF / PACF)</b>"
              f"<br><sub>Significant lags (ACF > 95% CI): {sig_str}</sub>",
        height=420, showlegend=False, template='plotly_white'
    )
    fig.show()
    print("  Visualization 13 complete: ACF / PACF")


# ─── VIZ 14: Active Returns & Best/Worst ─────────────────────────────────────

def _viz14_active_returns(returns_strategy, returns_benchmark,
                           monthly_returns_strat, monthly_returns_bench):
    fig = make_subplots(
        rows=1, cols=2,
        subplot_titles=(
            'Monthly Active Returns (Strategy - Benchmark)',
            'Best / Worst Monthly Returns'
        ),
        horizontal_spacing=0.12
    )

    if returns_benchmark is not None:
        daily_active = returns_strategy - returns_benchmark.reindex(returns_strategy.index)
        monthly_active = (
            daily_active.resample('ME')
            .apply(lambda x: (1 + x).prod() - 1) * 100
        )
        bar_colors = ['#2E7D32' if x >= 0 else '#C62828'
                      for x in monthly_active.values]
        fig.add_trace(
            go.Bar(
                x=monthly_active.index,
                y=monthly_active.values,
                name='Monthly Active Returns',
                marker=dict(color=bar_colors, opacity=1.0),
                hovertemplate='<b>%{x|%b %Y}</b><br>Active: %{y:.2f}%<extra></extra>'
            ),
            row=1, col=1
        )
        fig.add_hline(y=0, line_dash="solid", line_color="black",
                      line_width=1, row=1, col=1)
        fig.update_yaxes(title_text="Active Return (%)", row=1, col=1)

    best_months  = monthly_returns_strat.nlargest(5)
    worst_months = monthly_returns_strat.nsmallest(5)
    combined     = pd.concat([worst_months, best_months]).sort_values()
    strat_colors = ['#2E7D32' if x >= 0 else '#C62828' for x in combined.values]

    fig.add_trace(
        go.Bar(
            x=[idx.strftime('%Y-%m') for idx in combined.index],
            y=combined.values,
            marker=dict(color=strat_colors, opacity=1.0),
            name='Strategy',
            hovertemplate='<b>%{x}</b><br>Strategy: %{y:.2f}%<extra></extra>'
        ),
        row=1, col=2
    )

    if monthly_returns_bench is not None:
        combined_bench = monthly_returns_bench.reindex(combined.index)
        fig.add_trace(
            go.Bar(
                x=[idx.strftime('%Y-%m') for idx in combined_bench.index],
                y=combined_bench.values,
                marker=dict(color=BENCHMARK_COLOR, opacity=0.85),
                name='Benchmark',
                hovertemplate='<b>%{x}</b><br>Benchmark: %{y:.2f}%<extra></extra>'
            ),
            row=1, col=2
        )

    fig.add_hline(y=0, line_dash="solid", line_color="black",
                  line_width=1, row=1, col=2)
    fig.update_yaxes(title_text="Return (%)", row=1, col=2)

    fig.update_layout(
        title="<b>Active Returns & Best/Worst Analysis</b>",
        height=450, showlegend=True, template='plotly_white',
        barmode='group',
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1)
    )
    fig.show()
    print("  Visualization 14 complete: Active Returns & Best/Worst")


# ─── VIZ 15: Sector Attribution ───────────────────────────────────────────────

def _viz15_sector_attribution(pf, contract_specs, ohlc):
    if pf is None:
        print("  Visualization 15 skipped: no portfolio object for sector attribution")
        return

    if ohlc is None:
        print("  Visualization 15 skipped: no ohlc dict for symbol names")
        return

    try:
        trade_df = pf.trades.records
        closed   = trade_df[trade_df['status'] == 1].copy()

        if closed.empty:
            print("  Visualization 15 skipped: no closed trades")
            return

        cols = ohlc['close'].columns.tolist()
        closed = closed.copy()
        closed['symbol'] = closed['col'].apply(lambda x: cols[int(x)])
        closed['direction'] = closed['direction'].map({0: 'Long', 1: 'Short'})

        # Sector mapping
        sector_map = {}
        if contract_specs is not None and not contract_specs.empty:
            if contract_specs.index.name == 'pwb_symbol':
                sector_map = dict(zip(contract_specs.index, contract_specs['sector']))
            elif 'pwb_symbol' in contract_specs.columns:
                sector_map = dict(zip(contract_specs['pwb_symbol'], contract_specs['sector']))

        closed['sector'] = closed['symbol'].map(sector_map).fillna('Unknown')

        # P&L by sector + direction
        pnl_by = closed.groupby(['sector', 'direction'])['pnl'].agg(['sum', 'count'])
        pnl_by.columns = ['Total PnL', 'Trades']
        pnl_by = pnl_by.reset_index()

        sectors = sorted(pnl_by['sector'].unique())
        long_pnl  = []
        short_pnl = []
        for s in sectors:
            row_l = pnl_by[(pnl_by['sector'] == s) & (pnl_by['direction'] == 'Long')]
            row_s = pnl_by[(pnl_by['sector'] == s) & (pnl_by['direction'] == 'Short')]
            long_pnl.append(float(row_l['Total PnL'].values[0]) if not row_l.empty else 0)
            short_pnl.append(float(row_s['Total PnL'].values[0]) if not row_s.empty else 0)

        total_pnl = [l + s for l, s in zip(long_pnl, short_pnl)]

        fig = make_subplots(
            rows=1, cols=2,
            subplot_titles=('P&L by Sector (Long vs Short)', 'Total P&L by Sector'),
            horizontal_spacing=0.1
        )

        fig.add_trace(
            go.Bar(name='Long', x=sectors, y=long_pnl,
                   marker_color='#2E7D32',
                   hovertemplate='%{x}<br>Long PnL: $%{y:,.0f}<extra></extra>'),
            row=1, col=1
        )
        fig.add_trace(
            go.Bar(name='Short', x=sectors, y=short_pnl,
                   marker_color='#C62828',
                   hovertemplate='%{x}<br>Short PnL: $%{y:,.0f}<extra></extra>'),
            row=1, col=1
        )

        bar_colors_total = ['#2E7D32' if v >= 0 else '#C62828' for v in total_pnl]
        fig.add_trace(
            go.Bar(name='Total', x=sectors, y=total_pnl,
                   marker_color=bar_colors_total,
                   hovertemplate='%{x}<br>Total PnL: $%{y:,.0f}<extra></extra>',
                   showlegend=False),
            row=1, col=2
        )
        fig.add_hline(y=0, line_dash="dash", line_color="black", row=1, col=1)
        fig.add_hline(y=0, line_dash="dash", line_color="black", row=1, col=2)
        fig.update_yaxes(title_text="P&L ($)", row=1, col=1)
        fig.update_yaxes(title_text="P&L ($)", row=1, col=2)

        total_closed_pnl = float(closed['pnl'].sum())
        n_trades = len(closed)
        fig.update_layout(
            title=f"<b>Sector Attribution</b>"
                  f"<br><sub>Total Closed P&L: ${total_closed_pnl:,.0f} | "
                  f"{n_trades} closed trades across {len(sectors)} sectors</sub>",
            height=480, showlegend=True, template='plotly_white',
            barmode='group',
            legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1)
        )
        fig.show()
        print("  Visualization 15 complete: Sector Attribution")

    except Exception as e:
        print(f"  Visualization 15 skipped: {e}")


# ─── VIZ 16: Trade Duration Analysis ─────────────────────────────────────────

def _viz16_trade_duration(pf, ohlc):
    if pf is None:
        print("  Visualization 16 skipped: no portfolio object for trade duration")
        return

    try:
        trade_df = pf.trades.records
        closed   = trade_df[trade_df['status'] == 1].copy()

        if closed.empty:
            print("  Visualization 16 skipped: no closed trades")
            return

        if ohlc is not None:
            idx = ohlc['close'].index
            closed = closed.copy()
            closed['duration'] = closed.apply(
                lambda r: max((idx[int(r['exit_idx'])] - idx[int(r['entry_idx'])]).days, 1),
                axis=1
            )
        else:
            closed = closed.copy()
            closed['duration'] = (closed['exit_idx'] - closed['entry_idx']).clip(lower=1)

        closed['profitable'] = closed['pnl'] > 0
        closed['direction_label'] = closed['direction'].map({0: 'Long', 1: 'Short'})

        wins   = closed[closed['profitable']]
        losses = closed[~closed['profitable']]

        avg_win_dur  = wins['duration'].mean()   if not wins.empty   else 0
        avg_loss_dur = losses['duration'].mean() if not losses.empty else 0
        med_win_dur  = wins['duration'].median() if not wins.empty   else 0
        med_loss_dur = losses['duration'].median() if not losses.empty else 0

        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=(
                'Trade Duration Distribution (All)',
                'Avg Duration: Winners vs Losers',
                'Duration Buckets vs Win Rate',
                'Duration vs P&L Scatter'
            ),
            vertical_spacing=0.14,
            horizontal_spacing=0.1
        )

        # Histogram of durations (wins green, losses red)
        if not wins.empty:
            fig.add_trace(
                go.Histogram(
                    x=wins['duration'], name='Winners', nbinsx=25,
                    marker=dict(color='#2E7D32', opacity=0.7),
                    hovertemplate='Duration: %{x}d<br>Count: %{y}<extra></extra>'
                ),
                row=1, col=1
            )
        if not losses.empty:
            fig.add_trace(
                go.Histogram(
                    x=losses['duration'], name='Losers', nbinsx=25,
                    marker=dict(color='#C62828', opacity=0.7),
                    hovertemplate='Duration: %{x}d<br>Count: %{y}<extra></extra>'
                ),
                row=1, col=1
            )
        fig.update_xaxes(title_text="Duration (days)", row=1, col=1)
        fig.update_yaxes(title_text="Count", row=1, col=1)

        # Avg duration bar chart
        fig.add_trace(
            go.Bar(
                x=['Avg Win', 'Avg Loss', 'Med Win', 'Med Loss'],
                y=[avg_win_dur, avg_loss_dur, med_win_dur, med_loss_dur],
                marker_color=['#2E7D32', '#C62828', '#66BB6A', '#EF5350'],
                showlegend=False,
                hovertemplate='%{x}: %{y:.1f}d<extra></extra>'
            ),
            row=1, col=2
        )
        fig.update_yaxes(title_text="Days", row=1, col=2)

        # Duration buckets win rate
        bins = [0, 7, 30, 90, 180, 365, 10000]
        labels = ['0-7d', '8-30d', '31-90d', '91-180d', '181-365d', '>365d']
        bucket_wr  = []
        bucket_cnt = []
        for i in range(len(bins) - 1):
            mask = (closed['duration'] > bins[i]) & (closed['duration'] <= bins[i + 1])
            sub  = closed[mask]
            cnt  = len(sub)
            wr   = (sub['profitable'].sum() / cnt * 100) if cnt > 0 else np.nan
            bucket_wr.append(wr)
            bucket_cnt.append(cnt)

        bucket_colors = ['#2E7D32' if (wr and wr >= 50) else '#C62828' if wr else 'gray'
                         for wr in bucket_wr]
        fig.add_trace(
            go.Bar(
                x=labels, y=bucket_wr,
                marker_color=bucket_colors,
                showlegend=False,
                text=[f"{c} trades" for c in bucket_cnt],
                textposition='outside',
                hovertemplate='%{x}<br>Win Rate: %{y:.1f}%<br>%{text}<extra></extra>'
            ),
            row=2, col=1
        )
        fig.add_hline(y=50, line_dash="dash", line_color="gray",
                      annotation_text="50%", row=2, col=1)
        fig.update_yaxes(title_text="Win Rate (%)", range=[0, 110], row=2, col=1)

        # Duration vs P&L scatter
        scatter_colors = ['#2E7D32' if v else '#C62828' for v in closed['profitable']]
        fig.add_trace(
            go.Scatter(
                x=closed['duration'], y=closed['pnl'],
                mode='markers',
                marker=dict(color=scatter_colors, size=5, opacity=0.6),
                showlegend=False,
                hovertemplate='Duration: %{x}d<br>P&L: $%{y:,.0f}<extra></extra>'
            ),
            row=2, col=2
        )
        fig.add_hline(y=0, line_dash="dash", line_color="black", row=2, col=2)
        fig.update_xaxes(title_text="Duration (days)", row=2, col=2)
        fig.update_yaxes(title_text="P&L ($)", row=2, col=2)

        total_trades  = len(closed)
        overall_wr    = (closed['profitable'].sum() / total_trades * 100) if total_trades > 0 else 0
        fig.update_layout(
            title=f"<b>Trade Duration Analysis</b>"
                  f"<br><sub>{total_trades} closed trades | Win Rate: {overall_wr:.1f}% | "
                  f"Avg Win: {avg_win_dur:.0f}d | Avg Loss: {avg_loss_dur:.0f}d</sub>",
            height=700, showlegend=True, template='plotly_white',
            barmode='overlay',
            legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1)
        )
        fig.show()
        print("  Visualization 16 complete: Trade Duration Analysis")

    except Exception as e:
        print(f"  Visualization 16 skipped: {e}")


# ─── VIZ 17: Complete Drawdown Table ─────────────────────────────────────────

def _viz17_drawdown_table(equity_strategy):
    dd_df = _extract_drawdowns(equity_strategy, min_dd_pct=-2.0)

    if dd_df.empty:
        print("  Visualization 17 skipped: no drawdowns >= 2%")
        return

    # Top 20 by depth
    dd_show = dd_df.head(20).copy()

    cell_colors = []
    for depth in dd_show['Depth (%)']:
        if depth <= -20:
            cell_colors.append('#ffcccc')
        elif depth <= -10:
            cell_colors.append('#ffe8cc')
        else:
            cell_colors.append('white')

    col_names = list(dd_show.columns)
    cell_vals = [dd_show[c].astype(str).tolist() for c in col_names]

    # Color rows by depth
    n_rows  = len(dd_show)
    row_clr = []
    for depth in dd_show['Depth (%)']:
        if depth <= -20:
            row_clr.append('#fde8e8')
        elif depth <= -10:
            row_clr.append('#fff3cd')
        else:
            row_clr.append('white')

    fig = go.Figure(data=[go.Table(
        columnwidth=[90, 90, 100, 80, 110, 110, 100],
        header=dict(
            values=[f"<b>{c}</b>" for c in col_names],
            fill_color='#1f2d3d',
            font=dict(color='white', size=11),
            align='center'
        ),
        cells=dict(
            values=cell_vals,
            fill_color=[[row_clr[i] for i in range(n_rows)] for _ in col_names],
            font=dict(size=10),
            align='center',
            height=24
        )
    )])

    fig.update_layout(
        title=f"<b>Complete Drawdown Table with Recovery</b>"
              f"<br><sub>Top {len(dd_show)} drawdowns by depth (>= -2%) — "
              f"sorted deepest first</sub>",
        height=max(300, n_rows * 28 + 120),
        margin=dict(l=10, r=10, t=60, b=10),
        template='plotly_white'
    )
    fig.show()
    print(f"  Visualization 17 complete: Drawdown Table ({len(dd_show)} periods)")


# ─── VIZ 18: Performance by Market Regime ────────────────────────────────────

def _viz18_market_regime(returns_strategy, monthly_returns_strat,
                          returns_benchmark, equity_benchmark):
    if returns_benchmark is None or equity_benchmark is None:
        print("  Visualization 18 skipped: no benchmark for regime analysis")
        return

    # Define regime via 200-day SMA of benchmark equity
    sma200  = equity_benchmark.rolling(200).mean()
    daily_regime = (equity_benchmark > sma200).map({True: 'Bull', False: 'Bear'})

    # Map to monthly
    monthly_regime_raw = daily_regime.resample('ME').last()
    common = monthly_returns_strat.index.intersection(monthly_regime_raw.index)
    ms     = monthly_returns_strat.loc[common]
    regime = monthly_regime_raw.loc[common]

    mb = returns_benchmark.resample('ME').apply(lambda x: (1 + x).prod() - 1) * 100
    mb = mb.loc[common]

    bull_s = ms[regime == 'Bull']
    bear_s = ms[regime == 'Bear']
    bull_b = mb[regime == 'Bull']
    bear_b = mb[regime == 'Bear']

    def _stats(r):
        if len(r) == 0:
            return {"n": 0, "mean": 0, "win_rate": 0, "ann": 0}
        ann = ((1 + r / 100).prod() ** (12 / len(r)) - 1) * 100
        return {
            "n":       len(r),
            "mean":    r.mean(),
            "win_rate": (r > 0).mean() * 100,
            "ann":     ann,
        }

    bull_s_stats = _stats(bull_s)
    bear_s_stats = _stats(bear_s)
    bull_b_stats = _stats(bull_b)
    bear_b_stats = _stats(bear_b)

    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=(
            'Monthly Returns Distribution by Regime',
            'Annualized Return by Regime',
            'Win Rate by Regime',
            'Cumulative Return in Each Regime'
        ),
        vertical_spacing=0.14,
        horizontal_spacing=0.1
    )

    # Box plots by regime
    fig.add_trace(
        go.Box(y=bull_s.values, name='Bull (Strat)', marker_color='#2E7D32',
               boxpoints='outliers'),
        row=1, col=1
    )
    fig.add_trace(
        go.Box(y=bear_s.values, name='Bear (Strat)', marker_color='#C62828',
               boxpoints='outliers'),
        row=1, col=1
    )
    if len(bull_b) > 0:
        fig.add_trace(
            go.Box(y=bull_b.values, name='Bull (Bench)',
                   marker_color='#81C784', boxpoints='outliers'),
            row=1, col=1
        )
    if len(bear_b) > 0:
        fig.add_trace(
            go.Box(y=bear_b.values, name='Bear (Bench)',
                   marker_color='#EF9A9A', boxpoints='outliers'),
            row=1, col=1
        )
    fig.update_yaxes(title_text="Monthly Return (%)", row=1, col=1)

    # Annualized return bars
    fig.add_trace(
        go.Bar(
            x=['Bull', 'Bear'],
            y=[bull_s_stats['ann'], bear_s_stats['ann']],
            name='Strategy',
            marker_color=[
                '#2E7D32' if bull_s_stats['ann'] >= 0 else '#C62828',
                '#2E7D32' if bear_s_stats['ann'] >= 0 else '#C62828',
            ],
            showlegend=False,
            hovertemplate='%{x}: %{y:.1f}%/yr<extra></extra>'
        ),
        row=1, col=2
    )
    fig.add_hline(y=0, line_dash="dash", line_color="gray", row=1, col=2)
    fig.update_yaxes(title_text="Annualized Return (%)", row=1, col=2)

    # Win rate bars
    fig.add_trace(
        go.Bar(
            x=['Bull', 'Bear'],
            y=[bull_s_stats['win_rate'], bear_s_stats['win_rate']],
            name='Win Rate',
            marker_color=[STRATEGY_COLOR, STRATEGY_COLOR],
            showlegend=False,
            hovertemplate='%{x}: %{y:.1f}%<extra></extra>'
        ),
        row=2, col=1
    )
    fig.add_hline(y=50, line_dash="dash", line_color="gray",
                  annotation_text="50%", row=2, col=1)
    fig.update_yaxes(title_text="Win Rate (%)", range=[0, 100], row=2, col=1)

    # Cumulative return lines colored by regime
    # Plot equity, shade bull/bear periods
    cum_s  = (1 + returns_strategy).cumprod() - 1
    cum_s *= 100
    fig.add_trace(
        go.Scatter(
            x=cum_s.index, y=cum_s.values,
            name='Strategy Cumulative',
            line=dict(color=STRATEGY_COLOR, width=2),
            showlegend=False
        ),
        row=2, col=2
    )
    # Shade bear periods
    in_bear = False
    bear_start = None
    for date, r in daily_regime.items():
        if r == 'Bear' and not in_bear:
            in_bear = True
            bear_start = date
        elif r == 'Bull' and in_bear:
            in_bear = False
            fig.add_vrect(
                x0=bear_start, x1=date,
                fillcolor='rgba(200,0,0,0.08)',
                layer='below', line_width=0,
                row=2, col=2
            )
    if in_bear and bear_start:
        fig.add_vrect(
            x0=bear_start, x1=daily_regime.index[-1],
            fillcolor='rgba(200,0,0,0.08)',
            layer='below', line_width=0,
            row=2, col=2
        )
    fig.update_yaxes(title_text="Cumulative Return (%)", row=2, col=2)
    fig.add_hline(y=0, line_dash="dot", line_color="gray", row=2, col=2)

    n_bull = bull_s_stats['n']
    n_bear = bear_s_stats['n']
    fig.update_layout(
        title=f"<b>Performance by Market Regime (200-SMA of Benchmark)</b>"
              f"<br><sub>Bull: {n_bull} months (Strat: {bull_s_stats['ann']:.1f}%/yr) | "
              f"Bear: {n_bear} months (Strat: {bear_s_stats['ann']:.1f}%/yr)</sub>",
        height=700, showlegend=True, template='plotly_white',
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1)
    )
    fig.show()
    print("  Visualization 18 complete: Performance by Market Regime")


# ─── VIZ 19: Crisis Periods (2x4 Grid) ───────────────────────────────────────

def _viz19_crisis_periods(equity_strategy, equity_benchmark):
    crisis_names = list(CRISIS_PERIODS.keys())
    fig = make_subplots(
        rows=2, cols=4,
        subplot_titles=crisis_names,
        vertical_spacing=0.15,
        horizontal_spacing=0.08
    )

    row_col_map = [
        (1, 1), (1, 2), (1, 3), (1, 4),
        (2, 1), (2, 2), (2, 3), (2, 4)
    ]

    for idx, (crisis_name, (start, end)) in enumerate(CRISIS_PERIODS.items()):
        row, col = row_col_map[idx]
        try:
            crisis_strat = equity_strategy.loc[start:end]
            if len(crisis_strat) < 2:
                raise ValueError("Not enough data")
            norm_strat = crisis_strat / crisis_strat.iloc[0]
            fig.add_trace(
                go.Scatter(
                    x=norm_strat.index, y=norm_strat.values,
                    name='Strategy', line=dict(color=STRATEGY_COLOR, width=2),
                    showlegend=(idx == 0)
                ),
                row=row, col=col
            )
            if equity_benchmark is not None:
                crisis_bench = equity_benchmark.loc[start:end]
                if len(crisis_bench) >= 2:
                    norm_bench = crisis_bench / crisis_bench.iloc[0]
                    fig.add_trace(
                        go.Scatter(
                            x=norm_bench.index, y=norm_bench.values,
                            name='Benchmark', line=dict(color=BENCHMARK_COLOR, width=2),
                            showlegend=(idx == 0)
                        ),
                        row=row, col=col
                    )
        except Exception:
            fig.add_annotation(
                text="Not enough history",
                x=0.5, y=0.5, showarrow=False,
                font=dict(size=10, color="gray"),
                xref=f"x{idx + 1}", yref=f"y{idx + 1}"
            )

    fig.update_layout(
        title="<b>Crisis Periods Analysis (Normalized to 1.0)</b>",
        height=600, showlegend=True, template='plotly_white'
    )
    fig.show()
    print("  Visualization 19 complete: Crisis Periods Analysis")
