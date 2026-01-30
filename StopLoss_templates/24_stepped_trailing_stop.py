# pip install vectorbt pandas numpy yfinance plotly

"""
==============================================================================
STEPPED TRAILING STOP STRATEGY
==============================================================================

DESCRIPTION:
This trailing stop moves in predetermined increments rather than following 
every price tick. For example, it might advance by 0.5% for every 1% favorable 
movement, or move up one ATR for every two ATR gain. This reduces the frequency 
of stop adjustments while maintaining trend-following characteristics and 
filtering minor fluctuations.

HOW IT WORKS:
1. Enter position with initial stop (e.g., 2% below entry)
2. Define step size (e.g., 0.5% increments) and trigger distance (e.g., 1% gain)
3. When price gains 1%, move stop up by 0.5%
4. When price gains another 1%, move stop up another 0.5%
5. Continue stepping until exit

KEY FEATURES:
- Reduces transaction costs by 50-70% vs continuous trailing
- Filters out minor price fluctuations
- Easier to backtest and optimize
- Psychologically easier to manage

PARAMETERS TO ADJUST:
- STEP_TRIGGER_PCT: Price gain required to trigger stop move (0.5-2.0%)
- STEP_SIZE_PCT: Amount to move stop when triggered (0.25-1.0%)
- INITIAL_STOP_PCT: Initial stop distance from entry (1.0-3.0%)

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
STEP_TRIGGER_PCT = 1.0          # % gain required to trigger stop move
STEP_SIZE_PCT = 0.5             # % to move stop when triggered
INITIAL_STOP_PCT = 2.0          # Initial stop distance from entry

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
# STEPPED TRAILING STOP LOGIC (DO NOT MODIFY)
# ==============================================================================

# Initialize arrays
n = len(close)
stop_price = np.full(n, np.nan)
in_position = np.zeros(n, dtype=bool)
entry_price = np.full(n, np.nan)
highest_high = np.full(n, np.nan)
next_trigger_level = np.full(n, np.nan)
stop_steps = np.zeros(n, dtype=int)

# Track position state
current_entry = np.nan
current_stop = np.nan
current_highest = np.nan
current_trigger = np.nan
steps_taken = 0

for i in range(1, n):
    # Check if we should enter
    if entries.iloc[i] and not in_position[i-1]:
        in_position[i] = True
        current_entry = close.iloc[i]
        current_stop = current_entry * (1 - INITIAL_STOP_PCT / 100)
        current_highest = high.iloc[i]
        current_trigger = current_entry * (1 + STEP_TRIGGER_PCT / 100)
        steps_taken = 0
        
        entry_price[i] = current_entry
        stop_price[i] = current_stop
        highest_high[i] = current_highest
        next_trigger_level[i] = current_trigger
        stop_steps[i] = steps_taken
        
    # If in position, manage stepped trailing stop
    elif in_position[i-1]:
        in_position[i] = True
        entry_price[i] = current_entry
        
        # Update highest high
        if high.iloc[i] > current_highest:
            current_highest = high.iloc[i]
        
        # Check if we've hit the next trigger level
        while current_highest >= current_trigger:
            # Move stop up by step size
            step_amount = current_entry * (STEP_SIZE_PCT / 100)
            current_stop += step_amount
            
            # Set next trigger level
            current_trigger += current_entry * (STEP_TRIGGER_PCT / 100)
            steps_taken += 1
        
        stop_price[i] = current_stop
        highest_high[i] = current_highest
        next_trigger_level[i] = current_trigger
        stop_steps[i] = steps_taken
        
        # Check if stop hit
        if low.iloc[i] <= current_stop:
            in_position[i] = False
            current_entry = np.nan
            current_stop = np.nan
            current_highest = np.nan
            current_trigger = np.nan
            steps_taken = 0
        
        # Check if exit signal
        elif exits.iloc[i]:
            in_position[i] = False
            current_entry = np.nan
            current_stop = np.nan
            current_highest = np.nan
            current_trigger = np.nan
            steps_taken = 0

# Create exit signals from stop hits
stop_exits = pd.Series(False, index=close.index)
for i in range(1, n):
    if in_position[i-1] and not in_position[i]:
        stop_exits.iloc[i] = True

# Combine with signal exits
final_exits = exits | stop_exits

print(f"Stop loss exits: {stop_exits.sum()}")
print(f"Total exits: {final_exits.sum()}")

# Calculate stop adjustment statistics
max_steps = int(np.nanmax(stop_steps))
print(f"Maximum steps taken in a single trade: {max_steps}")

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
print("STEPPED TRAILING STOP - BACKTEST RESULTS")
print("="*80)
print(f"\nSymbol: {SYMBOL}")
print(f"Period: {START_DATE} to {END_DATE}")
print(f"Step Trigger: {STEP_TRIGGER_PCT}% gain")
print(f"Step Size: {STEP_SIZE_PCT}%")
print(f"Initial Stop: {INITIAL_STOP_PCT}%")
print(f"Max Steps in Trade: {max_steps}")
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
        f'{SYMBOL} Price with Stepped Trailing Stops',
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

# Add stop levels (stepped appearance)
stop_series = pd.Series(stop_price, index=close.index)
fig.add_trace(go.Scatter(
    x=stop_series.index, y=stop_series,
    name='Stop Level',
    line=dict(color='red', width=2, shape='hv'),  # hv creates step appearance
    opacity=0.7
), row=1, col=1)

# Add trigger levels
trigger_series = pd.Series(next_trigger_level, index=close.index)
fig.add_trace(go.Scatter(
    x=trigger_series.index, y=trigger_series,
    name='Next Trigger',
    line=dict(color='orange', width=1, dash='dot'),
    opacity=0.5
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
    title_text=f"Stepped Trailing Stop Strategy - {SYMBOL}",
    hovermode='x unified'
)

fig.update_xaxes(title_text="Date", row=3, col=1)
fig.update_yaxes(title_text="Price ($)", row=1, col=1)
fig.update_yaxes(title_text="RSI", row=2, col=1)
fig.update_yaxes(title_text="Value ($)", row=3, col=1)

fig.show()

print("\n✅ Backtest complete!")
