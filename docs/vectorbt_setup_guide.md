# VectorBT Backtesting Setup for the Qullamaggie System

## 1. Executive Summary

This document provides a comprehensive guide for setting up a high-performance backtesting environment for the Qullamaggie trend-following system using **VectorBT** within a **Hex.tech notebook**. Based on extensive research, **VectorBT is the optimal choice** for this project due to its exceptional speed, scalability, and alignment with the strategy's requirements. This guide outlines the necessary data preparation steps, a detailed implementation of the Qullamaggie system in VectorBT, and best practices for analysis and visualization.

## 2. Why VectorBT is the Optimal Choice

Our research compared VectorBT with other popular Python backtesting libraries like Backtrader and Zipline. VectorBT emerged as the clear winner for the following reasons:

| Feature | VectorBT | Backtrader | Zipline |
|---|---|---|---|
| **Speed** | ⚡⚡⚡ **Fastest** | ⚡ Slow | ⚡ Very Slow |
| **Architecture** | Vectorized (NumPy + Numba) | Event-Driven (Python loops) | Event-Driven (Python loops) |
| **Best For** | Large datasets, optimization | Beginners, live trading | Academic factor research |

- **Unmatched Speed**: VectorBT is benchmarked to be up to **1000x faster** than Backtrader [1]. This is critical for backtesting the Qullamaggie system over 53 years of data across 59 symbols.
- **Scalability**: VectorBT's vectorized nature allows for simultaneous backtesting of all symbols and effortless parameter optimization (e.g., testing different lookback periods for breakouts and moving averages).
- **Alignment with Qullamaggie System**: The strategy's rules (trend filters, breakout entries, trailing stops) can be expressed as vectorized signals, which is VectorBT's native approach.

## 3. Data Preparation and Transformation

VectorBT requires data in a "wide" format, where each symbol is a column and the index is a DateTime series. Our `GoldenOpp.GDX_GLD_Mining_Stocks_Prices` table is in a "long" (normalized) format, so we need to pivot it.

### 3.1. Connecting to MotherDuck and Pivoting Data

The following Python code, to be run in your Hex.tech notebook, connects to your MotherDuck database, retrieves the data, and transforms it into the required wide format.

```python
import duckdb
import pandas as pd
import vectorbt as vbt

# --- 1. Connect to MotherDuck ---
# Make sure to add your MotherDuck token as a secret in Hex.tech
MOTHERDUCK_TOKEN = "YOUR_MOTHERDUCK_TOKEN"
conn = duckdb.connect(f'md:?motherduck_token={MOTHERDUCK_TOKEN}')

# --- 2. Query the GoldenOpp Database ---
query = """
SELECT Date, Symbol, Open, High, Low, Close, Volume
FROM GoldenOpp.GDX_GLD_Mining_Stocks_Prices
ORDER BY Date, Symbol
"""
df_long = conn.execute(query).df()
df_long['Date'] = pd.to_datetime(df_long['Date'])

# --- 3. Pivot to Wide Format ---
close_prices = df_long.pivot(index='Date', columns='Symbol', values='Close')
high_prices = df_long.pivot(index='Date', columns='Symbol', values='High')
low_prices = df_long.pivot(index='Date', columns='Symbol', values='Low')
open_prices = df_long.pivot(index='Date', columns='Symbol', values='Open')
volume = df_long.pivot(index='Date', columns='Symbol', values='Volume')

# --- 4. Handle Missing Data ---
# Forward-fill to handle non-trading days and missing data
close_prices = close_prices.ffill()
high_prices = high_prices.ffill()
low_prices = low_prices.ffill()
open_prices = open_prices.ffill()
volume = volume.fillna(0) # Fill missing volume with 0

print("Data Transformation Complete!")
print(f"Close prices shape: {close_prices.shape}")
print(f"Date range: {close_prices.index.min()} to {close_prices.index.max()}")
```

## 4. Implementing the Qullamaggie System in VectorBT

Now, we'll implement the core components of the Qullamaggie system using VectorBT's functions.

### 4.1. Trend Filter

The system only takes long trades when the price is above the 50-day Simple Moving Average (SMA).

```python
# --- 1. Calculate the 50-day SMA ---
sma_50 = vbt.MA.run(close_prices, 50)

# --- 2. Create the trend filter ---
trend_filter = close_prices > sma_50.ma
```

### 4.2. Breakout Entry

The entry signal is a breakout above the high of the last 5 bars.

```python
# --- 1. Calculate the 5-day rolling high ---
breakout_high = high_prices.rolling(5).max()

# --- 2. Generate entry signals ---
# We enter if the close is above the previous bar's breakout high
entry_signals = (close_prices > breakout_high.shift(1)) & trend_filter
```

### 4.3. Trailing Stop Exit

The exit is a trailing stop using the 10-day or 20-day SMA. We'll use the 10-day SMA for this example.

```python
# --- 1. Calculate the 10-day SMA ---
sma_10 = vbt.MA.run(close_prices, 10)

# --- 2. Generate exit signals ---
# We exit if the close drops below the 10-day SMA
exit_signals = close_prices < sma_10.ma
```

### 4.4. Running the Backtest

With our entry and exit signals defined, we can now run the backtest using `Portfolio.from_signals`.

```python
# --- Run the backtest ---
pf = vbt.Portfolio.from_signals(
    close=close_prices,
    entries=entry_signals,
    exits=exit_signals,
    init_cash=100000,       # Initial capital
    fees=0.001,             # 0.1% commission per trade
    slippage=0.001,         # 0.1% slippage per trade
    freq='D'                # Daily frequency
)

# --- Print the results ---
print(pf.stats())
```

## 5. Performance Analysis and Visualization

VectorBT provides a rich set of tools for analyzing and visualizing the backtest results.

### 5.1. Key Performance Metrics

The `pf.stats()` output provides a comprehensive summary. Here are some of the most important metrics:

- **Total Return**: The total percentage return of the portfolio.
- **Max Drawdown**: The largest peak-to-trough decline in portfolio value.
- **Sharpe Ratio**: The risk-adjusted return (higher is better).
- **Calmar Ratio**: The ratio of annualized return to max drawdown (higher is better).
- **Win Rate**: The percentage of trades that were profitable.

### 5.2. Plotting Results

VectorBT's plotting capabilities are excellent for visualizing performance.

```python
# --- Plot the cumulative returns of the portfolio ---
pf.plot().show()

# --- Plot the underwater (drawdown) curve ---
pf.plot_underwater().show()

# --- Plot the trades on the price chart for a specific symbol ---
pf.plot_trades(close_prices['AEM'], title='AEM Trades').show()
```

## 6. Recommendations for Further Research

This setup provides a solid foundation. Here are some ideas for further research:

- **Parameter Optimization**: Use VectorBT's grid search capabilities to find the optimal lookback periods for the moving averages and breakout signals.
- **Walk-Forward Analysis**: Test the strategy on out-of-sample data to ensure its robustness.
- **Intraday Data**: For a more accurate implementation of the Qullamaggie system, consider using intraday data (e.g., 1-hour or 30-minute) for the breakout entries.
- **Position Sizing**: Implement more advanced position sizing models, such as volatility-based sizing.

## 7. References

[1] GitHub. (2021). *use-case question: performance comparison*. [https://github.com/polakowo/vectorbt/discussions/209](https://github.com/polakowo/vectorbt/discussions/209)

)

