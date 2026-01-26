"""
Data loading utilities for various sources.

This module provides functions to load data from MotherDuck, CSV files,
and other sources, preparing it for VectorBT backtesting.
"""

import pandas as pd
import duckdb
from typing import Optional, List
import os


def load_from_motherduck(
    table_name: str,
    motherduck_token: Optional[str] = None,
    date_column: str = 'Date',
    symbols: Optional[List[str]] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
) -> pd.DataFrame:
    """
    Load data from MotherDuck database.
    
    Args:
        table_name: Full table name (e.g., "GoldenOpp.GDX_GLD_Mining_Stocks_Prices")
        motherduck_token: MotherDuck authentication token (or use env var)
        date_column: Name of the date column
        symbols: List of symbols to filter (None = all symbols)
        start_date: Start date filter (YYYY-MM-DD format)
        end_date: End date filter (YYYY-MM-DD format)
    
    Returns:
        DataFrame with columns: Date, Symbol, Open, High, Low, Close, Volume, etc.
    
    Example:
        >>> df = load_from_motherduck("GoldenOpp.GDX_GLD_Mining_Stocks_Prices")
        >>> print(df.shape)
        (368281, 10)
    """
    # Get token from environment if not provided
    if motherduck_token is None:
        motherduck_token = os.getenv('MOTHERDUCK_TOKEN')
        if motherduck_token is None:
            raise ValueError("MotherDuck token must be provided or set in MOTHERDUCK_TOKEN env var")
    
    # Connect to MotherDuck
    conn = duckdb.connect(f'md:?motherduck_token={motherduck_token}')
    
    # Build query
    query = f"SELECT * FROM {table_name}"
    
    conditions = []
    if symbols:
        symbol_list = "', '".join(symbols)
        conditions.append(f"Symbol IN ('{symbol_list}')")
    if start_date:
        conditions.append(f"{date_column} >= '{start_date}'")
    if end_date:
        conditions.append(f"{date_column} <= '{end_date}'")
    
    if conditions:
        query += " WHERE " + " AND ".join(conditions)
    
    query += f" ORDER BY {date_column}, Symbol"
    
    # Execute and return
    df = conn.execute(query).df()
    df[date_column] = pd.to_datetime(df[date_column])
    
    conn.close()
    return df


def load_from_csv(
    file_path: str,
    date_column: str = 'Date',
    parse_dates: bool = True
) -> pd.DataFrame:
    """
    Load data from CSV file.
    
    Args:
        file_path: Path to CSV file
        date_column: Name of the date column
        parse_dates: Whether to parse dates
    
    Returns:
        DataFrame with parsed dates
    
    Example:
        >>> df = load_from_csv("data/sample/sample_ohlcv.csv")
    """
    df = pd.read_csv(file_path)
    if parse_dates and date_column in df.columns:
        df[date_column] = pd.to_datetime(df[date_column])
    return df


def validate_ohlcv_data(df: pd.DataFrame) -> bool:
    """
    Validate that DataFrame contains required OHLCV columns.
    
    Args:
        df: DataFrame to validate
    
    Returns:
        True if valid, raises ValueError otherwise
    
    Example:
        >>> validate_ohlcv_data(df)
        True
    """
    required_cols = ['Open', 'High', 'Low', 'Close', 'Volume']
    missing = [col for col in required_cols if col not in df.columns]
    
    if missing:
        raise ValueError(f"Missing required columns: {missing}")
    
    # Check for negative prices
    price_cols = ['Open', 'High', 'Low', 'Close']
    for col in price_cols:
        if (df[col] < 0).any():
            raise ValueError(f"Negative values found in {col}")
    
    # Check High >= Low
    if (df['High'] < df['Low']).any():
        raise ValueError("High prices less than Low prices detected")
    
    return True
