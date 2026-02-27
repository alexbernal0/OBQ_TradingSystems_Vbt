# Metrics Reference — OBQ Performance Reporting

Complete reference for all 22 metrics computed in the Extended Metrics Table (VIZ 2).
Each entry includes: definition, formula, typical range, interpretation, and Python implementation.

---

## Section 1 — Returns

### CAGR (%)
**Compound Annual Growth Rate** — the smoothed annualized return assuming annual compounding.

**Formula:**
```
CAGR = ( (Final_Value / Initial_Value) ^ (1 / N_years) - 1 ) × 100
```

**Range:** Typically −20% to +60% for systematic strategies.
**Interpretation:** "How much did $1 grow per year, compounded?" Higher is better.
**Python:**
```python
cagr = ((equity.iloc[-1] / equity.iloc[0]) ** (1 / (len(returns) / 252)) - 1) * 100
```

---

### Annual Volatility (%)
**Annualized standard deviation of daily returns.**

**Formula:**
```
Ann_Vol = std(daily_returns) × sqrt(252) × 100
```

**Range:** 5%–50% for most strategies; futures trend-following typically 10%–25%.
**Interpretation:** Lower is generally better, but only relative to return. High vol + high return can be fine.
**Python:**
```python
ann_vol = returns.std() * np.sqrt(252) * 100
```

---

### Sharpe Ratio
**Risk-adjusted return using total volatility as risk measure.** Assumes risk-free rate ≈ 0.

**Formula:**
```
Sharpe = mean(daily_returns) × 252 / (std(daily_returns) × sqrt(252))
       = mean(daily_returns) / std(daily_returns) × sqrt(252)
```

**Range:** <0 = bad, 0–0.5 = marginal, 0.5–1.0 = acceptable, 1.0–2.0 = good, >2.0 = exceptional.
**Interpretation:** How many units of return per unit of risk. Sharpe 1.0 means earning 1% excess return per 1% vol.
**Python:**
```python
sharpe = returns.mean() / returns.std() * np.sqrt(252)
```

---

### Sortino Ratio
**Risk-adjusted return using only downside volatility.** Better than Sharpe for asymmetric return distributions.

**Formula:**
```
Sortino = mean(daily_returns) × 252 / (std(negative_daily_returns) × sqrt(252))
```

**Range:** Higher is better. Typically 1.5–3× the Sharpe ratio for trend-following.
**Interpretation:** Like Sharpe but doesn't penalize upside volatility. More appropriate for positively skewed strategies.
**Python:**
```python
downside_std = returns[returns < 0].std()
sortino = returns.mean() / downside_std * np.sqrt(252)
```

---

### Calmar Ratio
**Return vs. maximum drawdown.** Measures how much return is generated per unit of worst-case loss.

**Formula:**
```
Calmar = CAGR (%) / abs(Max Drawdown (%))
```

**Range:** <0.5 = poor, 0.5–1.0 = acceptable, 1.0–2.0 = good, >2.0 = excellent.
**Interpretation:** Calmar 1.0 means the strategy earns 1% CAGR per 1% max drawdown.
**Python:**
```python
calmar = cagr / abs(max_dd)
```

---

### Win Rate (Monthly %)
**Percentage of calendar months with positive returns.**

**Formula:**
```
Win_Rate = count(monthly_returns > 0) / total_months × 100
```

**Range:** 50%–70% is typical for trend-following. Equity long-only often 55%–65%.
**Interpretation:** Higher is better but must be evaluated with avg win/loss size. 40% win rate with 3:1 reward/risk = profitable.
**Python:**
```python
monthly = returns.resample('ME').apply(lambda x: (1 + x).prod() - 1)
win_rate = (monthly > 0).mean() * 100
```

---

## Section 2 — Risk

### Max Drawdown (%)
**Largest peak-to-trough decline in equity, expressed as a percentage.**

**Formula:**
```
Max_DD = min( (equity - equity.cummax()) / equity.cummax() ) × 100
```

**Range:** Acceptable range depends on strategy type. Trend-following: −15% to −40%. Equity L/S: −10% to −30%.
**Interpretation:** Worst historical loss from a high-water mark. Critical for position sizing and client acceptance.
**Python:**
```python
max_dd = ((equity - equity.cummax()) / equity.cummax()).min() * 100
```

---

### CVaR 95% (daily %)
**Conditional Value at Risk at 95% confidence** — also called **Expected Shortfall**.
The average of the worst 5% of daily returns.

**Formula:**
```
CVaR_95 = mean(returns | returns <= percentile(returns, 5)) × 100
```

**Range:** −1% to −5% daily for most strategies. Trend-following: −0.5% to −2%.
**Interpretation:** "On my worst 5% of days, I lose this much on average." More informative than VaR because it describes the tail, not just the boundary.
**Python:**
```python
cvar_95 = returns[returns <= returns.quantile(0.05)].mean() * 100
```

---

### CVaR 99% (daily %)
Same as CVaR 95% but for the worst 1% of days — captures extreme tail risk.

**Formula:**
```
CVaR_99 = mean(returns | returns <= percentile(returns, 1)) × 100
```

**Interpretation:** The "black swan" metric. Large gap between CVaR 95% and CVaR 99% = fat-tailed distribution.
**Python:**
```python
cvar_99 = returns[returns <= returns.quantile(0.01)].mean() * 100
```

---

### Ulcer Index
**Measures the depth and duration of drawdowns.** Invented by Peter Martin (1987).

**Formula:**
```
Ulcer_Index = sqrt( mean( drawdown_pct² ) )
```
where `drawdown_pct` is the percentage decline from the running peak at each point.

**Range:** 0–30. <5 = comfortable, 5–15 = moderate, >15 = stressful.
**Interpretation:** Unlike Max DD (single worst event), Ulcer Index captures the *entire drawdown experience* — both depth and duration. A strategy that is underwater for 3 years at −10% scores worse than one that briefly hits −15% and recovers quickly.
**Python:**
```python
dd_pct = ((equity - equity.cummax()) / equity.cummax()) * 100
ulcer = np.sqrt((dd_pct ** 2).mean())
```

---

### Pain Index
**Mean absolute drawdown** — simpler version of Ulcer Index without squaring.

**Formula:**
```
Pain_Index = mean( |drawdown_pct| )
```

**Range:** 0–25. Lower is better.
**Interpretation:** Average percentage the portfolio was underwater over the entire period. Pain Index = 5% means on an average day the portfolio was 5% below its peak.
**Python:**
```python
pain_idx = ((equity - equity.cummax()) / equity.cummax() * 100).abs().mean()
```

---

### Lake Ratio
**Fraction of time the portfolio is "underwater" (below its high-water mark).**

**Formula:**
```
Lake_Ratio = 1 - mean( equity / equity.cummax() )
```

**Range:** 0–1. 0 = always at or above previous highs, 1 = always at zero.
**Interpretation:** A Lake Ratio of 0.10 means the portfolio spent 10% of its value "submerged" on average. Think of the equity curve as a mountain range — the "lakes" are the drawdown periods filled with water.
**Python:**
```python
lake_ratio = 1.0 - (equity / equity.cummax()).mean()
```

---

## Section 3 — Advanced

### Omega Ratio
**Ratio of probability-weighted gains to probability-weighted losses** above/below a threshold (typically 0).

**Formula:**
```
Omega(L) = sum( max(r - L, 0) ) / sum( max(L - r, 0) )
```
where `r` = daily/monthly returns, `L` = threshold (0 = breakeven).

**Range:** >1 = gains outweigh losses. Higher is better.
**Interpretation:** Omega incorporates all moments of the return distribution (unlike Sharpe which only uses mean and variance). Omega > 1 means positive expected value above the threshold. The Omega Curve (VIZ 10) shows how this changes at different return thresholds.
**Python:**
```python
gains  = np.sum(np.maximum(returns.values, 0))
losses = np.sum(np.maximum(-returns.values, 0))
omega  = gains / losses
```

---

### Serenity Ratio
**CAGR divided by the Ulcer Index** — analogous to Sharpe but uses Ulcer Index as the risk denominator.

**Formula:**
```
Serenity = CAGR (%) / Ulcer_Index
```

**Range:** >1 = good. >3 = excellent for trend-following.
**Interpretation:** Rewards strategies that grow capital without prolonged drawdown periods. Penalizes strategies that compound well but spend long periods underwater.
**Python:**
```python
serenity = cagr / ulcer
```

---

### Pain Ratio
**CAGR divided by the Pain Index** — analogous to Serenity but with the simpler Pain Index denominator.

**Formula:**
```
Pain_Ratio = CAGR (%) / Pain_Index
```

**Python:**
```python
pain_ratio = cagr / pain_idx
```

---

### Sharpe t-statistic
**Statistical significance of the Sharpe Ratio** — is the measured Sharpe distinguishable from zero?

**Formula:**
```
t_stat = Sharpe / SE(Sharpe)
SE(Sharpe) = sqrt( (1 + 0.5 × Sharpe²) / N_obs )
```
where `N_obs` = number of daily return observations.

**Range:** |t| > 1.96 = statistically significant at 95% confidence.
**Interpretation:** A Sharpe of 0.5 over 10 years (N≈2520) gives t ≈ 24 (highly significant). Over 1 year (N≈252) gives t ≈ 7.6. Short backtests with high Sharpe may still be statistically significant.
**Python:**
```python
n_obs = len(returns)
se = np.sqrt((1 + 0.5 * sharpe**2) / n_obs)
t_stat = sharpe / se
```

---

### Sharpe 95% CI
**95% confidence interval around the measured Sharpe Ratio.**

**Formula:**
```
CI = [Sharpe - 1.96 × SE, Sharpe + 1.96 × SE]
```

**Interpretation:** The true population Sharpe lies within this range with 95% probability. Wide CI (e.g., [0.2, 1.8]) = uncertain estimate; narrow CI (e.g., [1.1, 1.3]) = reliable.
**Python:**
```python
ci_lo = sharpe - 1.96 * se
ci_hi = sharpe + 1.96 * se
```

---

### Haircut Sharpe
**The lower bound of the 95% CI** — the "pessimistic" estimate of the true Sharpe.

**Formula:**
```
Haircut_Sharpe = Sharpe - 1.96 × SE(Sharpe)
```

**Interpretation:** If the haircut Sharpe is still > 0.5, you have high confidence the strategy is genuinely profitable even accounting for estimation error. Used to filter out lucky backtest results.
**Python:**
```python
haircut_sharpe = sharpe - 1.96 * se
```

---

## Section 4 — vs Benchmark

### Information Ratio
**Risk-adjusted active return** — Sharpe ratio of the strategy's excess returns over the benchmark.

**Formula:**
```
Active_Returns = Strategy_Daily_Returns - Benchmark_Daily_Returns
IR = mean(Active_Returns) × 252 / (std(Active_Returns) × sqrt(252))
   = mean(Active_Returns) / std(Active_Returns) × sqrt(252)
```

**Range:** >0.5 = good, >1.0 = excellent.
**Interpretation:** Measures consistency of outperformance. IR 0.75 means the strategy outperforms by 0.75 units of active risk annually.
**Python:**
```python
active = returns_strategy - returns_benchmark.reindex(returns_strategy.index)
ir = active.mean() / active.std() * np.sqrt(252)
```

---

### Tracking Error (%)
**Annualized standard deviation of active returns** — how closely the strategy tracks the benchmark.

**Formula:**
```
Tracking_Error = std(Active_Returns) × sqrt(252) × 100
```

**Range:** <1% = index-hugger, 1%–5% = low active, 5%–15% = moderate, >15% = high conviction.
**Interpretation:** Low TE = moves like the benchmark. Trend-following with a broad universe should have TE > 15% vs equity benchmarks (since it trades many uncorrelated assets).
**Python:**
```python
tracking_error = active.std() * np.sqrt(252) * 100
```

---

### Up Capture (%)
**Ratio of strategy's return to benchmark's return in up-market months** (months where benchmark > 0).

**Formula:**
```
Up_Capture = [ (prod(1 + strat_up_months))^(12/n_up) - 1 ]
           / [ (prod(1 + bench_up_months))^(12/n_up) - 1 ] × 100
```

**Range:** >100% = strategy outperforms in up markets.
**Interpretation:** Up Capture 120% = strategy gains 1.2% for every 1% the benchmark gains in bull markets. For trend-following: Up Capture 80–120% is typical; pure trend-following often has low Up Capture but very high Down Capture advantage.
**Python:**
```python
up_mask = monthly_bench > 0
n_up = up_mask.sum()
s_ann = (1 + monthly_strat[up_mask]).prod() ** (12 / n_up) - 1
b_ann = (1 + monthly_bench[up_mask]).prod() ** (12 / n_up) - 1
up_capture = s_ann / b_ann * 100
```

---

### Down Capture (%)
**Ratio of strategy's return to benchmark's return in down-market months** (months where benchmark < 0).

**Formula:** Same as Up Capture but for months where benchmark < 0.

**Range:** <100% = strategy loses less than benchmark in down markets (desirable).
**Interpretation:** Down Capture 60% = strategy loses only 0.60% for every 1% the benchmark loses in bear markets. The key metric for trend-following and hedged strategies. **Ideal combination: high Up Capture + low Down Capture.**

**Capture Ratio** = Up Capture / Down Capture. >1.0 = favorable asymmetry.
**Python:**
```python
dn_mask = monthly_bench < 0
n_dn = dn_mask.sum()
s_ann = (1 + monthly_strat[dn_mask]).prod() ** (12 / n_dn) - 1
b_ann = (1 + monthly_bench[dn_mask]).prod() ** (12 / n_dn) - 1
down_capture = s_ann / b_ann * 100
```

---

## Quick Summary Table

| Metric | Formula | Good Value | Key Insight |
|--------|---------|-----------|-------------|
| CAGR | `(End/Start)^(1/Years) - 1` | Strategy-dependent | Compounded annual growth |
| Sharpe | `μ/σ × √252` | >1.0 | Return per unit of total risk |
| Sortino | `μ/σ_down × √252` | >1.5 | Return per unit of downside risk |
| Calmar | `CAGR / |Max DD|` | >1.0 | Return per unit of worst loss |
| Max DD | `min((eq - peak)/peak)` | < −20% concern | Worst historical loss |
| CVaR 95% | `mean(r ≤ 5th pct)` | > −2% daily | Avg tail loss (worst 5% days) |
| Ulcer | `√mean(DD²)` | <5 | Depth + duration of drawdowns |
| Lake Ratio | `1 - mean(eq/peak)` | <0.10 | Fraction of equity "underwater" |
| Omega | `gains/losses` | >1.5 | All-moment return quality |
| Serenity | `CAGR/Ulcer` | >2.0 | Growth without prolonged underwater |
| Sharpe t-stat | `SR/SE` | >2.0 | Statistical significance of SR |
| Haircut SR | `SR - 1.96×SE` | >0.5 | Pessimistic Sharpe estimate |
| Info Ratio | `μ_active/σ_active × √252` | >0.5 | Consistency of outperformance |
| Tracking Error | `σ_active × √252 × 100` | >10% for active mgr | Divergence from benchmark |
| Up Capture | See formula | >100% | Participation in rallies |
| Down Capture | See formula | <100% | Protection in declines |
