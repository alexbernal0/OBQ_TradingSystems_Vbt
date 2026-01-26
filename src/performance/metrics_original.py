"""
Master 2025 Comprehensive Performance Tearsheet Functions
Includes ALL metrics, tables, and visualizations for strategy analysis
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from datetime import datetime

# ============================================================================
# CORE PERFORMANCE METRICS
# ============================================================================

def cum_returns(ret):
    """Cumulative returns"""
    return (1 + ret).cumprod() - 1

def cagr(ret, periods_per_year=252):
    """Compound Annual Growth Rate"""
    if len(ret) == 0:
        return 0
    cum = cum_returns(ret).iloc[-1]
    years = len(ret) / periods_per_year
    return (1 + cum) ** (1 / years) - 1 if years > 0 else 0

def max_drawdown(ret):
    """Maximum drawdown"""
    if len(ret) == 0:
        return 0
    cum = cum_returns(ret) + 1
    dd = (cum - cum.cummax()) / cum.cummax()
    return dd.min()

def volatility(ret, periods_per_year=252):
    """Annualized volatility"""
    return ret.std() * np.sqrt(periods_per_year) if len(ret) > 0 else 0

def sharpe(ret, rf=0.0, periods_per_year=252):
    """Sharpe ratio"""
    if len(ret) == 0:
        return 0
    excess = ret - rf/periods_per_year
    return excess.mean() / excess.std() * np.sqrt(periods_per_year) if excess.std() != 0 else 0

def sortino(ret, rf=0.0, periods_per_year=252):
    """Sortino ratio"""
    if len(ret) == 0:
        return 0
    excess = ret - rf/periods_per_year
    downside = excess[excess < 0]
    downside_std = downside.std() if len(downside) > 0 else 0
    return excess.mean() / downside_std * np.sqrt(periods_per_year) if downside_std != 0 else 0

def calmar(ret):
    """Calmar ratio"""
    c = cagr(ret)
    mdd = abs(max_drawdown(ret))
    return c / mdd if mdd != 0 else 0

def omega(ret, rf=0.0, periods_per_year=252):
    """Omega ratio"""
    if len(ret) == 0:
        return 1
    threshold = rf / periods_per_year
    gains = ret[ret > threshold].sum()
    losses = abs(ret[ret < threshold].sum())
    return gains / losses if losses != 0 else np.inf

def downside_dev(ret, rf=0.0, periods_per_year=252):
    """Downside deviation"""
    threshold = rf / periods_per_year
    downside = ret[ret < threshold]
    return downside.std() * np.sqrt(periods_per_year) if len(downside) > 0 else 0

def value_at_risk(ret, confidence=0.95):
    """Value at Risk"""
    return ret.quantile(1 - confidence) if len(ret) > 0 else 0

def conditional_var(ret, confidence=0.95):
    """Conditional VaR (Expected Shortfall)"""
    var = value_at_risk(ret, confidence)
    return ret[ret <= var].mean() if len(ret[ret <= var]) > 0 else 0

def ulcer_index(ret):
    """Ulcer Index"""
    if len(ret) == 0:
        return 0
    cum = cum_returns(ret) + 1
    dd = (cum - cum.cummax()) / cum.cummax() * 100
    return np.sqrt((dd ** 2).mean())

def serenity_index(ret, rf=0.0):
    """Serenity Index"""
    ui = ulcer_index(ret)
    c = cagr(ret) * 100
    return (c - rf * 100) / ui if ui != 0 else 0

def gain_pain_ratio(ret):
    """Gain to Pain ratio"""
    gains = ret[ret > 0].sum()
    losses = abs(ret[ret < 0].sum())
    return gains / losses if losses != 0 else np.inf

def payoff_ratio(ret):
    """Payoff ratio"""
    wins = ret[ret > 0]
    losses = ret[ret < 0]
    avg_win = wins.mean() if len(wins) > 0 else 0
    avg_loss = abs(losses.mean()) if len(losses) > 0 else 0
    return avg_win / avg_loss if avg_loss != 0 else np.inf

def profit_factor(ret):
    """Profit factor"""
    gains = ret[ret > 0].sum()
    losses = abs(ret[ret < 0].sum())
    return gains / losses if losses != 0 else np.inf

def common_sense_ratio(ret):
    """Common Sense ratio"""
    pf = profit_factor(ret)
    tail = tail_ratio(ret)
    return pf * tail if pf != np.inf and tail != np.inf else 0

def cpc_index(ret):
    """CPC Index"""
    win_rate = (ret > 0).mean()
    payoff = payoff_ratio(ret)
    return win_rate * payoff if payoff != np.inf else 0

def tail_ratio(ret, percentile=95):
    """Tail ratio"""
    right_tail = ret.quantile(percentile/100)
    left_tail = abs(ret.quantile((100-percentile)/100))
    return right_tail / left_tail if left_tail != 0 else np.inf

def outlier_win_ratio(ret):
    """Outlier win ratio"""
    mean = ret.mean()
    std = ret.std()
    outlier_wins = ret[ret > mean + 2*std]
    return len(outlier_wins) / len(ret) * 100 if len(ret) > 0 else 0

def outlier_loss_ratio(ret):
    """Outlier loss ratio"""
    mean = ret.mean()
    std = ret.std()
    outlier_losses = ret[ret < mean - 2*std]
    return len(outlier_losses) / len(ret) * 100 if len(ret) > 0 else 0

def kelly_criterion(ret):
    """Kelly Criterion"""
    if len(ret) == 0:
        return 0
    win_rate = (ret > 0).mean()
    payoff = payoff_ratio(ret)
    if payoff == np.inf:
        return 0
    return win_rate - (1 - win_rate) / payoff if payoff != 0 else 0

def recovery_factor(ret):
    """Recovery factor"""
    total_return = cum_returns(ret).iloc[-1] if len(ret) > 0 else 0
    mdd = abs(max_drawdown(ret))
    return total_return / mdd if mdd != 0 else 0

def drawdown_duration(ret):
    """Longest drawdown duration in days"""
    if len(ret) == 0:
        return 0
    cum = cum_returns(ret) + 1
    dd = (cum - cum.cummax()) / cum.cummax()
    in_dd = dd < 0
    dd_groups = (in_dd != in_dd.shift()).cumsum()
    dd_lengths = in_dd.groupby(dd_groups).sum()
    return dd_lengths.max() if not dd_lengths.empty else 0

def avg_drawdown(ret):
    """Average drawdown"""
    if len(ret) == 0:
        return 0
    cum = cum_returns(ret) + 1
    dd = (cum - cum.cummax()) / cum.cummax()
    in_dd = dd < 0
    dd_groups = (in_dd != in_dd.shift()).cumsum()
    dd_values = dd.groupby(dd_groups).min()
    return dd_values[dd_values < 0].mean() if len(dd_values[dd_values < 0]) > 0 else 0

def avg_dd_days(ret):
    """Average drawdown days"""
    if len(ret) == 0:
        return 0
    cum = cum_returns(ret) + 1
    dd = (cum - cum.cummax()) / cum.cummax()
    in_dd = dd < 0
    dd_groups = (in_dd != in_dd.shift()).cumsum()
    dd_lengths = in_dd.groupby(dd_groups).sum()
    return dd_lengths.mean() if not dd_lengths.empty else 0

def win_rate(ret, period='D'):
    """Win rate for given period"""
    if len(ret) == 0:
        return 0
    resampled = ret.resample(period).sum()
    return (resampled > 0).mean() * 100 if len(resampled) > 0 else 0

# ============================================================================
# COMPREHENSIVE METRICS CALCULATOR
# ============================================================================

def calculate_metrics(returns, benchmark_returns=None, rf=0.0):
    """Calculate all 60+ performance metrics"""
    metrics = {}

    # Basic metrics
    metrics['Risk-Free Rate'] = rf * 100
    metrics['Time in Market'] = (returns != 0).mean() * 100 if len(returns) > 0 else 0
    metrics['Cumulative Return'] = cum_returns(returns).iloc[-1] * 100 if len(returns) > 0 else 0
    metrics['CAGR%'] = cagr(returns) * 100
    metrics['Sharpe'] = sharpe(returns, rf)
    metrics['Sortino'] = sortino(returns, rf)
    metrics['Sortino/sqrt2'] = metrics['Sortino'] / np.sqrt(2) if 'Sortino' in metrics else 0
    metrics['Omega'] = omega(returns, rf)
    metrics['Max Drawdown'] = max_drawdown(returns) * 100
    metrics['Longest DD Days'] = drawdown_duration(returns)
    metrics['Volatility (ann.)'] = volatility(returns) * 100
    metrics['Calmar'] = calmar(returns)
    metrics['Skew'] = returns.skew() if len(returns) > 2 else 0
    metrics['Kurtosis'] = returns.kurt() if len(returns) > 3 else 0
    metrics['Expected Daily'] = returns.mean() * 100 if len(returns) > 0 else 0
    metrics['Expected Monthly'] = returns.resample('M').sum().mean() * 100 if len(returns) > 0 else 0
    metrics['Expected Yearly'] = returns.resample('Y').sum().mean() * 100 if len(returns) > 0 else 0
    metrics['Kelly Criterion'] = kelly_criterion(returns) * 100
    metrics['Risk of Ruin'] = 0.0  # Simplified
    metrics['Daily Value-at-Risk'] = value_at_risk(returns) * 100
    metrics['Expected Shortfall (cVaR)'] = conditional_var(returns) * 100
    metrics['Gain/Pain Ratio'] = gain_pain_ratio(returns)
    metrics['Gain/Pain (1M)'] = gain_pain_ratio(returns.resample('M').sum())
    metrics['Payoff Ratio'] = payoff_ratio(returns)
    metrics['Profit Factor'] = profit_factor(returns)
    metrics['Common Sense Ratio'] = common_sense_ratio(returns)
    metrics['CPC Index'] = cpc_index(returns)
    metrics['Tail Ratio'] = tail_ratio(returns)
    metrics['Outlier Win Ratio'] = outlier_win_ratio(returns)
    metrics['Outlier Loss Ratio'] = outlier_loss_ratio(returns)
    metrics['MTD'] = returns[returns.index >= returns.index[-1] - pd.Timedelta(30, 'D')].sum() * 100 if len(returns) > 0 else 0
    metrics['3M'] = returns[returns.index >= returns.index[-1] - pd.Timedelta(90, 'D')].sum() * 100 if len(returns) > 0 else 0
    metrics['6M'] = returns[returns.index >= returns.index[-1] - pd.Timedelta(180, 'D')].sum() * 100 if len(returns) > 0 else 0
    metrics['YTD'] = returns[returns.index.year == returns.index[-1].year].sum() * 100 if len(returns) > 0 else 0
    metrics['1Y'] = returns[returns.index >= returns.index[-1] - pd.Timedelta(365, 'D')].sum() * 100 if len(returns) > 0 else 0
    metrics['3Y (ann.)'] = cagr(returns[returns.index >= returns.index[-1] - pd.Timedelta(1095, 'D')]) * 100
    metrics['5Y (ann.)'] = cagr(returns[returns.index >= returns.index[-1] - pd.Timedelta(1825, 'D')]) * 100
    metrics['10Y (ann.)'] = cagr(returns[returns.index >= returns.index[-1] - pd.Timedelta(3650, 'D')]) * 100
    metrics['All-time (ann.)'] = cagr(returns) * 100
    metrics['Best Day'] = returns.max() * 100 if len(returns) > 0 else 0
    metrics['Worst Day'] = returns.min() * 100 if len(returns) > 0 else 0
    metrics['Best Month'] = returns.resample('M').sum().max() * 100 if len(returns) > 0 else 0
    metrics['Worst Month'] = returns.resample('M').sum().min() * 100 if len(returns) > 0 else 0
    metrics['Best Year'] = returns.resample('Y').sum().max() * 100 if len(returns) > 0 else 0
    metrics['Worst Year'] = returns.resample('Y').sum().min() * 100 if len(returns) > 0 else 0
    metrics['Avg. Drawdown'] = avg_drawdown(returns) * 100
    metrics['Avg. Drawdown Days'] = avg_dd_days(returns)
    metrics['Recovery Factor'] = recovery_factor(returns)
    metrics['Ulcer Index'] = ulcer_index(returns)
    metrics['Serenity Index'] = serenity_index(returns, rf)
    metrics['Avg. Up Month'] = returns.resample('M').sum()[returns.resample('M').sum() > 0].mean() * 100 if len(returns.resample('M').sum()[returns.resample('M').sum() > 0]) > 0 else 0
    metrics['Avg. Down Month'] = returns.resample('M').sum()[returns.resample('M').sum() < 0].mean() * 100 if len(returns.resample('M').sum()[returns.resample('M').sum() < 0]) > 0 else 0
    metrics['Win Days'] = win_rate(returns, 'D')
    metrics['Win Month'] = win_rate(returns, 'M')
    metrics['Win Quarter'] = win_rate(returns, 'Q')
    metrics['Win Year'] = win_rate(returns, 'Y')

    # Advanced
    if len(returns) > 1:
        n = len(returns)
        sr = sharpe(returns, rf)
        metrics['Prob. Sharpe Ratio'] = (1 / (1 + np.exp(-sr * np.sqrt(n)))) * 100
        autocorr = returns.autocorr(lag=1)
        adj_std = returns.std() * np.sqrt((1 + 2 * autocorr) / (1 - autocorr)) if autocorr != 1 else returns.std()
        metrics['Smart Sharpe'] = (returns.mean() - rf/252) / adj_std * np.sqrt(252) if adj_std != 0 else 0
        metrics['Smart Sortino'] = sortino(returns, rf) / np.sqrt(1 + 2 * autocorr) if 1 + 2 * autocorr > 0 else sortino(returns, rf)
        metrics['Smart Sortino/sqrt2'] = metrics['Smart Sortino'] / np.sqrt(2) if 'Smart Sortino' in metrics else 0
    else:
        metrics['Prob. Sharpe Ratio'] = 0
        metrics['Smart Sharpe'] = 0
        metrics['Smart Sortino'] = 0
        metrics['Smart Sortino/sqrt2'] = 0

    return metrics

# ============================================================================
# TABLE GENERATION FUNCTIONS
# ============================================================================

def generate_yearly_returns_table(returns):
    """Generate end-of-year returns table"""
    yearly = returns.resample('Y').sum() * 100
    cumulative = (1 + returns.resample('Y').sum()).cumprod() * 100 - 100
    
    df = pd.DataFrame({
        'Year': [d.year for d in yearly.index],
        'Return %': yearly.values,
        'Cumulative %': cumulative.values
    })
    return df

def generate_monthly_performance_grid(returns):
    """Generate monthly performance grid (year x month)"""
    monthly = returns.resample('M').sum() * 100
    
    # Create pivot table
    df = pd.DataFrame({
        'Year': [d.year for d in monthly.index],
        'Month': [d.month for d in monthly.index],
        'Return': monthly.values
    })
    
    pivot = df.pivot(index='Year', columns='Month', values='Return')
    pivot.columns = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
                     'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    
    # Add YTD column
    pivot['YTD'] = returns.groupby(returns.index.year).sum() * 100
    
    return pivot.fillna(0)

def generate_worst_drawdowns_table(returns, top_n=10):
    """Generate worst drawdowns table"""
    if len(returns) == 0:
        return pd.DataFrame()
    
    cum = cum_returns(returns) + 1
    dd = (cum - cum.cummax()) / cum.cummax()
    
    # Find drawdown periods
    in_dd = dd < 0
    dd_groups = (in_dd != in_dd.shift()).cumsum()
    
    drawdowns = []
    for group in dd_groups[in_dd].unique():
        dd_period = dd[dd_groups == group]
        if len(dd_period) > 0:
            start = dd_period.index[0]
            end = dd_period.index[-1]
            dd_value = dd_period.min()
            days = len(dd_period)
            drawdowns.append({
                'Start': start.strftime('%Y-%m-%d'),
                'End': end.strftime('%Y-%m-%d'),
                'Drawdown %': dd_value * 100,
                'Days': days
            })
    
    df = pd.DataFrame(drawdowns)
    if len(df) > 0:
        df = df.sort_values('Drawdown %').head(top_n)
    
    return df

# ============================================================================
# CRISIS PERIOD ANALYSIS
# ============================================================================

def plot_crisis_periods(strategy_returns, benchmark_returns, 
                       strategy_name="Strategy", benchmark_name="Benchmark"):
    """
    Generate Economic Stress/Crisis Period visualization
    Returns: (figure, crisis_df)
    """
    
    # Define crisis periods
    crises = [
        ("Dot-Com Bubble Crash", "2000-03-24", "2002-10-09"),
        ("9/11 Aftermath", "2001-09-10", "2001-09-21"),
        ("Global Financial Crisis", "2007-10-09", "2009-03-09"),
        ("European Debt Crisis", "2011-05-02", "2011-10-04"),
        ("2015-2016 Correction", "2015-08-10", "2016-02-11"),
        ("Volmageddon", "2018-01-26", "2018-02-09"),
        ("COVID Crash", "2020-02-20", "2020-03-23"),
        ("2022 Rate Hike Selloff", "2022-01-03", "2022-06-16")
    ]
    
    # Calculate crisis performance
    crisis_data = []
    for name, start, end in crises:
        start_dt = pd.to_datetime(start)
        end_dt = pd.to_datetime(end)
        
        strat_period = strategy_returns[(strategy_returns.index >= start_dt) & 
                                       (strategy_returns.index <= end_dt)]
        bench_period = benchmark_returns[(benchmark_returns.index >= start_dt) & 
                                        (benchmark_returns.index <= end_dt)]
        
        if len(strat_period) > 0 and len(bench_period) > 0:
            strat_ret = (1 + strat_period).prod() - 1
            bench_ret = (1 + bench_period).prod() - 1
            strat_dd = max_drawdown(strat_period)
            bench_dd = max_drawdown(bench_period)
            
            crisis_data.append({
                'Period': name,
                'Duration': len(strat_period),
                'Strategy Return': strat_ret * 100,
                'Strategy Max DD': strat_dd * 100,
                'Benchmark Return': bench_ret * 100,
                'Benchmark Max DD': bench_dd * 100,
                'Relative Perf': (strat_ret - bench_ret) * 100
            })
    
    crisis_df = pd.DataFrame(crisis_data)
    
    # Create visualization
    fig = plt.figure(figsize=(14, 10))
    gs = gridspec.GridSpec(4, 2, height_ratios=[2, 1, 1, 1], hspace=0.3, wspace=0.3)
    
    # Main equity curve with crisis shading
    ax1 = fig.add_subplot(gs[0, :])
    strat_cum = (1 + strategy_returns).cumprod()
    bench_cum = (1 + benchmark_returns).cumprod()
    
    ax1.plot(strat_cum.index, strat_cum.values, label=strategy_name, linewidth=1.5)
    ax1.plot(bench_cum.index, bench_cum.values, label=benchmark_name, linewidth=1.5, alpha=0.7)
    
    # Shade crisis periods
    colors = ['purple', 'red', 'orange', 'pink', 'yellow', 'gray', 'brown', 'cyan']
    for i, (name, start, end) in enumerate(crises):
        ax1.axvspan(pd.to_datetime(start), pd.to_datetime(end), 
                   alpha=0.2, color=colors[i % len(colors)], label=name)
    
    ax1.set_title('Economic Stress Equity Curve', fontsize=12, fontweight='bold')
    ax1.set_ylabel('Cumulative Growth')
    ax1.legend(loc='upper left', fontsize=7, ncol=2)
    ax1.grid(True, alpha=0.3)
    
    # Drawdown comparison
    ax2 = fig.add_subplot(gs[1, :])
    strat_cum_full = (1 + strategy_returns).cumprod()
    bench_cum_full = (1 + benchmark_returns).cumprod()
    strat_dd = (strat_cum_full - strat_cum_full.cummax()) / strat_cum_full.cummax() * 100
    bench_dd = (bench_cum_full - bench_cum_full.cummax()) / bench_cum_full.cummax() * 100
    
    ax2.fill_between(strat_dd.index, 0, strat_dd.values, alpha=0.5, label=f'{strategy_name} DD (%)')
    ax2.fill_between(bench_dd.index, 0, bench_dd.values, alpha=0.5, label=f'{benchmark_name} DD (%)')
    ax2.set_title('Drawdown (%)', fontsize=10)
    ax2.legend(fontsize=8)
    ax2.grid(True, alpha=0.3)
    
    # Individual crisis period charts (2x3 grid)
    for idx, (name, start, end) in enumerate(crises[:4]):
        row = 2 + idx // 2
        col = idx % 2
        ax = fig.add_subplot(gs[row, col])
        
        start_dt = pd.to_datetime(start)
        end_dt = pd.to_datetime(end)
        
        strat_period = strategy_returns[(strategy_returns.index >= start_dt) & 
                                       (strategy_returns.index <= end_dt)]
        bench_period = benchmark_returns[(benchmark_returns.index >= start_dt) & 
                                        (benchmark_returns.index <= end_dt)]
        
        if len(strat_period) > 0:
            strat_cum_crisis = (1 + strat_period).cumprod()
            bench_cum_crisis = (1 + bench_period).cumprod()
            
            ax.plot(strat_cum_crisis.index, strat_cum_crisis.values, label=strategy_name, linewidth=1)
            ax.plot(bench_cum_crisis.index, bench_cum_crisis.values, label=benchmark_name, linewidth=1, alpha=0.7)
            ax.set_title(f'{name}: ({start} to {end})', fontsize=8)
            ax.legend(fontsize=6)
            ax.grid(True, alpha=0.3)
            ax.tick_params(labelsize=6)
    
    plt.tight_layout()
    
    return fig, crisis_df

# ============================================================================
# USAGE EXAMPLE
# ============================================================================

"""
# Example usage:
import pandas as pd

# Load your returns
strategy_returns = pd.Series(...)  # Your strategy returns
benchmark_returns = pd.Series(...)  # Benchmark returns (e.g., SPY)

# Calculate metrics
metrics = calculate_metrics(strategy_returns, benchmark_returns)

# Generate tables
yearly_table = generate_yearly_returns_table(strategy_returns)
monthly_grid = generate_monthly_performance_grid(strategy_returns)
worst_dd_table = generate_worst_drawdowns_table(strategy_returns)

# Generate crisis visualization
fig, crisis_df = plot_crisis_periods(strategy_returns, benchmark_returns)
fig.savefig('crisis_analysis.png', dpi=150, bbox_inches='tight')

print("All metrics calculated!")
"""
