# ============================================================================
# QULLAMAGGIE STRATEGY - SINGLE SYMBOL BACKTEST WITH ALL VISUALIZATIONS
# ============================================================================
# This cell imports the tearsheet module and creates ALL visualizations
# 
# REQUIREMENTS:
# 1. Upload 'qullamaggie_tearsheet.py' to Hex Files section
# 2. Run the Setup Cell first (df_all_data must be available)
# ============================================================================

from qullamaggie_tearsheet import run_comprehensive_tearsheet
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np

# Run the comprehensive tearsheet (calculates metrics)
results = run_comprehensive_tearsheet(
    df_all_data=df_all_data,
    symbol='GLD',
    trend_sma=50,
    breakout_period=5,
    trailing_sma=10,
    initial_capital=100000,
    fees=0.001,
    slippage=0.001
)

# Extract results
pf_strategy = results['pf_strategy']
pf_benchmark = results['pf_benchmark']
equity_strategy = results['equity_strategy']
equity_benchmark = results['equity_benchmark']
returns_strategy = results['returns_strategy']
returns_benchmark = results['returns_benchmark']
close = results['close']
breakout_signal = results['breakout_signal']
metrics_strategy = results['metrics_strategy']
metrics_benchmark = results['metrics_benchmark']

# Calculate drawdowns
drawdown_strategy = pf_strategy.drawdown()
drawdown_benchmark = pf_benchmark.drawdown()

SYMBOL = 'GLD'
INITIAL_CAPITAL = 100000

print("\n📊 Creating comprehensive visualizations...")

# ============================================================================
# VIZ 1: ORIGINAL - Strategy Equity Curve with Buy Signals + Drawdown
# ============================================================================

fig1 = make_subplots(
    rows=2, cols=1,
    shared_xaxes=True,
    vertical_spacing=0.03,
    row_heights=[0.8, 0.2],  # Drawdown is 1/5 height
    subplot_titles=(
        f'{SYMBOL} - Qullamaggie Strategy Equity Curve',
        'Drawdown Underwater'
    )
)

# Equity curve
fig1.add_trace(
    go.Scatter(
        x=equity_strategy.index,
        y=equity_strategy.values,
        name='Portfolio Value',
        line=dict(color='#4C78A8', width=2),
        hovertemplate='<b>Date</b>: %{x}<br><b>Value</b>: $%{y:,.2f}<extra></extra>'
    ),
    row=1, col=1
)

# Add initial capital line
fig1.add_hline(
    y=INITIAL_CAPITAL,
    line_dash="dash",
    line_color="gray",
    annotation_text="Initial Capital",
    row=1, col=1
)

# Add buy signals
entry_dates = breakout_signal[breakout_signal].index
entry_prices = equity_strategy[entry_dates]
fig1.add_trace(
    go.Scatter(
        x=entry_dates,
        y=entry_prices,
        mode='markers',
        name='Buy Signal',
        marker=dict(symbol='triangle-up', size=8, color='green'),
        hovertemplate='<b>Buy</b><br>Date: %{x}<br>Value: $%{y:,.2f}<extra></extra>'
    ),
    row=1, col=1
)

# Drawdown underwater
drawdown_pct = drawdown_strategy * 100
fig1.add_trace(
    go.Scatter(
        x=drawdown_pct.index,
        y=drawdown_pct.values,
        name='Drawdown %',
        fill='tozeroy',
        line=dict(color='#E45756', width=1),
        hovertemplate='<b>Date</b>: %{x}<br><b>Drawdown</b>: %{y:.2f}%<extra></extra>'
    ),
    row=2, col=1
)

fig1.update_xaxes(title_text="Date", row=2, col=1)
fig1.update_yaxes(title_text="Portfolio Value ($)", row=1, col=1)
fig1.update_yaxes(title_text="Drawdown (%)", row=2, col=1)

fig1.update_layout(
    title=f"<b>{SYMBOL} - Qullamaggie Strategy Performance</b><br>" +
          f"<sub>CAGR: {metrics_strategy['CAGR']:.2f}% | Sharpe: {metrics_strategy['Sharpe Ratio']:.2f} | Max DD: {metrics_strategy['Max Drawdown']:.2f}% | " +
          f"Win Rate: {metrics_strategy['Win Rate']:.2f}% | SystemScore: {metrics_strategy.get('SystemScore', 0):.2f}</sub>",
    height=700,
    showlegend=True,
    hovermode='x unified',
    template='plotly_white'
)

fig1.show()
print("✅ Visualization 1 complete: Equity Curve + Drawdown")

# ============================================================================
# VIZ 2: Benchmark Comparison Graphs (2x2 Grid)
# ============================================================================

print("   Creating benchmark comparison graphs (2x2 grid)...")

# Calculate cumulative returns (normalized to start at 1.0)
cum_returns_strat = (1 + returns_strategy).cumprod()
cum_returns_bench = (1 + returns_benchmark).cumprod()

# Calculate volatility matched returns
vol_strat = returns_strategy.std()
vol_bench = returns_benchmark.std()
vol_adjustment = vol_strat / vol_bench if vol_bench != 0 else 1
returns_bench_adjusted = returns_benchmark * vol_adjustment
cum_returns_bench_adjusted = (1 + returns_bench_adjusted).cumprod()

# Calculate excess returns (cumulative alpha)
excess_equity = equity_strategy - equity_benchmark

# Create 2x2 grid
fig2 = make_subplots(
    rows=2, cols=2,
    subplot_titles=(
        'Cumulative Returns vs Benchmark',
        'Cumulative Returns (Log Scale)',
        'Volatility Matched Returns',
        'Strategy vs Benchmark Excess (Cumulative Alpha)'
    ),
    vertical_spacing=0.12,
    horizontal_spacing=0.1
)

# Top-left: Cumulative Returns (Normal Scale)
fig2.add_trace(
    go.Scatter(x=cum_returns_strat.index, y=cum_returns_strat.values, name='Strategy', 
               line=dict(color='blue', width=2)),
    row=1, col=1
)
fig2.add_trace(
    go.Scatter(x=cum_returns_bench.index, y=cum_returns_bench.values, name='Benchmark', 
               line=dict(color='orange', width=2)),
    row=1, col=1
)

# Top-right: Cumulative Returns (Log Scale)
fig2.add_trace(
    go.Scatter(x=cum_returns_strat.index, y=cum_returns_strat.values, name='Strategy', 
               line=dict(color='blue', width=2), showlegend=False),
    row=1, col=2
)
fig2.add_trace(
    go.Scatter(x=cum_returns_bench.index, y=cum_returns_bench.values, name='Benchmark', 
               line=dict(color='orange', width=2), showlegend=False),
    row=1, col=2
)
fig2.update_yaxes(type="log", row=1, col=2)

# Bottom-left: Volatility Matched
fig2.add_trace(
    go.Scatter(x=cum_returns_strat.index, y=cum_returns_strat.values, name='Strategy', 
               line=dict(color='blue', width=2), showlegend=False),
    row=2, col=1
)
fig2.add_trace(
    go.Scatter(x=cum_returns_bench_adjusted.index, y=cum_returns_bench_adjusted.values, 
               name='Benchmark (Vol Matched)', line=dict(color='orange', width=2, dash='dash'), showlegend=False),
    row=2, col=1
)

# Bottom-right: Excess Returns (Cumulative Alpha)
fig2.add_trace(
    go.Scatter(x=excess_equity.index, y=excess_equity.values, name='Excess', 
               fill='tozeroy', line=dict(color='green', width=2), 
               fillcolor='rgba(0, 255, 0, 0.2)' if excess_equity.iloc[-1] > 0 else 'rgba(255, 0, 0, 0.2)',
               showlegend=False),
    row=2, col=2
)
fig2.add_hline(y=0, line_dash="dash", line_color="gray", row=2, col=2)

fig2.update_layout(
    title=f"<b>Benchmark Comparison Analysis</b><br>" +
          f"<sub>Strategy Vol: {vol_strat*100*np.sqrt(252):.2f}% | Benchmark Vol: {vol_bench*100*np.sqrt(252):.2f}% | " +
          f"Final Excess: ${excess_equity.iloc[-1]:,.2f}</sub>",
    height=800,
    showlegend=True,
    template='plotly_white'
)

fig2.show()
print("✅ Visualization 2 complete: Benchmark Comparison 2x2 Grid")

# ============================================================================
# VIZ 3: Monthly Returns Heatmap with YTD Column
# ============================================================================

print("   Creating monthly returns heatmap...")

# Calculate monthly returns
monthly_returns_strat = returns_strategy.resample('ME').apply(lambda x: (1 + x).prod() - 1) * 100
monthly_returns_bench = returns_benchmark.resample('ME').apply(lambda x: (1 + x).prod() - 1) * 100

# Create pivot table for heatmap
monthly_pivot = pd.DataFrame({
    'Year': monthly_returns_strat.index.year,
    'Month': monthly_returns_strat.index.month,
    'Return': monthly_returns_strat.values
})
heatmap_data = monthly_pivot.pivot(index='Year', columns='Month', values='Return')

# Add YTD column
ytd_returns = []
for year in heatmap_data.index:
    year_data = monthly_returns_strat[monthly_returns_strat.index.year == year]
    ytd = ((1 + year_data/100).prod() - 1) * 100
    ytd_returns.append(ytd)
heatmap_data['YTD'] = ytd_returns

# Create heatmap
month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec', 'YTD']
fig3 = go.Figure(data=go.Heatmap(
    z=heatmap_data.values,
    x=month_names,
    y=heatmap_data.index,
    colorscale='RdYlGn',
    zmid=0,
    text=[[f'<b>{val:.2f}%</b>' if not np.isnan(val) else '' for val in row] for row in heatmap_data.values],
    texttemplate='%{text}',
    textfont={"size": 11, "family": "Arial Black"},
    showscale=False,
    hovertemplate='<b>%{y} %{x}</b><br>Return: %{z:.2f}%<extra></extra>'
))

fig3.update_layout(
    title=f"<b>Monthly Returns Heatmap (%)</b>",
    xaxis_title="Month",
    yaxis_title="Year",
    height=max(400, len(heatmap_data) * 25),
    template='plotly_white'
)

fig3.show()
print("✅ Visualization 3 complete: Monthly Returns Heatmap")

# ============================================================================
# VIZ 4: Annual Performance Table
# ============================================================================

print("   Creating annual performance table...")

# Calculate annual returns
annual_returns_strat = returns_strategy.resample('YE').apply(lambda x: (1 + x).prod() - 1) * 100
annual_returns_bench = returns_benchmark.resample('YE').apply(lambda x: (1 + x).prod() - 1) * 100
annual_excess = annual_returns_strat - annual_returns_bench

# Create table data
years = [str(year) for year in annual_returns_strat.index.year]

# Build table values properly
header_vals = ['<b>Return (%)</b>'] + [f'<b>{year}</b>' for year in years]

# Build cell values: first column is labels, remaining columns are data
cell_vals = [
    ['Model', 'Benchmark', 'Excess']  # First column: row labels
]

# Add each year's data as a column
for i in range(len(years)):
    year_col = [
        f'{annual_returns_strat.values[i]:.2f}',
        f'{annual_returns_bench.values[i]:.2f}',
        f'{annual_excess.values[i]:.2f}'
    ]
    cell_vals.append(year_col)

# Create color arrays for each cell
cell_colors = [['lightgray', 'lightgray', 'lightgray']]  # First column (labels)
for i in range(len(years)):
    year_colors = [
        'white' if annual_returns_strat.values[i] >= 0 else '#ffcccc',
        'white' if annual_returns_bench.values[i] >= 0 else '#ffcccc',
        'white' if annual_excess.values[i] >= 0 else '#ffcccc'
    ]
    cell_colors.append(year_colors)

# Create font color arrays
font_colors = [['black', 'black', 'black']]  # First column
for i in range(len(years)):
    year_font_colors = [
        'black' if annual_returns_strat.values[i] >= 0 else 'red',
        'black' if annual_returns_bench.values[i] >= 0 else 'red',
        'black' if annual_excess.values[i] >= 0 else 'red'
    ]
    font_colors.append(year_font_colors)

fig4 = go.Figure(data=[go.Table(
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

fig4.update_layout(
    title="<b>Performance by Calendar Year (%)</b>",
    height=200,
    margin=dict(l=0, r=0, t=40, b=0)
)

fig4.show()
print("✅ Visualization 4 complete: Annual Performance Table")

# ============================================================================
# VIZ 5-6: Rolling Metrics (2x2 Grids)
# ============================================================================

print("   Creating rolling metrics visualizations...")

# Calculate rolling metrics for BOTH strategy and benchmark
rolling_window = 252

# Strategy rolling metrics
rolling_sharpe_strat = returns_strategy.rolling(rolling_window).apply(
    lambda x: x.mean() / x.std() * np.sqrt(252) if x.std() != 0 else 0
)
rolling_sortino_strat = returns_strategy.rolling(rolling_window).apply(
    lambda x: x.mean() / x[x < 0].std() * np.sqrt(252) if (x < 0).any() and x[x < 0].std() != 0 else 0
)
rolling_vol_strat = returns_strategy.rolling(rolling_window).std() * np.sqrt(252) * 100
rolling_dd_strat = equity_strategy.rolling(rolling_window).apply(
    lambda x: ((x - x.max()) / x.max()).min() * 100
)

# Benchmark rolling metrics
rolling_sharpe_bench = returns_benchmark.rolling(rolling_window).apply(
    lambda x: x.mean() / x.std() * np.sqrt(252) if x.std() != 0 else 0
)
rolling_sortino_bench = returns_benchmark.rolling(rolling_window).apply(
    lambda x: x.mean() / x[x < 0].std() * np.sqrt(252) if (x < 0).any() and x[x < 0].std() != 0 else 0
)
rolling_vol_bench = returns_benchmark.rolling(rolling_window).std() * np.sqrt(252) * 100
rolling_dd_bench = equity_benchmark.rolling(rolling_window).apply(
    lambda x: ((x - x.max()) / x.max()).min() * 100
)

# Create rolling Sharpe & Sortino
fig5 = make_subplots(
    rows=1, cols=2,
    subplot_titles=('Rolling 252-Day Sharpe Ratio', 'Rolling 252-Day Sortino Ratio'),
    horizontal_spacing=0.1
)

# Add strategy lines
fig5.add_trace(
    go.Scatter(x=rolling_sharpe_strat.index, y=rolling_sharpe_strat.values, name='Strategy', 
               line=dict(color='blue', width=2)),
    row=1, col=1
)
fig5.add_trace(
    go.Scatter(x=rolling_sortino_strat.index, y=rolling_sortino_strat.values, name='Strategy', 
               line=dict(color='blue', width=2)),
    row=1, col=2
)

# Add benchmark lines
fig5.add_trace(
    go.Scatter(x=rolling_sharpe_bench.index, y=rolling_sharpe_bench.values, name='Benchmark', 
               line=dict(color='orange', width=2, dash='dash')),
    row=1, col=1
)
fig5.add_trace(
    go.Scatter(x=rolling_sortino_bench.index, y=rolling_sortino_bench.values, name='Benchmark', 
               line=dict(color='orange', width=2, dash='dash')),
    row=1, col=2
)

fig5.update_layout(
    title="<b>Rolling Risk-Adjusted Returns</b>",
    height=400,
    showlegend=True,
    template='plotly_white',
    legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1)
)

fig5.show()
print("✅ Visualization 5 complete: Rolling Sharpe & Sortino")

# Create rolling Vol & DD
fig6 = make_subplots(
    rows=1, cols=2,
    subplot_titles=('Rolling 252-Day Volatility (%)', 'Rolling 252-Day Max Drawdown (%)'),
    horizontal_spacing=0.1
)

# Add strategy lines
fig6.add_trace(
    go.Scatter(x=rolling_vol_strat.index, y=rolling_vol_strat.values, name='Strategy', 
               line=dict(color='blue', width=2)),
    row=1, col=1
)
fig6.add_trace(
    go.Scatter(x=rolling_dd_strat.index, y=rolling_dd_strat.values, name='Strategy', 
               line=dict(color='blue', width=2)),
    row=1, col=2
)

# Add benchmark lines
fig6.add_trace(
    go.Scatter(x=rolling_vol_bench.index, y=rolling_vol_bench.values, name='Benchmark', 
               line=dict(color='orange', width=2, dash='dash')),
    row=1, col=1
)
fig6.add_trace(
    go.Scatter(x=rolling_dd_bench.index, y=rolling_dd_bench.values, name='Benchmark', 
               line=dict(color='orange', width=2, dash='dash')),
    row=1, col=2
)

fig6.update_layout(
    title="<b>Rolling Risk Metrics</b>",
    height=400,
    showlegend=True,
    template='plotly_white',
    legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1)
)

fig6.show()
print("✅ Visualization 6 complete: Rolling Volatility & Max DD")

# ============================================================================
# VIZ 7: Distribution & Quantiles
# ============================================================================

print("   Creating distribution analysis...")

fig7 = make_subplots(
    rows=1, cols=2,
    subplot_titles=('Distribution of Monthly Returns', 'Returns Quantiles'),
    horizontal_spacing=0.1
)

# Histogram - Strategy vs Benchmark
fig7.add_trace(
    go.Histogram(x=monthly_returns_strat.values, nbinsx=30, name='Strategy',
                 marker=dict(color='#1f77b4', opacity=0.6)),
    row=1, col=1
)
fig7.add_trace(
    go.Histogram(x=monthly_returns_bench.values, nbinsx=30, name='Benchmark',
                 marker=dict(color='#ff7f0e', opacity=0.6)),
    row=1, col=1
)
fig7.add_vline(x=monthly_returns_strat.mean(), line_dash="dash", line_color="#1f77b4", 
               annotation_text="Strategy Mean", row=1, col=1)
fig7.add_vline(x=monthly_returns_bench.mean(), line_dash="dot", line_color="#ff7f0e", 
               annotation_text="Benchmark Mean", row=1, col=1)

# Box plot - Strategy vs Benchmark side-by-side
fig7.add_trace(
    go.Box(y=monthly_returns_strat.values, name='Strategy', marker=dict(color='#1f77b4')),
    row=1, col=2
)
fig7.add_trace(
    go.Box(y=monthly_returns_bench.values, name='Benchmark', marker=dict(color='#ff7f0e')),
    row=1, col=2
)

fig7.update_layout(
    title="<b>Return Distribution Analysis</b>",
    height=400,
    showlegend=True,
    template='plotly_white',
    barmode='overlay',
    legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1)
)

fig7.show()
print("✅ Visualization 7 complete: Distribution & Quantiles")

# ============================================================================
# VIZ 8: Active Returns & Best/Worst Analysis
# ============================================================================

print("   Creating active returns analysis...")

# Calculate active returns (strategy - benchmark)
active_returns = returns_strategy - returns_benchmark

fig8 = make_subplots(
    rows=1, cols=2,
    subplot_titles=('Daily Active Returns (Strategy - Benchmark)', 'Best/Worst Monthly Returns'),
    horizontal_spacing=0.1
)

# Active returns bar chart (with visible colors)
colors = ['#2E7D32' if x >= 0 else '#C62828' for x in active_returns.values]
fig8.add_trace(
    go.Bar(x=active_returns.index, y=active_returns.values * 100, name='Active Returns',
           marker=dict(color=colors)),
    row=1, col=1
)
fig8.add_hline(y=0, line_dash="solid", line_color="black", row=1, col=1)

# Best/Worst months - Strategy vs Benchmark comparison
best_months_strat = monthly_returns_strat.nlargest(5)
worst_months_strat = monthly_returns_strat.nsmallest(5)
combined_strat = pd.concat([worst_months_strat, best_months_strat]).sort_values()

# Get benchmark returns for the same months
combined_bench = monthly_returns_bench.loc[combined_strat.index]

fig8.add_trace(
    go.Bar(x=[f"{idx.strftime('%Y-%m')}" for idx in combined_strat.index], 
           y=combined_strat.values,
           marker=dict(color='#1f77b4'),
           name='Strategy'),
    row=1, col=2
)
fig8.add_trace(
    go.Bar(x=[f"{idx.strftime('%Y-%m')}" for idx in combined_bench.index], 
           y=combined_bench.values,
           marker=dict(color='#ff7f0e'),
           name='Benchmark'),
    row=1, col=2
)
fig8.add_hline(y=0, line_dash="solid", line_color="black", row=1, col=2)

fig8.update_layout(
    title="<b>Active Returns & Best/Worst Analysis</b>",
    height=400,
    showlegend=True,
    template='plotly_white',
    barmode='group',
    legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1)
)

fig8.show()
print("✅ Visualization 8 complete: Active Returns & Best/Worst")

# ============================================================================
# VIZ 9: Crisis Periods Analysis (2x4 Grid)
# ============================================================================

print("   Creating crisis periods analysis...")

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

fig9 = make_subplots(
    rows=2, cols=4,
    subplot_titles=list(CRISIS_PERIODS.keys()),
    vertical_spacing=0.15,
    horizontal_spacing=0.08
)

row_col_map = [(1,1), (1,2), (1,3), (1,4), (2,1), (2,2), (2,3), (2,4)]

for idx, (crisis_name, (start, end)) in enumerate(CRISIS_PERIODS.items()):
    row, col = row_col_map[idx]
    
    try:
        # Filter data for crisis period
        crisis_equity_strat = equity_strategy.loc[start:end]
        crisis_equity_bench = equity_benchmark.loc[start:end]
        
        if len(crisis_equity_strat) > 0:
            # Normalize to start at 1.0
            norm_strat = crisis_equity_strat / crisis_equity_strat.iloc[0]
            norm_bench = crisis_equity_bench / crisis_equity_bench.iloc[0]
            
            fig9.add_trace(
                go.Scatter(x=norm_strat.index, y=norm_strat.values, name='Strategy',
                           line=dict(color='blue', width=2), showlegend=(idx==0)),
                row=row, col=col
            )
            fig9.add_trace(
                go.Scatter(x=norm_bench.index, y=norm_bench.values, name='Benchmark',
                           line=dict(color='orange', width=2), showlegend=(idx==0)),
                row=row, col=col
            )
        else:
            # Not enough history
            fig9.add_annotation(
                text="Not enough history",
                xref=f"x{idx+1}", yref=f"y{idx+1}",
                x=0.5, y=0.5, showarrow=False,
                font=dict(size=12, color="gray"),
                row=row, col=col
            )
    except:
        # Error handling
        fig9.add_annotation(
            text="Not enough history",
            xref=f"x{idx+1}", yref=f"y{idx+1}",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=12, color="gray"),
            row=row, col=col
        )

fig9.update_layout(
    title="<b>Crisis Periods Analysis (Normalized to 1.0)</b>",
    height=600,
    showlegend=True,
    template='plotly_white'
)

fig9.show()
print("✅ Visualization 9 complete: Crisis Periods Analysis")

print("\n✅ All visualizations complete!")
print(f"\n💡 Tip: Access results dict for further analysis:")
print(f"   • results['pf_strategy'] - Strategy portfolio")
print(f"   • results['metrics_strategy'] - All strategy metrics")
print(f"   • results['equity_strategy'] - Strategy equity curve")
