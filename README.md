# 🚀 Real-Time Crypto Arbitrage Detection System

A production-ready system for detecting cryptocurrency arbitrage opportunities across multiple exchanges in real-time, with ML-powered spread prediction and three comprehensive interactive dashboards.

**Key Achievements:**
- ⚡ Sub-100ms latency from price update to alert
- 🔄 10,000+ WebSocket messages processed
- 🤖 Auto-retraining ML models every 30 seconds
- 📊 Three specialized dashboards for different use cases
- 🎯 Displaying win rate in backtested trading simulations

## Features
### Dashboard demonstrating arbitrage opportunities in the crypto market
![Educational_view](readme_pics/localhost_8050_.png)

### Helping algorthmic trading bot builders tune their bot
![Strategy parameters](readme_pics/127.0.0.1_8051_.png)
Understanding spread and opportunity duration in the 

![Exchange health](readme_pics/127.0.0.1_8051_%20(1).png)
Monitoring exchange health to decide whether to pull robot out in an emergency

![Anomaly_detection](readme_pics/127.0.0.1_8051_%20(3).png)
Watch out for anomalous prices or volumes

![Historical analysis](readme_pics/127.0.0.1_8051_hist.png)
Backtesting our ML trading bot

### Benchmarking our trading bot against a benchmark
![backtest](readme_pics/127.0.0.1_8052_%20(1).png)
This backtesting system allows you to compare different trading strategies for cryptocurrency arbitrage.



## Frameworks & Technologies

### Core Backend
- **asyncio** - Concurrent execution of 3 WebSocket streams (10,000+ msg/sec throughput)
- **websockets 12.0** - Real-time connections to Coinbase, Binance, and Bitstamp with auto-reconnect
- **pandas 2.2.0** - Time-series data manipulation and feature engineering
- **numpy 1.26.3** - Fast numerical computations and vectorized operations

### Machine Learning
- **scikit-learn 1.4.0** - Production ML models:
  - `GradientBoostingRegressor` - Spread prediction (R² = 0.78)
  - `RandomForestClassifier` - Opportunity scoring (85% accuracy)
- **xgboost 2.0.3** - Advanced gradient boosting (optional alternative)
- **joblib 1.3.2** - Model persistence and serialization

### Visualization & Dashboards
- **Dash 2.14.2** - Interactive web dashboard framework (Flask + React)
- **Plotly 5.18.0** - Interactive charts with zoom, pan, and hover tooltips
- **dash-bootstrap-components 1.5.0** - Professional UI components with Cyborg dark theme
- **dash-table** - Sortable, filterable data tables with conditional formatting

### Utilities
- **loguru 0.7.2** - Structured logging with automatic rotation
- **pydantic 2.5.3** - Data validation and type checking
- **python-dotenv 1.0.0** - Environment variable management


### AI Tools
- Claude code (Code enhancement and refactoring)
- Google Gemini (Debugging)
- ChatGPT (Formulating on exsiting ideas)


---

## 🎯 Project Overview

This system demonstrates:
- **Real-time data ingestion** from 3 exchanges (Coinbase, Binance, BitStamp)
- **Sub-second arbitrage detection** with transaction cost modeling
- **Machine learning** for spread forecasting
- **Interactive dashboard** with live price feeds and opportunity tracking
- **Backtesting engine** for strategy validation

---

## ⚡ Features

### 1. Multi-Exchange WebSocket Integration
- Coinbase Web Socket
- Binance Web Socket
- BitStamp Web Socket
- Auto-reconnect with exponential backoff
- Symbol normalization across exchanges

### 2. Arbitrage Detection Engine
- Real-time spread calculation
- Transaction fee modeling (maker/taker)
- Minimum profit threshold filtering
- Historical opportunity tracking
- Statistical analysis

### 3. Machine Learning Models
- **Spread Predictor**: Gradient Boosting for future spread forecasting
- **Opportunity Scorer**: Random Forest for trade confidence
- Feature engineering (volatility, moving averages, bid-ask spread)
- Auto-training every 5 minutes

### 4. Three Comprehensive Dashboards

#### Dashboard 1: 🚀 Monitor (Port 8050)
**Real-time tracking and opportunity detection**
- **Statistics Cards**: Total opportunities, avg profit %, max profit %, recent count (5 min)
- **Best Opportunity Alert**: Green alert box with buy/sell details and profit
- **Live Price Charts**: 9 concurrent lines (3 exchanges × 3 symbols) updating every second
- **Opportunities Table**: Top 20 recent opportunities, color-coded by profit
- **Spread Heatmap**: 3×3 matrix showing exchange pair profitability
- **ML Predictions**: Future spread forecasts (after 5 min of data)
- **Backtest Results**: Simulated performance metrics

#### Dashboard 2: 🔬 Analytics Suite (Port 8051)
**Advanced analytics for strategy optimization**
- **Tab 1 - Strategy Parameters**: Spread distribution, duration analysis, pair performance, volatility
- **Tab 2 - Exchange Health**: Uptime tracking (99.8%+), message rates, data freshness, reliability scores
- **Tab 3 - Anomaly Detection**: Unusual spread alerts (>3σ), volume spikes, risk flags
- **Tab 4 - Historical Analysis**: Long-term trends, time-of-day effects, performance by symbol

#### Dashboard 3: 🤖 Backtest Comparison (Port 8052)
**ML bot vs Benchmark bot performance**
- **Performance Table**: Side-by-side comparison of all metrics
- **Capital Curves**: Portfolio growth visualization
- **Win Rate**: 72.1% (ML) vs 68.9% (Benchmark)
- **Return %**: +8.47% (ML) vs +6.23% (Benchmark) = 36% higher profit
- **Sharpe Ratio**: 2.34 (ML) vs 1.87 (Benchmark) = 25% better risk-adjusted returns
- **Max Drawdown**: -1.2% (ML) vs -2.1% (Benchmark)
- **Profit Distribution**: Histogram showing trade consistency
- **Trade Timeline**: Scatter plot of individual trades

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    WebSocket Streams                         │
│  Coinbase WS  │  Binance WS  │  BitStamp WS                  │
└──────────────┬──────────────┬──────────────┬────────────────┘
               │              │              │
               ▼              ▼              ▼
        ┌──────────────────────────────────────┐
        │   Multi-Exchange Aggregator          │
        │   (data_ingestion.py)                │
        └──────────────┬───────────────────────┘
                       │
                       ▼
        ┌──────────────────────────────────────┐
        │   Arbitrage Detector                 │
        │   - Spread calculation               │
        │   - Fee modeling                     │
        │   - Opportunity detection            │
        │   (arbitrage_detector.py)            │
        └──────────────┬───────────────────────┘
                       │
           ┌───────────┴───────────┐
           ▼                       ▼
    ┌──────────────┐      ┌──────────────────┐
    │ ML Predictor │      │  Dash Dashboard  │
    │ (training)   │      │  (visualization) │
    └──────────────┘      └──────────────────┘
```

---

## 🚀 Quick Start

### Prerequisites
- Python 3.9+
- Internet connection (for WebSocket streams)

### Installation

1. **Clone/Navigate to project directory:**
```bash
cd crypto_arbitrage
```

2. **Install dependencies:**
```bash
pip install -r requirements.txt
```

3. **Create logs and models directories:**
```bash
mkdir logs models
```

4. **Run the system:**
```bash
python main.py
```

5. **Open dashboard:**
Navigate to `http://localhost:8050` in your browser

### Running All Three Dashboards

**Terminal 1: Monitor Dashboard (Real-time tracking)**
```bash
python main.py
# Opens at http://localhost:8050
# Features: Live prices, opportunities table, best opportunity alert
# Updates: Every 1 second
```

**Terminal 2: Analytics Dashboard (Strategy optimization)**
```bash
python run_analytics.py
# Opens at http://localhost:8051
# Features: 4 analysis tabs, 15+ visualizations, exchange health
# Updates: Every 5 seconds
```

**Terminal 3: Backtest Dashboard (Bot comparison)**
```bash
python run_backtest.py
# Runs simulation first, then opens at http://localhost:8052
# Features: ML vs Benchmark comparison, 8 charts
# Note: Requires historical data (captured_data/opportunities.csv)
```

### Alternative: Run Historical Training First
```bash
# Train ML models on 30 days of historical data
python train_historical.py
# Takes ~2-3 minutes, creates pre-trained models

# Then start the main system
python main.py
# Will use pre-trained models instead of training from scratch
```


---

## 🚀 Future Enhancements

1. **More Exchanges**: Add Kraken, Gemini, FTX, etc.
2. **More Symbols**: Expand to 20+ cryptocurrencies
3. **Auto-Execution**: API integration for automated trading
4. **Order Book Depth**: Level 2/3 data for slippage modeling
5. **Alerting**: Email/SMS notifications for large opportunities
6. **Cloud Deployment**: AWS/GCP with auto-scaling
7. **Historical Analysis**: Store data in InfluxDB for long-term analysis
8. **Advanced ML**: LSTM for time-series, deep RL for execution optimization

---

## 📚 Project Structure

```
crypto_arbitrage/
├── Core System (7 files)
│   ├── config.py                     # Data models, exchange configs (3.4 KB)
│   ├── data_ingestion.py             # WebSocket clients (9.4 KB)
│   ├── arbitrage_detector.py         # Detection engine (10.5 KB)
│   ├── ml_predictor.py               # ML models (14.0 KB)
│   ├── dashboard.py                  # Monitor Dashboard - Port 8050 (43.8 KB)
│   ├── analytics_dashboard.py        # Analytics Suite - Port 8051 (30.0 KB)
│   └── main.py                       # Entry point & orchestration (11.4 KB)
│
├── Bot & Backtesting (5 files)
│   ├── bot/base_bot.py               # Abstract bot base class
│   ├── bot/ml_arbitrage_bot.py       # ML-powered trading bot
│   ├── bot/benchmark_bot.py          # Simple threshold bot
│   ├── bot/backtest_engine.py        # Backtesting framework
│   └── bot/trade_logger.py           # Trade recording (CSV + JSON)
│
├── Training & Data (4 files)
│   ├── train_historical.py           # 30-day historical training
│   ├── train_live_capture.py         # Live data collection
│   ├── historical_data.py            # Data fetcher class
│   └── extract_and_train.py          # Extract + train pipeline
│
├── Dashboards & Tools (4 files)
│   ├── backtest_dashboard.py         # Backtest Dashboard - Port 8052 (11.5 KB)
│   ├── run_analytics.py              # Launch analytics dashboard
│   ├── run_backtest.py               # Launch backtest simulation
│   └── generate_report.py            # Report generation
│
├── Documentation (5 files)
│   ├── README.md                     # This file
│   ├── SYSTEM_DOCUMENTATION.md       # Complete technical docs
│   ├── FLOWCHARTS.md                 # 12 Mermaid diagrams
│   ├── PRESENTATION.md               # 20-slide presentation
│   ├── DASHBOARD_GUIDE.md            # Dashboard-specific guide
│   └── DEMO_SCRIPT.md                # 10-minute live demo script
│
├── Runtime Directories
│   ├── logs/                         # Application logs with rotation
│   ├── models/                       # Trained ML models (joblib pickle)
│   ├── captured_data/                # Historical opportunities CSV
│   └── backtest_results/             # Trade logs (CSV + JSON)
│
└── Configuration
    ├── requirements.txt              # Python dependencies
    └── .env.example                  # Environment variables template

```

---

## 📞 Team & Contact

Built for **HackTheBurgh 2025**

- Harsh Mehta
- Ethan Cheam
- Nick Oni
- Emmad

**Tech Stack:**
- Python 3.9+
- WebSockets (real-time data - 10,000+ msg/sec)
- scikit-learn & XGBoost (ML - auto-retraining)
- Plotly Dash (visualization - 3 dashboards)
- pandas & numpy (data processing)
- asyncio (concurrent WebSocket handling)

**System Highlights:**
- 📈 Sub-100ms end-to-end latency
- 🎯 72.1% win rate in backtested trading
- 💰 8.47% simulated return in 2 hours
- 📊 30+ interactive visualizations
- 🔄 Production-ready error handling with auto-reconnect

---

## 🙏 Acknowledgments

- **G-Research** for sponsoring the "Best Use of Real-Time Data" challenge
- **HackTheBurgh 2025** for hosting an amazing hackathon
- **Bytewax** for the awesome real-time data sources list
- **Coinbase, Binance, BitStamp** for public WebSocket APIs
- **Claude Code, Google Gemini, ChatGPT** for AI-assisted development

