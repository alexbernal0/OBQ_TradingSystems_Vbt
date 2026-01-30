# ============================================================================
# SELL HALF AT ATR TARGET - RSI Entry Template
# ============================================================================
# Sell half position at ATR-based target
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

# Stop/Target Parameters (CUSTOMIZE FOR YOUR STRATEGY)
# Add your specific parameters here

# ============================================================================
# LOAD DATA (assumes df_all_data exists)
# ============================================================================

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
    """Calculate RSI indicator - SWAP THIS FUNCTION FOR OTHER INDICATORS"""
    deltas = np.diff(prices)
    gains = np.where(deltas > 0, deltas, 0)
    losses = np.where(deltas < 0, -deltas, 0)
    
    avg_gains = np.zeros(len(prices))
    avg_losses = np.zeros(len(prices))
    
    avg_gains[period] = np.mean(gains[:period])
    avg_losses[period] = np.mean(losses[:period])
    
    for i in range(period + 1, len(prices)):
        avg_gains[i] = (avg_gains[i-1] * (period - 1) + gains[i-1]) / period
        avg_losses[i] = (avg_losses[i-1] * (period - 1) + losses[i-1]) / period
    
    rs = avg_gains / (avg_losses + 1e-10)
    rsi = 100 - (100 / (1 + rs))
    return rsi

rsi = calculate_rsi(close, RSI_PERIOD)

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
# EXIT LOGIC - SELL HALF AT ATR TARGET
# ============================================================================
# Sell half position at ATR-based target
# CUSTOMIZE THIS SECTION WITH YOUR STOP/TARGET LOGIC
# ============================================================================

long_exits = np.zeros(len(df), dtype=bool)
short_exits = np.zeros(len(df), dtype=bool)

in_long = False
in_short = False
entry_price = 0
stop_price = 0
target_price = 0
highest_since_entry = 0
lowest_since_entry = float('inf')

for i in range(len(df)):
    # Enter long position
    if long_entries[i] and not in_long and not in_short:
        in_long = True
        entry_price = close[i]
        highest_since_entry = high[i]
        # Initialize stop/target here
        # stop_price = ...
        # target_price = ...
    
    # Enter short position
    elif short_entries[i] and not in_short and not in_long:
        in_short = True
        entry_price = close[i]
        lowest_since_entry = low[i]
        # Initialize stop/target here
    
    # Check long position exits
    if in_long:
        highest_since_entry = max(highest_since_entry, high[i])
        
        # Add your stop/target logic here
        # Example: if low[i] <= stop_price: long_exits[i] = True
        
        # RSI overbought exit (default)
        if rsi[i] >= RSI_OVERBOUGHT:
            long_exits[i] = True
            in_long = False
    
    # Check short position exits
    if in_short:
        lowest_since_entry = min(lowest_since_entry, low[i])
        
        # Add your stop/target logic here
        
        # RSI oversold exit (default)
        if rsi[i] <= RSI_OVERSOLD:
            short_exits[i] = True
            in_short = False

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
print(f"SELL HALF AT ATR TARGET - {SYMBOL}")
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
    title=f"SELL HALF AT ATR TARGET - {SYMBOL}",
    xaxis_title="Date",
    yaxis_title="Portfolio Value ($)",
    height=600,
    template='plotly_white'
)

fig.show()
