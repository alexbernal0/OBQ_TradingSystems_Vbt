# OBQ Trading Systems - VectorBT Framework

This repository provides a professional, production-ready framework for developing, backtesting, and analyzing quantitative trading strategies using the **VectorBT** library.

## Overview

The framework is designed for rapid strategy development and robust performance analysis. It includes:

- **Modular Architecture**: Reusable helper functions for data loading, signal generation, and performance reporting.
- **Comprehensive Performance Tearsheets**: A "better than QuantStats" reporting module with 100+ metrics, benchmark comparisons, and crisis analysis.
- **Hex.tech Optimized**: Designed for seamless integration with Hex.tech notebooks, including data connections and modular file uploads.
- **Strategy Templates**: Pre-built templates for single symbol backtests, multi-symbol optimization, and full portfolio strategies.
- **VectorBT Knowledge Base**: A collection of best practices, code snippets, and troubleshooting guides for VectorBT.

## Key Features

- **High-Speed Backtesting**: Leverages VectorBT’s vectorized architecture for 1000x faster backtesting.
- **Scalability**: Multi-symbol, multi-strategy testing across decades of data.
- **Reproducibility**: Standardized templates, helpers, and workflows.
- **Comprehensive Reporting**: 100+ performance metrics including Ed Seykota’s Lake Ratio.

## 🚀 Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/alexbernal0/OBQ_TradingSystems_Vbt.git
cd OBQ_TradingSystems_Vbt
```

### 2. Install Dependencies

```bash
# For local development
pip install -r requirements.txt

# For Hex.tech environments (use in setup cell)
!pip install -q vectorbt pandas numpy plotly scipy statsmodels
```

### 3. Run a Backtest in Hex.tech

**Step 1: Upload `qullamaggie_tearsheet.py`**
- Go to the "Files" section in your Hex.tech project.
- Upload the `src/performance_reporting/qullamaggie_tearsheet.py` file.

**Step 2: Run the Setup Cell**
- Use the code from `strategies/qullamaggie/hex_setup_cell.py` to connect to MotherDuck and load data.

**Step 3: Run the Backtest Cell**
- Use the code from `strategies/qullamaggie/hex_cell_qullamaggie_condensed.py` to run the backtest and generate the report.

```python
# In a Hex.tech cell

# Import the tearsheet function from the uploaded file
from qullamaggie_tearsheet import run_comprehensive_tearsheet

# Run the comprehensive tearsheet
results = run_comprehensive_tearsheet(
    df_all_data=df_all_data, # Loaded in setup cell
    symbol=\'GLD\',
    trend_sma=50,
    breakout_period=5,
    trailing_sma=10,
    initial_capital=100000
)
```

## 📁 Repository Structure

```
OBQ_TradingSystems_Vbt/
├── src/
│   ├── data/                 # Data loading & transformation
│   ├── indicators/           # Custom indicators
│   ├── signals/              # Signal generation
│   ├── portfolio/            # Position sizing & risk management
│   ├── performance_reporting/ # NEW: Modular tearsheets & metrics
│   └── utils/                # Helper functions
│
├── strategies/
│   ├── qullamaggie/          # Qullamaggie strategy + Hex cells
│   └── template/             # Template for new strategies
│
├── VectorBT_Knowledge/       # Comprehensive VectorBT documentation
├── notebooks/                # Jupyter/Hex research notebooks
├── config/                   # Configuration files
├── tests/                    # Unit and integration tests
└── docs/                     # Additional documentation
```

## 📊 Performance Reporting Module

The new `src/performance_reporting/` module contains:

- **`qullamaggie_tearsheet.py`**: A standalone Python module that generates the full comprehensive tearsheet. It can be uploaded directly to Hex.tech.
- **`Master2025_...` files**: The original source for the 60+ custom metrics.

This modular approach keeps Hex.tech cells clean and makes the reporting logic reusable across different strategies and projects.

## 🎓 Learning Resources

- **[Getting Started Guide](docs/getting_started.md)**
- **[VectorBT Knowledge Base](VectorBT_Knowledge/README.md)**
- **[Qullamaggie Strategy Docs](strategies/qullamaggie/README.md)**

## 🤝 Contributing

We welcome contributions! Please see [Contributing Guidelines](docs/contributing.md).

## 📝 Branch Strategy

- **main**: Core infrastructure and shared components
- **strategy/qullamaggie**: Qullamaggie trend system

---

**Built with ❤️ for systematic traders who value speed, reproducibility, and rigor.**
