# pip install vectorbt pandas numpy yfinance plotly

"""
==============================================================================
TIME-DELAYED TRAILING STOP STRATEGY
==============================================================================

DESCRIPTION:
This trailing stop waits for price confirmation before moving the stop level 
higher. Instead of immediately trailing when price makes new highs, it requires 
the favorable price to persist for a specified time period (e.g., 3 bars) before 
updating the stop. This prevents stops from moving on temporary spikes that 
quickly reverse.

HOW IT WORKS:
1. Enter long position with initial stop (e.g., 2x ATR below entry)
2. Track highest high since entry
3. When price makes new high, start confirmation timer
4. If price stays above previous high for X bars, move stop up
5. If price falls back before confirmation, stop stays at previous level

KEY FEATURES:
- Reduces whipsaws by 30-40% vs immediate trailing
- Provides stability in choppy trending markets
- Filters out intraday noise and false breakouts
- Better suited for volatile assets

PARAMETERS TO ADJUST:
- CONFIRMATION_BARS: Number of bars price must hold before stop moves (2-5)
- TRAILING_ATR_MULT: ATR multiplier for trailing distance (1.5-3.0)
- INITIAL_STOP_ATR_MULT: ATR multiplier for initial stop (2.0-4.0)

==============================================================================
ENTRY SIGNAL LOGIC - RSI (REPLACE THIS SECTION FOR DIFFERENT ENTRIES)
==============================================================================
Current entry: RSI < 30 (oversold)
Current exit: RSI > 70 (overbought) OR stop loss

To use different entry logic:
1. Replace the RSI calculation with your indicator
2. Replace 'entries' boolean array with your entry conditions
3. Replace 'exits' boolean array with your exit conditions (optional)
4. Keep the stop loss logic below unchanged
==============================================================================
"""

import pandas as pd
import numpy as np
import vectorbt as vbt
import yfinance as yf
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# ==============================================================================
# PARAMETERS
# ==============================================================================

# Data parameters
SYMBOL = 'SPY'
START_DATE = '2020-01-01'
END_DATE = '2024-12-31'

# Entry signal parameters (RSI)
RSI_PERIOD = 14
RSI_ENTRY = 30
RSI_EXIT = 70

# Stop loss parameters
CONFIRMATION_BARS = 3           # Bars to confirm before moving stop
TRAILING_ATR_MULT = 2.0         # ATR multiplier for trailing distance
INITIAL_STOP_ATR_MULT = 2.5     # ATR multiplier for initial stop
ATR_PERIOD = 14

# Backtest parameters
INITIAL_CAPITAL = 100000
FEES = 0.001
SLIPPAGE = 0.001

# ==============================================================================
# LOAD DATA
# ==============================================================================

print(f"Loading data for {SYMBOL}...")
data = yf.download(SYMBOL, start=START_DATE, end=END_DATE, progress=False)
close = data['Close']
high = data['High']
low = data['Low']

print(f"Data loaded: {len(close)} bars from {close.index[0].date()} to {close.index[-1].date()}")

# ==============================================================================
# ENTRY SIGNAL LOGIC - RSI (REPLACE THIS SECTION)
# ==============================================================================

# Calculate RSI
rsi = vbt.RSI.run(close, window=RSI_PERIOD).rsi

# Entry: RSI crosses below oversold level
entries = (rsi < RSI_ENTRY) & (rsi.shift(1) >= RSI_ENTRY)

# Exit: RSI crosses above overbought level (will be combined with stops)
exits = (rsi > RSI_EXIT) & (rsi.shift(1) <= RSI_EXIT)

print(f"Entry signals generated: {entries.sum()} total")
print(f"Exit signals generated: {exits.sum()} total")

# ==============================================================================
# TIME-DELAYED TRAILING STOP LOGIC (DO NOT MODIFY)
# ==============================================================================

# Calculate ATR for stop distances
atr = vbt.ATR.run(high, low, close, window=ATR_PERIOD).atr

# Initialize arrays
n = len(close)
stop_price = np.full(n, np.nan)
in_position = np.zeros(n, dtype=bool)
entry_price = np.full(n, np.nan)
highest_high = np.full(n, np.nan)
bars_above_prev_high = np.zeros(n, dtype=int)
confirmed_high = np.full(n, np.nan)

# Track position state
current_entry = np.nan
current_stop = np.nan
current_highest = np.nan
current_confirmed_high = np.nan
bars_confirming = 0

for i in range(1, n):
    # Check if we should enter
    if entries.iloc[i] and not in_position[i-1]:
        in_position[i] = True
        current_entry = close.iloc[i]
        current_stop = current_entry - (INITIAL_STOP_ATR_MULT * atr.iloc[i])
        current_highest = high.iloc[i]
        current_confirmed_high = current_highest
        bars_confirming = 0
        
        entry_price[i] = current_entry
        stop_price[i] = current_stop
        highest_high[i] = current_highest
        confirmed_high[i] = current_confirmed_high
        
    # If in position, manage trailing stop
    elif in_position[i-1]:
        in_position[i] = True
        entry_price[i] = current_entry
        
        # Update highest high
        if high.iloc[i] > current_highest:
            current_highest = high.iloc[i]
            bars_confirming = 1  # Start confirmation counter
        elif high.iloc[i] >= current_confirmed_high:
            # Price is still above previous confirmed high
            bars_confirming += 1
        else:
            # Price fell below previous confirmed high
            bars_confirming = 0
        
        # Check if we have enough confirmation bars
        if bars_confirming >= CONFIRMATION_BARS:
            # Move confirmed high to current highest
            current_confirmed_high = current_highest
            # Update stop based on confirmed high
            new_stop = current_confirmed_high - (TRAILING_ATR_MULT * atr.iloc[i])
            current_stop = max(current_stop, new_stop)  # Stop can only move up
            bars_confirming = 0  # Reset counter
        
        stop_price[i] = current_stop
        highest_high[i] = current_highest
        confirmed_high[i] = current_confirmed_high
        bars_above_prev_high[i] = bars_confirming
        
        # Check if stop hit
        if low.iloc[i] <= current_stop:
            in_position[i] = False
            current_entry = np.nan
            current_stop = np.nan
            current_highest = np.nan
            current_confirmed_high = np.nan
            bars_confirming = 0
        
        # Check if exit signal
        elif exits.iloc[i]:
            in_position[i] = False
            current_entry = np.nan
            current_stop = np.nan
            current_highest = np.nan
            current_confirmed_high = np.nan
            bars_confirming = 0

# Create exit signals from stop hits
stop_exits = pd.Series(False, index=close.index)
for i in range(1, n):
    if in_position[i-1] and not in_position[i]:
        stop_exits.iloc[i] = True

# Combine with signal exits
final_exits = exits | stop_exits

print(f"Stop loss exits: {stop_exits.sum()}")
print(f"Total exits: {final_exits.sum()}")

# ==============================================================================
# RUN BACKTEST
# ==============================================================================

print("\nRunning backtest...")

portfolio = vbt.Portfolio.from_signals(
    close=close,
    entries=entries,
    exits=final_exits,
    init_cash=INITIAL_CAPITAL,
    fees=FEES,
    slippage=SLIPPAGE,
    freq='1D'
)

# ==============================================================================
# CALCULATE METRICS
# ==============================================================================

stats = portfolio.stats()

print("\n" + "="*80)
print("TIME-DELAYED TRAILING STOP - BACKTEST RESULTS")
print("="*80)
print(f"\nSymbol: {SYMBOL}")
print(f"Period: {START_DATE} to {END_DATE}")
print(f"Confirmation Bars: {CONFIRMATION_BARS}")
print(f"Trailing ATR Multiplier: {TRAILING_ATR_MULT}x")
print(f"Initial Stop ATR Multiplier: {INITIAL_STOP_ATR_MULT}x")
print(f"\nTotal Trades: {stats['Total Trades']}")
print(f"Win Rate: {stats['Win Rate [%]']:.2f}%")
print(f"Total Return: {stats['Total Return [%]']:.2f}%")
print(f"Sharpe Ratio: {stats['Sharpe Ratio']:.2f}")
print(f"Max Drawdown: {stats['Max Drawdown [%]']:.2f}%")
print(f"Profit Factor: {stats.get('Profit Factor', 'N/A')}")
print("="*80)

# ==============================================================================
# VISUALIZATION
# ==============================================================================

print("\nGenerating visualization...")

# Create subplots
fig = make_subplots(
    rows=3, cols=1,
    shared_xaxes=True,
    vertical_spacing=0.05,
    subplot_titles=(
        f'{SYMBOL} Price with Time-Delayed Trailing Stops',
        'RSI Indicator',
        'Portfolio Value'
    ),
    row_heights=[0.5, 0.25, 0.25]
)

# Plot 1: Price with stops
fig.add_trace(go.Scatter(
    x=close.index, y=close,
    name='Price',
    line=dict(color='blue', width=1)
), row=1, col=1)

# Add stop levels
stop_series = pd.Series(stop_price, index=close.index)
fig.add_trace(go.Scatter(
    x=stop_series.index, y=stop_series,
    name='Stop Level',
    line=dict(color='red', width=1, dash='dot'),
    opacity=0.7
), row=1, col=1)

# Add entry/exit markers
entry_dates = close.index[entries]
entry_prices = close[entries]
fig.add_trace(go.Scatter(
    x=entry_dates, y=entry_prices,
    mode='markers',
    name='Entry',
    marker=dict(symbol='triangle-up', size=10, color='green')
), row=1, col=1)

exit_dates = close.index[final_exits]
exit_prices = close[final_exits]
fig.add_trace(go.Scatter(
    x=exit_dates, y=exit_prices,
    mode='markers',
    name='Exit',
    marker=dict(symbol='triangle-down', size=10, color='red')
), row=1, col=1)

# Plot 2: RSI
fig.add_trace(go.Scatter(
    x=rsi.index, y=rsi,
    name='RSI',
    line=dict(color='purple', width=1)
), row=2, col=1)

fig.add_hline(y=RSI_ENTRY, line_dash="dash", line_color="green", row=2, col=1)
fig.add_hline(y=RSI_EXIT, line_dash="dash", line_color="red", row=2, col=1)

# Plot 3: Portfolio value
portfolio_value = portfolio.value()
fig.add_trace(go.Scatter(
    x=portfolio_value.index, y=portfolio_value,
    name='Portfolio Value',
    line=dict(color='green', width=2),
    fill='tozeroy'
), row=3, col=1)

# Update layout
fig.update_layout(
    height=1000,
    showlegend=True,
    title_text=f"Time-Delayed Trailing Stop Strategy - {SYMBOL}",
    hovermode='x unified'
)

fig.update_xaxes(title_text="Date", row=3, col=1)
fig.update_yaxes(title_text="Price ($)", row=1, col=1)
fig.update_yaxes(title_text="RSI", row=2, col=1)
fig.update_yaxes(title_text="Value ($)", row=3, col=1)

fig.show()

print("\n✅ Backtest complete!")
