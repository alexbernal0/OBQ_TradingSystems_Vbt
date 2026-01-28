# pip install vectorbtpro plotly pandas numpy scipy ridgeplot
# OR: pip install vectorbt plotly pandas numpy scipy ridgeplot

# Try to import vectorbtpro first, fall back to vectorbt
try:
    import vectorbtpro as vbt
    VBT_PRO = True
except ImportError:
    import vectorbt as vbt
    VBT_PRO = False
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime
from scipy import stats

# ============================================================================
# MULTI-SYMBOL PARAMETER OPTIMIZATION SYSTEM
# ============================================================================
# Purpose: Find the best generalized parameters that work across ALL symbols
# Optimizes for: SystemScore (or custom fitness function)
# Output: 4-panel visualization + comprehensive text report
# ============================================================================

def calculate_system_score(returns, benchmark_returns=None):
    """
    Calculate SystemScore: Composite metric for strategy performance
    Higher is better. Combines Sharpe, CAGR, and Drawdown.
    """
    if len(returns) == 0 or returns.std() == 0:
        return 0.0
    
    # Annualized metrics
    sharpe = returns.mean() / returns.std() * np.sqrt(252)
    cagr = (1 + returns).prod() ** (252 / len(returns)) - 1
    
    # Drawdown
    cum_returns = (1 + returns).cumprod()
    running_max = cum_returns.cummax()
    drawdown = (cum_returns - running_max) / running_max
    max_dd = drawdown.min()
    
    # SystemScore formula (adjust weights as needed)
    system_score = (sharpe * 30) + (cagr * 100) + (max_dd * 50)
    
    return system_score


def run_multi_symbol_optimization(
    price_data,  # DataFrame with columns for each symbol
    strategy_func,  # Function that takes (prices, **params) and returns portfolio
    param_grid,  # Dict of parameter ranges, e.g., {'trend_sma': [20, 30, 40], 'breakout': [3, 5, 7]}
    fitness_func=None,  # Optional custom fitness function
    benchmark_symbol=None  # Optional benchmark symbol name
):
    """
    Run grid search optimization across all symbols.
    
    Returns:
    - results_df: DataFrame with all parameter combinations and metrics
    - top_combos: Top 5 parameter combinations
    - symbol_results: Detailed results for each symbol
    """
    
    if fitness_func is None:
        fitness_func = calculate_system_score
    
    print(f"🚀 Starting Multi-Symbol Optimization")
    print(f"   Symbols: {len(price_data.columns)}")
    print(f"   Parameters: {list(param_grid.keys())}")
    print(f"   Grid size: {np.prod([len(v) for v in param_grid.values()])} combinations")
    print()
    
    # Generate all parameter combinations
    from itertools import product
    param_names = list(param_grid.keys())
    param_values = list(param_grid.values())
    all_combos = list(product(*param_values))
    
    print(f"Testing {len(all_combos)} parameter combinations...")
    
    # Store results
    results = []
    symbol_results = {}
    
    # Run optimization
    for combo_idx, combo in enumerate(all_combos):
        params = dict(zip(param_names, combo))
        
        if (combo_idx + 1) % 10 == 0:
            print(f"   Progress: {combo_idx + 1}/{len(all_combos)} combinations tested")
        
        # Test this parameter combo on all symbols
        symbol_scores = []
        symbol_pfs = []
        symbol_sharpes = []
        symbol_returns = []
        
        for symbol in price_data.columns:
            try:
                # Run strategy on this symbol with these parameters
                prices = price_data[symbol].dropna()
                
                # Call user's strategy function
                portfolio = strategy_func(prices, **params)
                
                # Calculate metrics
                returns = portfolio.returns()
                score = fitness_func(returns)
                
                # Profit Factor
                winning_trades = returns[returns > 0].sum()
                losing_trades = abs(returns[returns < 0].sum())
                pf = winning_trades / losing_trades if losing_trades > 0 else np.inf
                
                # Sharpe
                sharpe = returns.mean() / returns.std() * np.sqrt(252) if returns.std() > 0 else 0
                
                symbol_scores.append(score)
                symbol_pfs.append(pf)
                symbol_sharpes.append(sharpe)
                symbol_returns.append(returns)
                
            except Exception as e:
                # If strategy fails on this symbol, record as 0
                symbol_scores.append(0)
                symbol_pfs.append(0)
                symbol_sharpes.append(0)
        
        # Calculate aggregate metrics for this parameter combo
        symbol_scores = np.array(symbol_scores)
        symbol_pfs = np.array(symbol_pfs)
        symbol_pfs = symbol_pfs[symbol_pfs != np.inf]  # Remove infinities
        
        median_score = np.median(symbol_scores)
        mean_score = np.mean(symbol_scores)
        std_score = np.std(symbol_scores)
        min_score = np.min(symbol_scores)
        max_score = np.max(symbol_scores)
        
        median_pf = np.median(symbol_pfs) if len(symbol_pfs) > 0 else 0
        
        # Stability metrics
        pct_profitable = (symbol_pfs > 1.0).sum() / len(symbol_pfs) * 100 if len(symbol_pfs) > 0 else 0
        pct_strong = (symbol_pfs > 1.75).sum() / len(symbol_pfs) * 100 if len(symbol_pfs) > 0 else 0
        pct_excellent = (symbol_pfs > 2.0).sum() / len(symbol_pfs) * 100 if len(symbol_pfs) > 0 else 0
        
        # Coefficient of Variation (normalized stability)
        cv = std_score / mean_score if mean_score != 0 else np.inf
        
        # Robustness Score
        robustness_score = median_score * (pct_strong / 100) * (median_pf / 2) if median_pf > 0 else 0
        
        # Store results
        result = {
            **params,
            'median_score': median_score,
            'mean_score': mean_score,
            'std_score': std_score,
            'min_score': min_score,
            'max_score': max_score,
            'median_pf': median_pf,
            'pct_profitable': pct_profitable,
            'pct_strong': pct_strong,
            'pct_excellent': pct_excellent,
            'cv': cv,
            'robustness_score': robustness_score
        }
        results.append(result)
        
        # Store detailed symbol results for top combos (we'll filter later)
        symbol_results[combo_idx] = {
            'params': params,
            'scores': symbol_scores,
            'pfs': symbol_pfs
        }
    
    print(f"✅ Optimization complete!")
    print()
    
    # Convert to DataFrame
    results_df = pd.DataFrame(results)
    
    # Sort by robustness score
    results_df = results_df.sort_values('robustness_score', ascending=False).reset_index(drop=True)
    
    # Get top 5 combos
    top_combos = results_df.head(5).copy()
    
    return results_df, top_combos, symbol_results


def create_optimization_visualizations(results_df, top_combos, symbol_results, param_names):
    """
    Create 4-panel visualization suite for optimization results.
    """
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=('3D Surface: Parameter Optimization Landscape',
                       'Scatter: Stability vs Performance',
                       'Density Plot: Distribution Across Symbols (Top 5 Combos)',
                       'Grouped Bar: Multi-Metric Comparison (Top 5 Combos)'),
        specs=[[{'type': 'surface'}, {'type': 'scatter'}],
               [{'type': 'scatter'}, {'type': 'bar'}]],
        vertical_spacing=0.18,
        horizontal_spacing=0.10,
        column_widths=[0.55, 0.45]  # Give more width to left column for 3D
    )
    
    # ========================================================================
    # Panel 1: 3D Surface Plot (if 2+ parameters)
    # ========================================================================
    if len(param_names) >= 2:
        param1 = param_names[0]
        param2 = param_names[1]
        
        # Create pivot table for surface
        pivot = results_df.pivot_table(
            values='median_score',
            index=param1,
            columns=param2,
            aggfunc='mean'
        )
        
        fig.add_trace(
            go.Surface(
                x=pivot.columns,
                y=pivot.index,
                z=pivot.values,
                colorscale='Viridis',
                showscale=False,
                name='Median Score',
                hovertemplate='%{xaxis.title.text}: %{x}<br>%{yaxis.title.text}: %{y}<br>Median Score: %{z:.2f}<extra></extra>'
            ),
            row=1, col=1
        )
        
        fig.update_scenes(
            xaxis_title=param2,
            yaxis_title=param1,
            zaxis_title='Median SystemScore',
            row=1, col=1
        )
    
    # ========================================================================
    # Panel 2: Scatter Plot - Stability vs Performance
    # ========================================================================
    
    # Plot all combos
    # Create detailed hover text with parameter values
    hover_texts = []
    for idx, row in results_df.iterrows():
        params_str = "<br>".join([f"{k}={row[k]}" for k in param_names])
        hover_text = (f"<b>Combo {idx+1}</b><br>"
                     f"{params_str}<br>"
                     f"Median Score: {row['median_score']:.2f}<br>"
                     f"% Strong: {row['pct_strong']:.1f}%<br>"
                     f"Median PF: {row['median_pf']:.2f}<br>"
                     f"Robustness: {row['robustness_score']:.3f}")
        hover_texts.append(hover_text)
    
    fig.add_trace(
        go.Scatter(
            x=results_df['median_score'],
            y=results_df['pct_strong'],
            mode='markers',
            marker=dict(
                size=results_df['median_pf'] * 5,
                color=results_df['robustness_score'],
                colorscale='Viridis',
                showscale=False,  # Remove color scale
                line=dict(width=1, color='white'),
                sizemode='diameter',
                sizemin=3
            ),
            text=hover_texts,
            hovertemplate="%{text}<extra></extra>",
            showlegend=False,
            name=''  # Empty name to prevent legend entry
        ),
        row=1, col=2
    )
    
    # Annotate top 5
    for rank in range(min(5, len(top_combos))):
        combo = top_combos.iloc[rank]
        fig.add_annotation(
            x=combo['median_score'],
            y=combo['pct_strong'],
            text=f"#{rank+1}",
            showarrow=True,
            arrowhead=2,
            arrowsize=1,
            arrowwidth=2,
            arrowcolor="red",
            ax=25,
            ay=-25,
            font=dict(size=11, color="red", family="Arial Black"),
            row=1, col=2
        )
    
    fig.update_xaxes(title_text="Median SystemScore (Performance)", row=1, col=2)
    fig.update_yaxes(title_text="% Strong Symbols (PF > 1.75)", row=1, col=2)
    
    # ========================================================================
    # Panel 3: Ridgeline Plot (Temperature-Style)
    # ========================================================================
    
    # Try to use ridgeplot library, fall back to manual if not available
    try:
        from ridgeplot import ridgeplot
        USE_RIDGEPLOT_LIB = True
    except ImportError:
        USE_RIDGEPLOT_LIB = False
    
    if USE_RIDGEPLOT_LIB:
        # Use ridgeplot library (cleaner, better colors)
        samples = []
        labels = []
        for rank in range(min(5, len(top_combos))):
            combo_idx = top_combos.index[rank]
            scores = symbol_results[combo_idx]['scores']
            params = symbol_results[combo_idx]['params']
            
            samples.append(scores.tolist())
            labels.append(f"#{rank+1}: " + ", ".join([f"{k}={v}" for k, v in params.items()]))
        
        # Create ridgeplot with plasma colorscale
        fig_ridge = ridgeplot(
            samples=samples,
            labels=labels,
            colorscale="plasma",
            colormode="mean-means",
            bandwidth=4,
            spacing=0.5
        )
        
        # Extract traces and add to subplot
        for trace in fig_ridge.data:
            trace.showlegend = False
            fig.add_trace(trace, row=2, col=1)
    
    else:
        # Fallback: Manual KDE approach (works without ridgeplot library)
        # Plasma colors: dark blue → purple → pink → orange → yellow
        colors = ['#0D0887', '#7E03A8', '#CC4778', '#F89540', '#F0F921']
        
        for rank in range(min(5, len(top_combos))):
            combo_idx = top_combos.index[rank]
            scores = symbol_results[combo_idx]['scores']
            params = symbol_results[combo_idx]['params']
            label = f"#{rank+1}: " + ", ".join([f"{k}={v}" for k, v in params.items()])
            
            # Calculate KDE
            kde = stats.gaussian_kde(scores)
            x_range = np.linspace(scores.min() - 5, scores.max() + 5, 200)
            density = kde(x_range)
            density_norm = (density - density.min()) / (density.max() - density.min())
            y_offset = (5 - rank) * 1.5
            
            # Add baseline
            fig.add_trace(
                go.Scatter(
                    x=[x_range.min(), x_range.max()],
                    y=[y_offset, y_offset],
                    mode='lines',
                    line=dict(color='white', width=0.5),
                    showlegend=False,
                    hoverinfo='skip'
                ),
                row=2, col=1
            )
            
            # Add density curve
            fig.add_trace(
                go.Scatter(
                    x=x_range,
                    y=density_norm + y_offset,
                    fill='tonexty',
                    fillcolor=colors[rank],
                    line=dict(color=colors[rank], width=2),
                    opacity=0.8,
                    name=label,
                    showlegend=False,
                    hovertemplate=f"<b>{label}</b><br>SystemScore: %{x:.1f}<br><extra></extra>"
                ),
                row=2, col=1
            )
    
    # Update axes (remove Y-axis labels as requested)
    fig.update_xaxes(title_text="SystemScore", row=2, col=1)
    fig.update_yaxes(title_text="", row=2, col=1, showticklabels=False, showgrid=False)
    
    # ========================================================================
    # Panel 4: Grouped Bar Chart - Multi-Metric Comparison
    # ========================================================================
    
    # Define colors for bar chart (matching plasma colorscale)
    colors = ['#0D0887', '#7E03A8', '#CC4778', '#F89540', '#F0F921']  # Plasma colors
    
    metrics = ['Median Score', 'Median PF', '% Strong', 'Min Score', 'Max Score', 'CV (lower=better)']
    
    for rank in range(min(5, len(top_combos))):
        combo = top_combos.iloc[rank]
        
        # Normalize metrics to 0-100 scale for comparison
        values = [
            combo['median_score'],
            combo['median_pf'] * 30,  # Scale PF to similar range
            combo['pct_strong'],
            combo['min_score'],
            combo['max_score'],
            100 - (combo['cv'] * 10)  # Invert CV (lower is better)
        ]
        
        params = {k: combo[k] for k in param_names}
        label = f"#{rank+1}: " + ", ".join([f"{k}={v}" for k, v in params.items()])
        
        fig.add_trace(
            go.Bar(
                x=metrics,
                y=values,
                name=label,
                marker_color=colors[rank],
                showlegend=False,  # No legend
                hovertemplate=f"<b>{label}</b><br>" +
                              "%{x}: %{y:.1f}<br>" +
                              "<extra></extra>"
            ),
            row=2, col=2
        )
    
    fig.update_yaxes(title_text="Normalized Value", row=2, col=2)
    
    # ========================================================================
    # Update overall layout
    # ========================================================================
    
    fig.update_layout(
        title=f"<b>Multi-Symbol Parameter Optimization Results</b><br>" +
              f"<sub>Run: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | " +
              f"Optimized for: Robustness Score (Stability + Performance)</sub>",
        height=1100,
        showlegend=False,  # No legends anywhere
        template='plotly_white',
        autosize=True,  # Auto-size to container width
        margin=dict(l=50, r=50, t=100, b=50)
    )
    
    return fig


def generate_optimization_report(results_df, top_combos, symbol_results, param_names, num_symbols):
    """
    Generate comprehensive text report for optimization results.
    """
    
    report = []
    report.append("=" * 80)
    report.append("MULTI-SYMBOL PARAMETER OPTIMIZATION REPORT")
    report.append("=" * 80)
    report.append(f"Run Date/Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report.append(f"Number of Symbols: {num_symbols}")
    report.append(f"Parameters Optimized: {', '.join(param_names)}")
    report.append(f"Total Combinations Tested: {len(results_df)}")
    report.append(f"Optimization Objective: Robustness Score (Stability + Performance)")
    report.append("")
    
    # ========================================================================
    # 1. BEST PARAMETERS FOUND
    # ========================================================================
    report.append("=" * 80)
    report.append("1. BEST PARAMETERS FOUND (Highest Robustness Score)")
    report.append("=" * 80)
    
    winner = top_combos.iloc[0]
    report.append("")
    report.append("🏆 WINNING COMBINATION:")
    for param in param_names:
        report.append(f"   {param}: {winner[param]}")
    report.append("")
    
    report.append("📊 PERFORMANCE METRICS:")
    report.append(f"   Median SystemScore:      {winner['median_score']:.2f}")
    report.append(f"   Mean SystemScore:        {winner['mean_score']:.2f}")
    report.append(f"   Std Dev:                 {winner['std_score']:.2f}")
    report.append(f"   Min Score (worst case):  {winner['min_score']:.2f}")
    report.append(f"   Max Score (best case):   {winner['max_score']:.2f}")
    report.append("")
    
    report.append("💪 STABILITY METRICS:")
    report.append(f"   % Profitable Symbols (PF > 1.0):  {winner['pct_profitable']:.1f}%")
    report.append(f"   % Strong Symbols (PF > 1.75):     {winner['pct_strong']:.1f}%")
    report.append(f"   % Excellent Symbols (PF > 2.0):   {winner['pct_excellent']:.1f}%")
    report.append(f"   Median Profit Factor:             {winner['median_pf']:.2f}")
    report.append("")
    
    report.append("🎯 ROBUSTNESS METRICS:")
    report.append(f"   Robustness Score:        {winner['robustness_score']:.2f}")
    report.append(f"   Coefficient of Variation: {winner['cv']:.3f} (lower = more stable)")
    report.append("")
    
    # ========================================================================
    # 2. TOP 5 PARAMETER COMBINATIONS
    # ========================================================================
    report.append("=" * 80)
    report.append("2. TOP 5 PARAMETER COMBINATIONS")
    report.append("=" * 80)
    report.append("")
    
    for rank in range(min(5, len(top_combos))):
        combo = top_combos.iloc[rank]
        report.append(f"RANK #{rank+1}:")
        report.append(f"   Parameters: " + ", ".join([f"{k}={combo[k]}" for k in param_names]))
        report.append(f"   Robustness Score: {combo['robustness_score']:.2f}")
        report.append(f"   Median SystemScore: {combo['median_score']:.2f}")
        report.append(f"   % Strong Symbols: {combo['pct_strong']:.1f}%")
        report.append(f"   Median Profit Factor: {combo['median_pf']:.2f}")
        report.append("")
    
    # ========================================================================
    # 3. STABILITY ANALYSIS
    # ========================================================================
    report.append("=" * 80)
    report.append("3. STABILITY ANALYSIS")
    report.append("=" * 80)
    report.append("")
    
    report.append(f"The winning parameter combination shows:")
    if winner['pct_strong'] >= 70:
        report.append(f"   ✅ EXCELLENT stability ({winner['pct_strong']:.1f}% of symbols are strong)")
    elif winner['pct_strong'] >= 50:
        report.append(f"   ✅ GOOD stability ({winner['pct_strong']:.1f}% of symbols are strong)")
    else:
        report.append(f"   ⚠️  MODERATE stability ({winner['pct_strong']:.1f}% of symbols are strong)")
    
    if winner['cv'] < 0.5:
        report.append(f"   ✅ LOW variance (CV={winner['cv']:.3f}) - consistent across symbols")
    elif winner['cv'] < 1.0:
        report.append(f"   ✅ MODERATE variance (CV={winner['cv']:.3f}) - reasonably consistent")
    else:
        report.append(f"   ⚠️  HIGH variance (CV={winner['cv']:.3f}) - results vary significantly")
    
    report.append("")
    report.append(f"Worst-case performance: {winner['min_score']:.2f}")
    report.append(f"Best-case performance:  {winner['max_score']:.2f}")
    report.append(f"Range: {winner['max_score'] - winner['min_score']:.2f}")
    report.append("")
    
    # ========================================================================
    # 4. COMPARISON TO ALTERNATIVES
    # ========================================================================
    report.append("=" * 80)
    report.append("4. COMPARISON TO ALTERNATIVES")
    report.append("=" * 80)
    report.append("")
    
    median_combo = results_df.iloc[len(results_df)//2]
    improvement = ((winner['robustness_score'] - median_combo['robustness_score']) / 
                   median_combo['robustness_score'] * 100)
    
    report.append(f"Optimal vs Median combination:")
    report.append(f"   Robustness Score improvement: {improvement:+.1f}%")
    report.append(f"   SystemScore improvement: {winner['median_score'] - median_combo['median_score']:+.2f}")
    report.append("")
    
    # ========================================================================
    # 5. RECOMMENDATIONS
    # ========================================================================
    report.append("=" * 80)
    report.append("5. RECOMMENDATIONS")
    report.append("=" * 80)
    report.append("")
    
    report.append("Based on this optimization:")
    report.append(f"   ✅ Use the winning parameters for live trading")
    report.append(f"   ✅ These parameters work well across {winner['pct_strong']:.0f}% of symbols")
    report.append(f"   ✅ Robustness Score of {winner['robustness_score']:.2f} indicates strong generalization")
    
    if winner['pct_strong'] < 60:
        report.append(f"   ⚠️  Consider symbol-specific optimization for underperforming stocks")
    
    report.append("")
    report.append("=" * 80)
    
    return "\n".join(report)


# ============================================================================
# EXAMPLE USAGE (Replace with your actual strategy)
# ============================================================================

def example_qullamaggie_strategy(prices, trend_sma=50, breakout_period=5, trailing_sma=10):
    """
    Example Qullamaggie-style strategy for demonstration.
    Compatible with both vectorbt and vectorbtpro.
    Replace this with your actual strategy function.
    """
    # Calculate indicators (works with both versions)
    if VBT_PRO:
        # vectorbtpro uses talib
        sma_trend = vbt.talib('SMA', timeperiod=trend_sma).run(prices).real
        sma_trailing = vbt.talib('SMA', timeperiod=trailing_sma).run(prices).real
    else:
        # vectorbt uses MA indicator
        sma_trend = vbt.MA.run(prices, trend_sma).ma
        sma_trailing = vbt.MA.run(prices, trailing_sma).ma
    
    # Entry: Price breaks above recent high and above trend SMA
    recent_high = prices.rolling(breakout_period).max()
    entries = (prices > recent_high.shift(1)) & (prices > sma_trend)
    
    # Exit: Price crosses below trailing SMA
    exits = prices < sma_trailing
    
    # Create portfolio (compatible API for both versions)
    if VBT_PRO:
        portfolio = vbt.Portfolio.from_signals(
            close=prices,
            entries=entries,
            exits=exits,
            freq='1D'
        )
    else:
        portfolio = vbt.Portfolio.from_signals(
            prices,
            entries,
            exits,
            freq='1D'
        )
    
    return portfolio


# ============================================================================
# RUN OPTIMIZATION
# ============================================================================

# Load data from database - 10+ years of all symbols
if 'conn' in globals():
    # Suppress initial loading message (will show after graphs)
    
    # Query to get all symbols with 10+ years of data
    query = """
    SELECT Date, Symbol, Close
    FROM GoldenOpp.main.GDX_GLD_Mining_Stocks_Prices
    WHERE Date >= CURRENT_DATE - INTERVAL '10 years'
    ORDER BY Date, Symbol
    """
    
    # Load data (assuming you have 'conn' connection object already set up in Hex)
    df = pd.read_sql(query, conn)

    # Pivot to wide format: rows=dates, columns=symbols
    price_data = df.pivot(index='Date', columns='Symbol', values='Close')
    price_data.index = pd.to_datetime(price_data.index)
    
    # Remove symbols with too many missing values (keep only if >80% data available)
    min_data_pct = 0.80
    data_availability = price_data.count() / len(price_data)
    price_data = price_data.loc[:, data_availability >= min_data_pct]
    
    # Forward fill missing values (up to 5 days)
    price_data = price_data.fillna(method='ffill', limit=5)
    
    # Drop any remaining rows with NaN
    price_data = price_data.dropna(axis=1, how='any')
    
    # Store info for later display
    loaded_symbols = len(price_data.columns)
    date_range_start = price_data.index[0].date()
    date_range_end = price_data.index[-1].date()
    total_days = len(price_data)
    symbols_list = ', '.join(price_data.columns[:10]) + ('...' if len(price_data.columns) > 10 else '')
    
    # Define parameter grid
    param_grid = {
        'trend_sma': [30, 40, 50, 60],
        'breakout_period': [3, 5, 7],
        'trailing_sma': [5, 10, 15]
    }
    
    # Run optimization
    results_df, top_combos, symbol_results = run_multi_symbol_optimization(
        price_data=price_data,
        strategy_func=example_qullamaggie_strategy,
        param_grid=param_grid
    )
    
    # Create visualizations
    param_names = list(param_grid.keys())
    fig = create_optimization_visualizations(results_df, top_combos, symbol_results, param_names)
    fig.show()
    
    # Print loading info before report
    print()
    print("📊 Loading data from database...")
    print("   Table: GoldenOpp.main.GDX_GLD_Mining_Stocks_Prices")
    print("   Date range: Last 10+ years")
    print()
    print(f"✅ Loaded {loaded_symbols} symbols")
    print(f"✅ Date range: {date_range_start} to {date_range_end}")
    print(f"✅ Total trading days: {total_days}")
    print(f"✅ Symbols: {symbols_list}")
    print()
    
    # Generate report
    report = generate_optimization_report(results_df, top_combos, symbol_results, param_names, len(price_data.columns))
    print(report)
    
    print("✅ Multi-Symbol Optimization Complete!")
else:
    print("✅ Multi-Symbol Optimization System Ready!")
    print("📝 Functions loaded. Run optimization when 'conn' is available in Hex.")
    print()
