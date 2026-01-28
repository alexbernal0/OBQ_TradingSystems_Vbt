# Multi-Symbol Parameter Optimization - Usage Instructions

## Overview

This system finds the **best generalized parameters** that work across ALL symbols in your database. It optimizes for **Robustness Score** (a combination of performance, stability, and profitability).

---

## Quick Start

### 1. Load Your Data

```python
# Load price data from your database
# DataFrame should have: index=dates, columns=symbols
price_data = pd.read_sql("SELECT * FROM your_table", conn)
# or
price_data = pd.read_csv('your_data.csv', index_col=0, parse_dates=True)
```

### 2. Define Your Strategy Function

Your strategy function should take prices and parameters, return a vectorbt Portfolio:

```python
def your_strategy(prices, param1, param2, param3):
    # Your strategy logic here
    entries = ...  # Boolean series
    exits = ...    # Boolean series
    
    portfolio = vbt.Portfolio.from_signals(prices, entries, exits, freq='1D')
    return portfolio
```

### 3. Define Parameter Grid

```python
param_grid = {
    'param1': [10, 20, 30, 40, 50],
    'param2': [3, 5, 7, 10],
    'param3': [5, 10, 15, 20]
}
```

### 4. Run Optimization

```python
results_df, top_combos, symbol_results = run_multi_symbol_optimization(
    price_data=price_data,
    strategy_func=your_strategy,
    param_grid=param_grid
)
```

### 5. Create Visualizations

```python
param_names = list(param_grid.keys())
fig = create_optimization_visualizations(results_df, top_combos, symbol_results, param_names)
fig.show()
```

### 6. Generate Report

```python
report = generate_optimization_report(results_df, top_combos, symbol_results, param_names, len(price_data.columns))
print(report)
```

---

## Example: Qullamaggie Strategy

```python
def qullamaggie_strategy(prices, trend_sma=50, breakout_period=5, trailing_sma=10):
    # Calculate indicators
    sma_trend = vbt.MA.run(prices, trend_sma).ma
    sma_trailing = vbt.MA.run(prices, trailing_sma).ma
    
    # Entry: Price breaks above recent high and above trend SMA
    recent_high = prices.rolling(breakout_period).max()
    entries = (prices > recent_high.shift(1)) & (prices > sma_trend)
    
    # Exit: Price crosses below trailing SMA
    exits = prices < sma_trailing
    
    portfolio = vbt.Portfolio.from_signals(prices, entries, exits, freq='1D')
    return portfolio

# Define parameter grid
param_grid = {
    'trend_sma': [30, 40, 50, 60, 70],
    'breakout_period': [3, 5, 7, 10],
    'trailing_sma': [5, 10, 15, 20]
}

# Run optimization
results_df, top_combos, symbol_results = run_multi_symbol_optimization(
    price_data=price_data,
    strategy_func=qullamaggie_strategy,
    param_grid=param_grid
)

# Visualize
param_names = ['trend_sma', 'breakout_period', 'trailing_sma']
fig = create_optimization_visualizations(results_df, top_combos, symbol_results, param_names)
fig.show()

# Report
report = generate_optimization_report(results_df, top_combos, symbol_results, param_names, len(price_data.columns))
print(report)
```

---

## Understanding the Output

### 4-Panel Visualization

**Panel 1 (Top-Left): 3D Surface Plot**
- Shows optimization landscape
- Peaks = good parameter regions
- Plateaus = stable parameter regions (what we want!)

**Panel 2 (Top-Right): Scatter Plot - Stability vs Performance**
- X-axis: Median SystemScore (performance)
- Y-axis: % Strong Symbols (stability)
- Bubble size: Median Profit Factor
- Color: Robustness Score (bright = robust)
- **Top-right corner = WINNERS**

**Panel 3 (Bottom-Left): Violin + Box Plot**
- Shows distribution of results for top 5 combos
- Narrow violin = consistent across symbols (good!)
- Wide violin = high variance (risky)

**Panel 4 (Bottom-Right): Grouped Bar Chart**
- Compares top 5 combos across 6 metrics
- Shows trade-offs between different goals

### Text Report Sections

1. **Best Parameters Found**: The winning combination with full stats
2. **Top 5 Combinations**: Alternative good options
3. **Stability Analysis**: How consistent are the results?
4. **Comparison to Alternatives**: How much better is optimal?
5. **Recommendations**: What to do next

---

## Key Metrics Explained

### Robustness Score
```
Robustness Score = (Median SystemScore) × (% Strong / 100) × (Median PF / 2)
```
- Combines performance, stability, and profitability
- Higher is better
- Rewards combos that are BOTH good AND stable

### % Strong Symbols
- Percentage of symbols with Profit Factor > 1.75
- Industry benchmark for "strong" performance
- Higher = works on more symbols

### Coefficient of Variation (CV)
```
CV = Std Dev / Mean
```
- Normalized measure of consistency
- Lower = more stable across symbols
- < 0.5 = excellent consistency

### SystemScore
```
SystemScore = (Sharpe × 30) + (CAGR × 100) + (Max DD × 50)
```
- Composite metric combining risk and return
- Higher is better
- Adjust weights in `calculate_system_score()` if needed

---

## Tips for Best Results

### 1. Parameter Grid Size
- Start small (3-5 values per parameter) for testing
- Expand to larger grid once you verify it works
- Total combinations = product of all parameter lengths
- Example: 5 × 4 × 5 = 100 combinations

### 2. Computation Time
- Time = (# combos) × (# symbols) × (backtest time)
- Example: 100 combos × 59 symbols × 0.5 sec = ~50 minutes
- Use smaller date range for initial testing

### 3. Interpreting Results
- Look for **plateaus** not **spikes** in 3D surface
- Prioritize **% Strong Symbols** over raw SystemScore
- Check **worst-case performance** (Min Score) for robustness
- If top 5 combos are very similar, that's a good sign!

### 4. Custom Fitness Function
If you want to optimize for something other than SystemScore:

```python
def my_fitness_func(returns):
    # Your custom metric here
    sharpe = returns.mean() / returns.std() * np.sqrt(252)
    return sharpe

results_df, top_combos, symbol_results = run_multi_symbol_optimization(
    price_data=price_data,
    strategy_func=your_strategy,
    param_grid=param_grid,
    fitness_func=my_fitness_func  # Pass your function
)
```

---

## Troubleshooting

### "All Robustness Scores are 0"
- Your strategy isn't generating strong results (PF < 1.75)
- Try different parameter ranges
- Check if your strategy logic is correct
- Verify your data quality

### "High variance in results"
- Some symbols work well, others don't
- This is normal for trend-following strategies
- Consider filtering symbols before optimization
- Look at symbol-level breakdown in report

### "Optimization taking too long"
- Reduce parameter grid size
- Use smaller date range for testing
- Test on subset of symbols first
- Consider parallel processing (future enhancement)

---

## Next Steps After Optimization

1. **Review the top 5 combos** - Are they similar? (Good sign!)
2. **Check stability metrics** - Is % Strong > 60%?
3. **Examine worst-case** - Is Min Score acceptable?
4. **Test out-of-sample** - Run on different time period
5. **Symbol-specific analysis** - Which symbols struggle?
6. **Deploy to live trading** - Use winning parameters

---

## Saving Results

```python
# Save results DataFrame
results_df.to_csv('optimization_results.csv', index=False)

# Save top combos
top_combos.to_csv('top_5_combos.csv', index=False)

# Save visualization
fig.write_html('optimization_viz.html')

# Save report
with open('optimization_report.txt', 'w') as f:
    f.write(report)
```

---

## Questions?

This system is designed to be a **reusable template** for any strategy. The key is:
1. Your strategy function returns a vectorbt Portfolio
2. Your parameter grid defines the search space
3. The system finds the best generalized parameters

Adjust the `calculate_system_score()` function if you want different optimization objectives!
