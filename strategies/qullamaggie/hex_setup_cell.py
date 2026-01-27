# ============================================================================
# CELL 1: Install Libraries & Connect to MotherDuck
# ============================================================================
# Run this cell FIRST before any other code
# ============================================================================

# Install required libraries
!pip install -q vectorbt pandas numpy plotly scipy statsmodels matplotlib seaborn

print("=" * 80)
print("SETUP: Installing Libraries & Connecting to MotherDuck")
print("=" * 80)

# Import libraries
import pandas as pd
import numpy as np
import vectorbt as vbt
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import scipy.stats as stats
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

print(f"\n✅ Libraries installed successfully!")
print(f"\n📚 Library Versions:")
print(f"   • VectorBT: {vbt.__version__}")
print(f"   • Pandas: {pd.__version__}")
print(f"   • NumPy: {np.__version__}")
import plotly
print(f"   • Plotly: {plotly.__version__}")

# ============================================================================
# Connect to MotherDuck with Token
# ============================================================================

print(f"\n🦆 Connecting to MotherDuck...")
print("=" * 80)

import duckdb

# MotherDuck token (paste your token here)
MOTHERDUCK_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJlbWFpbCI6ImJlbkBvYnNpZGlhbnF1YW50aXRhdGl2ZS5jb20iLCJtZFJlZ2lvbiI6ImF3cy11cy1lYXN0LTEiLCJzZXNzaW9uIjoiYmVuLm9ic2lkaWFucXVhbnRpdGF0aXZlLmNvbSIsInBhdCI6IkFUZ3ZBQVZoN3VpZVAtWGVDNnIxc0RVbXVyRzlsVG5TRkMyaTByQXFpb3ciLCJ1c2VySWQiOiJlZGZhZTYyMi0yMTBlLTRiYmItODU3Mi1kZjBjZTA2MjNkOWIiLCJpc3MiOiJtZF9wYXQiLCJyZWFkT25seSI6ZmFsc2UsInRva2VuVHlwZSI6InJlYWRfd3JpdGUiLCJpYXQiOjE3NjU5MTAwMzl9.c7_uLy07jXSP5NhczE818Zf-EhGCdyIFv1wJtfIoMUs"

# Connect to MotherDuck with token
conn = duckdb.connect(f'md:?motherduck_token={MOTHERDUCK_TOKEN}')

print(f"✅ Connected to MotherDuck successfully!")

# Table name
table_name = "GoldenOpp.GDX_GLD_Mining_Stocks_Prices"

print(f"📊 Loading data from: {table_name}")

# Load the data
query = f"""
SELECT 
    Date,
    Symbol,
    Open,
    High,
    Low,
    Close,
    Adj_Close,
    Volume,
    Company_Name,
    Sector,
    Data_Source
FROM {table_name}
ORDER BY Date, Symbol
"""

df_raw = conn.execute(query).df()

# Convert date column to datetime
df_raw['Date'] = pd.to_datetime(df_raw['Date'])

print(f"\n✅ Data loaded successfully!")
print(f"   • Total rows: {len(df_raw):,}")
print(f"   • Unique symbols: {df_raw['Symbol'].nunique()}")
print(f"   • Date range: {df_raw['Date'].min().date()} to {df_raw['Date'].max().date()}")
print(f"   • Years of data: {(df_raw['Date'].max() - df_raw['Date'].min()).days / 365.25:.1f}")

# Display symbol list
symbols = sorted(df_raw['Symbol'].unique())
print(f"\n📈 Available Symbols ({len(symbols)}):")
print(f"   {', '.join(symbols)}")

# Display symbol summary
print(f"\n📊 Symbol Summary (Top 10 by data points):")
symbol_summary = df_raw.groupby('Symbol').agg({
    'Date': ['min', 'max', 'count'],
    'Close': ['mean', 'std']
}).round(2)
symbol_summary.columns = ['Start_Date', 'End_Date', 'Data_Points', 'Avg_Price', 'Price_StdDev']
symbol_summary = symbol_summary.sort_values('Data_Points', ascending=False)
print(symbol_summary.head(10))

# Display sample data
print(f"\n📋 Sample Data (first 5 rows):")
print(df_raw.head())

print("\n" + "=" * 80)
print("✅ SETUP COMPLETE - MotherDuck Connected & Data Loaded!")
print("=" * 80)

# ============================================================================
# Helper Functions for Data Transformation
# ============================================================================

def pivot_to_wide_format(df, value_column, date_column='Date', symbol_column='Symbol'):
    """
    Convert long format data to wide format for VectorBT.
    
    Args:
        df: DataFrame in long format
        value_column: Column to pivot (e.g., 'Close', 'High', 'Low')
        date_column: Date column name
        symbol_column: Symbol column name
    
    Returns:
        Wide format DataFrame with DatetimeIndex and symbols as columns
    """
    wide_df = df.pivot(index=date_column, columns=symbol_column, values=value_column)
    return wide_df.ffill()  # Forward fill missing values


def create_ohlcv_dict(df):
    """
    Create dictionary of OHLCV DataFrames in wide format.
    
    Args:
        df: Long format DataFrame with OHLCV columns
    
    Returns:
        Dictionary with keys: 'open', 'high', 'low', 'close', 'adj_close', 'volume'
    """
    ohlcv = {}
    
    for col in ['Open', 'High', 'Low', 'Close', 'Adj_Close', 'Volume']:
        if col in df.columns:
            key = col.lower()
            ohlcv[key] = pivot_to_wide_format(df, col)
    
    # Fill volume with 0 instead of forward fill
    if 'volume' in ohlcv:
        ohlcv['volume'] = ohlcv['volume'].fillna(0)
    
    return ohlcv


def filter_symbols(df, symbols):
    """
    Filter DataFrame to specific symbols.
    
    Args:
        df: Long format DataFrame
        symbols: List of symbols to keep (or single symbol as string)
    
    Returns:
        Filtered DataFrame
    """
    if isinstance(symbols, str):
        symbols = [symbols]
    return df[df['Symbol'].isin(symbols)].copy()


def filter_date_range(df, start_date=None, end_date=None):
    """
    Filter DataFrame to specific date range.
    
    Args:
        df: Long format DataFrame
        start_date: Start date (YYYY-MM-DD format or None)
        end_date: End date (YYYY-MM-DD format or None)
    
    Returns:
        Filtered DataFrame
    """
    df_filtered = df.copy()
    
    if start_date:
        df_filtered = df_filtered[df_filtered['Date'] >= pd.to_datetime(start_date)]
    if end_date:
        df_filtered = df_filtered[df_filtered['Date'] <= pd.to_datetime(end_date)]
    
    return df_filtered


print("\n📦 Helper functions loaded:")
print("   • pivot_to_wide_format() - Convert long to wide format")
print("   • create_ohlcv_dict() - Create OHLCV dictionary for VectorBT")
print("   • filter_symbols() - Filter to specific symbols")
print("   • filter_date_range() - Filter to date range")

# ============================================================================
# Store data in global scope for use in strategy cells
# ============================================================================

# Make raw data available globally
df_all_data = df_raw.copy()

print("\n✅ Data stored in 'df_all_data' variable")
print(f"   Shape: {df_all_data.shape}")
print(f"   Memory usage: {df_all_data.memory_usage(deep=True).sum() / 1024**2:.2f} MB")
print(f"\n🎯 Ready to run strategy backtests!")
print("=" * 80)
