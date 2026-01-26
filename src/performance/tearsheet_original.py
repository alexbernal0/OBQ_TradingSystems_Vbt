%matplotlib inline
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import datetime as dt

# Reload the Parquet file for ETF data
etf_df = pd.read_parquet('Active_US_ETFs_Database.parquet').reset_index()

# Assuming 'returns' is the pd.Series of daily strategy returns from previous cell
initial_cash = 1000000.0
cum_equity = initial_cash * (1 + returns).cumprod()
equity_df = pd.DataFrame({
    'Daily portfolio return %': returns * 100,
    'Cumulative equity curve total': cum_equity
}, index=returns.index)

# Extract strategy returns
strategy_returns = equity_df['Daily portfolio return %'] / 100

# Strip timezone from strategy_returns index
strategy_returns.index = strategy_returns.index.tz_localize(None)

# Find first date with non-zero return
non_zero_dates = strategy_returns[strategy_returns != 0].index
if not non_zero_dates.empty:
    start_date = non_zero_dates[0]
    strategy_returns = strategy_returns.loc[start_date:].copy()
else:
    print("No actual returns in the data.")
    strategy_returns = pd.Series()  # Empty if no returns

# Load benchmark returns (SPY as proxy)
bench_df = etf_df[etf_df['Symbol'] == 'SPY'].set_index('Date')['Close']
bench_df.index = bench_df.index.tz_localize(None)  # Ensure tz-naive
benchmark_returns = bench_df.pct_change().fillna(0)
benchmark_returns = benchmark_returns.reindex(strategy_returns.index).fillna(0)

def cum_returns(ret):
    return (1 + ret).cumprod() - 1

def cagr(ret, periods_per_year=252):
    if len(ret) == 0:
        return 0
    cum = cum_returns(ret).iloc[-1]
    years = len(ret) / periods_per_year
    return (1 + cum) ** (1 / years) - 1 if years > 0 else 0

def max_drawdown(ret):
    if len(ret) == 0:
        return 0
    cum = cum_returns(ret) + 1
    dd = cum / cum.cummax() - 1
    return dd.min()

def drawdown_duration(ret):
    if len(ret) == 0:
        return 0
    cum = cum_returns(ret) + 1
    peak = cum.cummax()
    dd = cum / peak - 1
    in_dd = dd < 0
    dd_groups = (in_dd != in_dd.shift()).cumsum()
    dd_durations = in_dd.groupby(dd_groups).cumcount() + 1
    return dd_durations.max() if in_dd.any() else 0

def volatility(ret, periods_per_year=252):
    return ret.std() * np.sqrt(periods_per_year) if len(ret) > 0 else 0

def downside_dev(ret, rf=0):
    if len(ret) == 0:
        return 0
    downside = ret[ret < rf]
    return np.sqrt((downside - rf).pow(2).mean()) * np.sqrt(252) if not downside.empty else 0

def sharpe(ret, rf=0, periods_per_year=252):
    if len(ret) == 0:
        return 0
    excess = ret - rf / periods_per_year
    return excess.mean() / excess.std() * np.sqrt(periods_per_year) if excess.std() != 0 else 0

def sortino(ret, rf=0, periods_per_year=252):
    if len(ret) == 0:
        return 0
    excess = ret - rf / periods_per_year
    down_std = np.sqrt((excess[excess < 0] ** 2).mean()) * np.sqrt(periods_per_year) if len(excess[excess < 0]) > 0 else 0
    return excess.mean() * periods_per_year / down_std if down_std != 0 else 0

def calmar(ret):
    if len(ret) == 0:
        return 0
    md = abs(max_drawdown(ret))
    return cagr(ret) / md if md != 0 else np.inf

def omega(ret, rf=0):
    if len(ret) == 0:
        return np.inf
    threshold = rf / 252
    pos = (ret[ret > threshold] - threshold).sum()
    neg = abs((ret[ret < threshold] - threshold).sum())
    return pos / neg if neg != 0 else np.inf

def recovery_factor(ret):
    if len(ret) == 0:
        return np.inf
    cum_ret = cum_returns(ret).iloc[-1]
    md = abs(max_drawdown(ret))
    return cum_ret / md if md != 0 else np.inf

def ulcer_index(ret):
    if len(ret) == 0:
        return 0
    cum = cum_returns(ret) + 1
    dd = (cum - cum.cummax()) / cum.cummax()
    return np.sqrt((dd ** 2).mean())

def serenity_index(ret, rf=0):
    if len(ret) == 0:
        return np.inf
    excess_ret = cagr(ret) - rf
    ui = ulcer_index(ret)
    return excess_ret / (ui ** 2) if ui != 0 else np.inf

def value_at_risk(ret, level=0.05):
    if len(ret) == 0:
        return 0
    return ret.quantile(level) if len(ret) > 1 else 0

def conditional_var(ret, level=0.05):
    if len(ret) == 0:
        return 0
    var = value_at_risk(ret, level)
    tail = ret[ret <= var]
    return tail.mean() if not tail.empty else 0

def kelly_criterion(ret):
    if len(ret) == 0:
        return 0
    win_prob = (ret > 0).mean()
    win_loss_ratio = ret[ret > 0].mean() / abs(ret[ret < 0].mean()) if (ret < 0).any() else np.inf
    return win_prob - (1 - win_prob) / win_loss_ratio if win_loss_ratio != 0 else 0

def payoff_ratio(ret):
    if len(ret) == 0 or not (ret < 0).any():
        return np.inf
    return ret[ret > 0].mean() / abs(ret[ret < 0].mean())

def profit_factor(ret):
    if len(ret) == 0 or not (ret < 0).any():
        return np.inf
    return ret[ret > 0].sum() / abs(ret[ret < 0].sum())

def gain_pain_ratio(ret):
    if len(ret) == 0 or not (ret < 0).any():
        return np.inf
    return ret.mean() / abs(ret[ret < 0].mean())

def common_sense_ratio(ret):
    pf = profit_factor(ret)
    tr = tail_ratio(ret)
    return pf * tr if tr != np.inf else np.inf

def cpc_index(ret):
    return payoff_ratio(ret) * profit_factor(ret) * (ret > 0).mean()

def tail_ratio(ret):
    if len(ret) < 2:
        return np.inf
    q05 = ret.quantile(0.05)
    return ret.quantile(0.95) / abs(q05) if q05 != 0 else np.inf

def outlier_win_ratio(ret):
    if len(ret) == 0 or not (ret > 0).any():
        return 0
    upper = ret.mean() + 3 * ret.std()
    lower = ret.mean() - 3 * ret.std()
    outliers = ret[(ret > upper) | (ret < lower)]
    win_out = outliers[outliers > 0]
    return win_out.mean() / ret[ret > 0].mean() if not win_out.empty else 0

def outlier_loss_ratio(ret):
    if len(ret) == 0 or not (ret < 0).any():
        return 0
    upper = ret.mean() + 3 * ret.std()
    lower = ret.mean() - 3 * ret.std()
    outliers = ret[(ret > upper) | (ret < lower)]
    loss_out = outliers[outliers < 0]
    return abs(loss_out.mean()) / abs(ret[ret < 0].mean()) if not loss_out.empty else 0

def avg_drawdown(ret):
    if len(ret) == 0:
        return 0
    cum = cum_returns(ret) + 1
    dd = (cum - cum.cummax()) / cum.cummax()
    in_dd = dd < 0
    dd_groups = (in_dd != in_dd.shift()).cumsum()
    avg_dd = dd[in_dd].groupby(dd_groups).mean().mean() if in_dd.any() else 0
    return avg_dd

def avg_dd_days(ret):
    if len(ret) == 0:
        return 0
    cum = cum_returns(ret) + 1
    dd = (cum - cum.cummax()) / cum.cummax()
    in_dd = dd < 0
    dd_groups = (in_dd != in_dd.shift()).cumsum()
    dd_lengths = in_dd.groupby(dd_groups).sum()
    return dd_lengths.mean() if not dd_lengths.empty else 0

def win_rate(ret, period='D'):
    if len(ret) == 0:
        return 0
    resampled = ret.resample(period).sum()
    return (resampled > 0).mean() * 100 if len(resampled) > 0 else 0

def calculate_metrics(returns, benchmark_returns=None, rf=0.0):
    metrics = {}

    # Basic metrics
    metrics['Risk-Free Rate'] = rf * 100
    metrics['Time in Market'] = (returns != 0).mean() * 100 if len(returns) > 0 else 0
    metrics['Cumulative Return'] = cum_returns(returns).iloc[-1] * 100 if len(returns) > 0 else 0
    metrics['CAGR﹪'] = cagr(returns) * 100
    metrics['Sharpe'] = sharpe(returns, rf)
    metrics['Sortino'] = sortino(returns, rf)
    metrics['Sortino/√2'] = metrics['Sortino'] / np.sqrt(2) if 'Sortino' in metrics else 0
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
        metrics['Smart Sortino/√2'] = metrics['Smart Sortino'] / np.sqrt(2) if 'Smart Sortino' in metrics else 0
    else:
        metrics['Prob. Sharpe Ratio'] = 0
        metrics['Smart Sharpe'] = 0
        metrics['Smart Sortino'] = 0
        metrics['Smart Sortino/√2'] = 0

    if benchmark_returns is not None and len(benchmark_returns) > 0:
        metrics['Correlation vs Benchmark'] = returns.corr(benchmark_returns)
        metrics['Beta'] = returns.cov(benchmark_returns) / benchmark_returns.var() if benchmark_returns.var() != 0 else 0
        metrics['Standard Deviation (monthly)'] = returns.resample('M').std().mean() if len(returns) > 0 else 0
        metrics['Downside Deviation'] = downside_dev(returns)
        metrics['VaR Historical'] = value_at_risk(returns) * 100
        metrics['Compound ROR'] = cagr(returns) * 100
        metrics['Winning Months (%)'] = win_rate(returns, 'M')
        metrics['Average Winning Month'] = metrics['Avg. Up Month']
        metrics['Average Losing Month'] = metrics['Avg. Down Month']

    return metrics

def get_drawdowns(returns):
    if len(returns) == 0:
        return pd.DataFrame()
    cum = (1 + returns).cumprod()
    peak = cum.cummax()
    dd = (cum / peak - 1) * 100
    in_dd = dd < 0
    dd_starts = dd[(dd.shift(1) >= 0) & (dd < 0)].index  # Start when DD begins
    dd_ends = dd[(dd.shift(-1) >= 0) & (dd < 0)].index  # End when DD ends
    drawdowns = []
    for start, end in zip(dd_starts, dd_ends):
        period_dd = dd[start:end]
        min_dd = period_dd.min()
        days = (end - start).days
        drawdowns.append({'Started': start, 'Recovered': end, 'Drawdown': min_dd, 'Days': days})
    df_dd = pd.DataFrame(drawdowns).sort_values('Drawdown').reset_index(drop=True)
    return df_dd

def get_eoy_returns(returns):
    if len(returns) == 0:
        return pd.DataFrame()
    yearly = returns.resample('Y').sum()
    cum = (1 + yearly).cumprod() - 1
    eoy = pd.DataFrame({
        'Year': yearly.index.year,
        'Return': yearly * 100,
        'Cumulative': cum * 100
    })
    return eoy

def get_monthly_table(returns):
    if len(returns) == 0:
        return pd.DataFrame()
    monthly = returns.resample('M').sum() * 100
    pivot = pd.pivot_table(monthly.reset_index(), values=monthly.name, index=monthly.index.year, columns=monthly.index.month)
    pivot.columns = pd.date_range("2020-01-01", periods=12, freq="M").strftime('%b')
    pivot['Year'] = pivot.sum(1)
    return pivot

def get_return_report(returns):
    periods = {
        '1 Month': 'M',
        '3 Months': '3M',
        '6 Months': '6M',
        '1 Year': 'Y',
        '3 Years': '3Y',
        '5 Years': '5Y',
        '10 Years': '10Y'
    }
    report = pd.DataFrame(columns=['Period', 'Best', 'Worst', 'Average', 'Median', 'Last'])
    for name, freq in periods.items():
        res = returns.resample(freq).sum() * 100
        if len(res) > 0:
            report = pd.concat([report, pd.DataFrame({
                'Period': [name],
                'Best': [res.max()],
                'Worst': [res.min()],
                'Average': [res.mean()],
                'Median': [res.median()],
                'Last': [res.iloc[-1]]
            })], ignore_index=True)
    return report

def plot_cumulative(returns, benchmark_returns, crises):
    fig, ax = plt.subplots(figsize=(12, 6))
    cum_s = (1 + returns).cumprod()
    cum_b = (1 + benchmark_returns).cumprod()
    ax.plot(cum_s, label='Strategy', color='blue')
    ax.plot(cum_b, label='Benchmark', color='orange')
    for crisis, (start, end, color) in crises.items():
        if start <= cum_s.index.max() and end >= cum_s.index.min():
            ax.axvspan(max(start, cum_s.index.min()), min(end, cum_s.index.max()), color=color, alpha=0.3)
            ax.text(max(start, cum_s.index.min()), ax.get_ylim()[1], crisis, rotation=90, va='bottom')
    ax.legend()
    ax.set_title('Economic Stress Equity Curve')
    return fig

def plot_drawdown(returns, benchmark_returns, crises):
    fig, ax = plt.subplots(figsize=(12, 6))
    cum_s = (1 + returns).cumprod()
    dd_s = cum_s / cum_s.cummax() - 1
    cum_b = (1 + benchmark_returns).cumprod()
    dd_b = cum_b / cum_b.cummax() - 1
    ax.plot(dd_s, label='Strategy DD %', color='blue')
    ax.plot(dd_b, label='Benchmark DD %', color='orange')
    for _, (start, end, color) in crises.items():
        if start <= dd_s.index.max() and end >= dd_s.index.min():
            ax.axvspan(max(start, dd_s.index.min()), min(end, dd_s.index.max()), color=color, alpha=0.3)
    ax.legend()
    return fig

def plot_crisis_periods(returns, benchmark_returns, crises):
    figs = []
    for name, (start, end, _) in crises.items():
        if start <= returns.index.max() and end >= returns.index.min():
            fig, ax = plt.subplots(figsize=(6, 4))
            period_ret_s = returns[max(start, returns.index.min()):min(end, returns.index.max())]
            period_ret_b = benchmark_returns[max(start, benchmark_returns.index.min()):min(end, benchmark_returns.index.max())]
            cum_s = (1 + period_ret_s).cumprod()
            cum_b = (1 + period_ret_b).cumprod()
            ax.plot(cum_s, label='Strategy', color='blue')
            ax.plot(cum_b, label='Benchmark', color='orange')
            ax.set_title(name)
            ax.legend()
            figs.append(fig)