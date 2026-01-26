# Data Preparation for VectorBT

## Overview

VectorBT requires data in **wide format** where each symbol is a column and the index is a DateTime series. This differs from the normalized (long) format commonly used in databases.

## Data Format Requirements

### Long Format (Database Storage)

```python
   Date       Symbol  Open   High   Low    Close  Volume
0  2025-01-01 AAPL    150.0  152.0  149.0  151.0  1000000
1  2025-01-01 MSFT    300.0  305.0  299.0  303.0  500000
2  2025-01-02 AAPL    151.0  153.0  150.0  152.0  1100000
3  2025-01-02 MSFT    303.0  307.0  302.0  305.0  550000
```

### Wide Format (VectorBT Required)

```python
            AAPL   MSFT
Date                   
2025-01-01  151.0  303.0
2025-01-02  152.0  305.0
```

## Transformation Process

### Using Repository Helpers

```python
from src.data.loaders import load_from_motherduck
from src.data.transformers import pivot_to_wide_format

# Load data from MotherDuck
df_long = load_from_motherduck("GoldenOpp.GDX_GLD_Mining_Stocks_Prices")

# Transform to wide format
close_prices = pivot_to_wide_format(df_long, 'Close')
high_prices = pivot_to_wide_format(df_long, 'High')
low_prices = pivot_to_wide_format(df_long, 'Low')
```

### Manual Transformation

```python
import pandas as pd

# Pivot each OHLCV component separately
close_prices = df_long.pivot(index='Date', columns='Symbol', values='Close')
high_prices = df_long.pivot(index='Date', columns='Symbol', values='High')
low_prices = df_long.pivot(index='Date', columns='Symbol', values='Low')
open_prices = df_long.pivot(index='Date', columns='Symbol', values='Open')
volume = df_long.pivot(index='Date', columns='Symbol', values='Volume')
```

## Handling Missing Data

### Forward Fill (Recommended for Prices)

```python
close_prices = close_prices.ffill()  # Use last known price
```

### Fill with Zero (Recommended for Volume)

```python
volume = volume.fillna(0)  # No volume = 0
```

### Drop Missing Data

```python
# Drop symbols with too much missing data
min_data_points = 252  # At least 1 year
close_prices = close_prices.dropna(thresh=min_data_points, axis=1)
```

## Data Quality Checks

### Using Repository Helpers

```python
from src.data.loaders import validate_ohlcv_data
from src.data.transformers import filter_by_data_quality

# Validate data integrity
validate_ohlcv_data(df_long)

# Filter low-quality symbols
close_prices = filter_by_data_quality(
    close_prices,
    min_data_points=252,
    max_missing_pct=0.5
)
```

### Manual Validation

```python
# Check for negative prices
assert (close_prices >= 0).all().all(), "Negative prices found"

# Check for inf/nan after filling
assert not close_prices.isin([np.inf, -np.inf]).any().any(), "Inf values found"

# Verify High >= Low
assert (high_prices >= low_prices).all().all(), "High < Low detected"
```

## Memory Optimization

### For Large Datasets

```python
# Use float32 instead of float64 to save memory
close_prices = close_prices.astype('float32')

# Or work with date ranges
close_prices_recent = close_prices.loc['2020-01-01':]
```

### Chunked Processing

```python
# Process symbols in batches
symbols = close_prices.columns.tolist()
batch_size = 20

for i in range(0, len(symbols), batch_size):
    batch_symbols = symbols[i:i+batch_size]
    batch_data = close_prices[batch_symbols]
    # Process batch...
```

## Best Practices

1. **Always validate data** before backtesting
2. **Use adjusted close prices** for accurate results
3. **Forward fill price data** to handle non-trading days
4. **Fill volume with zero** instead of forward fill
5. **Filter low-quality symbols** before analysis
6. **Use appropriate date ranges** for testing
7. **Monitor memory usage** with large datasets

## Common Pitfalls

❌ **Don't**: Use raw close prices (ignores splits/dividends)  
✅ **Do**: Use adjusted close prices

❌ **Don't**: Drop all rows with any missing data  
✅ **Do**: Forward fill or filter by data quality

❌ **Don't**: Mix different trading calendars without alignment  
✅ **Do**: Use `align_trading_calendars()` helper

❌ **Don't**: Load entire 50-year dataset if testing recent strategy  
✅ **Do**: Filter to relevant date range first

## Next Steps

- [OHLCV Handling](02_ohlcv_handling.md) - Working with price data
- [Missing Data Strategies](03_missing_data.md) - Advanced handling techniques
- [Hex Data Integration](04_hex_data_integration.md) - Hex.tech workflows
