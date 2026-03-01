# OBQ Fundamental Backtester - Build Blueprint
## Version 1.0 | Obsidian Quantitative

Status: PLAN MODE - Blueprint only. No code built yet.
Last Updated: 2026-03-01
DB Paths: D:/OBQ_AI/obq_ai.duckdb + D:/OBQ_AI/obq_fundamentals.duckdb

---

## 1. System Overview

The OBQ Fundamental Backtester answers one question with zero tolerance for error:
  Does this fundamental factor, as known at the time, predict future stock returns?

Architecture:
  OBQ_AI App (PyWebView/Flask)
    -> OBQ Fundamental Backtester Engine (this system)
       -> obq_ai.duckdb: equity_ts (74M), ohlcv (102M), index_membership, securities (63K)
       -> obq_fundamentals.duckdb: filings_pit, factor_scores.*, backtest.*
---

## 2. Immutable Laws (Never Violate)

LAW 1 - ZERO SURVIVORSHIP BIAS
  Universe MUST include delisted, bankrupt, acquired stocks at every rebalance date.
  Dropping these inflates backtest CAGR by 1-3% artificially.

LAW 2 - ZERO LOOK-AHEAD BIAS
  Factor scores ONLY use data where filing_date <= rebalance_date.
  filing_date = SEC submission date (correct PIT gate).
  report_date/period_end = LOOK-AHEAD if used as gate.
  Example: Q3 ends Sep 30. 10-Q filed Nov 14. USE Nov 14.

LAW 3 - LOCAL DUCKDB ONLY
  No MotherDuck. No EODHD API. No external data during backtest runs.

LAW 4 - TOTAL-RETURN ADJUSTED PRICES
  Always equity_ts.close. Never unadjusted_close for returns.

LAW 5 - INTERVAL-BASED UNIVERSE JOINS
  Always: date_in <= rebal AND (date_out IS NULL OR date_out >= rebal)
  Never: YEAR(date_in) or status=active

LAW 6 - NO FAKE DATA, EVER

LAW 7 - DUCKDB-NATIVE HEAVY LIFTING
  All aggregations, joins, rankings in SQL. Python = orchestration only. No row loops.

Design Targets:
  - Lightning fast: Full 15-year Russell 1000 backtest in < 60 seconds
  - Free stack: duckdb, pandas, numpy - zero paid infrastructure
  - App-ready: Results flow directly into PyWebView/Flask UI

---

## 3. Data Architecture

Primary DB: D:/OBQ_AI/obq_ai.duckdb (19.5 GB)
  equity_ts    (symbol, date)         74M   Forward return computation
  ohlcv        (date, symbol)        102M   Cross-sectional screens
  index_membership (date_in, date_out) 20K+ Universe construction (intervals)
  securities   (symbol)              63K    Sector/GICS/equity filter
  weekly_equity_ts, weekly_ohlcv     16M each  Weekly screens and backtests

Fundamentals DB: D:/OBQ_AI/obq_fundamentals.duckdb (287 MB+)
  EXISTS:   universe.obq_master_universe (2938 rows)
  EXISTS:   fundamentals.filings_raw
  EXISTS:   fundamentals.filings_ttm
  TO BUILD: fundamentals.filings_pit
  TO BUILD: factor_scores.{growth, value, quality, momentum, financial_strength, composite}
  TO BUILD: backtest.{results, quintile_returns, run_log}

Cross-Database Access:
  conn = duckdb.connect(D:/OBQ_AI/obq_ai.duckdb)
  conn.execute(ATTACH D:/OBQ_AI/obq_fundamentals.duckdb AS fdb)

---

## 4. Survivorship-Bias-Free Universe Construction

Cardinal Rule: EVERY universe query MUST use interval join. No exceptions.

CORRECT Pattern (always use this):
  SELECT im.symbol, s.name, s.gics_l1 AS sector, im.date_in, im.date_out
  FROM index_membership im
  JOIN securities s ON s.symbol = im.symbol
  WHERE im.index_name = :index_name
    AND im.date_in    <= :rebalance_date
    AND (im.date_out IS NULL OR im.date_out >= :rebalance_date)
    AND s.is_equity = TRUE;

WRONG Patterns (NEVER use):
  WRONG: WHERE YEAR(im.date_in) <= YEAR(:rebalance_date)
  WRONG: WHERE s.status = active
  WRONG: WHERE u.is_currently_active = TRUE
  WRONG: WHERE forward_return IS NOT NULL  [drops bankruptcies = survivorship bias]

Delisted Stock Return Rules:
  Bankruptcy:   (last_price / entry_price) - 1, typically -80% to -100%
  Acquisition:  (acq_price / entry_price) - 1, often positive
  Delisted BEFORE rebalance: excluded by PIT universe (correct)
  Delisted AFTER rebalance:  MUST be included in return computation

---

## 5. Point-in-Time Factor Score Loading

THE critical distinction:
  report_date/period_end = quarter-end. NOT public yet. DO NOT USE AS GATE.
  filing_date = SEC submission (30-75 days after quarter end). USE THIS.

fundamentals.filings_pit Schema (TO BUILD):
  symbol, filing_date [THE PIT gate key], period_end, period_type,
  revenue, gross_profit, operating_income, ebitda, net_income, eps_diluted,
  total_assets, total_liabilities, total_equity,
  accounts_payable, cash_and_equivalents, long_term_debt,
  operating_cash_flow, capital_expenditures, free_cash_flow,
  shares_outstanding,
  TTM pre-aggregated: revenue_ttm, gross_profit_ttm, operating_income_ttm,
    ebitda_ttm, net_income_ttm, eps_diluted_ttm, free_cash_flow_ttm,
  invested_capital [= total_assets - accounts_payable - cash_and_equivalents],
  created_at, updated_at
  Index: CREATE INDEX idx_pit ON filings_pit(symbol, filing_date DESC)

PIT Lookup Pattern (MANDATORY - ROW_NUMBER approach):
  WITH latest_filing AS (
      SELECT f.*,
             ROW_NUMBER() OVER (PARTITION BY f.symbol ORDER BY f.filing_date DESC) AS rn
      FROM fdb.fundamentals.filings_pit f
      WHERE f.filing_date <= :rebalance_date  [THE PIT GATE]
        AND f.symbol IN (SELECT symbol FROM universe)
  ) SELECT * FROM latest_filing WHERE rn = 1;

Factor Score Table Schema (all 5 follow this pattern):
  symbol, score_date, filing_date (audit trail),
  component scores 0-100 percentile-ranked, growth_score (0-100),
  universe_name, percentile_rank, created_at, updated_at
  PRIMARY KEY (symbol, score_date, universe_name)

Auto-Sync Hook:
  def after_norgate_sync_hook():
      if latest_rebal > last_scored:
          for f in [growth, value, quality, momentum, financial_strength]:
              compute_factor_score(f, from_date=last_scored, to_date=latest_rebal)
          update_composite_score()

---

## 6. Forward Return Computation

### Principle
Forward returns are computed ON DEMAND from raw price data. They are NEVER pre-stored as
a fixed table — market prices change and delisted stocks must be included at their actual
last-traded price, not dropped.

### Return Periods
| Period | Approx Trading Days | Primary Use |
|--------|--------------------|-----------------------------|
| 1M     | 21                 | Short-term signal check     |
| 3M     | 63                 | Quarterly factor decay      |
| 6M     | 126                | Semi-annual rebalance       |
| 12M    | 252                | **PRIMARY backtest period** |
| 24M    | 504                | Long-horizon validation     |

### Canonical Return SQL (Delisted-Safe)


### Critical Rules
- NEVER use  — this silently drops delisted/bankrupt stocks
- Delisted stocks get their actual last-traded price as exit_price (is_early_exit = TRUE)
- is_early_exit flag is stored so performance attribution can separate full vs partial holds
- Use  (total-return adjusted), NEVER raw close
- equity_ts.close IS the adjusted close in OBQ schema — confirm column name before building

---

## 7. Quintile Construction

### Methodology
- Use SQL NTILE(5) -- percentage-based, adapts to any universe size
- NEVER use fixed count (e.g., top 50 stocks) -- distorts Q1-Q5 spread
- Q1 = HIGHEST score (best factor), Q5 = LOWEST score (worst factor)
- Minimum threshold: 30 stocks per quintile (skip rebal date if universe < 150)
- NULL-scored stocks: EXCLUDED from Q1-Q5 assignment, INCLUDED in benchmark return

### True Benchmark (Critical)
The benchmark is equal-weighted ALL index members regardless of score availability.
This includes NULL-scored stocks and delisted stocks that were members on rebal_date.
Benchmark = AVG(return_12m) across full universe, not just scored stocks.

### NTILE vs Fixed Count
| Approach | Universe=1000 | Universe=200 | Universe=80 |
|----------|--------------|-------------|------------|
| Fixed 50 per quintile | OK | only 40/quintile | only 16/quintile |
| NTILE(5) 20% | 200/quintile | 40/quintile | 16/quintile |
Fixed count silently produces non-standard quintiles when universe shrinks.
NTILE(5) always gives 20% slices regardless of universe size.

---

## 8. Performance Metrics

### Per-Run Aggregate Metrics
| Metric | Formula | Notes |
|--------|---------|-------|
| CAGR | (1 + total_return)^(1/years) - 1 | Geometric not arithmetic |
| Sharpe | mean(excess_returns) / std(excess_returns) * sqrt(252) | vs risk-free rate |
| Max Drawdown | min(cumret / cummax(cumret) - 1) | Full holding period |
| Win Rate | count(return > 0) / count(*) | Per quintile |
| Benchmark Spread | Q1_return - benchmark_return | Key alpha signal |
| Q1-Q5 Spread | Q1_return - Q5_return | Factor monotonicity |
| Sector Hit Rate | count(sectors Q1 > benchmark) / count(sectors) | Consistency |

### Rolling Metrics (for UI time-series charts)
- Rolling 12M Sharpe (36M window)
- Rolling Q1 vs Benchmark cumulative return
- Rolling Q1-Q5 spread over time
- Annual win rate by calendar year

---

## 9. Obsidian Backtest Score (Proprietary 5-Star Rating)

5 dimensions, each scored 0-4 stars, weighted into composite.
NEVER modify thresholds or weights -- these are OBQ proprietary.

OBSIDIAN_THRESHOLDS benchmark_win_rate: [0.50, 0.60, 0.70, 0.80]
OBSIDIAN_THRESHOLDS quintile_monotonicity: [0.25, 0.50, 0.75, 1.00]
OBSIDIAN_THRESHOLDS sector_consistency: [0.40, 0.55, 0.65, 0.75]
OBSIDIAN_THRESHOLDS absolute_spread: [0.02, 0.04, 0.06, 0.09]
OBSIDIAN_THRESHOLDS yoy_consistency: [0.45, 0.55, 0.65, 0.75]

OBSIDIAN_WEIGHTS benchmark_win_rate: 0.20
OBSIDIAN_WEIGHTS quintile_monotonicity: 0.25
OBSIDIAN_WEIGHTS sector_consistency: 0.20
OBSIDIAN_WEIGHTS absolute_spread: 0.20
OBSIDIAN_WEIGHTS yoy_consistency: 0.15

Scoring: for each dimension, check value against 4 thresholds ascending.
Stars = number of thresholds crossed (0-4).
Composite = sum(dim_stars * weight), rounded to nearest integer.

| Stars | Meaning |
|-------|---------|
| 4 | Exceptional -- deploy in live strategy |
| 3 | Strong -- monitor and consider |
| 2 | Moderate -- use in composite only |
| 1 | Weak -- investigate before use |
| 0 | Failed -- do not use |

---

## 10. Results Storage

### DuckDB Schema (backtest schema in obq_ai.duckdb)

CREATE SCHEMA IF NOT EXISTS backtest;

CREATE TABLE IF NOT EXISTS backtest.runs (
    run_id          VARCHAR PRIMARY KEY,
    factor_name     VARCHAR NOT NULL,
    universe_name   VARCHAR NOT NULL,
    start_date      DATE NOT NULL,
    end_date        DATE NOT NULL,
    rebal_frequency VARCHAR NOT NULL,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    obsidian_stars  INTEGER,
    obsidian_detail JSON
);

CREATE TABLE IF NOT EXISTS backtest.quintile_returns (
    run_id       VARCHAR REFERENCES backtest.runs(run_id),
    rebal_date   DATE NOT NULL,
    quintile     INTEGER NOT NULL,
    n_stocks     INTEGER,
    avg_return   DOUBLE,
    return_std   DOUBLE,
    n_delisted   INTEGER,
    PRIMARY KEY (run_id, rebal_date, quintile)
);

CREATE TABLE IF NOT EXISTS backtest.annual_metrics (
    run_id              VARCHAR REFERENCES backtest.runs(run_id),
    year                INTEGER NOT NULL,
    q1_return           DOUBLE,
    q5_return           DOUBLE,
    benchmark_return    DOUBLE,
    q1_beats_benchmark  BOOLEAN,
    q1_q5_spread        DOUBLE,
    PRIMARY KEY (run_id, year)
);

### Flask API Endpoints (UI Integration)
POST   /api/backtest/run                  -> trigger backtest, return run_id
GET    /api/backtest/results/<run_id>     -> full results JSON
GET    /api/backtest/quintile-chart/<run_id> -> chart data {dates, q1..q5, benchmark}
GET    /api/backtest/list                 -> all saved runs with obsidian scores
DELETE /api/backtest/<run_id>             -> remove a run

---

## 11. Performance Requirements

| Operation | Target | Method |
|-----------|--------|--------|
| Full 15Y R1000 backtest | < 60 seconds | DuckDB columnar SQL |
| Single rebalance date | < 2 seconds | Pre-scored factors |
| Quintile chart render | < 500ms | Cached results table |
| Score recompute (incremental) | < 5 seconds | Date-bounded SQL |

### Architecture Principles for Speed
1. DuckDB-native SQL -- all heavy computation in SQL, Python for orchestration only
2. Pre-scored factors -- backtest reads scores, NOT raw fundamentals at query time
3. Dual-attach -- open fdb and main as ATTACH in same connection (one round-trip)
4. No Python row loops -- NTILE, window functions, aggregations all in single SQL pass
5. Columnar storage -- sort factor score tables by (score_date, symbol) for zone-map optimization

### Connection Pattern
import duckdb
def get_backtest_conn():
    conn = duckdb.connect(r"D:\OBQ_AI\obq_ai.duckdb")
    conn.execute("ATTACH r'D:\OBQ_AIdb.duckdb' AS fdb (READ_ONLY)")
    return conn

---

## 12. File and Module Structure

OBQ_Fundamental_Backtest/
  BUILD_BLUEPRINT.md
  README.md
  backtest_engine/
    connection.py          -- DuckDB dual-attach connection manager
    universe.py            -- Survivorship-bias-free universe builder
    factor_loader.py       -- Load pre-scored factors from DB
    returns.py             -- Forward return computation, delisted-safe
    quintiles.py           -- NTILE(5) quintile construction
    portfolio.py           -- Equal-weighted portfolio aggregation
    sector.py              -- Sector consistency analysis
    rolling.py             -- Rolling metrics for time-series charts
    obsidian_score.py      -- 5-star rating computation
    results.py             -- Write/read backtest schema tables
    runner.py              -- Orchestrates full backtest pipeline
  factor_scores/
    base.py                -- FactorScoreBase abstract class
    growth.py              -- OBQ Growth Score 6 components
    value.py               -- OBQ Value Score 3 dimensions 4 ratios
    quality.py             -- OBQ Quality Score 8 components
    momentum.py            -- OBQ Momentum Score TBD read PDF first
    financial_strength.py  -- OBQ Financial Strength Score TBD
    composite.py           -- Weighted composite of all 5 scores
  schema/
    backtest_schema.sql
  sync/
    auto_sync_hook.py      -- After-Norgate hook to recompute scores
  tests/
    test_survivorship_bias.py
    test_lookahead_bias.py
    test_returns_include_delisted.py
    test_quintile_coverage.py
  examples/
    run_growth_backtest.py
    run_composite_backtest.py

---

## 13. Factor Score Registry

### OBQ Growth Score (6 Components, 100 pts)
| Component | Weight | Metric | Periods |
|-----------|--------|--------|---------|
| Revenue Growth | 20% | Revenue per share CAGR | 1Y 3Y 5Y equal-weighted |
| FCF Growth | 20% | FCF per share CAGR | 1Y 3Y 5Y equal-weighted |
| EBITDA Growth | 20% | EBITDA per share CAGR | 1Y 3Y 5Y equal-weighted |
| EPS Growth | 15% | Diluted EPS CAGR | 1Y 3Y 5Y equal-weighted |
| Invested Capital Efficiency | 15% | Revenue / Invested Capital growth | 1Y 3Y |
| Operating Income Growth | 10% | Operating Income per share CAGR | 1Y 3Y 5Y |

All components: cross-sectional percentile rank 0-100 within universe on rebal_date.
Per-share normalization is critical -- do NOT use raw totals.

### OBQ Value Score (3 Dimensions)
| Dimension | Weight | Description |
|-----------|--------|-------------|
| VS_Sector | 40% | Valuation vs sector peers (4 ratios) |
| VS_History | 35% | Current vs own 5Y historical average (4 ratios) |
| VS_Universe | 25% | Percentile rank vs full universe (4 ratios) |

Ratio weights within each dimension: P/FCF 40%, P/E 30%, P/S 20%, P/B 10%
Lower ratio = higher score. VS_Sector can go negative -- clamp to [0, 100].

### OBQ Quality Score (8 Components)
| Component | Key Issue |
|-----------|-----------|
| ROIC | Near-zero denominator risk -- add epsilon guard NOPAT / MAX(IC, 0.001) |
| ROE | Standard -- no issues |
| Gross Margin | Standard |
| Net Margin | Standard |
| Asset Turnover | Standard |
| Debt/Equity | Invert: lower = better |
| Interest Coverage | Cap outliers at 99th percentile |
| Accruals Ratio | Lower = better, invert |

### OBQ Momentum Score
TBD -- read OBQ_MOMENTUM_SCORE_REPORT.pdf before implementing.

### OBQ Financial Strength Score
TBD -- read OBQ_Financial_Strength_Score_Documentation.pdf before implementing.

### Composite Score (Default Weights)
Growth 25% | Value 20% | Quality 25% | Momentum 15% | Financial Strength 15%
Weights are configurable per run -- stored in backtest.runs metadata JSON.

---

## 14. Critical Anti-Patterns (Never Do These)

These patterns were found in the Manus draft and MUST NOT appear in the OBQ implementation.

| # | Anti-Pattern | Why Wrong | Fix |
|---|-------------|-----------|-----|
| 1 | WHERE return_12m IS NOT NULL | Drops delisted/bankrupt stocks = survivorship bias | Include all; use is_early_exit flag |
| 2 | Universe join by YEAR() | Allows look-ahead, misses mid-year delistings | Interval join: date_in <= rebal AND (date_out IS NULL OR date_out >= rebal) |
| 3 | filing_date not enforced | Uses future fundamental data = look-ahead bias | Always: filing_date <= rebal_date |
| 4 | Fixed N stocks per quintile | Breaks when universe shrinks | NTILE(5) percentage-based |
| 5 | fill_value=0 in sector unstack | Zero is not missing data, corrupts sector averages | Use NaN/NULL, exclude missing sectors |
| 6 | Benchmark = top 250 only | Excludes bottom half of index | Benchmark = ALL index members equal-weighted |
| 7 | MotherDuck as data source | Latency, internet dependency, cost | Local DuckDB at D:\OBQ_AI\ only |
| 8 | Raw close for returns | Not total-return adjusted | adjusted_close -- equity_ts.close in OBQ schema |

---

## 15. Validation and Testing

### Test 1: Survivorship Bias Check
Verify universe includes stocks that delisted AFTER the rebalance date.
Query index_membership for all symbols with date_in <= rebal AND date_out >= rebal.
Assert that every such symbol appears in the computed universe.
Fail loudly if any delisted stock is missing.

### Test 2: Look-Ahead Bias Check
For every fundamental data row used in factor scoring, verify filing_date <= rebal_date.
Collect all factor inputs, filter rows where filing_date > rebal_date.
Assert zero violations. This test must pass for EVERY rebalance date in the backtest.

### Test 3: Delisted Stocks in Returns
For every symbol in the universe on rebal_date, verify it appears in forward_returns.
Delisted stocks must have a non-null return (their actual last-traded price).
Delisted stocks must have is_early_exit = True.
Missing symbols in returns = survivorship bias in the return calculation.

### Test 4: Quintile Coverage
For every rebalance date in a completed backtest run, verify:
  - Exactly 5 quintiles exist (Q1 through Q5)
  - Each quintile has n_stocks >= 30
  - Total stocks in Q1-Q5 == total scored stocks in universe for that date
If any rebal date has thin quintiles (< 30), log warning and skip that date.

### Running Tests
Run all 4 tests before marking any Phase complete.
Tests must pass against production data, not synthetic data.
Any failure requires root-cause fix before proceeding to next phase.

---

## 16. Build Sequence (Phased)

### Phase 1 -- Schema and Data Validation (1-2 days)
- Create backtest schema in obq_ai.duckdb
- Run SHOW TABLES on both obq_ai.duckdb and fdb.duckdb -- document all table names
- Audit index_membership: verify date_out is populated for delisted stocks
- Audit fundamentals tables: confirm filing_date presence and coverage
- Run all 4 validation tests against existing data before writing any engine code

### Phase 2 -- Factor Score Replication (3-5 days)
- Read OBQ_MOMENTUM_SCORE_REPORT.pdf
- Read OBQ_Financial_Strength_Score_Documentation.pdf
- Read Fundamentals_Database_Complete_Manual.pdf
- Implement Growth Score SQL (documentation most complete)
- Implement Value Score SQL
- Implement Quality Score SQL with ROIC epsilon guard
- Implement Momentum Score SQL
- Implement Financial Strength Score SQL
- Unit test each score against known values from JCN documentation

### Phase 3 -- Backtest Engine Core (2-3 days)
- backtest_engine/universe.py: survivorship-bias-free builder
- backtest_engine/returns.py: delisted-safe forward returns
- backtest_engine/quintiles.py: NTILE(5) implementation
- backtest_engine/portfolio.py: equal-weighted aggregation
- backtest_engine/obsidian_score.py: 5-star rating
- backtest_engine/runner.py: orchestration

### Phase 4 -- Testing and Validation (1-2 days)
- Run all 4 bias tests across full available history
- Compare Q1-Q5 spreads to Manus draft (differences expected -- ours is correct)
- Validate Obsidian Score computation on known-good factors

### Phase 5 -- Results and UI Integration (1-2 days)
- backtest_engine/results.py: write to backtest schema
- Flask: POST /api/backtest/run, GET /api/backtest/results, GET /api/backtest/quintile-chart
- PyWebView frontend: backtest runner view and results display

### Phase 6 -- Auto-Sync Hook (1 day)
- sync/auto_sync_hook.py: trigger after Norgate data refresh
- Incremental score computation (new dates only)
- Error handling and logging

### Phase 7 -- Documentation and Examples (0.5 days)
- examples/run_growth_backtest.py
- examples/run_composite_backtest.py
- README.md with quick start

---

## 17. Known Issues and Open Questions

### CRITICAL (must resolve before building any engine code)
| Issue | Risk | Resolution |
|-------|------|-----------|
| index_membership date_out may be 0% populated | Survivorship bias completely wrong | Query table first; may need to rebuild from Norgate delisting data |
| filing_date may not exist in all fundamental rows | Look-ahead bias if fallback to report_date | Audit fundamentals table; NEVER silently fall back to report_date |

### HIGH (resolve before Phase 2 factor score build)
| Issue | Risk | Resolution |
|-------|------|-----------|
| ROIC near-zero denominator | Division by zero or outlier contamination | NOPAT / NULLIF(GREATEST(invested_capital, 0.001), 0) |
| Momentum Score PDF not yet read | Cannot implement correctly | Read OBQ_MOMENTUM_SCORE_REPORT.pdf before Phase 2 |
| Financial Strength Score PDF not yet read | Cannot implement correctly | Read OBQ_Financial_Strength_Score_Documentation.pdf before Phase 2 |

### MEDIUM (resolve during build)
| Issue | Risk | Resolution |
|-------|------|-----------|
| VS_Sector can go negative | Score outside [0,100] | GREATEST(0, LEAST(100, vs_sector_score)) |
| equity_ts.close exact column name unknown | May differ from assumption | DESCRIBE equity_ts before building returns.py |
| Commission model not specified | Overstates returns | Default 0.05% per side unless user specifies otherwise |

---

## Appendix: Key Table Names (Local DuckDB -- Verify Before Building)

| Logical Purpose | Assumed Table | Location |
|----------------|--------------|----------|
| Universe membership | index_membership | obq_ai.duckdb main |
| Price / return data | equity_ts | obq_ai.duckdb main |
| Fundamental data PIT | filings_pit | fdb.duckdb (ATTACH) |
| Factor scores computed | backtest.factor_scores_* | obq_ai.duckdb main |
| Backtest results | backtest.runs / backtest.quintile_returns | obq_ai.duckdb main |

ALWAYS run SHOW TABLES against both databases before building.
NEVER assume column names -- run DESCRIBE <table> first.

---

OBQ_Fundamental_Backtest_Blueprint.md -- Version 1.0
Status: DRAFT -- Pending user sign-off before implementation begins
Authors: OBQ Intelligence (Sisyphus) + Alex Bernal
Last Updated: 2026-03-01
