# ============================================================================
# QULLAMAGGIE STRATEGY - SINGLE SYMBOL BACKTEST
# ============================================================================
# This cell imports the tearsheet module and runs the comprehensive analysis
# 
# REQUIREMENTS:
# 1. Upload 'qullamaggie_tearsheet.py' to Hex Files section
# 2. Run the Setup Cell first (df_all_data must be available)
# ============================================================================

from qullamaggie_tearsheet import run_comprehensive_tearsheet

# Run the comprehensive tearsheet
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

# Extract results for visualization
pf_strategy = results['pf_strategy']
pf_benchmark = results['pf_benchmark']
equity_strategy = results['equity_strategy']
equity_benchmark = results['equity_benchmark']
returns_strategy = results['returns_strategy']
returns_benchmark = results['returns_benchmark']
close = results['close']
breakout_signal = results['breakout_signal']

print("\n📊 Creating visualizations...")

# ============================================================================
# VISUALIZATION 1: Original Equity Curve + Drawdown
# ============================================================================

import plotly.graph_objects as go
from plotly.subplots import make_subplots

fig1 = make_subplots(
    rows=2, cols=1,
    shared_xaxes=True,
    vertical_spacing=0.03,
    row_heights=[0.8, 0.2],
    subplot_titles=(
        'GLD - Qullamaggie Strategy Equity Curve',
        'Drawdown Underwater'
    )
)

# Equity curve
fig1.add_trace(go.Scatter(
    x=equity_strategy.index,
    y=equity_strategy,
    mode='lines',
    name='Strategy',
    line=dict(color='blue', width=2)
), row=1, col=1)

# Buy signals
buy_dates = breakout_signal[breakout_signal].index
buy_prices = equity_strategy[buy_dates]
fig1.add_trace(go.Scatter(
    x=buy_dates,
    y=buy_prices,
    mode='markers',
    name='Buy Signal',
    marker=dict(color='green', size=8, symbol='triangle-up')
), row=1, col=1)

# Initial capital line
fig1.add_hline(y=100000, line_dash="dash", line_color="gray", row=1, col=1)

# Drawdown
drawdown = pf_strategy.drawdown() * 100
fig1.add_trace(go.Scatter(
    x=drawdown.index,
    y=drawdown,
    mode='lines',
    name='Drawdown',
    fill='tozeroy',
    line=dict(color='red', width=1),
    fillcolor='rgba(255, 0, 0, 0.3)'
), row=2, col=1)

fig1.update_xaxes(title_text="Date", row=2, col=1)
fig1.update_yaxes(title_text="Portfolio Value ($)", row=1, col=1)
fig1.update_yaxes(title_text="Drawdown (%)", row=2, col=1)
fig1.update_layout(height=600, showlegend=True, hovermode='x unified')
fig1.show()

print("✅ Visualization 1 complete: Equity Curve + Drawdown")

# ============================================================================
# Note: Additional visualizations from the full tearsheet can be added here
# For now, this condensed version shows the core equity curve and metrics
# ============================================================================

print("\n✅ All visualizations complete!")
print(f"\n💡 Tip: Access results dict for further analysis:")
print(f"   • results['pf_strategy'] - Strategy portfolio")
print(f"   • results['metrics_strategy'] - All strategy metrics")
print(f"   • results['equity_strategy'] - Strategy equity curve")
