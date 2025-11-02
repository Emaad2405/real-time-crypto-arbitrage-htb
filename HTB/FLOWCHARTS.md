# Crypto Arbitrage System - Flowcharts & Diagrams

All diagrams use Mermaid syntax for easy rendering in GitHub, documentation tools, and presentation software.

---

## 1. System Architecture Overview

```mermaid
graph TB
    subgraph "Data Sources"
        WS1[Coinbase WebSocket<br/>0.6% fee]
        WS2[Binance WebSocket<br/>0.1% fee]
        WS3[Bitstamp WebSocket<br/>0.5% fee]
    end

    subgraph "Data Ingestion Layer"
        AGG[MultiExchangeAggregator<br/>- Symbol normalization<br/>- Stale filtering]
    end

    subgraph "Core Detection Engine"
        DET[ArbitrageDetector<br/>- Real-time detection<br/>- Price buffer<br/>- Opportunity list]
        BUFFER[(Price Buffer<br/>deque 1000 items)]
        OPPS[(Opportunities<br/>List)]
    end

    subgraph "ML Layer"
        PRED[SpreadPredictor<br/>GradientBoosting]
        SCORE[OpportunityScorer<br/>RandomForest]
        TRAIN[Training Loop<br/>Every 5 min]
    end

    subgraph "Dashboards"
        DASH1[Monitor Dashboard<br/>Port 8050]
        DASH2[Analytics Dashboard<br/>Port 8051]
        DASH3[Backtest Dashboard<br/>Port 8052]
    end

    WS1 & WS2 & WS3 --> AGG
    AGG --> DET
    DET --> BUFFER
    DET --> OPPS
    BUFFER --> TRAIN
    TRAIN --> PRED
    TRAIN --> SCORE
    DET --> DASH1
    DET --> DASH2
    OPPS --> DASH3
    PRED --> DASH1
    SCORE --> DASH3

    style DET fill:#4CAF50,color:#fff
    style PRED fill:#2196F3,color:#fff
    style SCORE fill:#2196F3,color:#fff
    style DASH1 fill:#FF9800,color:#fff
    style DASH2 fill:#FF9800,color:#fff
    style DASH3 fill:#FF9800,color:#fff
```

---

## 2. End-to-End Data Flow Pipeline

```mermaid
flowchart TD
    START([WebSocket Message Received]) --> PARSE[Parse Exchange-Specific Format]
    PARSE --> NORM[Normalize Symbol<br/>BTCUSDT → BTC-USD]
    NORM --> STALE{Price Age<br/><5 seconds?}
    STALE -->|No| DROP[Drop Stale Price]
    STALE -->|Yes| UPDATE[Update Price in Detector]

    UPDATE --> BUFFER_ADD[Add to Price Buffer]
    UPDATE --> LATEST[Update Latest Prices Dict]

    LATEST --> DETECT[Arbitrage Detection Loop]
    DETECT --> COMPARE{For each<br/>exchange pair}
    COMPARE --> CALC[Calculate Spread<br/>sell - buy / buy]
    CALC --> FEES[Subtract Exchange Fees]
    FEES --> PROFIT{Profit ≥<br/>0.5%?}

    PROFIT -->|No| COMPARE
    PROFIT -->|Yes| EMIT[Emit ArbitrageOpportunity]
    EMIT --> OPP_LIST[Add to Opportunities List]

    BUFFER_ADD --> ML_CHECK{5 minutes<br/>elapsed?}
    ML_CHECK -->|No| WAIT[Continue collecting]
    ML_CHECK -->|Yes| FEATURE[Engineer Features<br/>10 per exchange]

    FEATURE --> TRAIN_SPREAD[Train SpreadPredictor]
    FEATURE --> TRAIN_SCORE[Train OpportunityScorer]
    TRAIN_SPREAD --> SAVE1[Save Model to Disk]
    TRAIN_SCORE --> SAVE2[Save Model to Disk]

    OPP_LIST --> DASH_POLL{Dashboard<br/>polling?}
    DASH_POLL -->|Every 1s| RENDER[Render Dashboard Components]
    RENDER --> BROWSER[Push to Browser via WebSocket]

    BROWSER --> END([User Sees Alert])
    DROP --> END2([Discarded])
    WAIT --> END3([Buffer continues])

    style EMIT fill:#4CAF50,color:#fff
    style TRAIN_SPREAD fill:#2196F3,color:#fff
    style TRAIN_SCORE fill:#2196F3,color:#fff
    style BROWSER fill:#FF9800,color:#fff
```

---

## 3. ML Pipeline Detailed Workflow

```mermaid
flowchart LR
    subgraph "Data Collection"
        WS[WebSocket Streams] --> PB[(Price Buffer<br/>1000 items/symbol)]
    end

    subgraph "Feature Engineering"
        PB --> FE[Extract Features]
        FE --> F1[Price Features<br/>price, change, MA]
        FE --> F2[Volatility Features<br/>std, rolling vol]
        FE --> F3[Market Features<br/>bid-ask, volume]
        FE --> F4[Time Features<br/>hour, minute]
    end

    subgraph "Model Training"
        F1 & F2 & F3 & F4 --> MATRIX[Feature Matrix<br/>N × 30]
        MATRIX --> SPLIT[Train/Test Split<br/>80/20]
        SPLIT --> T1[Train SpreadPredictor<br/>GradientBoosting]
        SPLIT --> T2[Train OpportunityScorer<br/>RandomForest]
    end

    subgraph "Validation & Persistence"
        T1 --> V1[Evaluate R² Score]
        T2 --> V2[Evaluate Accuracy]
        V1 --> S1[Save spread_predictor.pkl]
        V2 --> S2[Save opportunity_scorer.pkl]
    end

    subgraph "Inference"
        S1 --> I1[Predict Future Spreads]
        S2 --> I2[Score Opportunities]
        I1 --> DASH[Dashboard Display]
        I2 --> BOT[ML Bot Decision]
    end

    style T1 fill:#2196F3,color:#fff
    style T2 fill:#2196F3,color:#fff
    style I1 fill:#4CAF50,color:#fff
    style I2 fill:#4CAF50,color:#fff
```

---

## 4. Arbitrage Detection Algorithm

```mermaid
flowchart TD
    START([New Price Update<br/>for Symbol X]) --> GET[Get All Prices for X<br/>from all exchanges]
    GET --> FILTER{Filter prices<br/>age < 5s?}
    FILTER -->|No prices| SKIP[Skip detection]
    FILTER -->|Have prices| LOOP{For each<br/>pair A, B}

    LOOP --> GET_PRICES[Get price_A and price_B]
    GET_PRICES --> SPREAD[Calculate spread<br/>spread = price_B - price_A / price_A]
    SPREAD --> FEE[Subtract fees<br/>profit = spread - fee_A - fee_B]
    FEE --> THRESHOLD{profit ≥<br/>MIN_THRESHOLD<br/>0.5%?}

    THRESHOLD -->|No| NEXT[Check next pair]
    THRESHOLD -->|Yes| CREATE[Create ArbitrageOpportunity]
    CREATE --> OPP_DATA[Populate opportunity:<br/>- Buy exchange: A<br/>- Sell exchange: B<br/>- Buy price: price_A<br/>- Sell price: price_B<br/>- Spread: spread<br/>- Profit %: profit<br/>- Timestamp: now]

    OPP_DATA --> EMIT[Emit to Opportunities List]
    EMIT --> LOG[Log opportunity]
    LOG --> NEXT

    NEXT --> LOOP
    LOOP -->|No more pairs| END([Detection Complete])
    SKIP --> END

    style CREATE fill:#4CAF50,color:#fff
    style EMIT fill:#4CAF50,color:#fff
    style THRESHOLD fill:#FF9800,color:#fff
```

---

## 5. Dashboard Update Cycle

```mermaid
sequenceDiagram
    participant Browser
    participant DashApp as Dash App
    participant Detector
    participant MLModels as ML Models
    participant Buffer as Price Buffer

    Note over Browser,Buffer: Every 1 second

    Browser->>DashApp: Interval Timer Triggers
    DashApp->>Detector: get_recent_opportunities(5 min)
    Detector-->>DashApp: List[ArbitrageOpportunity]

    DashApp->>Detector: get_best_opportunity()
    Detector-->>DashApp: Best opportunity

    DashApp->>Detector: get_statistics()
    Detector-->>DashApp: Total, avg, max stats

    DashApp->>Buffer: get_price_data()
    Buffer-->>DashApp: Recent price history

    DashApp->>MLModels: predict_spreads()
    MLModels-->>DashApp: Predicted spreads

    DashApp->>DashApp: Render Components:<br/>- Stats cards<br/>- Best opportunity alert<br/>- Price charts<br/>- Opportunities table<br/>- Spread heatmap<br/>- ML predictions

    DashApp->>Browser: Push Updates via WebSocket
    Browser->>Browser: Update UI (React)

    Note over Browser,Buffer: Sub-100ms total latency
```

---

## 6. Backtesting Workflow

```mermaid
flowchart TD
    START([Start Backtest]) --> LOAD[Load Historical Opportunities<br/>from captured_data/]
    LOAD --> INIT[Initialize Bots:<br/>- ML Bot initial capital $10k<br/>- Benchmark Bot initial capital $10k]

    INIT --> LOOP{For each<br/>opportunity}

    LOOP --> ML_DECIDE[ML Bot: Get Opportunity Score]
    ML_DECIDE --> ML_THRESHOLD{Score ≥<br/>threshold?}
    ML_THRESHOLD -->|Yes| ML_EXEC[ML Bot: Execute Trade]
    ML_THRESHOLD -->|No| ML_SKIP[ML Bot: Skip]

    LOOP --> BENCH_DECIDE[Benchmark Bot: Check Spread]
    BENCH_DECIDE --> BENCH_THRESHOLD{Spread ≥<br/>threshold?}
    BENCH_THRESHOLD -->|Yes| BENCH_EXEC[Benchmark Bot: Execute Trade]
    BENCH_THRESHOLD -->|No| BENCH_SKIP[Benchmark Bot: Skip]

    ML_EXEC --> ML_SIM[Simulate Trade:<br/>- Apply slippage 0.1%<br/>- Apply fees<br/>- Delay 100ms]
    BENCH_EXEC --> BENCH_SIM[Simulate Trade:<br/>- Apply slippage 0.1%<br/>- Apply fees<br/>- Delay 100ms]

    ML_SIM --> ML_LOG[Log Trade Result]
    BENCH_SIM --> BENCH_LOG[Log Trade Result]

    ML_LOG & BENCH_LOG & ML_SKIP & BENCH_SKIP --> NEXT{More<br/>opportunities?}
    NEXT -->|Yes| LOOP
    NEXT -->|No| METRICS[Calculate Performance Metrics]

    METRICS --> M1[Win Rate]
    METRICS --> M2[Total Profit]
    METRICS --> M3[Sharpe Ratio]
    METRICS --> M4[Max Drawdown]

    M1 & M2 & M3 & M4 --> COMPARE[Compare ML vs Benchmark]
    COMPARE --> SAVE[Save Results:<br/>- CSV trade logs<br/>- JSON summary]
    SAVE --> DASH[Display in Dashboard]
    DASH --> END([Backtest Complete])

    style ML_EXEC fill:#2196F3,color:#fff
    style BENCH_EXEC fill:#FF9800,color:#fff
    style COMPARE fill:#4CAF50,color:#fff
```

---

## 7. WebSocket Connection Management

```mermaid
stateDiagram-v2
    [*] --> Disconnected
    Disconnected --> Connecting: start()
    Connecting --> Connected: WebSocket open
    Connecting --> Reconnecting: Connection failed
    Connected --> Processing: Message received
    Processing --> Connected: Message processed
    Connected --> Disconnected: Connection closed
    Connected --> Reconnecting: Connection error
    Reconnecting --> Connecting: Wait backoff time<br/>(1s → 2s → 4s → 8s → 16s)
    Reconnecting --> [*]: Max retries exceeded

    note right of Processing
        1. Parse JSON
        2. Normalize symbol
        3. Filter stale
        4. Trigger detection
    end note

    note right of Reconnecting
        Exponential backoff
        prevents hammering
        exchange servers
    end note
```

---

## 8. Trading Bot Decision Flow

```mermaid
flowchart TD
    START([New Arbitrage Opportunity Detected]) --> SPLIT{Which Bot?}

    SPLIT -->|ML Bot| ML1[Load ML Models]
    ML1 --> ML2[Extract Features from Opportunity]
    ML2 --> ML3[Get OpportunityScorer Score]
    ML3 --> ML4{Score ≥<br/>confidence<br/>threshold?}
    ML4 -->|No| ML_SKIP[Skip Trade]
    ML4 -->|Yes| ML5[Get SpreadPredictor Prediction]
    ML5 --> ML6{Predicted<br/>spread still<br/>positive?}
    ML6 -->|No| ML_SKIP
    ML6 -->|Yes| ML_EXEC[Execute Trade]

    SPLIT -->|Benchmark Bot| BENCH1[Calculate Spread]
    BENCH1 --> BENCH2{Spread ≥<br/>MIN_PROFIT<br/>threshold?}
    BENCH2 -->|No| BENCH_SKIP[Skip Trade]
    BENCH2 -->|Yes| BENCH_EXEC[Execute Trade]

    ML_EXEC & BENCH_EXEC --> TRADE[Place Buy/Sell Orders]
    TRADE --> SIMULATE[Simulate Reality:<br/>- Slippage<br/>- Execution delay<br/>- Actual fees]
    SIMULATE --> CALC[Calculate Profit/Loss]
    CALC --> UPDATE[Update Portfolio]
    UPDATE --> LOG[Log Trade]

    LOG & ML_SKIP & BENCH_SKIP --> END([Wait for Next Opportunity])

    style ML_EXEC fill:#2196F3,color:#fff
    style BENCH_EXEC fill:#FF9800,color:#fff
    style TRADE fill:#4CAF50,color:#fff
```

---

## 9. Component Interaction Diagram

```mermaid
graph TB
    subgraph "External Systems"
        EX1[Coinbase API]
        EX2[Binance API]
        EX3[Bitstamp API]
    end

    subgraph "Ingestion Layer (data_ingestion.py)"
        C1[CoinbaseClient]
        C2[BinanceClient]
        C3[BitstampClient]
        AGG[MultiExchangeAggregator]
    end

    subgraph "Detection Layer (arbitrage_detector.py)"
        DET[ArbitrageDetector]
        BUFFER[(Price Buffer)]
        LATEST[(Latest Prices)]
        OPPS[(Opportunities)]
    end

    subgraph "ML Layer (ml_predictor.py)"
        PRED[SpreadPredictor]
        SCORE[OpportunityScorer]
        FEATURE[Feature Engineering]
    end

    subgraph "Bot Layer (bot/)"
        BASE[BaseBot]
        ML[MLArbitrageBot]
        BENCH[BenchmarkBot]
        ENGINE[BacktestEngine]
    end

    subgraph "UI Layer (dashboards)"
        DASH1[Monitor Dashboard]
        DASH2[Analytics Dashboard]
        DASH3[Backtest Dashboard]
    end

    EX1 -->|WebSocket| C1
    EX2 -->|WebSocket| C2
    EX3 -->|WebSocket| C3
    C1 & C2 & C3 --> AGG
    AGG -->|Callback| DET
    DET --> BUFFER
    DET --> LATEST
    DET --> OPPS
    BUFFER --> FEATURE
    FEATURE --> PRED
    FEATURE --> SCORE
    DET --> DASH1
    DET --> DASH2
    OPPS --> ENGINE
    ENGINE --> ML
    ENGINE --> BENCH
    BASE -.->|inherits| ML
    BASE -.->|inherits| BENCH
    PRED --> ML
    SCORE --> ML
    ENGINE --> DASH3

    style DET fill:#4CAF50,color:#fff
    style PRED fill:#2196F3,color:#fff
    style SCORE fill:#2196F3,color:#fff
    style DASH1 fill:#FF9800,color:#fff
    style DASH2 fill:#FF9800,color:#fff
    style DASH3 fill:#FF9800,color:#fff
```

---

## 10. Latency Breakdown Timeline

```mermaid
gantt
    title End-to-End Latency: Price Update → Alert Display
    dateFormat SSS
    axisFormat %Lms

    section Data Reception
    WebSocket receive           :a1, 000, 10ms
    Message parsing             :a2, after a1, 5ms

    section Processing
    Symbol normalization        :b1, after a2, 1ms
    Stale filter check          :b2, after b1, 1ms
    Arbitrage detection         :b3, after b2, 1ms
    Opportunity emission        :b4, after b3, 1ms

    section Dashboard Update
    Dashboard callback trigger  :c1, after b4, 20ms
    Component rendering         :c2, after c1, 30ms
    Browser WebSocket push      :c3, after c2, 15ms

    section Display
    Browser React update        :d1, after c3, 15ms
```

**Total Latency**: ~83ms (Target: <100ms ✅)

---

## 11. Data Model Entity Relationship

```mermaid
erDiagram
    PRICE_DATA {
        string exchange
        string symbol
        float price
        datetime timestamp
        float bid
        float ask
        float volume
    }

    ARBITRAGE_OPPORTUNITY {
        string symbol
        string buy_exchange
        string sell_exchange
        float buy_price
        float sell_price
        float spread
        float profit_percent
        datetime timestamp
    }

    EXCHANGE_CONFIG {
        string name
        string ws_url
        float fee
        list symbols
    }

    TRADE_RESULT {
        int trade_id
        string bot_name
        string symbol
        string buy_exchange
        string sell_exchange
        float buy_price
        float sell_price
        float quantity
        float profit
        float portfolio_value
        datetime timestamp
    }

    ML_FEATURES {
        float price
        float price_change
        float price_ma_5
        float price_ma_20
        float price_std_5
        float volatility
        float bid_ask_spread
        float volume_ma
        int hour
        int minute
    }

    PRICE_DATA ||--o{ ARBITRAGE_OPPORTUNITY : "generates"
    EXCHANGE_CONFIG ||--o{ PRICE_DATA : "provides"
    ARBITRAGE_OPPORTUNITY ||--o{ TRADE_RESULT : "executed as"
    PRICE_DATA ||--o{ ML_FEATURES : "engineered into"
    ML_FEATURES ||--o{ TRADE_RESULT : "informs"
```

---

## 12. Deployment Architecture (Production)

```mermaid
graph TB
    subgraph "Cloud Infrastructure"
        subgraph "Data Ingestion Cluster"
            WS1[WebSocket Worker 1<br/>Coinbase]
            WS2[WebSocket Worker 2<br/>Binance]
            WS3[WebSocket Worker 3<br/>Bitstamp]
        end

        subgraph "Processing Cluster"
            DET1[Detection Node 1]
            DET2[Detection Node 2]
            LB[Load Balancer]
        end

        subgraph "ML Cluster"
            ML1[ML Training Node]
            ML2[ML Inference Node]
        end

        subgraph "Storage Layer"
            REDIS[(Redis Cache<br/>Latest Prices)]
            POSTGRES[(PostgreSQL<br/>Opportunities)]
            S3[(S3 Bucket<br/>Models)]
        end

        subgraph "Web Tier"
            NGINX[Nginx Reverse Proxy]
            DASH1[Dashboard Instance 1]
            DASH2[Dashboard Instance 2]
        end

        subgraph "Monitoring"
            PROM[Prometheus]
            GRAF[Grafana]
            ALERT[Alertmanager]
        end
    end

    WS1 & WS2 & WS3 --> LB
    LB --> DET1 & DET2
    DET1 & DET2 --> REDIS
    DET1 & DET2 --> POSTGRES
    REDIS --> ML1
    ML1 --> S3
    S3 --> ML2
    ML2 --> DASH1 & DASH2
    POSTGRES --> DASH1 & DASH2
    NGINX --> DASH1 & DASH2

    DET1 & DET2 --> PROM
    ML1 --> PROM
    PROM --> GRAF
    PROM --> ALERT

    style LB fill:#FF9800,color:#fff
    style REDIS fill:#F44336,color:#fff
    style POSTGRES fill:#2196F3,color:#fff
    style NGINX fill:#4CAF50,color:#fff
```

---

## How to Use These Diagrams

### In Presentations
1. Copy Mermaid code blocks
2. Paste into:
   - [Mermaid Live Editor](https://mermaid.live)
   - PowerPoint with Mermaid plugin
   - Google Slides with Mermaid extension
3. Export as SVG/PNG for high-quality images

### In Documentation
- GitHub automatically renders Mermaid in markdown files
- GitLab, Bitbucket also support native Mermaid rendering
- Confluence: Use Mermaid Diagrams macro

### In IDEs
- VS Code: Install "Markdown Preview Mermaid Support" extension
- JetBrains IDEs: Built-in Mermaid support in markdown preview
- Obsidian: Native Mermaid rendering

### For Live Demo
- Use Mermaid Live Editor in browser
- Zoom in/out for emphasis
- Click "Actions" → "Copy SVG" for clean exports
