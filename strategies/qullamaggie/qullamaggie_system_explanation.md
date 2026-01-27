# Qullamaggie Breakout System - Plain English Explanation

## Overview

The **Qullamaggie Breakout System** is a trend-following trading strategy designed to capture momentum moves by entering on breakouts while the stock is in a longer-term uptrend. The system was created by trader Kristjan Kullamägi (known as Qullamaggie) and focuses on buying strength in stocks that are already trending upward.

## Core Philosophy

The fundamental idea behind this system is simple: **buy breakouts with tight stops in the direction of the longer-term trend**. This means you're looking for stocks that are already in an uptrend on a larger timeframe (like the daily chart), and then you enter when the price breaks out to new highs on a smaller timeframe (like the 1-hour or 30-minute chart).

## How the System Works

### 1. **Trend Filter (The Big Picture)**

Before considering any trade, the system first checks if the stock is in a longer-term uptrend. By default, it uses the **daily timeframe** to determine this, but you can customize it to any timeframe you prefer.

The system uses **Simple Moving Averages (SMAs)** as trend filters:
- **10-period SMA** (fast moving average)
- **20-period SMA** (medium moving average)  
- **50-period SMA** (slow moving average)

The key rule is: **only take trades when the price is above the slowest moving average** (typically the 50 SMA on the daily chart). This ensures you're trading in the direction of the established trend and not trying to catch falling knives.

### 2. **Entry Signal (The Breakout)**

Once the trend filter confirms an uptrend, the system looks for a **breakout** on a smaller timeframe. A breakout occurs when the price moves above the highest high of the last several bars (the "lookback period," which defaults to 5 bars).

Think of this as the price breaking through a recent resistance level. When price pushes above this level, it signals that buyers are in control and momentum is building.

### 3. **Stop Loss Placement (Risk Management)**

Risk management is critical in this system. When you enter a trade, the system places a **tight stop loss** at the lowest low of the last several bars (again, typically 5 bars back). This is called the "initial stop placement."

The idea is to risk a small amount on each trade. If the breakout fails and price drops back below recent lows, you exit quickly with a small loss. This tight stop allows you to take multiple attempts at catching a big winner without risking too much capital on any single trade.

### 4. **Exit Strategy (Trailing Stop)**

This is where the system gets interesting. Instead of using a fixed profit target, the system uses a **trailing stop** based on the moving averages from the larger timeframe (daily chart).

Here's how it works:

- Once you're in a profitable position (price is above the moving average), the system trails your stop using either the **10 SMA or 20 SMA** (your choice) on the daily timeframe.
- As long as the daily candle closes **above** your chosen moving average, you stay in the trade.
- If the daily candle closes **below** your chosen moving average, you exit the position.

This approach allows you to ride strong trends for as long as they last, while automatically exiting when the momentum starts to fade. The moving average acts as a dynamic support level that moves up with the price.

### 5. **Optional ATR Filter (Quality Control)**

The system includes an optional feature using the **Average True Range (ATR)**, which measures volatility. The ATR filter helps you identify stocks that are in **contracting ranges** (consolidating) before the breakout.

Here's the logic: if the difference between your breakout point and your stop loss is below a certain percentage of the daily ATR, it suggests the stock has been consolidating (low volatility). These tight consolidations often lead to explosive breakouts with favorable risk/reward ratios.

This filter helps you avoid chasing stocks that have already made big moves and ensures you're entering at the beginning of a potential momentum surge.

## Key Advantages

1. **Trend Alignment**: You're always trading with the bigger trend, which significantly improves your win rate and profit potential.

2. **Tight Risk Control**: The tight initial stop means you can afford to be wrong many times while waiting for the big winners.

3. **Let Winners Run**: The trailing stop based on moving averages allows you to capture large moves without trying to predict exact tops.

4. **Objective Rules**: The system provides clear, mechanical rules for entry, exit, and risk management, reducing emotional decision-making.

## Potential Challenges

The creator acknowledges one weakness: **whipsaw near the moving averages**. When you enter a trade and the price is very close to the daily moving averages, you can get stopped out quickly as price bounces around those levels. This is a known limitation of using moving averages as trailing stops, but it's a trade-off for the ability to catch and ride strong trends.

## Summary in Simple Terms

Imagine you're trying to catch a wave while surfing. The Qullamaggie system works like this:

1. **First, you check if the ocean has good waves** (is the stock in an uptrend on the daily chart?)
2. **Then you wait for a specific wave to form** (price breaks above recent highs)
3. **You paddle and catch the wave with a safety leash** (enter with a tight stop loss)
4. **You ride the wave as long as it's strong** (trail your stop with the moving average)
5. **When the wave loses power, you bail out** (exit when price closes below the moving average)

The system is designed for **swing trading** stocks that are in strong uptrends, allowing you to capture multi-day or multi-week momentum moves while keeping your risk tight on each individual trade.
