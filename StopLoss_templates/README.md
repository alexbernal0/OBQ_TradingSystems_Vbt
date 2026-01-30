# Stop Loss & Target Templates for VectorBT

This folder contains **22 professional stop loss and profit target templates** converted from Backtrader to VectorBT format. All templates use **RSI as the entry signal**, which is designed to be easily swappable with any other entry logic.

---

## 📚 Table of Contents

1. [Quick Start](#quick-start)
2. [Template Categories](#template-categories)
3. [How to Use](#how-to-use)
4. [How to Swap Entry Signals](#how-to-swap-entry-signals)
5. [Template List](#template-list)
6. [Parameter Customization](#parameter-customization)

---

## 🚀 Quick Start

Each template is a complete, standalone Python script that:
- ✅ Uses VectorBT for backtesting
- ✅ Includes RSI entry signal (easily replaceable)
- ✅ Implements specific stop/target logic
- ✅ Generates performance metrics
- ✅ Creates equity curve visualization

**To use a template:**
1. Choose a stop loss method from the list below
2. Load your OHLC data into `df_all_data` DataFrame
3. Run the template script
4. (Optional) Swap the RSI entry logic with your own signals

---

## 📊 Template Categories

### **Basic Stop Methods** (5 templates)
Simple, straightforward stop loss approaches
- No Stop Loss
- Fixed Percentage
- Fixed Account Percentage
- Fixed ATR
- Anchored Dollar Amount

### **ATR-Based Methods** (4 templates)
Volatility-adjusted stops using Average True Range
- ATR Percentage Stop
- ATR Profit Target
- ATR Breakeven Stop
- ATR Trailing Stop

### **Percentage-Based Methods** (3 templates)
Price percentage-based exits
- Percentage Breakeven Stop
- Trailing Percentage Stop
- Percentage Profit Target

### **Partial Exit Methods** (3 templates)
Scale out of positions
- Sell Half at Percentage Target
- Sell Half + Breakeven Stop
- Sell Half at ATR Target

### **Advanced Methods** (4 templates)
Sophisticated exit strategies
- Account Percentage Target
- Target Then Trail
- ATR Target + ATR Trail
- Swing High/Low Stop

### **Technical Indicator Stops** (3 templates)
Stops based on technical indicators
- Chandelier Stop
- Parabolic SAR Stop
- Quantile Dynamic Stop

---

## 🎯 How to Use

### **Step 1: Prepare Your Data**

All templates expect a DataFrame named `df_all_data` with these columns:
```python
# Required columns (case-sensitive):
- Symbol    # Stock/crypto ticker
- Date      # Datetime index
- Open      # Opening price
- High      # High price
- Low       # Low price
- Close     # Closing price
```

### **Step 2: Choose a Template**

Select a stop loss method based on your trading style:
- **Conservative**: Fixed percentage (2-5%), ATR stop
- **Aggressive**: Trailing stops, partial exits
- **Trend Following**: ATR trailing, Parabolic SAR
- **Mean Reversion**: Fixed stops, profit targets

### **Step 3: Run the Template**

```python
# Example: Run the fixed percentage stop template
python 02_fixed_percentage_stop.py
```

### **Step 4: Analyze Results**

Each template outputs:
- Total Return
- Sharpe Ratio
- Max Drawdown
- Win Rate
- Total Trades
- Equity Curve Chart

---

## 🔄 How to Swap Entry Signals

All templates use RSI for entries, but this is **designed to be easily replaced**. Here's how:

### **Section to Replace: Entry Signal Logic**

Look for this section in any template:

```python
# ============================================================================
# ENTRY SIGNAL LOGIC - RSI (REPLACE THIS SECTION FOR DIFFERENT ENTRIES)
# ============================================================================

def calculate_rsi(prices, period=14):
    """Calculate RSI indicator - SWAP THIS FUNCTION FOR OTHER INDICATORS"""
    # ... RSI calculation code ...
    return rsi

rsi = calculate_rsi(close, RSI_PERIOD)

long_entries = np.zeros(len(df), dtype=bool)
short_entries = np.zeros(len(df), dtype=bool)

for i in range(RSI_PERIOD + 1, len(df)):
    # Long entry: RSI crosses above oversold
    if rsi[i-1] < RSI_OVERSOLD and rsi[i] > RSI_OVERSOLD:
        long_entries[i] = True
    
    # Short entry: RSI crosses below overbought
    if rsi[i-1] > RSI_OVERBOUGHT and rsi[i] < RSI_OVERBOUGHT:
        short_entries[i] = True
```

### **Example: Replace with Moving Average Crossover**

```python
# ============================================================================
# ENTRY SIGNAL LOGIC - MA CROSSOVER (YOUR CUSTOM LOGIC)
# ============================================================================

# Calculate moving averages
fast_ma = vbt.MA.run(df['Close'], 10).ma.values
slow_ma = vbt.MA.run(df['Close'], 50).ma.values

long_entries = np.zeros(len(df), dtype=bool)
short_entries = np.zeros(len(df), dtype=bool)

for i in range(50, len(df)):
    # Long entry: Fast MA crosses above Slow MA
    if fast_ma[i-1] < slow_ma[i-1] and fast_ma[i] > slow_ma[i]:
        long_entries[i] = True
    
    # Short entry: Fast MA crosses below Slow MA
    if fast_ma[i-1] > slow_ma[i-1] and fast_ma[i] < slow_ma[i]:
        short_entries[i] = True
```

### **Example: Replace with Breakout Signal**

```python
# ============================================================================
# ENTRY SIGNAL LOGIC - BREAKOUT (YOUR CUSTOM LOGIC)
# ============================================================================

LOOKBACK = 20  # Breakout period

long_entries = np.zeros(len(df), dtype=bool)
short_entries = np.zeros(len(df), dtype=bool)

for i in range(LOOKBACK, len(df)):
    # Long entry: Close breaks above recent high
    recent_high = np.max(high[i-LOOKBACK:i])
    if close[i] > recent_high:
        long_entries[i] = True
    
    # Short entry: Close breaks below recent low
    recent_low = np.min(low[i-LOOKBACK:i])
    if close[i] < recent_low:
        short_entries[i] = True
```

### **What NOT to Change**

❌ **Don't modify the exit logic section** - that's the stop loss/target method
❌ **Don't change the backtest setup** - VectorBT portfolio creation
❌ **Don't alter the results/visualization code**

✅ **Only replace the entry signal calculation and entry arrays**

---

## 📋 Template List

| # | File | Method | Description |
|---|------|--------|-------------|
| 01 | `01_no_stop.py` | No Stop Loss | Exit only on opposite signal |
| 02 | `02_fixed_percentage_stop.py` | Fixed % Stop | Fixed percentage from entry |
| 03 | `03_fixed_account_pct_stop.py` | Account % Stop | Based on account equity |
| 04 | `04_fixed_atr_stop.py` | Fixed ATR Stop | ATR multiplier from entry |
| 05 | `05_anchored_dollar_stop.py` | Dollar Stop | Fixed dollar amount |
| 06 | `06_atr_percentage_stop.py` | ATR % Stop | Percentage of ATR |
| 07 | `07_atr_target.py` | ATR Target | Profit target at ATR distance |
| 08 | `08_atr_breakeven.py` | ATR Breakeven | Move to breakeven at target |
| 09 | `09_atr_trailing.py` | ATR Trailing | Trail at ATR distance |
| 10 | `10_percentage_breakeven.py` | % Breakeven | Move to breakeven at % target |
| 11 | `11_trailing_percentage.py` | Trailing % | Trail at fixed percentage |
| 12 | `12_percentage_target.py` | % Target | Fixed percentage profit target |
| 13 | `13_sell_half_percentage.py` | Sell Half % | Partial exit at % target |
| 14 | `14_sell_half_breakeven.py` | Sell Half + BE | Partial exit + breakeven |
| 15 | `15_sell_half_atr.py` | Sell Half ATR | Partial exit at ATR target |
| 16 | `16_account_pct_target.py` | Account % Target | Exit at account % profit |
| 17 | `17_target_then_trail.py` | Target→Trail | Switch to trailing after target |
| 18 | `18_target_trail_atr.py` | ATR Target+Trail | Combined ATR method |
| 19 | `19_swing_stop.py` | Swing Stop | Based on swing highs/lows |
| 20 | `20_chandelier_stop.py` | Chandelier Stop | ATR volatility stop |
| 21 | `21_parabolic_sar.py` | Parabolic SAR | SAR trailing stop |
| 22 | `22_quantile_stop.py` | Quantile Stop | Dynamic quantile-based |

---

## ⚙️ Parameter Customization

### **Common Parameters (All Templates)**

```python
SYMBOL = 'BTC'              # Change to your symbol
INITIAL_CAPITAL = 100000    # Starting capital
FEES = 0.001                # 0.1% trading fees
SLIPPAGE = 0.001            # 0.1% slippage
```

### **RSI Entry Parameters (Default)**

```python
RSI_PERIOD = 14             # RSI calculation period
RSI_OVERBOUGHT = 70         # Overbought threshold
RSI_OVERSOLD = 30           # Oversold threshold
```

### **Stop/Target Parameters (Varies by Template)**

Each template has specific parameters. Examples:

**Fixed Percentage Stop:**
```python
STOP_LOSS_PCT = 0.10        # 10% stop loss
```

**ATR Trailing Stop:**
```python
ATR_PERIOD = 14             # ATR calculation period
ATR_MULTIPLIER = 2.5        # Stop at 2.5x ATR
```

**Sell Half + Breakeven:**
```python
TARGET_PCT = 0.15           # 15% target for partial exit
STOP_PCT = 0.05             # 5% initial stop
```

---

## 🎓 Best Practices

### **1. Match Stop Method to Strategy Type**

| Strategy Type | Recommended Stops |
|---------------|-------------------|
| Trend Following | ATR Trailing, Parabolic SAR |
| Mean Reversion | Fixed %, Profit Targets |
| Breakout | ATR Breakeven, Chandelier |
| Swing Trading | Swing Stop, % Trailing |

### **2. Backtest Multiple Methods**

Don't assume one method is best. Test 3-5 different stop methods on your data and compare:
- Risk-adjusted returns (Sharpe Ratio)
- Maximum drawdown
- Win rate vs. profit factor trade-off

### **3. Optimize Parameters**

Use VectorBT's optimization features to find optimal parameters:
```python
# Example: Optimize stop loss percentage
results = vbt.Portfolio.from_signals(
    close=df['Close'],
    entries=entries,
    exits=exits,
    init_cash=INITIAL_CAPITAL,
    fees=FEES,
    slippage=SLIPPAGE,
    freq='1D'
).optimize(
    stop_loss_pct=[0.05, 0.10, 0.15, 0.20],
    metric='sharpe_ratio'
)
```

### **4. Combine Methods**

Advanced traders can combine multiple stop methods:
- Initial stop: Fixed %
- After profit: Move to breakeven
- Final exit: Trailing stop

---

## 📖 Additional Resources

- **VectorBT Documentation**: https://vectorbt.dev/
- **Original Backtrader Strategies**: See `StopMethods.ipynb` (source file)
- **Main Repo README**: `../README.md`

---

## 🤝 Contributing

Found a bug or want to add a new stop method? 
- Open an issue on GitHub
- Submit a pull request
- Follow the existing template structure

---

## 📝 License

MIT License - See main repository for details

---

## ⚠️ Disclaimer

These templates are for educational purposes only. Past performance does not guarantee future results. Always test strategies thoroughly before live trading.

---

**Created**: January 2026  
**Version**: 1.0  
**Maintained by**: OBQ Trading Systems
