# ============================================================================
# NO STOP LOSS - RSI Entry Template
# ============================================================================
# Exit only on opposite RSI signal (no stop loss)
# Template uses RSI for entries - easily swappable with any other signal logic
# ============================================================================

import pandas as pd
import numpy as np
import vectorbt as vbt
import plotly.graph_objects as go

# ============================================================================
# PARAMETERS
# ============================================================================

SYMBOL = 'BTC'
INITIAL_CAPITAL = 100000
FEES = 0.001
SLIPPAGE = 0.001

# Entry Signal Parameters (RSI - SWAP THIS SECTION FOR OTHER SIGNALS)
RSI_PERIOD = 14
RSI_OVERBOUGHT = 70
RSI_OVERSOLD = 30

# ============================================================================
# LOAD DATA (assumes df_all_data exists with OHLC columns)
# ============================================================================

# Filter for symbol
df = df_all_data[df_all_data['Symbol'] == SYMBOL].copy()
df = df.sort_values('Date').reset_index(drop=True)
df.set_index('Date', inplace=True)

close = df['Close'].values
high = df['High'].values
low = df['Low'].values

# ============================================================================
# ENTRY SIGNAL LOGIC - RSI (REPLACE THIS SECTION FOR DIFFERENT ENTRIES)
# ============================================================================

def calculate_rsi(prices, period=14):
    """Calculate RSI indicator"""
    deltas = np.diff(prices)
    gains = np.where(deltas > 0, deltas, 0)
    losses = np.where(deltas < 0, -deltas, 0)
    
    avg_gains = np.zeros(len(prices))
    avg_losses = np.zeros(len(prices))
    
    # Initial averages
    avg_gains[period] = np.mean(gains[:period])
    avg_losses[period] = np.mean(losses[:period])
    
    # Smoothed averages
    for i in range(period + 1, len(prices)):
        avg_gains[i] = (avg_gains[i-1] * (period - 1) + gains[i-1]) / period
        avg_losses[i] = (avg_losses[i-1] * (period - 1) + losses[i-1]) / period
    
    rs = avg_gains / (avg_losses + 1e-10)
    rsi = 100 - (100 / (1 + rs))
    return rsi

# Calculate RSI
rsi = calculate_rsi(close, RSI_PERIOD)

# Generate entry signals
long_entries = np.zeros(len(df), dtype=bool)
short_entries = np.zeros(len(df), dtype=bool)

for i in range(RSI_PERIOD + 1, len(df)):
    # Long entry: RSI crosses above oversold
    if rsi[i-1] < RSI_OVERSOLD and rsi[i] > RSI_OVERSOLD:
        long_entries[i] = True
    
    # Short entry: RSI crosses below overbought
    if rsi[i-1] > RSI_OVERBOUGHT and rsi[i] < RSI_OVERBOUGHT:
        short_entries[i] = True

# ============================================================================
# EXIT LOGIC - NO STOP LOSS (Exit on opposite signal only)
# ============================================================================

long_exits = np.zeros(len(df), dtype=bool)
short_exits = np.zeros(len(df), dtype=bool)

for i in range(RSI_PERIOD + 1, len(df)):
    # Exit long when RSI reaches overbought
    if rsi[i] >= RSI_OVERBOUGHT:
        long_exits[i] = True
    
    # Exit short when RSI reaches oversold
    if rsi[i] <= RSI_OVERSOLD:
        short_exits[i] = True

# Combine entries and exits
entries = long_entries | short_entries
exits = long_exits | short_exits

# ============================================================================
# RUN BACKTEST
# ============================================================================

pf = vbt.Portfolio.from_signals(
    close=df['Close'],
    entries=entries,
    exits=exits,
    init_cash=INITIAL_CAPITAL,
    fees=FEES,
    slippage=SLIPPAGE,
    freq='1D'
)

# ============================================================================
# PRINT RESULTS
# ============================================================================

stats = pf.stats()

print(f"\n{'='*60}")
print(f"NO STOP LOSS STRATEGY - {SYMBOL}")
print(f"{'='*60}\n")

print(f"Total Return:        {pf.total_return() * 100:.2f}%")
print(f"Sharpe Ratio:        {stats.get('Sharpe Ratio', 0):.2f}")
print(f"Max Drawdown:        {abs(stats.get('Max Drawdown [%]', 0)):.2f}%")
print(f"Win Rate:            {stats.get('Win Rate [%]', 0):.2f}%")
print(f"Total Trades:        {stats.get('Total Trades', 0):.0f}")

print(f"\n{'='*60}\n")

# ============================================================================
# VISUALIZATION
# ============================================================================

equity = pf.value()
fig = go.Figure()

fig.add_trace(go.Scatter(
    x=equity.index,
    y=equity.values,
    name='Strategy',
    line=dict(color='#2E86AB', width=2)
))

fig.update_layout(
    title=f"No Stop Loss Strategy - {SYMBOL}",
    xaxis_title="Date",
    yaxis_title="Portfolio Value ($)",
    height=600,
    template='plotly_white'
)

fig.show()
