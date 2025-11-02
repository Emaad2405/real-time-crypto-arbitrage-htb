# Crypto Arbitrage Bot Backtesting System

## Overview

This backtesting system allows you to compare different trading strategies for cryptocurrency arbitrage. It includes:

1. **ML-Powered Bot** - Uses trained machine learning models for decision making
2. **Benchmark Bot** - Simple threshold-based strategy for baseline comparison
3. **Backtest Engine** - Realistic trade simulation with slippage and fees
4. **Dashboard** - Interactive visualization of bot performance comparison

## Quick Start

### Run Backtest

```bash
python run_backtest.py
```

This will:
1. Load trained ML models from `models/` directory
2. Initialize both bots (ML and Benchmark)
3. Load historical opportunities from `captured_data/`
4. Run backtest simulation
5. Display results and launch dashboard on **http://localhost:8052**

### View Results

- **Console**: See summary statistics in terminal output
- **CSV**: Trade logs saved to `backtest_results/trades_TIMESTAMP.csv`
- **JSON**: Detailed summary in `backtest_results/trades_TIMESTAMP.json`
- **Dashboard**: Interactive charts at **http://localhost:8052**

## Bot Configuration

### ML Arbitrage Bot

Located in [`bot/ml_arbitrage_bot.py`](bot/ml_arbitrage_bot.py)

**Default Parameters:**
- `min_ml_confidence`: 0.4 (40% ML confidence threshold)
- `min_spread_threshold`: -1.0 (minimum spread percentage)
- `min_profit_threshold`: -2.0 (minimum profit after fees)
- `max_position_size`: 0.10 (max 10% of capital per trade)

**Decision Logic:**
1. Uses OpportunityScorer to get ML confidence score (0-1)
2. Executes if ML confidence > threshold
3. Position size scales with ML confidence (higher confidence = larger trades)

### Benchmark Bot

Located in [`bot/benchmark_bot.py`](bot/benchmark_bot.py)

**Default Parameters:**
- `min_spread_threshold`: -0.5 (minimum spread percentage)
- `min_profit_threshold`: -2.0 (minimum profit after fees)
- `position_size_pct`: 0.05 (fixed 5% of capital per trade)

**Decision Logic:**
1. Simple threshold-based: Execute if spread > threshold AND profit > threshold
2. Fixed position sizing (no ML-based adjustment)

## File Structure

```
crypto_arbitrage/
├── bot/
│   ├── __init__.py               # Package initialization
│   ├── base_bot.py               # Abstract base class for all bots
│   ├── ml_arbitrage_bot.py       # ML-powered trading bot
│   ├── benchmark_bot.py          # Simple threshold bot
│   ├── backtest_engine.py        # Backtesting framework
│   └── trade_logger.py           # Trade recording and persistence
│
├── backtest_dashboard.py         # Interactive comparison dashboard (port 8052)
├── run_backtest.py               # Main backtest entry point
│
├── models/
│   ├── spread_predictor_live.pkl # Trained spread prediction model
│   └── opportunity_scorer_live.pkl # Trained opportunity classification model
│
├── captured_data/
│   └── opportunities_*.csv       # Historical arbitrage opportunities
│
└── backtest_results/
    ├── trades_*.csv              # Trade execution logs
    └── trades_*.json             # Detailed backtest summary
```

## Performance Metrics

The system calculates comprehensive performance metrics:

### Basic Metrics
- **Total Trades**: Number of trades executed
- **Win Rate**: Percentage of profitable trades
- **Net Profit**: Total profit in USD
- **Return**: Percentage return on initial capital

### Advanced Metrics
- **Sharpe Ratio**: Risk-adjusted returns
- **Max Drawdown**: Maximum peak-to-trough decline
- **Profit Factor**: Ratio of winning to losing trades
- **Avg Profit/Trade**: Average profit per executed trade

## Dashboard Features

Access the interactive dashboard at **http://localhost:8052**

### Visualizations

1. **Performance Table** - Side-by-side bot comparison
2. **Capital Curves** - Capital over time for each bot
3. **Win Rate Comparison** - Bar chart of success rates
4. **Return Comparison** - Overall returns comparison
5. **Profit Distribution** - Histogram of trade profits
6. **Sharpe Ratio** - Risk-adjusted performance
7. **Max Drawdown** - Risk visualization
8. **Trade Timeline** - Scatter plot of trades over time

## Customization

### Adjust Bot Parameters

Edit [`run_backtest.py`](run_backtest.py:L42-L69) to modify:

```python
# ML Bot
ml_bot = MLArbitrageBot(
    spread_predictor=spread_predictor,
    opportunity_scorer=opportunity_scorer,
    initial_capital=10000.0,
    min_ml_confidence=0.6,  # ← ADJUST THIS
    min_spread_threshold=0.5  # ← AND THIS
)

# Benchmark Bot
benchmark_bot = BenchmarkBot(
    initial_capital=10000.0,
    min_spread_threshold=1.0,  # ← ADJUST THIS
    position_size_pct=0.05  # ← AND THIS
)
```

### Add New Bots

1. Create new class inheriting from `BaseBot`
2. Implement `should_execute_trade()` method
3. Implement `calculate_position_size()` method
4. Add to `run_backtest.py`

Example:

```python
from bot.base_bot import BaseBot

class MyCustomBot(BaseBot):
    def __init__(self, initial_capital=10000.0):
        super().__init__(name="My_Custom_Bot", initial_capital=initial_capital)
        # Add custom parameters

    def should_execute_trade(self, opportunity):
        # Your decision logic
        return True  # or False

    def calculate_position_size(self, opportunity):
        # Your position sizing logic
        return self.current_capital * 0.05  # Example: 5% of capital
```

## Realistic Simulation

The backtest engine simulates real-world trading conditions:

- **Slippage**: 0.1% price slippage (configurable)
- **Fees**: 0.1% per side (0.2% total)
- **Execution Time**: 100ms simulated latency
- **Capital Constraints**: Cannot trade more than available capital
- **Risk Management**: Maximum position size limits

## Interpreting Results

### Both Bots Lose Money

This is expected if:
- Historical data contains mostly negative profit opportunities
- Spreads are too small after fees
- Market conditions were unfavorable

**Solution**:
- Collect data during high volatility periods
- Adjust minimum profit thresholds
- Filter opportunities before backtesting

### ML Bot Underperforms Benchmark

Possible causes:
- ML models need retraining
- Training data doesn't match test conditions
- Overfit to specific market conditions

**Solution**:
- Retrain models with more recent data
- Adjust ML confidence thresholds
- Review feature engineering

### Benchmark Bot Wins

This suggests:
- Simple strategies may be sufficient
- ML overhead not justified for current data
- Market is efficiently priced

**Solution**:
- Analyze which features ML is using
- Consider hybrid approach
- Focus on better opportunity detection

## Notes

- **WARNING**: This is a SIMULATION. Real trading involves additional complexity:
  - Order book depth
  - Liquidity constraints
  - Exchange API limits
  - Network latency
  - Concurrent traders

- **Data Quality**: Backtest results are only as good as the input data

- **Overfitting**: High performance in backtest doesn't guarantee future profits

- **Execution**: Paper trading recommended before live deployment

## Troubleshooting

### No Opportunities Loaded

```
❌ No opportunities found! Please run data collection first.
```

**Fix**: Run `python main.py` first to collect live arbitrage data

### ML Models Not Found

```
❌ Failed to load one or more ML models
```

**Fix**: Train models first using the ML training scripts

### Out of Memory

For large datasets (>100K opportunities), the system may use significant memory.

**Fix**: Limit opportunities processed:

```python
results = engine.run_backtest(
    opportunities=opportunities,
    max_opportunities=10000  # Process only first 10K
)
```

### Dashboard Won't Start

```
Address already in use: port 8052
```

**Fix**: Kill existing process or change port in `backtest_dashboard.py`

## Future Enhancements

Potential improvements:
- [ ] Live paper trading mode
- [ ] Multi-exchange order routing
- [ ] Reinforcement learning bots
- [ ] Parameter optimization (grid search)
- [ ] Walk-forward analysis
- [ ] Monte Carlo simulation
- [ ] Transaction cost analysis
- [ ] Market impact modeling

## Support

For issues or questions:
1. Check logs in `logs/backtest_*.log`
2. Review trade logs in `backtest_results/`
3. Verify ML models are trained and loaded correctly

---

**Built with**: Python, Dash, Plotly, scikit-learn, pandas, numpy
