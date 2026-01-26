# GoldenOpp Data Transformation for VectorBT

## Current Data Structure

**GoldenOpp.GDX_GLD_Mining_Stocks_Prices** (Normalized format):
```
Symbol      VARCHAR      Stock ticker
Date        TIMESTAMP    Trading date  
Company_Name VARCHAR     Full company name
Open        DOUBLE       Opening price
High        DOUBLE       Highest price
Low         DOUBLE       Lowest price
Close       DOUBLE       Closing price
Adj_Close   DOUBLE       Adjusted close
Volume      BIGINT       Trading volume
Sector      VARCHAR      Industry sector
Data_Source VARCHAR      Source identifier
```

**Total**: 368,281 rows × 59 symbols × 53 years (1972-2025)

## VectorBT Required Format

### Option 1: Wide Format (Recommended for Multi-Symbol)

**Structure**: Each OHLCV component in separate DataFrame with DateTime index and symbols as columns

```python
# Close prices DataFrame
                 AEM    AG   AGI   ARMN   ASM    AU  ...  WPM
Date                                                  
1972-06-01      NaN   NaN   NaN    NaN   NaN   NaN  ...  NaN
1980-03-17    12.50   NaN   NaN    NaN   NaN   NaN  ...  NaN
...             ...   ...   ...    ...   ...   ...  ...  ...
2025-12-15    85.23  12.4  3.45   8.90  15.2  25.6  ... 62.3

# High prices DataFrame (same structure)
# Low prices DataFrame (same structure)
# Open prices DataFrame (same structure)
# Volume DataFrame (same structure)
```

### Option 2: Multi-Level Columns (Advanced)

```python
# Single DataFrame with hierarchical columns
                 AEM                    AG                    
               Open  High   Low Close Open  High   Low Close ...
Date                                                           
1972-06-01      NaN   NaN   NaN   NaN  NaN   NaN   NaN   NaN
...
```

## Transformation SQL Query

```sql
-- Extract data from GoldenOpp for VectorBT
SELECT 
    Date,
    Symbol,
    Open,
    High,
    Low,
    Close,
    Adj_Close,
    Volume
FROM GoldenOpp.GDX_GLD_Mining_Stocks_Prices
WHERE Symbol IN (
    -- 56 stocks
    'AEM', 'AG', 'AGI', 'ARMN', 'ASM', 'AU', 'B', 'BGL', 'BTG', 'BVN',
    'CDE', 'CGAU', 'CMCL', 'CTGO', 'DC', 'DRD', 'EGO', 'EQX', 'EXK', 'FNV',
    'FSM', 'GFI', 'GLDG', 'GROY', 'HL', 'HMY', 'IAG', 'IAUX', 'IDR', 'KGC',
    'MTA', 'MUX', 'NEM', 'NG', 'NGD', 'OR', 'ORLA', 'PAAS', 'PPTA', 'RGLD',
    'SA', 'SKE', 'SSRM', 'SVM', 'TFPM', 'VZLA', 'WPM',
    -- 9 international symbols
    'NFG CN', 'ALK AU', 'EMR AU', 'PNR AU', 'PRU AU', 'RSG AU', 
    'ASM AU', 'TXG CN', 'AAUC CN',
    -- 4 ETFs
    'GLD', 'SLV', 'GDX', 'GDXJ'
)
ORDER BY Date, Symbol;
```

## Python Transformation Code

```python
import duckdb
import pandas as pd
import vectorbt as vbt

# Connect to MotherDuck
token = "your_motherduck_token"
conn = duckdb.connect(f'md:?motherduck_token={token}')

# Load data from GoldenOpp
query = """
SELECT Date, Symbol, Open, High, Low, Close, Adj_Close, Volume
FROM GoldenOpp.GDX_GLD_Mining_Stocks_Prices
ORDER BY Date, Symbol
"""
df = conn.execute(query).df()

# Convert Date to datetime and set as index
df['Date'] = pd.to_datetime(df['Date'])

# Pivot to wide format for each OHLCV component
close_prices = df.pivot(index='Date', columns='Symbol', values='Close')
high_prices = df.pivot(index='Date', columns='Symbol', values='High')
low_prices = df.pivot(index='Date', columns='Symbol', values='Low')
open_prices = df.pivot(index='Date', columns='Symbol', values='Open')
adj_close_prices = df.pivot(index='Date', columns='Symbol', values='Adj_Close')
volume = df.pivot(index='Date', columns='Symbol', values='Volume')

# Handle missing data
# Option 1: Forward fill (use last known price)
close_prices = close_prices.ffill()

# Option 2: Drop symbols with too much missing data
min_data_points = 252  # At least 1 year of data
close_prices = close_prices.dropna(thresh=min_data_points, axis=1)

# Option 3: Drop dates where too many symbols are missing
close_prices = close_prices.dropna(thresh=len(close_prices.columns)*0.5, axis=0)

# Verify structure
print(f"Close prices shape: {close_prices.shape}")
print(f"Date range: {close_prices.index.min()} to {close_prices.index.max()}")
print(f"Symbols: {close_prices.columns.tolist()}")

# Save to CSV for Hex.tech (optional)
close_prices.to_csv('close_prices.csv')
high_prices.to_csv('high_prices.csv')
low_prices.to_csv('low_prices.csv')
open_prices.to_csv('open_prices.csv')
volume.to_csv('volume.csv')
```

## Using OHLCV Accessor in VectorBT

```python
# Option 1: Use separate DataFrames
# Calculate indicators on close prices
fast_ma = vbt.MA.run(close_prices, window=10)
slow_ma = vbt.MA.run(close_prices, window=50)

# For breakout detection, need high prices
breakout_high = high_prices.rolling(5).max()
entries = close_prices > breakout_high.shift(1)

# For stop loss, need low prices
breakout_low = low_prices.rolling(5).min()
exits = close_prices < breakout_low.shift(1)

# Run backtest
pf = vbt.Portfolio.from_signals(
    close_prices,
    entries,
    exits,
    init_cash=100000,
    fees=0.001  # 0.1% commission
)

# Option 2: Create OHLCV DataFrame with multi-level columns
ohlcv = pd.concat({
    'Open': open_prices,
    'High': high_prices,
    'Low': low_prices,
    'Close': close_prices,
    'Volume': volume
}, axis=1)

# Reorder to (Symbol, OHLCV) format
ohlcv = ohlcv.swaplevel(axis=1).sort_index(axis=1)

# Use OHLCV accessor
ohlcv_acc = ohlcv.vbt.ohlcv(freq='D')

# Access individual components
close = ohlcv_acc.close
high = ohlcv_acc.high
low = ohlcv_acc.low
```

## Memory Considerations

**Data size estimation**:
- 368,281 rows in normalized format
- After pivot: ~13,000 dates × 59 symbols = ~767,000 cells per OHLCV component
- 5 components (OHLCV + Adj_Close) × 767,000 × 8 bytes = ~30 MB
- With indicators and signals: ~100-200 MB in memory

**Optimization strategies**:
1. **Filter date range**: Test on recent years first (e.g., 2010-2025)
2. **Reduce symbol count**: Start with liquid stocks only
3. **Use Adj_Close only**: Skip Open/High/Low if not needed for strategy
4. **Chunked processing**: Process symbols in batches if memory constrained

## Handling International Symbols

**Challenge**: Symbols like "NFG CN", "ALK AU" contain spaces and suffixes

**Solutions**:
```python
# Option 1: Clean symbol names
df['Symbol'] = df['Symbol'].str.replace(' ', '_')  # NFG_CN, ALK_AU

# Option 2: Map to standard tickers
symbol_map = {
    'NFG CN': 'NFG_CN',
    'ALK AU': 'ALK_AU',
    # ... etc
}
df['Symbol'] = df['Symbol'].map(symbol_map).fillna(df['Symbol'])

# Option 3: Filter to US-only symbols (if international data problematic)
us_symbols = df[~df['Symbol'].str.contains(' ')]['Symbol'].unique()
```

## Handling Different Trading Calendars

**Issue**: Stocks trade Mon-Fri, but data may have gaps

**VectorBT handling**:
```python
# Option 1: Forward fill missing dates
close_prices = close_prices.asfreq('D').ffill()

# Option 2: Use business days only
close_prices = close_prices.asfreq('B')  # Business day frequency

# Option 3: Let VectorBT handle it (automatic alignment)
# VectorBT aligns data automatically when running backtests
```

## Recommended Approach for Qullamaggie System

**Step 1**: Load data with date filter (start with recent 10 years)
```python
query = """
SELECT Date, Symbol, Open, High, Low, Close, Volume
FROM GoldenOpp.GDX_GLD_Mining_Stocks_Prices
WHERE Date >= '2015-01-01'
ORDER BY Date, Symbol
"""
```

**Step 2**: Pivot to wide format (separate DataFrames for OHLC)

**Step 3**: Calculate indicators
- Daily 10, 20, 50 SMA on close prices
- 5-bar high/low on intraday timeframe (simulate with daily for now)

**Step 4**: Generate signals
- Entry: Close > 5-bar high AND Close > 50 SMA
- Exit: Close < 10 or 20 SMA (trailing stop)

**Step 5**: Run vectorized backtest across all symbols simultaneously

**Step 6**: Analyze results per symbol and aggregate portfolio performance

This approach leverages VectorBT's vectorization for maximum speed while maintaining the Qullamaggie system logic.
