# VectorBT Research Report: Optimal Backtesting Framework for the Qullamaggie Trend System

**Prepared for**: Qullamaggie Trend System Project  
**Date**: January 26, 2026  
**Author**: Manus AI

---

## Executive Summary

This report presents the findings of comprehensive research into backtesting frameworks for implementing the Qullamaggie trend-following system on a universe of 59 gold mining stocks and ETFs with 53 years of historical data. After evaluating VectorBT against alternative Python backtesting libraries and analyzing its architecture, performance characteristics, and data requirements, we conclude that **VectorBT is the optimal choice** for this project. The library's vectorized architecture delivers execution speeds up to 1000x faster than traditional event-driven frameworks, making it uniquely suited for testing strategies across large datasets with multiple parameter combinations. This report provides detailed guidance on data transformation, implementation patterns, and best practices for deploying the Qullamaggie system in a Hex.tech notebook environment.

---

## 1. Introduction

The Qullamaggie Breakout system is a trend-following momentum strategy that combines daily trend filters with intraday breakout entries and trailing stop exits. Successfully backtesting this system requires processing 368,281 rows of historical data across 59 symbols spanning five decades. The choice of backtesting framework significantly impacts development velocity, computational efficiency, and the ability to optimize strategy parameters. This research evaluates VectorBT as the primary candidate and compares it against established alternatives to determine the best fit for project requirements.

---

## 2. VectorBT Architecture and Core Principles

VectorBT represents a paradigm shift in Python backtesting by operating entirely on vectorized NumPy arrays rather than event-driven loops. This architectural decision has profound implications for performance and scalability.

### 2.1 The Vectorization Advantage

Traditional backtesting frameworks like Backtrader and Zipline process market data sequentially, executing Python code for each bar in the time series. While this event-driven approach mirrors how traders think about markets, it creates severe performance bottlenecks when working with large datasets. VectorBT instead represents each trading strategy instance as a multi-dimensional array, allowing operations to be broadcast across all data points simultaneously.

The performance difference is dramatic. Benchmark tests show VectorBT executing backtests approximately **1000x faster** than Backtrader on identical strategies [1]. For example, a pairs trading strategy that took hours in Backtrader completed in seconds with VectorBT while producing identical results [1]. This speed advantage compounds when testing multiple parameter combinations or running walk-forward analyses.

### 2.2 Technology Stack

VectorBT's performance stems from its carefully chosen technology stack:

| Component | Role | Performance Impact |
|-----------|------|-------------------|
| **NumPy** | Array operations | 5x faster than pure Python |
| **Pandas** | Time series handling | Familiar interface, optimized C code |
| **Numba** | JIT compilation | **Machine code speed** (1000x+ faster) |
| **Plotly** | Interactive visualization | Rich dashboards for analysis |

The key innovation is Numba, a just-in-time compiler that converts Python code to native machine code. VectorBT uses Numba extensively for portfolio simulation, allowing complex iterative logic (like trailing stops and position management) to execute at speeds comparable to C implementations while maintaining Python's readability [2].

### 2.3 Data Model

VectorBT treats columns in a DataFrame as separate backtesting instances rather than features of a single instrument. This seemingly simple design choice enables massive parallelization. When testing the same strategy across 59 symbols, VectorBT processes all symbols simultaneously in a single vectorized operation, whereas traditional frameworks would loop through each symbol sequentially.

---

## 3. Comparative Analysis: VectorBT vs Alternatives

To validate VectorBT as the optimal choice, we evaluated three leading Python backtesting frameworks across multiple dimensions.

### 3.1 Performance Comparison

| Framework | Architecture | Speed | Best Use Case |
|-----------|-------------|-------|---------------|
| **VectorBT** | Vectorized (NumPy + Numba) | ⚡⚡⚡ **Fastest** (millions of trades/second) | Large datasets, parameter optimization, quantitative research |
| **Backtrader** | Event-driven (Python loops) | ⚡ Acceptable for small/medium data | Beginners, live trading, multi-timeframe strategies |
| **Zipline** | Event-driven (per-bar Python) | ⚡ Slow (hours for large datasets) | Equity factor research, academic studies |

### 3.2 VectorBT Strengths

**Blazing Speed**: VectorBT's vectorized architecture eliminates Python loops, the primary bottleneck in backtesting. The library can simulate millions of trades in under a second, making it feasible to test strategies across decades of data for dozens of symbols in minutes rather than hours [3].

**Parameter Sweeps**: The Qullamaggie system has several tunable parameters (breakout lookback period, moving average lengths, trailing stop distance). VectorBT can test 1,000+ parameter combinations simultaneously through its grid search capabilities, a task that would be prohibitively slow in traditional frameworks [3].

**Interactive Dashboards**: Integration with Plotly and ipywidgets enables visual exploration of strategy performance. Users can interactively adjust parameters and immediately see updated equity curves, drawdown plots, and trade distributions [3].

**Custom Indicators**: VectorBT's indicator factory system allows creation of complex multi-input indicators that integrate seamlessly with the backtesting engine. This is particularly valuable for implementing the Qullamaggie system's breakout detection and trailing stop logic.

### 3.3 VectorBT Weaknesses

**Learning Curve**: VectorBT requires familiarity with vectorized programming concepts. Developers accustomed to event-driven thinking must shift their mental model from "what happens on each bar" to "how do I express this as an array operation." This conceptual leap can be challenging initially but pays dividends in performance [3].

**Mental Model Shift**: The vectorized approach is less intuitive for strategies with complex state dependencies. However, the Qullamaggie system's relatively straightforward rules (trend filter, breakout entry, trailing stop) map naturally to vectorized signals, mitigating this concern.

### 3.4 Why Not Backtrader or Zipline?

**Backtrader** excels at live trading integration and offers a gentler learning curve, but its event-driven architecture makes it unsuitable for large-scale optimization [4]. Testing the Qullamaggie system across 59 symbols with multiple parameter combinations would take hours or days.

**Zipline** was designed for equity factor research and offers a sophisticated pipeline API, but it suffers from installation challenges (designed for Python 3.5-3.6) and poor performance on large datasets [3]. Its strengths don't align with our project's requirements.

### 3.5 Verdict

For the Qullamaggie system, VectorBT is the clear winner. The project's requirements—large dataset (368,281 rows), multi-symbol backtesting (59 symbols), parameter optimization, and quantitative analysis—align perfectly with VectorBT's strengths. The learning curve is justified by the dramatic performance gains and research capabilities.

---

## 4. Data Format Requirements

VectorBT's performance depends on properly structured data. The library expects data in "wide" format with a DateTime index and symbols as columns, which differs from our current normalized database structure.

### 4.1 Current GoldenOpp Structure

The `GoldenOpp.GDX_GLD_Mining_Stocks_Prices` table uses a normalized (long) format:

```
Symbol      VARCHAR      Stock ticker
Date        TIMESTAMP    Trading date
Open        DOUBLE       Opening price
High        DOUBLE       Highest price
Low         DOUBLE       Lowest price
Close       DOUBLE       Closing price
Adj_Close   DOUBLE       Adjusted close
Volume      BIGINT       Trading volume
Sector      VARCHAR      Industry sector
Data_Source VARCHAR      Source identifier
```

This structure is optimal for database storage and querying but must be transformed for VectorBT.

### 4.2 Required Wide Format

VectorBT requires separate DataFrames for each OHLCV component:

```python
# Close prices DataFrame
                 AEM    AG   AGI   ARMN   ASM    AU  ...  WPM
Date                                                  
1972-06-01      NaN   NaN   NaN    NaN   NaN   NaN  ...  NaN
1980-03-17    12.50   NaN   NaN    NaN   NaN   NaN  ...  NaN
...             ...   ...   ...    ...   ...   ...  ...  ...
2025-12-15    85.23  12.4  3.45   8.90  15.2  25.6  ... 62.3
```

This format enables VectorBT to process all symbols simultaneously through NumPy broadcasting.

### 4.3 Transformation Code

```python
import duckdb
import pandas as pd

# Connect to MotherDuck
conn = duckdb.connect(f'md:?motherduck_token={MOTHERDUCK_TOKEN}')

# Load data
query = """
SELECT Date, Symbol, Open, High, Low, Close, Volume
FROM GoldenOpp.GDX_GLD_Mining_Stocks_Prices
ORDER BY Date, Symbol
"""
df = conn.execute(query).df()
df['Date'] = pd.to_datetime(df['Date'])

# Pivot to wide format
close_prices = df.pivot(index='Date', columns='Symbol', values='Close')
high_prices = df.pivot(index='Date', columns='Symbol', values='High')
low_prices = df.pivot(index='Date', columns='Symbol', values='Low')
open_prices = df.pivot(index='Date', columns='Symbol', values='Open')
volume = df.pivot(index='Date', columns='Symbol', values='Volume')

# Handle missing data
close_prices = close_prices.ffill()  # Forward fill for non-trading days
high_prices = high_prices.ffill()
low_prices = low_prices.ffill()
open_prices = open_prices.ffill()
volume = volume.fillna(0)
```

### 4.4 Memory Considerations

The transformed data will occupy approximately 30-50 MB in memory (767,000 cells × 5 OHLCV components × 8 bytes per float). With indicators and signals, expect total memory usage around 100-200 MB, well within the capacity of modern systems and Hex.tech notebooks.

---

## 5. Implementing the Qullamaggie System

The Qullamaggie system's logic maps naturally to VectorBT's signal-based approach.

### 5.1 System Components

**Trend Filter**: Only take long positions when price is above the 50-day SMA on the daily timeframe.

```python
sma_50 = vbt.MA.run(close_prices, 50)
trend_filter = close_prices > sma_50.ma
```

**Breakout Entry**: Enter when price breaks above the 5-bar high.

```python
breakout_high = high_prices.rolling(5).max()
entry_signals = (close_prices > breakout_high.shift(1)) & trend_filter
```

**Trailing Stop Exit**: Exit when price closes below the 10-day SMA.

```python
sma_10 = vbt.MA.run(close_prices, 10)
exit_signals = close_prices < sma_10.ma
```

### 5.2 Running the Backtest

```python
pf = vbt.Portfolio.from_signals(
    close=close_prices,
    entries=entry_signals,
    exits=exit_signals,
    init_cash=100000,
    fees=0.001,      # 0.1% commission
    slippage=0.001,  # 0.1% slippage
    freq='D'
)

# Analyze results
print(pf.stats())
print(f"Total Return: {pf.total_return():.2%}")
print(f"Sharpe Ratio: {pf.sharpe_ratio():.2f}")
print(f"Max Drawdown: {pf.max_drawdown():.2%}")
```

### 5.3 Stop Loss Implementation

VectorBT offers two approaches for implementing stops:

**Built-in Parameters** (Simple):
```python
pf = vbt.Portfolio.from_signals(
    close_prices,
    entries,
    exits,
    sl_stop=0.10,  # 10% stop loss
    ts_stop=0.15   # 15% trailing stop
)
```

**Custom Logic** (More Control):
```python
# Trailing stop based on rolling maximum
rolling_max = close_prices.cummax()
trailing_stop_exit = close_prices < (rolling_max * 0.90)  # 10% trail

# Combine with SMA exit
exits = trailing_stop_exit | (close_prices < sma_10.ma)
```

For the Qullamaggie system, the custom approach is preferable as it allows implementing the specific SMA-based trailing stop logic described in the TradingView script.

---

## 6. Performance Analysis and Metrics

VectorBT provides comprehensive performance analytics through the `Portfolio` object.

### 6.1 Key Metrics

| Metric | Description | Interpretation |
|--------|-------------|----------------|
| **Total Return** | Cumulative percentage return | Overall profitability |
| **Sharpe Ratio** | Risk-adjusted return | Higher is better (>1 is good) |
| **Max Drawdown** | Largest peak-to-trough decline | Risk measure (lower is better) |
| **Calmar Ratio** | Return / Max Drawdown | Risk-adjusted performance |
| **Win Rate** | Percentage of profitable trades | Consistency measure |
| **Profit Factor** | Gross profit / Gross loss | Should be >1.5 for robust strategies |

### 6.2 Visualization

```python
# Equity curve
pf.plot().show()

# Drawdown analysis
pf.plot_underwater().show()

# Trade distribution
pf.trades.plot().show()

# Per-symbol performance
pf.total_return().sort_values(ascending=False).plot(kind='bar')
```

---

## 7. Optimization and Parameter Tuning

VectorBT's vectorization enables efficient parameter optimization.

### 7.1 Grid Search Example

```python
# Test multiple parameter combinations
breakout_periods = [3, 5, 7, 10]
ma_periods = [10, 20, 30]
trailing_stops = [10, 20, 50]

# VectorBT can test all combinations simultaneously
results = []
for bp in breakout_periods:
    for ma in ma_periods:
        for ts in trailing_stops:
            # Calculate signals with parameters
            breakout_high = high_prices.rolling(bp).max()
            sma = vbt.MA.run(close_prices, ma)
            trailing_sma = vbt.MA.run(close_prices, ts)
            
            entries = (close_prices > breakout_high.shift(1)) & (close_prices > sma.ma)
            exits = close_prices < trailing_sma.ma
            
            # Run backtest
            pf = vbt.Portfolio.from_signals(close_prices, entries, exits, init_cash=100000)
            
            results.append({
                'breakout_period': bp,
                'ma_period': ma,
                'trailing_stop': ts,
                'total_return': pf.total_return().mean(),
                'sharpe_ratio': pf.sharpe_ratio().mean(),
                'max_drawdown': pf.max_drawdown().mean()
            })

# Analyze results
results_df = pd.DataFrame(results)
best_params = results_df.loc[results_df['sharpe_ratio'].idxmax()]
print(f"Best parameters: {best_params}")
```

### 7.2 Walk-Forward Analysis

To avoid overfitting, implement walk-forward testing:

```python
# Split data into training and testing periods
train_end = '2020-12-31'
test_start = '2021-01-01'

close_train = close_prices.loc[:train_end]
close_test = close_prices.loc[test_start:]

# Optimize on training data
# ... (grid search code)

# Test on out-of-sample data
pf_test = vbt.Portfolio.from_signals(close_test, entries_test, exits_test, init_cash=100000)
print(f"Out-of-sample Sharpe: {pf_test.sharpe_ratio().mean():.2f}")
```

---

## 8. Recommendations

### 8.1 Implementation Roadmap

**Phase 1: Initial Setup** (Week 1)
- Set up Hex.tech notebook with VectorBT installation
- Connect to MotherDuck and transform data to wide format
- Implement basic Qullamaggie system with fixed parameters
- Validate results against manual calculations

**Phase 2: Refinement** (Week 2)
- Implement custom trailing stop logic matching TradingView script
- Add position sizing rules (equal weight, volatility-adjusted, etc.)
- Incorporate transaction costs and slippage
- Analyze per-symbol performance

**Phase 3: Optimization** (Week 3)
- Run parameter grid search for optimal lookback periods
- Perform walk-forward analysis to test robustness
- Compare against buy-and-hold benchmarks (GDX, GDXJ)
- Generate comprehensive performance reports

**Phase 4: Advanced Analysis** (Week 4)
- Analyze performance across different market regimes (bull/bear markets)
- Test sensitivity to parameter changes
- Implement portfolio-level position management
- Create interactive dashboard for strategy monitoring

### 8.2 Best Practices

**Start with Recent Data**: Begin testing with the last 10-15 years (2010-2025) to reduce computation time during development. Expand to full historical data once the implementation is validated.

**Validate Incrementally**: Test each component (trend filter, breakout entry, trailing stop) independently before combining them. This makes debugging easier and builds confidence in the implementation.

**Use Adjusted Close Prices**: For accurate backtests, use adjusted close prices that account for splits and dividends. Our GoldenOpp database includes this data.

**Account for Survivorship Bias**: The Norgate data in our database is survivorship-bias-free, which is critical for accurate historical testing. Ensure this data is used for all backtests.

**Compare to Benchmarks**: Always compare strategy performance to buy-and-hold returns for GDX and GDXJ ETFs to assess whether the active strategy adds value.

### 8.3 Potential Enhancements

**Intraday Data**: The Qullamaggie system is designed for intraday breakout entries on 1-hour or 30-minute charts. If intraday data becomes available, implement the system on that timeframe for more accurate results.

**Dynamic Position Sizing**: Implement volatility-based position sizing (e.g., using ATR) to adjust position sizes based on market conditions.

**Sector Rotation**: Use the sector information in the database to implement sector rotation rules (e.g., only trade stocks in sectors showing relative strength).

**Machine Learning Integration**: Use VectorBT's fast backtesting as a fitness function for machine learning models that predict breakout success probability.

---

## 9. Conclusion

VectorBT is the optimal backtesting framework for implementing the Qullamaggie trend system on the GoldenOpp dataset. Its vectorized architecture delivers execution speeds up to 1000x faster than traditional frameworks, enabling rapid iteration, comprehensive parameter optimization, and deep analysis across 59 symbols and 53 years of data. The library's signal-based approach aligns naturally with the Qullamaggie system's logic, and its rich analytics capabilities support thorough performance evaluation.

The data transformation from GoldenOpp's normalized format to VectorBT's wide format is straightforward and can be accomplished with a simple pivot operation. Once transformed, the data enables simultaneous backtesting across all symbols, leveraging VectorBT's vectorization for maximum efficiency.

By following the implementation roadmap and best practices outlined in this report, the Qullamaggie system can be deployed in a Hex.tech notebook environment with confidence that the backtesting infrastructure will support rigorous analysis and optimization. The combination of high-quality survivorship-bias-free data, a powerful backtesting engine, and a well-defined trading system creates an excellent foundation for quantitative research and strategy development.

---

## 10. References

[1] GitHub. (2021). *use-case question: performance comparison*. Retrieved from https://github.com/polakowo/vectorbt/discussions/209

[2] VectorBT. (2024). *Fundamentals - VectorBT® PRO*. Retrieved from https://vectorbt.pro/documentation/fundamentals/

[3] Trading Dude. (2025). *Battle-Tested Backtesters: Comparing VectorBT, Zipline, and Backtrader for Financial Strategy Development*. Medium. Retrieved from https://medium.com/@trading.dude/battle-tested-backtesters-comparing-vectorbt-zipline-and-backtrader-for-financial-strategy-dee33d33a9e0

[4] Greyhound Analytics. (2022). *Vectorbt vs Backtrader*. Retrieved from https://greyhoundanalytics.com/blog/vectorbt-vs-backtrader/

---

**Document Version**: 1.0  
**Last Updated**: January 26, 2026  
**Next Review**: After Phase 1 implementation completion
