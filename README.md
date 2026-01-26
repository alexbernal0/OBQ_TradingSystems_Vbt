# OBQ Trading Systems with VectorBT

A professional, scalable framework for developing, backtesting, and analyzing systematic trading strategies using VectorBT. Optimized for Hex.tech notebook environments with comprehensive helper functions, performance reporting, and knowledge base.

## 🎯 Project Overview

This repository provides a complete infrastructure for quantitative trading system development with a focus on:

- **Speed**: Leveraging VectorBT's vectorized architecture for 1000x faster backtesting
- **Scalability**: Multi-symbol, multi-strategy testing across decades of data
- **Reproducibility**: Standardized templates, helpers, and workflows
- **Hex.tech Integration**: Optimized for notebook-based development and reporting

## 🚀 Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/YOUR_USERNAME/OBQ_TradingSystems_Vbt.git
cd OBQ_TradingSystems_Vbt

# Install dependencies
pip install -r requirements.txt

# For Hex.tech environments
pip install -r requirements_hex.txt
```

### Basic Usage

```python
import vectorbt as vbt
from src.data.loaders import load_from_motherduck
from src.data.transformers import pivot_to_wide_format

# Load data
df = load_from_motherduck("GoldenOpp.GDX_GLD_Mining_Stocks_Prices")

# Transform to VectorBT format
close_prices = pivot_to_wide_format(df, 'Close')

# Run a simple backtest
fast_ma = vbt.MA.run(close_prices, 10)
slow_ma = vbt.MA.run(close_prices, 50)

entries = fast_ma.ma_crossed_above(slow_ma)
exits = fast_ma.ma_crossed_below(slow_ma)

pf = vbt.Portfolio.from_signals(close_prices, entries, exits, init_cash=100000)
print(pf.stats())
```

## 📁 Repository Structure

```
OBQ_TradingSystems_Vbt/
├── src/                      # Core library code
│   ├── data/                 # Data loading and transformation
│   ├── indicators/           # Custom indicators
│   ├── signals/              # Entry/exit signal generation
│   ├── portfolio/            # Position sizing and risk management
│   ├── performance/          # Metrics, tables, and tearsheets
│   ├── backtesting/          # Backtesting engine and optimization
│   └── utils/                # Helper functions
│
├── strategies/               # Trading strategy implementations
│   ├── qullamaggie/          # Qullamaggie trend-following system
│   └── template/             # Template for new strategies
│
├── VectorBT_Knowledge/       # Comprehensive VectorBT documentation
│   ├── fundamentals/         # Architecture and concepts
│   ├── data/                 # Data preparation guides
│   ├── signals/              # Signal generation patterns
│   ├── portfolio/            # Portfolio construction
│   ├── performance/          # Performance analysis
│   ├── optimization/         # Parameter optimization
│   └── troubleshooting/      # Common issues and solutions
│
├── notebooks/                # Jupyter notebooks
│   ├── examples/             # Educational examples
│   ├── research/             # Exploratory analysis
│   └── hex_templates/        # Hex.tech specific templates
│
├── config/                   # Configuration files
├── data/                     # Data storage (gitignored)
├── tests/                    # Unit and integration tests
└── docs/                     # Additional documentation
```

## 🎓 Learning Resources

### For Beginners

1. **[Getting Started Guide](docs/getting_started.md)** - Installation and first backtest
2. **[Data Preparation](VectorBT_Knowledge/data/01_data_preparation.md)** - Understanding data formats
3. **[Basic Backtest Example](notebooks/examples/03_basic_backtest.ipynb)** - Step-by-step walkthrough

### For Intermediate Users

4. **[Signal Generation Patterns](VectorBT_Knowledge/signals/01_signal_generation.md)** - Creating entry/exit rules
5. **[Custom Indicators](notebooks/examples/04_custom_indicators.ipynb)** - Building your own indicators
6. **[Performance Analysis](VectorBT_Knowledge/performance/01_performance_analysis.md)** - Interpreting results

### For Advanced Users

7. **[Parameter Optimization](VectorBT_Knowledge/optimization/01_parameter_optimization.md)** - Grid search techniques
8. **[Walk-Forward Analysis](notebooks/examples/08_walk_forward.ipynb)** - Out-of-sample testing
9. **[VectorBT Research Report](docs/vectorbt_research_report.md)** - Deep dive into architecture

## 🔧 Hex.tech Setup

This repository is optimized for Hex.tech notebook environments. See [Hex Setup Guide](config/hex_setup.md) for detailed instructions.

**Key Features for Hex.tech:**
- Built-in MotherDuck integration
- Plotly-based interactive visualizations
- Modular cell structure for imports
- Caching strategies for expensive operations

## 📊 Current Strategies

### Qullamaggie Trend System

A momentum-based breakout strategy with tight stops and trailing exits. See [strategy documentation](strategies/qullamaggie/README.md) for details.

**Key Features:**
- Daily trend filter (50 SMA)
- 5-bar breakout entries
- SMA-based trailing stops
- Tested on 56 gold mining stocks + 4 ETFs
- 53 years of survivorship-bias-free data

## 🧪 Testing

```bash
# Run all tests
pytest tests/

# Run with coverage
pytest --cov=src tests/

# Run specific test file
pytest tests/test_data_loaders.py
```

## 📈 Performance Reporting

The repository includes comprehensive performance reporting adapted from industry-standard tearsheet templates:

- **60+ performance metrics** (Sharpe, Sortino, Calmar, etc.)
- **Visualization suite** (equity curves, drawdowns, heatmaps)
- **Benchmark comparisons**
- **Monthly/yearly return tables**
- **Trade analysis**

See [Performance Module](src/performance/README.md) for details.

## 🤝 Contributing

We welcome contributions! Please see [Contributing Guidelines](docs/contributing.md) for details on:

- Code style and standards
- Testing requirements
- Documentation expectations
- Pull request process

## 📝 Branch Strategy

- **main**: Core infrastructure and shared components
- **strategy/qullamaggie**: Qullamaggie trend system
- **strategy/[name]**: Additional strategies (separate branches)
- **feature/[name]**: New features or enhancements
- **fix/[name]**: Bug fixes

## 🔗 Related Projects

- **GoldenOpp Database**: Survivorship-bias-free gold mining stock data (MotherDuck)
- **VectorBT**: High-performance backtesting library ([vectorbt.dev](https://vectorbt.dev))
- **Hex.tech**: Collaborative data workspace ([hex.tech](https://hex.tech))

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

## 📧 Contact

**Obsidian Quantitative**  
Email: ben@obsidianquantitative.com  
Project maintained by: OBQ Trading Systems Team

## 🙏 Acknowledgments

- **Kristjan Kullamägi (Qullamaggie)** - Original trading system methodology
- **VectorBT Team** - Exceptional backtesting framework
- **MotherDuck** - Cloud-native data warehouse
- **Manus AI** - Repository structure and documentation assistance

---

**Built with ❤️ for systematic traders who value speed, reproducibility, and rigor.**
