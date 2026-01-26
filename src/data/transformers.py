"""
Data transformation utilities for VectorBT format conversion.

This module provides functions to transform data from long (normalized) format
to wide format required by VectorBT.
"""

import pandas as pd
from typing import Optional, List, Dict


def pivot_to_wide_format(
    df: pd.DataFrame,
    value_column: str,
    date_column: str = 'Date',
    symbol_column: str = 'Symbol',
    fill_method: Optional[str] = 'ffill'
) -> pd.DataFrame:
    """
    Pivot long-format data to wide format for VectorBT.
    
    Args:
        df: Long-format DataFrame
        value_column: Column to pivot (e.g., 'Close', 'High', 'Low')
        date_column: Date column name
        symbol_column: Symbol column name
        fill_method: Method to fill missing values ('ffill', 'bfill', None)
    
    Returns:
        Wide-format DataFrame with DatetimeIndex and symbols as columns
    
    Example:
        >>> close_prices = pivot_to_wide_format(df, 'Close')
        >>> print(close_prices.shape)
        (13000, 59)
    """
    # Pivot the data
    wide_df = df.pivot(index=date_column, columns=symbol_column, values=value_column)
    
    # Fill missing values if requested
    if fill_method == 'ffill':
        wide_df = wide_df.ffill()
    elif fill_method == 'bfill':
        wide_df = wide_df.bfill()
    
    return wide_df


def create_ohlcv_dict(
    df: pd.DataFrame,
    date_column: str = 'Date',
    symbol_column: str = 'Symbol',
    fill_method: Optional[str] = 'ffill'
) -> Dict[str, pd.DataFrame]:
    """
    Create dictionary of OHLCV DataFrames in wide format.
    
    Args:
        df: Long-format DataFrame with OHLCV columns
        date_column: Date column name
        symbol_column: Symbol column name
        fill_method: Method to fill missing values
    
    Returns:
        Dictionary with keys: 'open', 'high', 'low', 'close', 'volume'
    
    Example:
        >>> ohlcv = create_ohlcv_dict(df)
        >>> close_prices = ohlcv['close']
    """
    ohlcv_dict = {}
    
    for col in ['Open', 'High', 'Low', 'Close', 'Volume']:
        if col in df.columns:
            key = col.lower()
            ohlcv_dict[key] = pivot_to_wide_format(
                df, col, date_column, symbol_column, fill_method
            )
    
    # Special handling for volume (fill with 0 instead of forward fill)
    if 'volume' in ohlcv_dict:
        ohlcv_dict['volume'] = ohlcv_dict['volume'].fillna(0)
    
    return ohlcv_dict


def filter_by_data_quality(
    df: pd.DataFrame,
    min_data_points: int = 252,
    max_missing_pct: float = 0.5
) -> pd.DataFrame:
    """
    Filter symbols based on data quality criteria.
    
    Args:
        df: Wide-format DataFrame
        min_data_points: Minimum number of non-null data points required
        max_missing_pct: Maximum percentage of missing data allowed
    
    Returns:
        Filtered DataFrame with only high-quality symbols
    
    Example:
        >>> clean_data = filter_by_data_quality(close_prices, min_data_points=252)
    """
    # Count non-null values per symbol
    non_null_counts = df.count()
    
    # Calculate missing percentage
    total_rows = len(df)
    missing_pct = 1 - (non_null_counts / total_rows)
    
    # Filter symbols
    valid_symbols = non_null_counts[
        (non_null_counts >= min_data_points) & 
        (missing_pct <= max_missing_pct)
    ].index
    
    return df[valid_symbols]


def align_trading_calendars(
    *dfs: pd.DataFrame,
    method: str = 'inner'
) -> List[pd.DataFrame]:
    """
    Align multiple DataFrames to the same trading calendar.
    
    Args:
        *dfs: Variable number of DataFrames to align
        method: Alignment method ('inner', 'outer', 'left', 'right')
    
    Returns:
        List of aligned DataFrames
    
    Example:
        >>> close_aligned, volume_aligned = align_trading_calendars(
        ...     close_prices, volume, method='inner'
        ... )
    """
    if len(dfs) == 0:
        return []
    
    # Get common index
    if method == 'inner':
        common_index = dfs[0].index
        for df in dfs[1:]:
            common_index = common_index.intersection(df.index)
    elif method == 'outer':
        common_index = dfs[0].index
        for df in dfs[1:]:
            common_index = common_index.union(df.index)
    else:
        raise ValueError(f"Unknown method: {method}")
    
    # Reindex all DataFrames
    aligned = [df.reindex(common_index) for df in dfs]
    
    return aligned
