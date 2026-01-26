# VectorBT Knowledge Base

Comprehensive documentation for using VectorBT effectively in trading system development.

## 📚 Contents

### Fundamentals
- [VectorBT Architecture](fundamentals/01_vectorbt_architecture.md) - How VectorBT works under the hood
- [Vectorization Concepts](fundamentals/02_vectorization_concepts.md) - Understanding vectorized programming
- [Performance Optimization](fundamentals/03_performance_optimization.md) - Speed and memory optimization

### Data Handling
- [Data Preparation](data/01_data_preparation.md) - Required data formats and transformations
- [OHLCV Handling](data/02_ohlcv_handling.md) - Working with price data
- [Missing Data](data/03_missing_data.md) - Handling gaps and missing values
- [Hex Data Integration](data/04_hex_data_integration.md) - Hex.tech specific workflows

### Signal Generation
- [Signal Generation Basics](signals/01_signal_generation.md) - Creating entry/exit signals
- [Indicator Factories](signals/02_indicator_factories.md) - Custom indicator creation
- [Signal Combination](signals/03_signal_combination.md) - Combining multiple signals
- [Common Patterns](signals/04_common_patterns.md) - Frequently used signal patterns

### Portfolio Construction
- [Portfolio from Signals](portfolio/01_portfolio_construction.md) - Using Portfolio.from_signals()
- [Position Sizing](portfolio/02_position_sizing.md) - Size parameter options
- [Stops and Targets](portfolio/03_stops_and_targets.md) - Stop loss implementation
- [Portfolio Optimization](portfolio/04_portfolio_optimization.md) - Multi-asset portfolios

### Performance Analysis
- [Performance Metrics](performance/01_performance_analysis.md) - Available metrics and statistics
- [Visualization](performance/02_visualization.md) - Plotting results
- [Benchmark Comparison](performance/03_benchmark_comparison.md) - Comparing to benchmarks
- [Hex Reporting](performance/04_hex_reporting.md) - Creating reports in Hex.tech

### Optimization
- [Parameter Optimization](optimization/01_parameter_optimization.md) - Grid search techniques
- [Walk-Forward Analysis](optimization/02_walk_forward_analysis.md) - Out-of-sample testing
- [Overfitting Prevention](optimization/03_overfitting_prevention.md) - Avoiding curve fitting

### Troubleshooting
- [Common Errors](troubleshooting/common_errors.md) - Frequent issues and solutions
- [Performance Issues](troubleshooting/performance_issues.md) - Speed and memory problems
- [Hex-Specific Issues](troubleshooting/hex_specific_issues.md) - Hex.tech specific problems

## 🎯 Quick Reference

### Data Format Cheat Sheet

**Long Format (Database)**:
```
Date       | Symbol | Open | High | Low  | Close | Volume
2025-01-01 | AAPL   | 150  | 152  | 149  | 151   | 1000000
2025-01-01 | MSFT   | 300  | 305  | 299  | 303   | 500000
```

**Wide Format (VectorBT)**:
```
           | AAPL | MSFT
2025-01-01 | 151  | 303
2025-01-02 | 152  | 305
```

### Common Operations

**Load and Transform Data**:
```python
from src.data.loaders import load_from_motherduck
from src.data.transformers import create_ohlcv_dict

df = load_from_motherduck("GoldenOpp.GDX_GLD_Mining_Stocks_Prices")
ohlcv = create_ohlcv_dict(df)
close_prices = ohlcv['close']
```

**Generate Signals**:
```python
import vectorbt as vbt

# Moving average crossover
fast_ma = vbt.MA.run(close_prices, 10)
slow_ma = vbt.MA.run(close_prices, 50)

entries = fast_ma.ma_crossed_above(slow_ma)
exits = fast_ma.ma_crossed_below(slow_ma)
```

**Run Backtest**:
```python
pf = vbt.Portfolio.from_signals(
    close_prices,
    entries,
    exits,
    init_cash=100000,
    fees=0.001
)

print(pf.stats())
```

## 📖 Learning Path

1. **Start Here**: [Data Preparation](data/01_data_preparation.md)
2. **Then**: [Signal Generation Basics](signals/01_signal_generation.md)
3. **Next**: [Portfolio from Signals](portfolio/01_portfolio_construction.md)
4. **Finally**: [Performance Analysis](performance/01_performance_analysis.md)

## 🔗 External Resources

- [Official VectorBT Documentation](https://vectorbt.dev/documentation/)
- [VectorBT PRO Documentation](https://vectorbt.pro/documentation/)
- [VectorBT GitHub](https://github.com/polakowo/vectorbt)
- [VectorBT Discord Community](https://discord.gg/vectorbt)

## 📝 Contributing

Found an error or want to add content? See [Contributing Guidelines](../docs/contributing.md).
