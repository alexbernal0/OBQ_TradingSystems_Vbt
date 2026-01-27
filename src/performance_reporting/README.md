# Performance Reporting

This folder contains all performance reporting and tearsheet generation modules for backtesting strategies.

## Overview

The performance reporting system provides comprehensive "better than QuantStats" tearsheets with 100+ metrics, benchmark comparisons, crisis analysis, and professional visualizations.

## Files

### Core Modules

**`qullamaggie_tearsheet.py`**
- Comprehensive tearsheet module for Qullamaggie strategy
- 100+ performance metrics including Ed Seykota's Lake Ratio
- Benchmark comparison (strategy vs buy & hold)
- Crisis period analysis (8 major market events)
- Modular design for easy Hex.tech integration

**`Master2025_Comprehensive_Functions.py`**
- Original comprehensive metrics calculation functions
- 60+ performance metrics
- Statistical analysis functions
- Trade analysis utilities

**`Master2025ComprehensiveTearsheetFunctions.py`**
- Original tearsheet generation functions
- Visualization templates
- Report formatting utilities

## Usage in Hex.tech

### 1. Upload Module

Upload `qullamaggie_tearsheet.py` to your Hex.tech Files section.

### 2. Import and Run

```python
from qullamaggie_tearsheet import run_comprehensive_tearsheet

results = run_comprehensive_tearsheet(
    df_all_data=df_all_data,
    symbol='GLD',
    trend_sma=50,
    breakout_period=5,
    trailing_sma=10,
    initial_capital=100000
)
```

### 3. Access Results

```python
# Portfolio objects
pf_strategy = results['pf_strategy']
pf_benchmark = results['pf_benchmark']

# Metrics dictionaries
metrics_strategy = results['metrics_strategy']
metrics_benchmark = results['metrics_benchmark']

# Time series data
equity_strategy = results['equity_strategy']
returns_strategy = results['returns_strategy']
```

## Metrics Included

### Returns Metrics (10)
- Cumulative Return, CAGR, Annualized Return
- MTD, 3M, 6M, YTD, 1Y, 3Y, 5Y, 10Y returns

### Risk Metrics (15)
- Volatility (Annual, Downside)
- Max Drawdown, Avg Drawdown, DD Duration
- VaR, CVaR, Ulcer Index
- Lake Ratio (Ed Seykota)

### Risk-Adjusted Returns (10)
- Sharpe, Sortino, Calmar, Omega Ratios
- Probabilistic Sharpe Ratio
- Smart Sharpe, Smart Sortino (autocorrelation-adjusted)

### Trade Metrics (12)
- Total/Winning/Losing Trades
- Win Rate, Profit Factor
- Avg Win/Loss, Largest Win/Loss
- SystemScore: (CAGR × Win Rate) / |Max DD|

### Statistical Metrics (8)
- Skewness, Kurtosis
- Best/Worst Day/Month/Year
- Outlier Win/Loss Ratios

### Period Analysis (10)
- Win Days/Months/Quarters/Years %
- Avg Up/Down Month
- Time in Market %

### Advanced Metrics (10)
- Gain/Pain Ratio (Daily & Monthly)
- Common Sense Ratio
- CPC Index
- Payoff Ratio, Recovery Factor

**Total: 100+ Comprehensive Metrics**

## Visualizations

The tearsheet generates professional Plotly visualizations:

1. **Equity Curve + Drawdown**
   - Strategy equity with buy signals
   - Drawdown underwater plot (1/5 height)

2. **Benchmark Comparison (2x2 Grid)**
   - Cumulative Returns
   - Log Scale Returns
   - Volatility Matched
   - Excess Returns (Cumulative Alpha)

3. **Monthly Returns Heatmap**
   - Color-coded monthly returns
   - YTD column
   - Bold, readable text

4. **Annual Performance Table**
   - Strategy vs Benchmark by year
   - Excess returns
   - Color-coded (red for negative)

5. **Rolling Metrics (2x2 Grids)**
   - Rolling Sharpe & Sortino
   - Rolling Volatility & Max DD
   - Distribution & Quantiles
   - Active Returns & Best/Worst

6. **Crisis Periods Analysis**
   - 8 major market events
   - Normalized equity curves
   - Performance comparison table

## Customization

### Adding New Metrics

To add a new metric to the tearsheet:

1. Add calculation to `calculate_all_metrics()` function
2. Add display to `print_metrics_report()` function
3. Update this README with metric description

### Adding New Visualizations

Create visualization functions following the Plotly pattern:

```python
def create_custom_viz(data, params):
    fig = go.Figure()
    # Add traces
    fig.update_layout(...)
    return fig
```

## Best Practices

1. **Always test locally** before deploying to Hex.tech
2. **Use modular design** - separate calculation from visualization
3. **Document all metrics** - include formulas and interpretations
4. **Validate data** - check for NaN, inf, and edge cases
5. **Optimize performance** - vectorize calculations where possible

## Dependencies

```python
pandas>=2.0.0
numpy>=1.24.0
vectorbt>=0.26.0
plotly>=5.17.0
scipy>=1.10.0
```

## Future Enhancements

- [ ] PDF export functionality
- [ ] Multi-strategy comparison
- [ ] Interactive parameter optimization
- [ ] Real-time performance tracking
- [ ] Email report delivery
- [ ] Custom metric builder UI

## References

- **QuantStats**: https://github.com/ranaroussi/quantstats
- **VectorBT**: https://vectorbt.dev/
- **Lake Ratio**: https://www.seykota.com/tribe/risk/index.htm

## Support

For issues or questions:
1. Check the main repo README
2. Review VectorBT Knowledge Base
3. Consult strategy-specific documentation

---

**Version**: 1.0.0  
**Last Updated**: 2026-01-27  
**Maintainer**: OBQ Trading Systems
