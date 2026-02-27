# Glossary — OBQ Performance Reporting

Complete reference of all terms used in the OBQ Performance Reporting system,
covering performance metrics, risk concepts, VectorBT internals, and trading terminology.

---

## A

**Active Return**
The return of a strategy minus the return of its benchmark over the same period.
`Active Return = Strategy Return − Benchmark Return`

**Annualized Return**
A return scaled to a 1-year period, assuming compounding.
Formula: `(1 + total_return)^(252/n_days) - 1`

**ATR (Average True Range)**
A volatility indicator measuring the average range of price movement over N bars.
`True Range = max(High−Low, |High−Prev_Close|, |Low−Prev_Close|)`
`ATR = Wilder_Smoothed(True_Range, N)`

**ATR Trailing Stop**
An exit mechanism where the stop level is set at `peak − ATR_multiplier × ATR` for longs.
The peak updates every bar but never moves backward, creating a ratcheting stop.

**Autocorrelation (ACF)**
The correlation of a time series with a lagged version of itself.
Positive autocorrelation = momentum; negative = mean reversion.
Formula: `ACF(lag) = cov(r_t, r_{t-lag}) / var(r)`

---

## B

**Bear Market**
A period when the market is in a sustained decline. In this system, defined as benchmark equity < 200-day SMA.

**Benchmark**
A reference index used to measure relative performance. Typically SPX (S&P 500) for equity-correlated strategies. The benchmark is auto-rebased to match the strategy's starting equity value.

**Bull Market**
A period of sustained upward price movement. Defined as benchmark equity > 200-day SMA.

---

## C

**CAGR (Compound Annual Growth Rate)**
The smoothed annualized return that would achieve the same total return as the actual path.
`CAGR = (End/Start)^(1/Years) − 1`

**Calendar Day Duration**
Trade duration measured in actual calendar days (not trading days). Used in VIZ 16.

**Calmar Ratio**
Return-to-drawdown ratio: `CAGR / |Max Drawdown|`. Higher = better.
Named after California Managed Account Reports newsletter (1991).

**Capture Ratio**
`Up Capture / Down Capture`. Values >1.0 indicate favorable asymmetry: the strategy participates more in gains than in losses.

**CVaR (Conditional Value at Risk)**
Also called Expected Shortfall. The average return in the worst X% of observations.
`CVaR_95 = mean(r | r ≤ 5th percentile)`.
Preferred over VaR because it describes the tail, not just the boundary.

---

## D

**Daily Return**
The percentage change in portfolio value from one trading day to the next.
`r_t = (equity_t − equity_{t-1}) / equity_{t-1}`

**Drawdown**
The percentage decline from a peak (high-water mark) to a trough.
`DD_t = (equity_t − max(equity_{1:t})) / max(equity_{1:t})`

**Drawdown Duration**
Number of calendar days from the start of a drawdown (previous peak) to the trough.

**Drawdown Recovery**
The return to the previous peak level after a trough. "Ongoing" if the strategy has not yet recovered.

---

## E

**Equity Curve**
The time series of portfolio total value (cash + open positions) over the backtest period.
Also called NAV (Net Asset Value).

**Excess Kurtosis**
Kurtosis of a distribution minus 3 (the kurtosis of a normal distribution).
Positive excess kurtosis = fat tails (more extreme events than normal).
`Excess_Kurtosis = E[(r − μ)^4] / σ^4 − 3`

**Expected Shortfall**
See CVaR.

---

## F

**Fat Tails**
A return distribution with more probability mass in the extreme values than a normal distribution.
Indicated by excess kurtosis > 0. Common in financial returns; trend-following strategies often have positive skew + fat tails (many small losses, occasional large gains).

---

## G

**Haircut Sharpe**
The lower bound of the 95% confidence interval around the measured Sharpe Ratio.
Represents a "pessimistic" estimate that accounts for statistical uncertainty.
`Haircut_Sharpe = Sharpe − 1.96 × SE(Sharpe)`

**High-Water Mark (HWM)**
The highest portfolio value achieved at any point in history. Drawdown is always measured from the HWM.

---

## I

**Information Ratio (IR)**
The Sharpe ratio of active returns (strategy minus benchmark).
`IR = annualized_mean(active_returns) / annualized_std(active_returns)`
Measures how consistently the strategy outperforms its benchmark per unit of active risk.

**Intra-Month Drawdown**
The worst peak-to-trough decline within a single calendar month.
Reveals hidden intra-month volatility that doesn't appear in monthly return figures.

---

## J

**Jarque-Bera Test**
A statistical test for normality based on skewness and kurtosis.
`JB = n/6 × (S² + K²/4)` where S = skewness, K = excess kurtosis.
Under normality, JB follows a chi-squared distribution with 2 degrees of freedom.
p-value < 0.05 → reject normality hypothesis.

---

## K

**Kurtosis**
Measure of "tail heaviness" of a return distribution.
Normal distribution kurtosis = 3. Financial returns typically have kurtosis > 3 (leptokurtic = fat tails).

---

## L

**Lag (ACF/PACF)**
The time offset used in autocorrelation. Lag 1 = correlation of today's return with yesterday's return.

**Lake Ratio**
The fraction of the equity curve that is "underwater" (below the running high-water mark), weighted by depth.
`Lake_Ratio = 1 − mean(equity / equity.cummax())`
Analogy: imagine filling the drawdown regions with water — the Lake Ratio is the total volume of "water" relative to the area under the equity curve.

---

## M

**Max Drawdown**
The largest peak-to-trough decline in portfolio value over the entire history.
`Max_DD = min( (equity − equity.cummax()) / equity.cummax() )`

**Monthly Return**
The compounded return over a calendar month.
`Monthly_Return = product(1 + daily_returns) − 1`

---

## N

**NAV (Net Asset Value)**
Total portfolio value = cash + market value of all open positions. Used interchangeably with equity curve.

**Normalization**
Scaling a price series to start at 1.0 for comparison (used in VIZ 19 crisis panels).
`normalized = price / price.iloc[0]`

---

## O

**Omega Ratio**
The ratio of probability-weighted gains to probability-weighted losses above/below a threshold L.
`Omega(L) = ∫_L^∞ [1 − F(r)] dr / ∫_{-∞}^L F(r) dr`
In discrete form: `Omega = sum(max(r−L, 0)) / sum(max(L−r, 0))`
Omega > 1 at threshold 0 means the strategy has positive expected value.

**Omega Curve**
A plot of the Omega Ratio as a function of the threshold L.
The x-intercept where Omega = 1 shows the minimum return threshold the strategy satisfies.

---

## P

**PACF (Partial Autocorrelation Function)**
Like ACF but removes the influence of intermediate lags. Useful for identifying the true order of an autoregressive process.

**Pain Index**
Mean absolute drawdown over the entire period.
`Pain_Index = mean(|drawdown_pct|)`
Simple version of the Ulcer Index without squaring.

**Pain Ratio**
`CAGR / Pain_Index`. Return earned per unit of average drawdown pain.

---

## Q

**Q-Q Plot (Quantile-Quantile)**
A graphical test of normality. Plots empirical quantiles against theoretical normal quantiles. Points lying on the straight line = perfectly normal. S-shaped deviation = fat tails. Curves away from the line = skewness.

---

## R

**Realized P&L**
Profit or loss from a closed trade: `(Exit_Price − Entry_Price) × Size` for longs.

**Recovery Duration**
Number of calendar days from the trough of a drawdown back to the previous high-water mark.

**Rolling Window**
A moving calculation over the most recent N periods. In this system: 252 trading days (≈ 1 year).

---

## S

**Sector Attribution**
Analysis of strategy P&L broken down by the sector of each instrument (e.g., Energy, Metals, Fixed Income). Useful for identifying concentration risk and which sectors contribute most to returns.

**Serenity Ratio**
`CAGR / Ulcer_Index`. Return earned per unit of drawdown stress. Penalizes both deep and prolonged drawdowns.

**Sharpe Ratio**
`mean(daily_returns) / std(daily_returns) × √252`. Return per unit of total volatility.
Named after William F. Sharpe (1966).

**Skewness**
Asymmetry of the return distribution.
- Positive skew: many small losses, occasional large gains (trend-following profile)
- Negative skew: many small gains, occasional large losses (option selling profile)
`Skewness = E[(r − μ)³] / σ³`

**Sortino Ratio**
Like Sharpe but uses only downside volatility (standard deviation of negative returns).
`Sortino = mean(returns) / std(returns < 0) × √252`

**SMA (Simple Moving Average)**
`SMA(n)_t = mean(close_{t-n+1}, ..., close_t)`

**Stop Loss**
A pre-defined price level at which a position is automatically closed to limit further losses. In ATR trailing stops, this level moves up with the price for long positions.

---

## T

**t-Statistic (Sharpe)**
Tests whether the measured Sharpe Ratio is statistically distinguishable from zero.
`t = Sharpe / SE(Sharpe)`, where `SE = sqrt((1 + 0.5×SR²) / N_obs)`
|t| > 1.96 → significant at 95% confidence.

**Tracking Error**
Annualized standard deviation of active returns.
`TE = std(r_strategy − r_benchmark) × √252 × 100`
Measures how closely the strategy tracks its benchmark.

**Trade Duration**
Number of calendar days a position is held from entry to exit.

---

## U

**Ulcer Index**
`sqrt(mean(drawdown_pct²))`. Measures both the depth and duration of drawdowns simultaneously by squaring the drawdown percentages. Deep long drawdowns penalize more than shallow short ones.

**Unrealized P&L**
Current profit or loss on an open position: `(Current_Price − Entry_Price) × Size` for longs.

**Up Capture Ratio**
The annualized return of the strategy in months when the benchmark was positive,
divided by the annualized return of the benchmark in those same months × 100.

---

## V

**VaR (Value at Risk)**
The return threshold such that X% of returns are worse.
`VaR_95 = 5th percentile of daily returns`
Note: VaR is just the boundary, not the average. CVaR describes the average beyond the boundary.

**VBT (VectorBT)**
vectorbt — an ultra-fast Python backtesting library using NumPy array operations and Numba JIT compilation.

**VBT Portfolio Object**
The result of `vbt.Portfolio.from_order_func(...)` or similar. Contains all order and trade records, supports `.value()`, `.trades.records`, `.orders.records`, `.stats()`.

**VBT trades.records**
A DataFrame with columns: `id, col, size, entry_idx, entry_price, entry_fees, exit_idx, exit_price, exit_fees, pnl, return, direction (0=Long/1=Short), status (0=Open/1=Closed)`.

**VBT orders.records**
A DataFrame with columns: `id, col, idx, size, price, fees, side (0=Buy/1=Sell)`.

---

## W

**Win Rate**
The percentage of trades (or time periods) that are profitable.
Monthly Win Rate = `count(monthly_returns > 0) / total_months × 100`

---

## Y

**YTD (Year-to-Date)**
The compounded return from the start of the calendar year to the current date.
`YTD = product(1 + monthly_returns_this_year) − 1`
