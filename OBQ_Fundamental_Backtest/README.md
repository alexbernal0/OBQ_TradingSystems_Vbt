# OBQ Fundamental Backtest

Production-grade, survivorship-bias-free, point-in-time accurate factor backtesting system.

## Overview

This module backtests the five OBQ factor scores (Growth, Value, Quality, Momentum, Financial Strength)
against the Russell 1000 universe using local DuckDB as the sole data source.

## Key Properties

- **Zero survivorship bias** -- uses interval-based index_membership joins
- **Zero look-ahead bias** -- all fundamentals gated by filing_date <= rebal_date
- **Lightning fast** -- DuckDB-native SQL, pre-scored factors, no Python row loops
- **Obsidian Backtest Score** -- proprietary 5-star rating (5 dimensions, weighted composite)
- **Delisted stock handling** -- returns computed for all stocks including bankruptcies

## Status

PLANNED -- blueprint complete, implementation pending user sign-off.
See BUILD_BLUEPRINT.md for full specification.

## Data Sources

- Universe: index_membership table (local obq_ai.duckdb)
- Prices: equity_ts table (local obq_ai.duckdb)
- Fundamentals: filings_pit table (local fdb.duckdb, ATTACHed)

## Build Phases

1. Schema and data validation
2. Factor score replication (5 scores from JCN documentation)
3. Backtest engine core
4. Testing and bias validation
5. Results and UI integration
6. Auto-sync hook
7. Documentation and examples

## References

- BUILD_BLUEPRINT.md -- full architecture specification
- JCN Score Documentation PDFs -- factor score methodology
- OBQ_AI_BUILD_GUIDE_v5.md -- parent application architecture
