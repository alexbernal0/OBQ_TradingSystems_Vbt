# Multi-Symbol Parameter Optimization System - Design Proposal

## Overview

A comprehensive template for optimizing trading strategy parameters across all symbols in the database, finding the **best generalized parameters** that work well across the entire universe of stocks and ETFs.

---

## System Architecture

### Input Parameters
- **Strategy Function**: Any strategy with configurable parameters
- **Parameter Ranges**: Grid search ranges for each parameter
  - Example: `trend_sma: [20, 30, 40, 50, 60]`
  - Example: `breakout_period: [3, 5, 7, 10]`
  - Example: `trailing_sma: [5, 10, 15, 20]`
- **Fitness Function**: Default to **SystemScore** (optimizable to other metrics)
- **Symbol Universe**: All symbols in `GDX_GLD_Mining_Stocks_Prices` table (59 symbols)

### Optimization Process
1. **Grid Search**: Test all parameter combinations across all symbols
2. **Aggregate Metrics**: For each parameter combo, calculate:
   - Mean SystemScore across all symbols
   - Median SystemScore (more robust to outliers)
   - Std Dev of SystemScore (measures stability)
   - % of symbols with positive returns
   - % of symbols with SystemScore > threshold
   - Worst symbol performance (robustness check)
   - Best symbol performance (upside potential)
3. **Rank Combinations**: Sort by aggregate fitness function
4. **Select Winner**: Best parameter combo that generalizes across all symbols

### Output Components

#### 1. Text Report
- **Optimization Summary**: Process description, parameters tested, symbols included
- **Best Parameters**: Winning combination with detailed statistics
- **Stability Analysis**: How consistent are results across symbols?
- **Symbol-Level Breakdown**: Which symbols work best/worst with optimal parameters
- **Robustness Metrics**: Performance in different market conditions
- **Comparison to Alternatives**: How much better is optimal vs. other combos?

#### 2. Visualization Suite (2x2 Grid)

Based on Plotly research, I propose these 4 visualizations:

---

### **Panel 1: 3D Surface Plot or Heatmap** (Parameter Space Visualization)

**If 3 parameters**: Use **3D Surface Plot**
- X-axis: Parameter 1 (e.g., trend_sma)
- Y-axis: Parameter 2 (e.g., breakout_period)
- Z-axis: Mean SystemScore
- Color: SystemScore value
- Shows optimization landscape in 3D
- Interactive rotation to explore from different angles
- Peak = optimal parameter combination

**If 2 parameters**: Use **2D Heatmap**
- X-axis: Parameter 1
- Y-axis: Parameter 2
- Color: Mean SystemScore
- Annotated with values
- Clear visual of "hot spots" (best regions)

**If 4+ parameters**: Use **Contour Plot** showing top 2 most important parameters

---

### **Panel 2: Parallel Coordinates Plot** (Multi-Dimensional Parameter Explorer)

**Why this is PERFECT for optimization**:
- Shows ALL parameters and metrics simultaneously
- Each line = one parameter combination tested
- Color-coded by SystemScore (dark = bad, bright = good)
- **Interactive filtering**: User can drag to filter parameter ranges
- **Interactive rearranging**: Drag axes to reorder
- Shows correlations between parameters and outcomes

**Axes (left to right)**:
1. Trend SMA
2. Breakout Period
3. Trailing SMA
4. Mean SystemScore
5. Sharpe Ratio
6. Win Rate %
7. Max Drawdown %
8. % Profitable Symbols

**Benefits**:
- See which parameter ranges consistently produce good results
- Identify parameter interactions (e.g., high trend_sma + low breakout works well)
- Filter to see only top 10% performers
- Scientific AND visually striking

---

### **Panel 3: Violin Plot with Box Plot Overlay** (Stability Analysis)

**Shows distribution of SystemScore across all symbols for top 5 parameter combinations**

- X-axis: Parameter combinations (labeled)
- Y-axis: SystemScore
- Violin: Full distribution shape (shows if results are bimodal, skewed, etc.)
- Box plot overlay: Shows median, quartiles, outliers
- Color-coded by parameter combo

**Why this matters**:
- A parameter combo with high mean but huge variance = risky (works great for some, terrible for others)
- A parameter combo with slightly lower mean but tight distribution = stable (works consistently)
- Shows outliers (which symbols are extreme performers)
- Balances scientific rigor with visual appeal

---

### **Panel 4: Grouped Bar Chart** (Multi-Metric Comparison)

**Compares top 5 parameter combinations across 6 key metrics**

- X-axis: 6 metrics (SystemScore, Sharpe, CAGR, Win Rate, Max DD, % Profitable Symbols)
- Y-axis: Metric value (normalized to 0-100 scale for comparison)
- Bars: Grouped by parameter combination (5 groups, 6 bars each)
- Color-coded by parameter combo (consistent with Panel 3)

**Alternative**: **Radar Chart** (Spider Chart)
- Each parameter combo = one polygon
- 6-8 axes radiating from center (one per metric)
- Shows which combo is "best all-around"
- Visually striking and easy to compare shapes

**Why this matters**:
- SystemScore might be highest for Combo A, but Combo B has better Sharpe and lower drawdown
- Shows trade-offs between metrics
- Helps user decide if they want to optimize for different goals

---

## Additional Visualizations (Optional Enhancements)

### 5. Symbol Performance Heatmap
- Rows: Symbols (59 stocks/ETFs)
- Columns: Top 5 parameter combinations
- Color: SystemScore for that symbol with those parameters
- Shows which symbols are "easy" (work with any parameters) vs "hard" (sensitive to parameters)

### 6. Parameter Sensitivity Analysis
- Line chart showing how each metric changes as you vary ONE parameter while holding others constant
- Helps understand which parameters matter most

### 7. Scatter Plot Matrix (SPLOM)
- Shows pairwise relationships between all parameters and SystemScore
- Identifies correlations and non-linear relationships

---

## Proposed 2x2 Grid Layout

```
┌─────────────────────────────┬─────────────────────────────┐
│                             │                             │
│  Panel 1: 3D Surface Plot   │  Panel 2: Parallel Coords   │
│  (Parameter Space)          │  (Multi-Dimensional)        │
│                             │                             │
│  Shows optimization         │  Shows ALL parameters       │
│  landscape with peak        │  and metrics with           │
│                             │  interactive filtering      │
│                             │                             │
├─────────────────────────────┼─────────────────────────────┤
│                             │                             │
│  Panel 3: Violin + Box Plot │  Panel 4: Grouped Bar Chart │
│  (Stability Analysis)       │  (Multi-Metric Comparison)  │
│                             │                             │
│  Shows distribution of      │  Compares top 5 combos      │
│  results across symbols     │  across 6 key metrics       │
│  for top 5 combos           │                             │
│                             │                             │
└─────────────────────────────┴─────────────────────────────┘
```

---

## Why This Visualization Suite Works

### Scientific Rigor ✅
- **3D Surface/Heatmap**: Standard in optimization literature
- **Parallel Coordinates**: Used in multi-objective optimization research
- **Violin Plots**: Statistical best practice for distribution comparison
- **Multi-Metric Comparison**: Essential for understanding trade-offs

### Visual Appeal ✅
- **3D Surface**: Stunning, interactive, easy to understand
- **Parallel Coordinates**: Colorful, modern, impressive
- **Violin Plots**: Beautiful curves, more interesting than box plots alone
- **Grouped Bars/Radar**: Clean, professional, easy to compare

### Interactivity ✅
- All Plotly charts are fully interactive
- Hover for details
- Zoom, pan, rotate (3D)
- Filter and rearrange (parallel coordinates)
- Download as PNG

### Information Density ✅
- Each panel tells a different story
- Together they provide complete picture:
  1. Where is the optimum? (Panel 1)
  2. How do parameters interact? (Panel 2)
  3. How stable are results? (Panel 3)
  4. What are the trade-offs? (Panel 4)

---

## Implementation Plan

### Phase 1: Build Optimization Engine
- Grid search across all parameter combinations
- Run backtest for each combo on each symbol
- Aggregate results into summary DataFrame

### Phase 2: Create Visualization Functions
- Function for 3D surface plot
- Function for parallel coordinates
- Function for violin plots
- Function for grouped bar chart
- Combine into 2x2 subplot

### Phase 3: Generate Text Report
- Template for optimization summary
- Statistical analysis of results
- Symbol-level breakdown
- Robustness analysis

### Phase 4: Package as Reusable Template
- Modular functions
- Easy to adapt for any strategy
- Clear documentation
- Example usage with Qullamaggie strategy

---

## Alternative Visualization Options

If you prefer different charts for any panel:

### Panel 1 Alternatives:
- Contour plot with filled contours
- 2D heatmap with annotations
- Scatter plot (if continuous parameters)

### Panel 2 Alternatives:
- Scatterplot matrix (SPLOM) - shows pairwise relationships
- Facet grid - small multiples of scatter plots

### Panel 3 Alternatives:
- Box plots only (simpler)
- Strip chart with jitter (shows individual points)
- Histogram grid (one per combo)

### Panel 4 Alternatives:
- Radar chart (spider chart) - visually striking
- Stacked bar chart
- Bullet chart (for target comparison)

---

## Next Steps

1. **Get your approval** on this visualization suite
2. **Build the optimization engine** with grid search
3. **Create the 4 visualization functions**
4. **Test with Qullamaggie strategy** on GLD data
5. **Generate sample output** for your review
6. **Refine and finalize** the template

---

## Questions for You

1. Do you approve this 2x2 grid layout?
2. Any preferences for Panel 4: Grouped Bar Chart vs Radar Chart?
3. Should we include the optional Symbol Performance Heatmap as a 5th visualization?
4. Any other metrics you want to see in the parallel coordinates or bar chart?
5. Should optimization prioritize:
   - Highest mean SystemScore?
   - Most stable (lowest variance)?
   - Best worst-case (highest minimum)?
   - Balanced (weighted combination)?

Let me know your thoughts and I'll start building!
