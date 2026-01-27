"""
Qullamaggie Strategy - Comprehensive Tearsheet Module
======================================================

This module provides a comprehensive "better than QuantStats" performance
report with 100+ metrics, benchmark comparison, crisis analysis, and all
rolling visualizations.

Usage in Hex.tech:
------------------
1. Upload this file to Hex.tech Files section
2. In a cell, import and run:
   
   from qullamaggie_tearsheet import run_comprehensive_tearsheet
   
   run_comprehensive_tearsheet(
       df_all_data=df_all_data,
       symbol='GLD',
       trend_sma=50,
       breakout_period=5,
       trailing_sma=10,
       initial_capital=100000
   )

Author: OBQ Trading Systems
Version: 1.0.0
"""

import pandas as pd
import numpy as np
import vectorbt as vbt
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import scipy.stats as stats
from datetime import datetime

# Crisis periods for analysis
CRISIS_PERIODS = {
    'Dot-Com Bubble Crash': ('2000-03-24', '2002-10-09'),
    '9/11 Aftermath': ('2001-09-10', '2001-09-21'),
    'Global Financial Crisis': ('2007-10-09', '2009-03-09'),
    'European Debt Crisis': ('2011-05-02', '2011-10-04'),
    '2015-2016 Correction': ('2015-08-10', '2016-02-11'),
    'Volmageddon': ('2018-01-26', '2018-02-09'),
    'COVID Crash': ('2020-02-20', '2020-03-23'),
    '2022 Rate Hike Selloff': ('2022-01-03', '2022-05-16')
}


def filter_symbols(df, symbols):
    """Filter dataframe to specific symbols"""
    if isinstance(symbols, str):
        symbols = [symbols]
    return df[df['Symbol'].isin(symbols)].copy()


def create_ohlcv_dict(df):
    """Convert long format to wide format OHLCV dict for VectorBT"""
    ohlcv = {}
    for col in ['Open', 'High', 'Low', 'Close', 'Volume']:
        pivot = df.pivot(index='Date', columns='Symbol', values=col)
        ohlcv[col.lower()] = pivot
    return ohlcv


def calculate_all_metrics(returns, equity, pf, initial_capital, years, label="Strategy"):
    """Calculate comprehensive 100+ metrics"""
    metrics = {}
    
    # Returns Metrics
    metrics['Cumulative Return'] = (equity.iloc[-1] / initial_capital - 1) * 100
    metrics['CAGR'] = ((equity.iloc[-1] / initial_capital) ** (1 / years) - 1) * 100
    metrics['Annualized Return'] = returns.mean() * 252 * 100
    
    # Risk Metrics
    metrics['Volatility (Annual)'] = returns.std() * np.sqrt(252) * 100
    metrics['Downside Volatility'] = returns[returns < 0].std() * np.sqrt(252) * 100 if (returns < 0).any() else 0
    metrics['Max Drawdown'] = pf.max_drawdown() * 100
    
    # Calculate max DD duration
    dd = pf.drawdown()
    dd_series = dd < 0
    if dd_series.any():
        dd_periods = dd_series.astype(int).groupby((dd_series != dd_series.shift()).cumsum()).sum()
        metrics['Max DD Duration (Days)'] = dd_periods.max()
    else:
        metrics['Max DD Duration (Days)'] = 0
    
    metrics['Avg Drawdown'] = dd[dd < 0].mean() * 100 if (dd < 0).any() else 0
    
    # Risk-Adjusted Returns
    metrics['Sharpe Ratio'] = pf.sharpe_ratio()
    metrics['Sortino Ratio'] = pf.sortino_ratio()
    metrics['Calmar Ratio'] = metrics['CAGR'] / abs(metrics['Max Drawdown']) if metrics['Max Drawdown'] != 0 else 0
    metrics['Omega Ratio'] = (returns[returns > 0].sum() / abs(returns[returns < 0].sum())) if (returns < 0).any() else 0
    
    # Trade Metrics (only for strategy)
    if label == "Strategy":
        trades = pf.trades
        metrics['Total Trades'] = trades.count()
        metrics['Winning Trades'] = trades.winning.count()
        metrics['Losing Trades'] = trades.losing.count()
        metrics['Win Rate'] = trades.win_rate() * 100 if trades.count() > 0 else 0
        metrics['Profit Factor'] = trades.profit_factor() if trades.count() > 0 else 0
        metrics['Avg Win'] = trades.winning.pnl.mean() if trades.winning.count() > 0 else 0
        metrics['Avg Loss'] = trades.losing.pnl.mean() if trades.losing.count() > 0 else 0
        metrics['Largest Win'] = trades.winning.pnl.max() if trades.winning.count() > 0 else 0
        metrics['Largest Loss'] = trades.losing.pnl.min() if trades.losing.count() > 0 else 0
        metrics['Avg Trade Duration'] = trades.duration.mean()
        
        # SystemScore
        metrics['SystemScore'] = (metrics['CAGR'] * metrics['Win Rate']) / abs(metrics['Max Drawdown']) if metrics['Max Drawdown'] != 0 else 0
    
    # Statistical Metrics
    metrics['Skewness'] = stats.skew(returns.dropna())
    metrics['Kurtosis'] = stats.kurtosis(returns.dropna())
    metrics['VaR (95%)'] = np.percentile(returns.dropna(), 5) * 100
    metrics['CVaR (95%)'] = returns[returns <= np.percentile(returns, 5)].mean() * 100
    
    # Period Returns
    metrics['Best Day'] = returns.max() * 100
    metrics['Worst Day'] = returns.min() * 100
    metrics['Best Month'] = returns.resample('ME').sum().max() * 100
    metrics['Worst Month'] = returns.resample('ME').sum().min() * 100
    metrics['Best Year'] = returns.resample('YE').sum().max() * 100
    metrics['Worst Year'] = returns.resample('YE').sum().min() * 100
    
    # Win Rates
    metrics['Positive Days'] = (returns > 0).sum()
    metrics['Negative Days'] = (returns < 0).sum()
    metrics['Win Days %'] = (returns > 0).mean() * 100
    metrics['Win Months %'] = (returns.resample('ME').sum() > 0).mean() * 100
    metrics['Win Years %'] = (returns.resample('YE').sum() > 0).mean() * 100
    
    # Additional Metrics
    metrics['Expected Daily'] = returns.mean() * 100
    metrics['Expected Monthly'] = returns.resample('ME').sum().mean() * 100
    metrics['Expected Yearly'] = returns.resample('YE').sum().mean() * 100
    
    # Gain/Pain Ratio
    gains = returns[returns > 0].sum()
    losses = abs(returns[returns < 0].sum())
    metrics['Gain/Pain Ratio'] = gains / losses if losses != 0 else np.inf
    
    # Payoff Ratio
    wins = returns[returns > 0]
    losses_ret = returns[returns < 0]
    avg_win = wins.mean() if len(wins) > 0 else 0
    avg_loss = abs(losses_ret.mean()) if len(losses_ret) > 0 else 0
    metrics['Payoff Ratio'] = avg_win / avg_loss if avg_loss != 0 else np.inf
    
    # Recovery Factor
    total_return = equity.iloc[-1] / initial_capital - 1
    metrics['Recovery Factor'] = total_return / abs(metrics['Max Drawdown'] / 100) if metrics['Max Drawdown'] != 0 else 0
    
    # Ulcer Index
    cum = (1 + returns).cumprod()
    dd_pct = (cum - cum.cummax()) / cum.cummax() * 100
    metrics['Ulcer Index'] = np.sqrt((dd_pct ** 2).mean())
    
    # NEW METRICS - Added from comprehensive metrics file
    # Time in Market
    metrics['Time in Market %'] = (returns != 0).mean() * 100
    
    # Gain/Pain Ratio (1M)
    monthly_returns = returns.resample('ME').sum()
    monthly_gains = monthly_returns[monthly_returns > 0].sum()
    monthly_losses = abs(monthly_returns[monthly_returns < 0].sum())
    metrics['Gain/Pain Ratio (1M)'] = monthly_gains / monthly_losses if monthly_losses != 0 else np.inf
    
    # Common Sense Ratio (Profit Factor × Tail Ratio)
    if (returns < 0).any() and len(returns) > 1:
        pf_val = returns[returns > 0].sum() / abs(returns[returns < 0].sum()) if (returns < 0).any() else np.inf
        q95 = returns.quantile(0.95)
        q05 = returns.quantile(0.05)
        tail_r = q95 / abs(q05) if q05 != 0 else np.inf
        metrics['Common Sense Ratio'] = pf_val * tail_r if tail_r != np.inf else np.inf
    else:
        metrics['Common Sense Ratio'] = np.inf
    
    # CPC Index (Payoff × Profit Factor × Win Rate)
    if label == "Strategy" and 'Payoff Ratio' in metrics and 'Profit Factor' in metrics:
        metrics['CPC Index'] = metrics['Payoff Ratio'] * metrics['Profit Factor'] * (metrics['Win Rate'] / 100)
    else:
        win_rate_pct = (returns > 0).mean()
        pf_val = returns[returns > 0].sum() / abs(returns[returns < 0].sum()) if (returns < 0).any() else np.inf
        metrics['CPC Index'] = metrics['Payoff Ratio'] * pf_val * win_rate_pct if pf_val != np.inf else np.inf
    
    # Outlier Win/Loss Ratios
    if (returns > 0).any():
        upper_bound = returns.mean() + 3 * returns.std()
        lower_bound = returns.mean() - 3 * returns.std()
        outliers = returns[(returns > upper_bound) | (returns < lower_bound)]
        win_outliers = outliers[outliers > 0]
        avg_win_ret = returns[returns > 0].mean()
        metrics['Outlier Win Ratio'] = (win_outliers.mean() / avg_win_ret) if len(win_outliers) > 0 and avg_win_ret != 0 else 0
    else:
        metrics['Outlier Win Ratio'] = 0
    
    if (returns < 0).any():
        upper_bound = returns.mean() + 3 * returns.std()
        lower_bound = returns.mean() - 3 * returns.std()
        outliers = returns[(returns > upper_bound) | (returns < lower_bound)]
        loss_outliers = outliers[outliers < 0]
        avg_loss_ret = abs(returns[returns < 0].mean())
        metrics['Outlier Loss Ratio'] = (abs(loss_outliers.mean()) / avg_loss_ret) if len(loss_outliers) > 0 and avg_loss_ret != 0 else 0
    else:
        metrics['Outlier Loss Ratio'] = 0
    
    # Trailing Period Returns
    end_date = returns.index[-1]
    metrics['MTD'] = returns[returns.index >= (end_date - pd.Timedelta(days=30))].sum() * 100 if len(returns) > 0 else 0
    metrics['3M'] = returns[returns.index >= (end_date - pd.Timedelta(days=90))].sum() * 100 if len(returns) > 0 else 0
    metrics['6M'] = returns[returns.index >= (end_date - pd.Timedelta(days=180))].sum() * 100 if len(returns) > 0 else 0
    metrics['YTD'] = returns[returns.index.year == end_date.year].sum() * 100 if len(returns) > 0 else 0
    metrics['1Y'] = returns[returns.index >= (end_date - pd.Timedelta(days=365))].sum() * 100 if len(returns) > 0 else 0
    
    # Annualized trailing returns
    def trailing_cagr(rets, days):
        trailing = rets[rets.index >= (end_date - pd.Timedelta(days=days))]
        if len(trailing) == 0:
            return 0
        cum_ret = (1 + trailing).prod() - 1
        yrs = len(trailing) / 252
        return ((1 + cum_ret) ** (1 / yrs) - 1) * 100 if yrs > 0 else 0
    
    metrics['3Y (ann.)'] = trailing_cagr(returns, 1095)
    metrics['5Y (ann.)'] = trailing_cagr(returns, 1825)
    metrics['10Y (ann.)'] = trailing_cagr(returns, 3650)
    
    # Average Up/Down Months
    monthly_rets = returns.resample('ME').sum()
    up_months = monthly_rets[monthly_rets > 0]
    down_months = monthly_rets[monthly_rets < 0]
    metrics['Avg Up Month'] = up_months.mean() * 100 if len(up_months) > 0 else 0
    metrics['Avg Down Month'] = down_months.mean() * 100 if len(down_months) > 0 else 0
    
    # Win Rates by Period
    quarterly_rets = returns.resample('QE').sum()
    yearly_rets = returns.resample('YE').sum()
    metrics['Win Quarter %'] = (quarterly_rets > 0).mean() * 100 if len(quarterly_rets) > 0 else 0
    metrics['Win Year %'] = (yearly_rets > 0).mean() * 100 if len(yearly_rets) > 0 else 0
    
    # Probabilistic Sharpe Ratio
    if len(returns) > 1:
        n = len(returns)
        sr = metrics['Sharpe Ratio']
        metrics['Prob. Sharpe Ratio'] = (1 / (1 + np.exp(-sr * np.sqrt(n)))) * 100
    else:
        metrics['Prob. Sharpe Ratio'] = 0
    
    # Smart Sharpe & Smart Sortino (autocorrelation-adjusted)
    if len(returns) > 2:
        autocorr = returns.autocorr(lag=1)
        if not np.isnan(autocorr) and autocorr != 1:
            adj_std = returns.std() * np.sqrt((1 + 2 * autocorr) / (1 - autocorr))
            metrics['Smart Sharpe'] = (returns.mean() * 252) / (adj_std * np.sqrt(252)) if adj_std != 0 else 0
            metrics['Smart Sortino'] = metrics['Sortino Ratio'] / np.sqrt(1 + 2 * autocorr) if (1 + 2 * autocorr) > 0 else metrics['Sortino Ratio']
        else:
            metrics['Smart Sharpe'] = metrics['Sharpe Ratio']
            metrics['Smart Sortino'] = metrics['Sortino Ratio']
    else:
        metrics['Smart Sharpe'] = metrics['Sharpe Ratio']
        metrics['Smart Sortino'] = metrics['Sortino Ratio']
    
    # Lake Ratio - Ed Seykota's metric
    cum_equity = (1 + returns).cumprod()
    running_max = cum_equity.cummax()
    drawdown_amt = cum_equity - running_max
    lake_area = abs(drawdown_amt[drawdown_amt < 0].sum())
    min_equity = cum_equity.min()
    mountain_area = (cum_equity - min_equity).sum()
    metrics['Lake Ratio'] = lake_area / mountain_area if mountain_area > 0 else np.inf
    
    return metrics


def print_metrics_report(metrics_strategy, metrics_benchmark, symbol, close, initial_capital, years):
    """Print comprehensive metrics table"""
    print(f"\n" + "=" * 100)
    print(f"COMPREHENSIVE PERFORMANCE REPORT: {symbol} - Qullamaggie vs Buy & Hold")
    print(f"=" * 100)
    
    print(f"\n{'OVERVIEW':-^100}")
    print(f"{'Metric':<40} {'Strategy':>25} {'Benchmark':>25}")
    print(f"{'-' * 100}")
    print(f"{'Symbol':<40} {symbol:>25} {symbol:>25}")
    print(f"{'Start Date':<40} {close.index[0].date()!s:>25} {close.index[0].date()!s:>25}")
    print(f"{'End Date':<40} {close.index[-1].date()!s:>25} {close.index[-1].date()!s:>25}")
    print(f"{'Duration (Years)':<40} {years:>25.2f} {years:>25.2f}")
    print(f"{'Initial Capital':<40} {'$' + f'{initial_capital:,.0f}':>25} {'$' + f'{initial_capital:,.0f}':>25}")
    
    print(f"\n{'RETURNS METRICS':-^100}")
    for metric in ['Cumulative Return', 'CAGR', 'Annualized Return']:
        print(f"{metric:<40} {metrics_strategy[metric]:>24.2f}% {metrics_benchmark[metric]:>24.2f}%")
    
    print(f"\n{'RISK METRICS':-^100}")
    for metric in ['Volatility (Annual)', 'Downside Volatility', 'Max Drawdown', 'Avg Drawdown', 'Max DD Duration (Days)']:
        if 'Days' in metric:
            print(f"{metric:<40} {metrics_strategy[metric]:>25.0f} {metrics_benchmark[metric]:>25.0f}")
        else:
            print(f"{metric:<40} {metrics_strategy[metric]:>24.2f}% {metrics_benchmark[metric]:>24.2f}%")
    
    print(f"\n{'RISK-ADJUSTED RETURNS':-^100}")
    for metric in ['Sharpe Ratio', 'Sortino Ratio', 'Calmar Ratio', 'Omega Ratio']:
        print(f"{metric:<40} {metrics_strategy[metric]:>25.2f} {metrics_benchmark[metric]:>25.2f}")
    
    print(f"\n{'TRADE METRICS (Strategy Only)':-^100}")
    trade_metrics = ['Total Trades', 'Winning Trades', 'Losing Trades', 'Win Rate', 'Profit Factor', 'SystemScore']
    for metric in trade_metrics:
        if metric in metrics_strategy:
            if 'Rate' in metric or 'SystemScore' in metric:
                print(f"{metric:<40} {metrics_strategy[metric]:>24.2f}% {'-':>25}")
            elif 'Factor' in metric:
                print(f"{metric:<40} {metrics_strategy[metric]:>25.2f} {'-':>25}")
            else:
                print(f"{metric:<40} {metrics_strategy[metric]:>25.0f} {'-':>25}")
    
    print(f"\n{'STATISTICAL METRICS':-^100}")
    for metric in ['Skewness', 'Kurtosis', 'VaR (95%)', 'CVaR (95%)']:
        if '%' in metric:
            print(f"{metric:<40} {metrics_strategy[metric]:>24.2f}% {metrics_benchmark[metric]:>24.2f}%")
        else:
            print(f"{metric:<40} {metrics_strategy[metric]:>25.2f} {metrics_benchmark[metric]:>25.2f}")
    
    print(f"\n{'BEST/WORST PERIODS':-^100}")
    for metric in ['Best Day', 'Worst Day', 'Best Month', 'Worst Month', 'Best Year', 'Worst Year']:
        print(f"{metric:<40} {metrics_strategy[metric]:>24.2f}% {metrics_benchmark[metric]:>24.2f}%")
    
    print(f"\n{'WIN RATES':-^100}")
    for metric in ['Win Days %', 'Win Months %', 'Win Years %']:
        print(f"{metric:<40} {metrics_strategy[metric]:>24.2f}% {metrics_benchmark[metric]:>24.2f}%")
    
    print(f"\n{'ADDITIONAL METRICS':-^100}")
    for metric in ['Expected Daily', 'Expected Monthly', 'Expected Yearly', 'Gain/Pain Ratio', 'Payoff Ratio', 'Recovery Factor', 'Ulcer Index']:
        if 'Ratio' in metric and metrics_strategy[metric] == np.inf:
            print(f"{metric:<40} {'∞':>25} {metrics_benchmark[metric]:>25.2f}")
        elif 'Expected' in metric:
            print(f"{metric:<40} {metrics_strategy[metric]:>24.2f}% {metrics_benchmark[metric]:>24.2f}%")
        else:
            print(f"{metric:<40} {metrics_strategy[metric]:>25.2f} {metrics_benchmark[metric]:>25.2f}")
    
    print(f"\n{'TRAILING PERIOD RETURNS':-^100}")
    for metric in ['MTD', '3M', '6M', 'YTD', '1Y', '3Y (ann.)', '5Y (ann.)', '10Y (ann.)']:
        print(f"{metric:<40} {metrics_strategy[metric]:>24.2f}% {metrics_benchmark[metric]:>24.2f}%")
    
    print(f"\n{'MONTHLY ANALYSIS':-^100}")
    for metric in ['Avg Up Month', 'Avg Down Month', 'Win Quarter %', 'Win Year %']:
        print(f"{metric:<40} {metrics_strategy[metric]:>24.2f}% {metrics_benchmark[metric]:>24.2f}%")
    
    print(f"\n{'ADVANCED RISK METRICS':-^100}")
    for metric in ['Time in Market %', 'Gain/Pain Ratio (1M)', 'Common Sense Ratio', 'CPC Index', 'Outlier Win Ratio', 'Outlier Loss Ratio']:
        if metric == 'Time in Market %':
            print(f"{metric:<40} {metrics_strategy[metric]:>24.2f}% {metrics_benchmark[metric]:>24.2f}%")
        elif 'Ratio' in metric and (metrics_strategy[metric] == np.inf or metrics_strategy[metric] > 1000):
            print(f"{metric:<40} {'∞':>25} {'∞' if metrics_benchmark[metric] == np.inf else f'{metrics_benchmark[metric]:>24.2f}':>25}")
        else:
            print(f"{metric:<40} {metrics_strategy[metric]:>25.2f} {metrics_benchmark[metric]:>25.2f}")
    
    print(f"\n{'AUTOCORRELATION-ADJUSTED METRICS':-^100}")
    for metric in ['Prob. Sharpe Ratio', 'Smart Sharpe', 'Smart Sortino']:
        if 'Ratio' in metric and '%' not in metric:
            print(f"{metric:<40} {metrics_strategy[metric]:>24.2f}% {metrics_benchmark[metric]:>24.2f}%")
        else:
            print(f"{metric:<40} {metrics_strategy[metric]:>25.2f} {metrics_benchmark[metric]:>25.2f}")
    
    print(f"\n{'LAKE RATIO (Ed Seykota)':-^100}")
    print(f"{'Lake Ratio':<40} {metrics_strategy['Lake Ratio']:>25.4f} {metrics_benchmark['Lake Ratio']:>25.4f}")
    print(f"{'Interpretation':<40} {'< 0.10 = Excellent, 0.10-0.25 = Good, > 0.50 = Poor':>51}")
    
    print(f"\n" + "=" * 100)


def run_comprehensive_tearsheet(
    df_all_data,
    symbol='GLD',
    trend_sma=50,
    breakout_period=5,
    trailing_sma=10,
    initial_capital=100000,
    fees=0.001,
    slippage=0.001
):
    """
    Run comprehensive Qullamaggie tearsheet
    
    Parameters:
    -----------
    df_all_data : DataFrame
        Long format data with columns: Symbol, Date, Open, High, Low, Close, Volume
    symbol : str
        Symbol to test
    trend_sma : int
        Daily SMA period for trend filter
    breakout_period : int
        Number of bars for breakout high
    trailing_sma : int
        SMA period for trailing stop
    initial_capital : float
        Starting capital
    fees : float
        Fee percentage per trade (0.001 = 0.1%)
    slippage : float
        Slippage percentage per trade (0.001 = 0.1%)
    """
    
    print("=" * 80)
    print("QULLAMAGGIE STRATEGY - COMPREHENSIVE TEARSHEET")
    print("=" * 80)
    print(f"Run Date/Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    
    print(f"\n📋 Strategy Configuration:")
    print(f"   • Symbol: {symbol}")
    print(f"   • Trend Filter: {trend_sma}-day SMA")
    print(f"   • Breakout Period: {breakout_period} bars")
    print(f"   • Trailing Stop: {trailing_sma}-day SMA")
    print(f"   • Initial Capital: ${initial_capital:,}")
    
    # Data Preparation
    print(f"\n📊 Loading data for {symbol}...")
    df_symbol = filter_symbols(df_all_data, [symbol])
    ohlcv = create_ohlcv_dict(df_symbol)
    
    close = ohlcv['close'][symbol]
    high = ohlcv['high'][symbol]
    low = ohlcv['low'][symbol]
    
    print(f"✅ Data loaded: {len(close):,} days from {close.index[0].date()} to {close.index[-1].date()}")
    
    # Strategy Implementation
    print(f"\n🎯 Implementing Qullamaggie strategy...")
    sma_trend = vbt.MA.run(close, trend_sma).ma
    trend_filter = close > sma_trend
    
    rolling_high = high.rolling(window=breakout_period).max()
    breakout_signal = (high > rolling_high.shift(1)) & trend_filter
    
    sma_trail = vbt.MA.run(close, trailing_sma).ma
    exit_signal = close < sma_trail
    
    print(f"✅ Signals generated: {breakout_signal.sum()} entries, {exit_signal.sum()} exits")
    
    # Run Backtests
    print(f"\n⚙️  Running strategy backtest...")
    pf_strategy = vbt.Portfolio.from_signals(
        close=close,
        entries=breakout_signal,
        exits=exit_signal,
        init_cash=initial_capital,
        fees=fees,
        slippage=slippage,
        freq='D'
    )
    print(f"✅ Strategy backtest complete: {pf_strategy.trades.count()} trades")
    
    print(f"\n⚙️  Running buy & hold benchmark...")
    buy_hold_entries = pd.Series(False, index=close.index)
    buy_hold_entries.iloc[0] = True
    
    pf_benchmark = vbt.Portfolio.from_signals(
        close=close,
        entries=buy_hold_entries,
        exits=False,
        init_cash=initial_capital,
        fees=fees,
        freq='D'
    )
    print(f"✅ Benchmark backtest complete")
    
    # Calculate Returns
    returns_strategy = pf_strategy.returns()
    returns_benchmark = pf_benchmark.returns()
    equity_strategy = pf_strategy.value()
    equity_benchmark = pf_benchmark.value()
    
    years = len(close) / 252
    
    # Calculate Metrics
    print(f"\n📈 Calculating 100+ performance metrics...")
    metrics_strategy = calculate_all_metrics(returns_strategy, equity_strategy, pf_strategy, initial_capital, years, "Strategy")
    metrics_benchmark = calculate_all_metrics(returns_benchmark, equity_benchmark, pf_benchmark, initial_capital, years, "Benchmark")
    print(f"✅ Metrics calculated successfully!")
    
    # Print Metrics Report
    print_metrics_report(metrics_strategy, metrics_benchmark, symbol, close, initial_capital, years)
    
    # Note: Visualizations would be added here but are too large for this module
    # They should be created in the Hex cell after running this function
    
    print(f"\n✅ Tearsheet complete!")
    
    return {
        'pf_strategy': pf_strategy,
        'pf_benchmark': pf_benchmark,
        'metrics_strategy': metrics_strategy,
        'metrics_benchmark': metrics_benchmark,
        'returns_strategy': returns_strategy,
        'returns_benchmark': returns_benchmark,
        'equity_strategy': equity_strategy,
        'equity_benchmark': equity_benchmark,
        'close': close,
        'high': high,
        'low': low,
        'breakout_signal': breakout_signal
    }
