# Qullamaggie Trend-Following System

A momentum-based breakout strategy with tight stops and trailing exits, based on the trading methodology of Kristjan Kullamägi (Qullamaggie).

## 📊 System Overview

The Qullamaggie system is designed to catch strong trending moves by:
1. **Filtering for uptrends** using daily moving averages
2. **Entering on breakouts** when price exceeds recent highs
3. **Using tight initial stops** to limit risk per trade
4. **Trailing stops** to capture large moves while protecting profits

See [System Explanation](docs/system_explanation.md) for detailed methodology.

## 🎯 Strategy Parameters

### Default Configuration

```yaml
# Trend Filter
trend_sma_period: 50          # Daily SMA for trend identification
trend_filter_enabled: true    # Only trade when above 50 SMA

# Entry Signal
breakout_period: 5            # Number of bars for breakout high
entry_timeframe: "daily"      # Timeframe for breakout detection

# Exit Signal
trailing_sma_period: 10       # SMA period for trailing stop
use_20sma_trail: false        # Alternative: use 20 SMA instead

# Position Sizing
initial_capital: 100000       # Starting capital
position_size_pct: 0.10       # 10% of capital per position
max_positions: 10             # Maximum concurrent positions

# Risk Management
fees: 0.001                   # 0.1% commission per trade
slippage: 0.001               # 0.1% slippage assumption
```

## 📈 Performance Summary

**Backtest Period**: 1972-2025 (53 years)  
**Universe**: 56 gold mining stocks + 4 ETFs  
**Data Source**: GoldenOpp.GDX_GLD_Mining_Stocks_Prices (MotherDuck)

### Key Metrics
*(To be filled after initial backtest)*

- **CAGR**: TBD
- **Sharpe Ratio**: TBD
- **Max Drawdown**: TBD
- **Win Rate**: TBD
- **Profit Factor**: TBD

## 🚀 Quick Start

### In Hex.tech

1. **Load the data**:
```python
from src.data.loaders import load_from_motherduck
from src.data.transformers import create_ohlcv_dict

df = load_from_motherduck("GoldenOpp.GDX_GLD_Mining_Stocks_Prices")
ohlcv = create_ohlcv_dict(df)
```

2. **Run the strategy**:
```python
from strategies.qullamaggie.strategy import QullamaggieStrategy

strategy = QullamaggieStrategy()
pf = strategy.run(ohlcv['close'], ohlcv['high'], ohlcv['low'])
print(pf.stats())
```

3. **Generate tearsheet**:
```python
from src.performance.tearsheet import generate_tearsheet

generate_tearsheet(pf, benchmark='GDX', output_file='qullamaggie_tearsheet.pdf')
```

## 📁 Files

- **strategy.py**: Main strategy implementation
- **config.yaml**: Strategy parameters
- **backtest_hex.py**: Hex.tech notebook code
- **optimization.py**: Parameter optimization script
- **docs/system_explanation.md**: Plain English system description
- **docs/tradingview_script.txt**: Original TradingView Pine Script
- **results/**: Backtest results (gitignored)

## 🔧 Customization

### Adjusting Parameters

Edit `config.yaml` or pass parameters directly:

```python
strategy = QullamaggieStrategy(
    trend_sma_period=50,
    breakout_period=5,
    trailing_sma_period=20  # Use 20 SMA instead of 10
)
```

### Testing Different Universes

```python
# Test on specific symbols
symbols = ['AEM', 'NEM', 'FNV', 'WPM', 'KGC']
df_filtered = df[df['Symbol'].isin(symbols)]
ohlcv = create_ohlcv_dict(df_filtered)
```

### Date Range Testing

```python
# Test recent period only
df_recent = df[df['Date'] >= '2015-01-01']
ohlcv = create_ohlcv_dict(df_recent)
```

## 🧪 Optimization

Run parameter optimization:

```python
from strategies.qullamaggie.optimization import optimize_parameters

results = optimize_parameters(
    ohlcv,
    breakout_periods=[3, 5, 7, 10],
    trailing_sma_periods=[10, 20, 30, 50]
)
```

See [optimization.py](optimization.py) for details.

## 📊 Performance Analysis

### Generate Comprehensive Report

```python
from src.performance.tearsheet import generate_comprehensive_tearsheet

generate_comprehensive_tearsheet(
    pf,
    benchmark_symbol='GDX',
    output_file='results/qullamaggie_full_report.pdf'
)
```

### Compare to Benchmarks

```python
# Load benchmark data
gdx_prices = ohlcv['close']['GDX']
gdxj_prices = ohlcv['close']['GDXJ']

# Compare performance
from src.performance.metrics import compare_to_benchmark

comparison = compare_to_benchmark(pf, gdx_prices)
print(comparison)
```

## 🎓 Learning Resources

- [System Explanation](docs/system_explanation.md) - How the system works
- [VectorBT Data Preparation](../../VectorBT_Knowledge/data/01_data_preparation.md)
- [Signal Generation Guide](../../VectorBT_Knowledge/signals/01_signal_generation.md)
- [Performance Analysis](../../VectorBT_Knowledge/performance/01_performance_analysis.md)

## 🐛 Troubleshooting

### Common Issues

**Issue**: "No trades generated"  
**Solution**: Check that trend filter isn't too restrictive. Try `trend_filter_enabled=false` for testing.

**Issue**: "Memory error with full dataset"  
**Solution**: Filter to recent years first: `df[df['Date'] >= '2015-01-01']`

**Issue**: "Different results than TradingView"  
**Solution**: TradingView uses intraday data for entries. Daily data is an approximation.

## 📝 Notes

- **Intraday vs Daily**: Original system uses 1H/30min charts for breakout entries. This implementation uses daily data as a proxy.
- **Survivorship Bias**: Data is survivorship-bias-free (includes delisted stocks).
- **Transaction Costs**: Default 0.1% fees + 0.1% slippage. Adjust based on your broker.

## 🔗 References

- [Original TradingView Script](https://www.tradingview.com/script/cDCAPrd1-Qullamaggie-Breakout/)
- [Qullamaggie Twitter](https://twitter.com/qullamaggie)
- [VectorBT Documentation](https://vectorbt.dev)

## 📧 Questions?

Open an issue or contact: ben@obsidianquantitative.com

---

**Last Updated**: January 26, 2026  
**Status**: Ready for backtesting
