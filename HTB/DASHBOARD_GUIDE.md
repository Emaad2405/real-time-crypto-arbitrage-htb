# Dashboard-Specific Guide
## Complete Reference for All Three Dashboards

---

## Dashboard 1: 🚀 Crypto Arbitrage Monitor

**File:** [dashboard.py](dashboard.py)
**Port:** 8050
**Purpose:** Real-time monitoring and opportunity tracking
**Update Frequency:** 1 second

### Launch Command
```bash
python main.py
# Dashboard automatically opens at http://localhost:8050
```

---

### Component Breakdown

#### 1. Statistics Cards (Top Row)

**Location:** Top of dashboard, 4 cards in a row

**Card 1: Total Opportunities**
```
┌────────────────────────┐
│ Total Opportunities    │
│        142             │
└────────────────────────┘
```
- **Data Source:** `len(detector.opportunities)`
- **Calculation:** All opportunities since system start
- **Updates:** Every 1 second
- **Color:** Blue background

**Card 2: Average Profit %**
```
┌────────────────────────┐
│ Average Profit %       │
│       0.73%            │
└────────────────────────┘
```
- **Data Source:** `mean(opp.profit_percent for opp in opportunities)`
- **Calculation:** Mean of all profit percentages (after fees)
- **Updates:** Every 1 second
- **Color:** Green background

**Card 3: Maximum Profit %**
```
┌────────────────────────┐
│ Maximum Profit %       │
│       2.15%            │
└────────────────────────┘
```
- **Data Source:** `max(opp.profit_percent for opp in opportunities)`
- **Calculation:** Highest profit opportunity detected
- **Updates:** Every 1 second
- **Color:** Orange background

**Card 4: Recent Opportunities (5 min)**
```
┌────────────────────────┐
│ Recent (5 min)         │
│         12             │
└────────────────────────┘
```
- **Data Source:** `detector.get_recent_opportunities(minutes=5)`
- **Calculation:** Opportunities in last 5 minutes
- **Updates:** Every 1 second
- **Color:** Purple background

**Implementation:**
```python
def create_stats_cards(opportunities):
    total = len(opportunities)
    avg_profit = np.mean([o.profit_percent for o in opportunities]) if opportunities else 0
    max_profit = max([o.profit_percent for o in opportunities]) if opportunities else 0
    recent = len([o for o in opportunities if (datetime.now() - o.timestamp).seconds < 300])

    return html.Div([
        dbc.Col([dbc.Card([dbc.CardBody([html.H4(total), html.P("Total Opportunities")])])]),
        dbc.Col([dbc.Card([dbc.CardBody([html.H4(f"{avg_profit:.2f}%"), html.P("Avg Profit")])])]),
        dbc.Col([dbc.Card([dbc.CardBody([html.H4(f"{max_profit:.2f}%"), html.P("Max Profit")])])]),
        dbc.Col([dbc.Card([dbc.CardBody([html.H4(recent), html.P("Recent (5 min)")])])])
    ])
```

---

#### 2. Best Opportunity Alert

**Location:** Below statistics cards

**Normal State (Opportunity Detected):**
```
┌─────────────────────────────────────────────────────────────┐
│ 🚀 BEST OPPORTUNITY                                         │
│                                                             │
│ Buy BTC-USD @ Binance: $43,250.00                          │
│ Sell BTC-USD @ Coinbase: $43,580.00                        │
│ Spread: $330.00                                             │
│ Profit: +0.76% (after fees: 0.1% + 0.6%)                   │
│ Time: 14:23:45                                              │
└─────────────────────────────────────────────────────────────┘
```
- **Color:** Green (`success` theme)
- **Font Size:** Large (H3 for profit %)
- **Updates:** Every 1 second

**No Opportunity State:**
```
┌─────────────────────────────────────────────────────────────┐
│ ℹ️ No opportunities detected in the last 5 minutes          │
│ Waiting for profitable spreads...                           │
└─────────────────────────────────────────────────────────────┘
```
- **Color:** Gray (`secondary` theme)
- **Updates:** Every 1 second

**Implementation:**
```python
def create_best_opportunity_alert(best_opp):
    if not best_opp:
        return dbc.Alert("No opportunities detected", color="secondary")

    return dbc.Alert([
        html.H3("🚀 BEST OPPORTUNITY"),
        html.P(f"Buy {best_opp.symbol} @ {best_opp.buy_exchange}: ${best_opp.buy_price:.2f}"),
        html.P(f"Sell {best_opp.symbol} @ {best_opp.sell_exchange}: ${best_opp.sell_price:.2f}"),
        html.P(f"Spread: ${best_opp.spread:.2f}"),
        html.H4(f"Profit: +{best_opp.profit_percent:.2f}%", style={'color': 'green'}),
        html.Small(f"Time: {best_opp.timestamp.strftime('%H:%M:%S')}")
    ], color="success")
```

---

#### 3. Live Price Charts

**Location:** Center of dashboard

**Chart Configuration:**
- **Type:** Multi-line time-series chart (Plotly `go.Scatter`)
- **Lines:** 9 total (3 symbols × 3 exchanges)
- **X-axis:** Time (last 5 minutes, rolling window)
- **Y-axis:** Price (USD)
- **Updates:** Every 1 second

**Color Coding:**
- **Coinbase:** Blue (`#1f77b4`)
- **Binance:** Green (`#2ca02c`)
- **Bitstamp:** Red (`#d62728`)

**Trace Labels:**
```
BTC-USD - Coinbase (blue solid line)
BTC-USD - Binance (green solid line)
BTC-USD - Bitstamp (red solid line)
ETH-USD - Coinbase (blue dashed line)
ETH-USD - Binance (green dashed line)
ETH-USD - Bitstamp (red dashed line)
SOL-USD - Coinbase (blue dotted line)
SOL-USD - Binance (green dotted line)
SOL-USD - Bitstamp (red dotted line)
```

**Interactive Features:**
- Hover tooltip: Shows exact price, timestamp, exchange
- Zoom: Click and drag on chart
- Pan: Shift + drag
- Reset: Double-click
- Legend toggle: Click exchange name to hide/show

**Implementation:**
```python
def create_price_chart(price_buffer):
    fig = go.Figure()

    colors = {'coinbase': '#1f77b4', 'binance': '#2ca02c', 'bitstamp': '#d62728'}
    symbols = ['BTC-USD', 'ETH-USD', 'SOL-USD']
    exchanges = ['coinbase', 'binance', 'bitstamp']

    for symbol in symbols:
        for exchange in exchanges:
            prices = [p for p in price_buffer[symbol] if p.exchange == exchange]
            if prices:
                fig.add_trace(go.Scatter(
                    x=[p.timestamp for p in prices],
                    y=[p.price for p in prices],
                    mode='lines',
                    name=f"{symbol} - {exchange}",
                    line=dict(color=colors[exchange])
                ))

    fig.update_layout(
        title="Live Price Tracking",
        xaxis_title="Time",
        yaxis_title="Price (USD)",
        hovermode='x unified',
        template='plotly_dark'
    )

    return fig
```

**Data Source:**
```python
# Called every second
price_buffer = detector.get_price_buffer()  # Dict[str, deque[PriceData]]
# Example: price_buffer['BTC-USD'] = deque([PriceData(...), ...], maxlen=1000)
```

---

#### 4. Opportunities Table

**Location:** Below price charts

**Table Schema:**
```
┌──────────┬────────┬─────────────┬──────────────┬────────┬──────────┐
│ Time     │ Symbol │ Buy Exchange│ Sell Exchange│ Spread │ Profit % │
├──────────┼────────┼─────────────┼──────────────┼────────┼──────────┤
│ 14:23:45 │ BTC    │ Binance     │ Coinbase     │ $330   │  0.76%   │
│ 14:23:42 │ ETH    │ Bitstamp    │ Binance      │ $12.50 │  0.68%   │
│ 14:23:38 │ BTC    │ Binance     │ Bitstamp     │ $280   │  0.64%   │
│ 14:23:35 │ SOL    │ Coinbase    │ Binance      │ $0.85  │  0.61%   │
│ ...      │ ...    │ ...         │ ...          │ ...    │  ...     │
└──────────┴────────┴─────────────┴──────────────┴────────┴──────────┘
```

**Features:**
- **Sorting:** Default sort by profit % (descending)
- **Row Limit:** Top 20 opportunities
- **Color Coding:**
  - Green row: Profit > 1.0%
  - Yellow row: Profit 0.7-1.0%
  - White row: Profit < 0.7%
- **Updates:** Every 1 second

**Columns:**

| Column | Format | Example |
|--------|--------|---------|
| Time | `HH:MM:SS` | `14:23:45` |
| Symbol | Short symbol | `BTC`, `ETH`, `SOL` |
| Buy Exchange | Exchange name | `Binance` |
| Sell Exchange | Exchange name | `Coinbase` |
| Spread | `$X.XX` | `$330.00` |
| Profit % | `X.XX%` | `0.76%` |

**Implementation:**
```python
def create_opportunities_table(opportunities):
    # Sort by profit descending, take top 20
    sorted_opps = sorted(opportunities, key=lambda x: x.profit_percent, reverse=True)[:20]

    data = []
    for opp in sorted_opps:
        # Color code based on profit
        if opp.profit_percent > 1.0:
            style = {'backgroundColor': '#d4edda'}  # Green
        elif opp.profit_percent > 0.7:
            style = {'backgroundColor': '#fff3cd'}  # Yellow
        else:
            style = {}

        data.append({
            'Time': opp.timestamp.strftime('%H:%M:%S'),
            'Symbol': opp.symbol.split('-')[0],  # BTC-USD → BTC
            'Buy Exchange': opp.buy_exchange.capitalize(),
            'Sell Exchange': opp.sell_exchange.capitalize(),
            'Spread': f"${opp.spread:.2f}",
            'Profit %': f"{opp.profit_percent:.2f}%",
            'style': style
        })

    return dash_table.DataTable(
        id='opportunities-table',
        columns=[{'name': col, 'id': col} for col in data[0].keys() if col != 'style'],
        data=data,
        style_data_conditional=[{'if': {'row_index': i}, **row['style']} for i, row in enumerate(data)],
        style_header={'backgroundColor': '#343a40', 'color': 'white', 'fontWeight': 'bold'},
        style_cell={'textAlign': 'left', 'padding': '10px'},
        sort_action='native',
        filter_action='native'
    )
```

---

#### 5. Spread Heatmap

**Location:** Right side of dashboard

**Heatmap Structure:**
```
Exchange Pair Spread Matrix (%)

              Coinbase   Binance   Bitstamp
Coinbase        0.00      -0.12      +0.18
Binance        +0.12       0.00      +0.25
Bitstamp       -0.18      -0.25       0.00
```

**Color Scale:**
- **Dark Green:** +0.5% or higher (very profitable)
- **Light Green:** +0.2% to +0.5% (moderately profitable)
- **Yellow:** 0% to +0.2% (slightly profitable)
- **Orange:** -0.2% to 0% (slightly unprofitable)
- **Red:** -0.2% or lower (unprofitable)

**Interpretation:**
- **Row = Buy Exchange**
- **Column = Sell Exchange**
- **Value = Average spread when buying from row, selling to column**

**Example Reading:**
- `Binance (row) → Coinbase (col) = +0.12%`
- Meaning: Buy on Binance, sell on Coinbase for 0.12% profit

**Interactive Features:**
- Hover tooltip: Shows exact spread value
- Click cell: Filters opportunities table to that exchange pair

**Implementation:**
```python
def create_spread_heatmap(opportunities):
    exchanges = ['coinbase', 'binance', 'bitstamp']
    spread_matrix = np.zeros((3, 3))

    for i, buy_ex in enumerate(exchanges):
        for j, sell_ex in enumerate(exchanges):
            if i == j:
                spread_matrix[i][j] = 0.0
            else:
                # Get all opportunities for this pair
                pair_opps = [o for o in opportunities
                            if o.buy_exchange == buy_ex and o.sell_exchange == sell_ex]
                spread_matrix[i][j] = np.mean([o.profit_percent for o in pair_opps]) if pair_opps else 0.0

    fig = go.Figure(data=go.Heatmap(
        z=spread_matrix,
        x=[e.capitalize() for e in exchanges],
        y=[e.capitalize() for e in exchanges],
        colorscale='RdYlGn',  # Red-Yellow-Green
        zmid=0,  # Center at 0
        text=spread_matrix,
        texttemplate='%{text:.2f}%',
        textfont={"size": 12},
        colorbar=dict(title="Spread %")
    ))

    fig.update_layout(
        title="Exchange Pair Spread Heatmap",
        xaxis_title="Sell Exchange",
        yaxis_title="Buy Exchange",
        template='plotly_dark'
    )

    return fig
```

---

#### 6. ML Predictions

**Location:** Bottom left of dashboard

**Display Condition:** Only shown after 5 minutes of data collection

**Before 5 Minutes:**
```
┌─────────────────────────────────────────────────────────────┐
│ ℹ️ ML Predictions                                           │
│ Collecting data... (3:42 / 5:00)                            │
│ Predictions will appear after 5 minutes of live data        │
└─────────────────────────────────────────────────────────────┘
```

**After 5 Minutes (Predictions Available):**
```
┌─────────────────────────────────────────────────────────────┐
│ 🤖 ML Spread Predictions (Next 30 Seconds)                  │
│                                                             │
│ BTC-USD: Binance → Coinbase                                │
│   Predicted Spread: +0.68%                                  │
│   Confidence: 85% (R² = 0.78)                               │
│                                                             │
│ ETH-USD: Bitstamp → Binance                                │
│   Predicted Spread: +0.52%                                  │
│   Confidence: 78% (R² = 0.78)                               │
│                                                             │
│ SOL-USD: Coinbase → Binance                                │
│   Predicted Spread: +0.41%                                  │
│   Confidence: 72% (R² = 0.78)                               │
└─────────────────────────────────────────────────────────────┘
```

**Features:**
- **Top 3 Predicted Opportunities:** Sorted by predicted spread (descending)
- **Prediction Horizon:** 30 seconds ahead
- **Confidence:** Based on model R² score
- **Updates:** Every 1 second (model retrains every 5 minutes)

**Implementation:**
```python
def create_ml_predictions(predictor, price_buffer):
    if not predictor.is_trained:
        return dbc.Alert("Collecting data for ML training...", color="info")

    predictions = []
    for symbol in ['BTC-USD', 'ETH-USD', 'SOL-USD']:
        pred_spread = predictor.predict_spread(symbol, price_buffer[symbol])
        predictions.append({
            'symbol': symbol,
            'spread': pred_spread,
            'confidence': predictor.get_confidence()  # R² score
        })

    # Sort by predicted spread
    predictions.sort(key=lambda x: x['spread'], reverse=True)

    children = [html.H4("🤖 ML Spread Predictions (Next 30 Seconds)")]
    for pred in predictions[:3]:  # Top 3
        children.extend([
            html.Hr(),
            html.P([
                html.Strong(f"{pred['symbol']}"),
                html.Br(),
                f"Predicted Spread: +{pred['spread']:.2f}%",
                html.Br(),
                f"Confidence: {pred['confidence']*100:.0f}% (R² = {pred['confidence']:.2f})"
            ])
        ])

    return dbc.Alert(children, color="primary")
```

---

#### 7. Backtest Results

**Location:** Bottom right of dashboard

**Display:**
```
┌─────────────────────────────────────────────────────────────┐
│ 📊 Simulated Performance (if all opportunities executed)    │
│                                                             │
│ Initial Capital:      $10,000.00                            │
│ Final Capital:        $10,847.32                            │
│                                                             │
│ Total Trades:         142                                   │
│ Winning Trades:       103 (72.5%)                           │
│ Losing Trades:        39 (27.5%)                            │
│                                                             │
│ Total Profit:         $847.32 (+8.47%)                      │
│ Average Profit/Trade: $5.97                                 │
│ Largest Win:          $52.30                                │
│ Largest Loss:         -$18.45                               │
│                                                             │
│ Sharpe Ratio:         2.34 (excellent)                      │
│ Max Drawdown:         -1.2%                                 │
│ Sortino Ratio:        3.12                                  │
└─────────────────────────────────────────────────────────────┘
```

**Calculation Details:**

**Trade Simulation:**
```python
for opportunity in opportunities:
    # Apply slippage (0.1%)
    actual_buy_price = opportunity.buy_price * 1.001
    actual_sell_price = opportunity.sell_price * 0.999

    # Apply fees
    buy_fee = actual_buy_price * EXCHANGE_FEES[opportunity.buy_exchange]
    sell_fee = actual_sell_price * EXCHANGE_FEES[opportunity.sell_exchange]

    # Calculate profit
    profit = (actual_sell_price - actual_buy_price) - (buy_fee + sell_fee)

    # Update capital
    if profit > 0:
        winning_trades += 1
    else:
        losing_trades += 1

    capital += profit
```

**Metrics:**

| Metric | Formula | Interpretation |
|--------|---------|----------------|
| **Win Rate** | `winning_trades / total_trades * 100` | Percentage of profitable trades |
| **Sharpe Ratio** | `(mean_return - risk_free_rate) / std_return` | Risk-adjusted return (>2 = excellent) |
| **Max Drawdown** | `max(peak - trough) / peak` | Largest peak-to-trough decline |
| **Sortino Ratio** | `(mean_return - risk_free_rate) / downside_std` | Downside risk-adjusted return |

---

### Dashboard Update Mechanism

**Callback Function:**
```python
@app.callback(
    [
        Output('stats-cards', 'children'),
        Output('best-opportunity-alert', 'children'),
        Output('price-chart', 'figure'),
        Output('opportunities-table', 'data'),
        Output('spread-heatmap', 'figure'),
        Output('ml-predictions', 'children'),
        Output('backtest-results', 'children')
    ],
    [Input('interval-component', 'n_intervals')]
)
def update_dashboard(n):
    # Fetch fresh data
    opportunities = detector.get_recent_opportunities(minutes=5)
    best_opp = detector.get_best_opportunity()
    stats = detector.get_statistics()
    price_buffer = detector.get_price_buffer()

    # Create components
    stats_cards = create_stats_cards(opportunities)
    best_alert = create_best_opportunity_alert(best_opp)
    price_fig = create_price_chart(price_buffer)
    table_data = create_opportunities_table(opportunities)
    heatmap_fig = create_spread_heatmap(opportunities)
    ml_preds = create_ml_predictions(predictor, price_buffer)
    backtest = create_backtest_results(opportunities)

    return [stats_cards, best_alert, price_fig, table_data, heatmap_fig, ml_preds, backtest]
```

**Interval Component:**
```python
dcc.Interval(
    id='interval-component',
    interval=1000,  # Update every 1 second (1000ms)
    n_intervals=0
)
```

---

### Performance Optimization Tips

**1. Limit Data Rendering:**
```python
# Only render last 5 minutes of price data
price_data_5min = [p for p in price_buffer if (now() - p.timestamp).seconds < 300]
```

**2. Use `scattergl` for Large Datasets:**
```python
fig.add_trace(go.Scattergl(  # Use WebGL for >1000 points
    x=timestamps,
    y=prices,
    mode='lines'
))
```

**3. Debounce Table Updates:**
```python
# Only update table if data actually changed
if hash(opportunities) != previous_hash:
    update_table()
```

**4. Lazy Load Components:**
```python
# Don't render ML predictions until 5 min mark
if runtime < 300:
    return dcc.Loading(html.Div("Loading..."))
```

---

## Dashboard 2: 🔬 Arbitrage Analytics Suite

**File:** [analytics_dashboard.py](analytics_dashboard.py)
**Port:** 8051
**Purpose:** Advanced analytics and strategy optimization
**Update Frequency:** 5 seconds

### Launch Command
```bash
python run_analytics.py
# Dashboard opens at http://localhost:8051
```

---

### Tab Structure

#### Tab 1: Strategy Parameters Discovery

**Goal:** Find optimal trading parameters based on historical data

**Visualizations:**

##### 1. Spread Distribution Histogram

```
Distribution of Spreads Detected (After Fees)

Frequency
    35 |           ███
    30 |         █████
    25 |       ███████
    20 |     █████████
    15 |   ███████████
    10 | █████████████████
     5 |███████████████████
     0 ─────────────────────────────
       0.0  0.3  0.5  0.7  1.0  1.5  2.0  2.5
                Spread % (after fees)

Statistics:
- Mean: 0.68%
- Median: 0.61%
- Std Dev: 0.32%
- 25th Percentile: 0.52%
- 75th Percentile: 0.82%
- 95th Percentile: 1.25%

Recommended Profit Thresholds:
- Conservative: 0.82% (75th percentile, ~25% of opportunities)
- Moderate: 0.61% (50th percentile, ~50% of opportunities)
- Aggressive: 0.52% (25th percentile, ~75% of opportunities)
```

**Implementation:**
```python
def create_spread_distribution(opportunities):
    spreads = [o.profit_percent for o in opportunities]

    fig = go.Figure()
    fig.add_trace(go.Histogram(
        x=spreads,
        nbinsx=30,
        name='Spread Distribution',
        marker_color='#2ca02c'
    ))

    # Add percentile lines
    fig.add_vline(x=np.percentile(spreads, 25), line_dash="dash",
                  annotation_text="25th %ile")
    fig.add_vline(x=np.percentile(spreads, 50), line_dash="solid",
                  annotation_text="Median")
    fig.add_vline(x=np.percentile(spreads, 75), line_dash="dash",
                  annotation_text="75th %ile")
    fig.add_vline(x=np.percentile(spreads, 95), line_dash="dot",
                  annotation_text="95th %ile")

    fig.update_layout(
        title="Spread Distribution (After Fees)",
        xaxis_title="Spread %",
        yaxis_title="Frequency",
        template='plotly_dark'
    )

    return fig
```

##### 2. Opportunity Duration Analysis

```
How Long Do Opportunities Last?

Duration Distribution (seconds)

Frequency
    25 |     ███
    20 |   █████
    15 | ███████
    10 |█████████
     5 |███████████
     0 ─────────────────────────
       0  2  4  6  8 10 12 14 16
          Duration (seconds)

Statistics:
- Mean Duration: 4.2 seconds
- Median Duration: 3.1 seconds
- 95th Percentile: 12.5 seconds
- Max Duration: 28.3 seconds

Implications:
- Need execution speed <3 seconds to capture 50% of opportunities
- Need <4.2 seconds to capture 70% of opportunities
- Need <12.5 seconds to capture 95% of opportunities

Execution Speed Requirements:
┌─────────────────┬────────────────────┐
│ Execution Time  │ % Opportunities    │
├─────────────────┼────────────────────┤
│ <1 second       │ 15%                │
│ <3 seconds      │ 50%                │
│ <5 seconds      │ 75%                │
│ <10 seconds     │ 90%                │
│ <15 seconds     │ 98%                │
└─────────────────┴────────────────────┘
```

**Calculation:**
```python
def analyze_opportunity_duration(opportunities):
    # Group opportunities by symbol + exchange pair
    grouped = defaultdict(list)
    for opp in opportunities:
        key = (opp.symbol, opp.buy_exchange, opp.sell_exchange)
        grouped[key].append(opp)

    durations = []
    for key, opps in grouped.items():
        # Sort by timestamp
        opps.sort(key=lambda x: x.timestamp)

        # Calculate duration as time between first and last occurrence
        if len(opps) > 1:
            duration = (opps[-1].timestamp - opps[0].timestamp).total_seconds()
            durations.append(duration)

    return {
        'mean': np.mean(durations),
        'median': np.median(durations),
        'percentile_95': np.percentile(durations, 95),
        'max': max(durations)
    }
```

##### 3. Exchange Pair Performance

```
Most Profitable Exchange Pairs (Last 24 Hours)

┌─────────────────────────┬──────┬──────────┬──────────┬──────────┐
│ Exchange Pair           │ Opps │ Avg %    │ Max %    │ Win Rate │
├─────────────────────────┼──────┼──────────┼──────────┼──────────┤
│ Binance → Coinbase      │  47  │  0.82%   │  2.15%   │  78.7%   │
│ Bitstamp → Binance      │  35  │  0.71%   │  1.89%   │  74.3%   │
│ Coinbase → Bitstamp     │  28  │  0.64%   │  1.42%   │  71.4%   │
│ Binance → Bitstamp      │  22  │  0.59%   │  1.31%   │  68.2%   │
│ Coinbase → Binance      │  10  │  0.54%   │  0.98%   │  60.0%   │
│ Bitstamp → Coinbase     │   8  │  0.51%   │  0.87%   │  62.5%   │
└─────────────────────────┴──────┴──────────┴──────────┴──────────┘

Insights:
1. Binance → Coinbase is the best pair (highest avg %, most opportunities)
2. Buying on Binance is generally more profitable (lower fees: 0.1%)
3. Selling on Coinbase has higher prices (but 0.6% fee eats profit)
4. Win rate >70% for top 3 pairs

Recommendation: Focus trading on top 3 pairs for best risk/reward
```

**Bar Chart Visualization:**
```python
def create_exchange_pair_performance(opportunities):
    # Count opportunities per exchange pair
    pair_stats = defaultdict(lambda: {'count': 0, 'spreads': []})

    for opp in opportunities:
        pair = f"{opp.buy_exchange} → {opp.sell_exchange}"
        pair_stats[pair]['count'] += 1
        pair_stats[pair]['spreads'].append(opp.profit_percent)

    # Create bar chart
    pairs = []
    counts = []
    avg_spreads = []

    for pair, stats in sorted(pair_stats.items(),
                              key=lambda x: np.mean(x[1]['spreads']),
                              reverse=True):
        pairs.append(pair.replace(' → ', ' to ').title())
        counts.append(stats['count'])
        avg_spreads.append(np.mean(stats['spreads']))

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=pairs,
        y=avg_spreads,
        marker_color=counts,
        marker_colorscale='Viridis',
        text=[f"{s:.2f}%" for s in avg_spreads],
        textposition='outside'
    ))

    fig.update_layout(
        title="Average Spread by Exchange Pair",
        xaxis_title="Exchange Pair",
        yaxis_title="Average Spread %",
        template='plotly_dark'
    )

    return fig
```

##### 4. Symbol Volatility & Correlation

**Volatility Chart:**
```
Rolling 1-Hour Volatility (Standard Deviation of Returns)

Volatility %
    1.5 |                    ╱╲
    1.2 |                   ╱  ╲    ╱╲
    1.0 |         ╱╲       ╱    ╲  ╱  ╲
    0.8 |        ╱  ╲     ╱      ╲╱    ╲
    0.6 |       ╱    ╲   ╱             ╲
    0.4 |  ╱╲  ╱      ╲ ╱               ╲
    0.2 | ╱  ╲╱        ╲╱
    0.0 ─────────────────────────────────────
        10:00  11:00  12:00  13:00  14:00  15:00
                      Time

Legend:
- Blue: BTC-USD (0.45% avg volatility)
- Green: ETH-USD (0.68% avg volatility)
- Red: SOL-USD (1.12% avg volatility)

Insight: Higher volatility → More arbitrage opportunities
```

**Correlation Matrix:**
```
Exchange Price Correlation (Pearson Correlation)

              Coinbase  Binance  Bitstamp
Coinbase        1.00     0.94      0.89
Binance         0.94     1.00      0.91
Bitstamp        0.89     0.91      1.00

Interpretation:
- High correlation (>0.9) = Prices move together
- Lower correlation = More arbitrage opportunities
- Binance-Bitstamp has highest correlation (0.91)
- Coinbase-Bitstamp has lowest correlation (0.89)

Implication: Coinbase-Bitstamp pair should have more opportunities
(but data shows Binance-Coinbase is more profitable due to fees)
```

**Implementation:**
```python
def create_correlation_heatmap(price_buffer):
    exchanges = ['coinbase', 'binance', 'bitstamp']
    symbols = ['BTC-USD', 'ETH-USD', 'SOL-USD']

    # Build price matrix
    price_matrix = []
    for symbol in symbols:
        for exchange in exchanges:
            prices = [p.price for p in price_buffer[symbol] if p.exchange == exchange]
            price_matrix.append(prices)

    # Calculate correlation
    corr_matrix = np.corrcoef(price_matrix)

    fig = go.Figure(data=go.Heatmap(
        z=corr_matrix,
        x=[f"{e.title()}" for e in exchanges],
        y=[f"{e.title()}" for e in exchanges],
        colorscale='Blues',
        zmin=0, zmax=1,
        text=corr_matrix,
        texttemplate='%{text:.2f}',
        textfont={"size": 12}
    ))

    fig.update_layout(
        title="Exchange Price Correlation Matrix",
        template='plotly_dark'
    )

    return fig
```

---

#### Tab 2: Exchange Health Monitoring

**Goal:** Ensure data quality and identify exchange issues

##### 1. Exchange Uptime Tracking

```
Exchange Uptime (Last 24 Hours)

Coinbase:  99.8% ████████████████████░  (23h 57m)
Binance:   99.9% █████████████████████  (23h 58m)
Bitstamp:  98.5% ███████████████████░░  (23h 38m)

Downtime Events:
┌──────────┬───────────┬──────────┬──────────┐
│ Exchange │ Start     │ Duration │ Reason   │
├──────────┼───────────┼──────────┼──────────┤
│ Bitstamp │ 08:23:15  │  8 min   │ API down │
│ Coinbase │ 12:45:32  │  3 min   │ Restart  │
│ Bitstamp │ 16:12:08  │  4 min   │ Unknown  │
└──────────┴───────────┴──────────┴──────────┘

Status Indicators:
✅ Coinbase: Connected (last update 0.5s ago)
✅ Binance: Connected (last update 0.3s ago)
⚠️  Bitstamp: Slow (last update 3.2s ago)
```

**Implementation:**
```python
def calculate_uptime(connection_log):
    total_time = 86400  # 24 hours in seconds
    downtime = 0

    for event in connection_log:
        if event['type'] == 'disconnect':
            downtime += event['duration']

    uptime_pct = (total_time - downtime) / total_time * 100
    return uptime_pct
```

##### 2. Message Rate Monitoring

```
WebSocket Messages per Second (Real-Time)

Messages/sec
    800 |              ╱╲
    600 |        ╱╲   ╱  ╲    ╱╲
    400 |   ╱╲  ╱  ╲ ╱    ╲  ╱  ╲
    200 |  ╱  ╲╱    ╲╱      ╲╱    ╲
      0 ─────────────────────────────
        0s   10s  20s  30s  40s  50s

Current Rates:
- Coinbase:  342 msg/sec
- Binance:   581 msg/sec
- Bitstamp:  198 msg/sec
- TOTAL:   1,121 msg/sec

Expected Rates:
- Coinbase:  300-400 msg/sec ✅
- Binance:   500-600 msg/sec ✅
- Bitstamp:  150-250 msg/sec ✅

Alerts:
(No anomalies detected)
```

##### 3. Data Freshness Indicators

```
Price Data Staleness (Real-Time)

Symbol     Exchange    Last Update      Age      Status
────────────────────────────────────────────────────────
BTC-USD    Coinbase    14:23:45.123    0.2s     ✅
BTC-USD    Binance     14:23:45.089    0.3s     ✅
BTC-USD    Bitstamp    14:23:42.456    3.1s     ⚠️

ETH-USD    Coinbase    14:23:45.234    0.1s     ✅
ETH-USD    Binance     14:23:45.167    0.2s     ✅
ETH-USD    Bitstamp    14:23:43.892    1.5s     ✅

SOL-USD    Coinbase    14:23:44.987    0.4s     ✅
SOL-USD    Binance     14:23:45.234    0.1s     ✅
SOL-USD    Bitstamp    14:23:41.123    4.2s     ⚠️

Status Legend:
✅ Fresh (<2 seconds old)
⚠️  Stale (2-5 seconds old)
❌ Very stale (>5 seconds old, filtered out)

Warnings:
⚠️  Bitstamp BTC-USD data is stale (3.1s)
⚠️  Bitstamp SOL-USD data is stale (4.2s)
```

##### 4. Exchange Reliability Score

```
Composite Reliability Score (0-100)

Binance:  97 ████████████████████░   Excellent
Coinbase: 95 ███████████████████░░   Excellent
Bitstamp: 89 ██████████████████░░░   Good

Scoring Factors (Weighted):
┌──────────────────┬────────┬────────┬──────────┐
│ Factor           │ Weight │ Binance│ Coinbase │
├──────────────────┼────────┼────────┼──────────┤
│ Uptime %         │  30%   │  99.9  │   99.8   │
│ Message Rate     │  20%   │  581   │   342    │
│ Data Freshness   │  25%   │  0.25s │   0.30s  │
│ Error Rate       │  15%   │  0.1%  │   0.2%   │
│ Latency          │  10%   │  45ms  │   52ms   │
└──────────────────┴────────┴────────┴──────────┘

Recommendation:
- Primary data source: Binance (highest reliability)
- Secondary: Coinbase (high reliability)
- Tertiary: Bitstamp (good but slower)
```

---

#### Tab 3: Anomaly Detection

##### 1. Unusual Spread Detection

```
Anomaly Alerts (Real-Time)

🚨 ALERT: Unusual Spread Detected
Time: 14:18:32
Symbol: BTC-USD
Exchange Pair: Binance → Coinbase
Spread: 2.85% (normally 0.65% ± 0.25%)
Deviation: +8.8σ (sigma)

Likely Causes:
1. Large market order on one exchange
2. Liquidity event (order book thin)
3. Exchange API lag
4. Flash crash on one exchange

Action Taken:
- Flagged for manual review
- Excluded from ML training (outlier)
- Risk warning issued to trading bots

─────────────────────────────────────────────────

🔍 INVESTIGATING: Price Divergence
Time: 14:22:15
Symbol: ETH-USD
Exchanges: Coinbase ($2,340) vs Binance ($2,355)
Divergence: +0.64% (unusual but within 3σ)
Duration: 8 seconds (still active)

Monitoring: Will alert if persists >30 seconds
```

**Z-Score Calculation:**
```python
def detect_anomalies(opportunities):
    spreads = [o.profit_percent for o in opportunities]
    mean_spread = np.mean(spreads)
    std_spread = np.std(spreads)

    anomalies = []
    for opp in opportunities:
        z_score = (opp.profit_percent - mean_spread) / std_spread
        if abs(z_score) > 3:  # >3 sigma
            anomalies.append({
                'opportunity': opp,
                'z_score': z_score,
                'severity': 'HIGH' if abs(z_score) > 5 else 'MEDIUM'
            })

    return anomalies
```

##### 2. Volume Spike Detection

```
Volume Anomalies Detected

BTC-USD @ Binance
────────────────────────────────────
Normal Volume:     125 BTC/min
Current Volume:    487 BTC/min (+289%)
Time:              14:25:18
Duration:          Last 90 seconds

Analysis:
- Volume >3x normal → Large institutional order
- Spread temporarily increased to 1.8%
- Arbitrage opportunity duration extended to 12 seconds
- Reversion to mean expected within 5 minutes

Action:
✅ Opportunity flagged as "high confidence"
✅ ML bot increased position size (+20%)

─────────────────────────────────────

SOL-USD @ Coinbase
────────────────────────────────────
Normal Volume:     45 SOL/min
Current Volume:    18 SOL/min (-60%)
Time:              14:28:45
Duration:          Last 3 minutes

Analysis:
- Low liquidity → Higher slippage risk
- Spread appears profitable but risky to execute
- Market maker may have withdrawn liquidity

Action:
⚠️  Opportunity flagged as "low confidence"
⚠️  ML bot reduced position size (-50%)
```

##### 3. Risk Flags Summary

```
Active Risk Warnings

⚠️  HIGH VOLATILITY
    Symbol: ETH-USD
    1-hour volatility: 1.2% (normal: 0.6%)
    Recommendation: Reduce position size

⚠️  EXCHANGE LAG
    Exchange: Bitstamp
    Latency: >3 seconds (normal: <1 second)
    Recommendation: Use caution with Bitstamp opportunities

✅  ALL OTHER SYSTEMS NORMAL
    BTC-USD: Normal volatility, good liquidity
    SOL-USD: Normal volatility, normal liquidity
    Coinbase: Normal latency
    Binance: Normal latency
```

---

#### Tab 4: Historical Analysis

##### 1. Long-Term Trend Analysis

```
Arbitrage Opportunities per Hour (Last 7 Days)

Opportunities/hour
    70 |        *
    60 |       * *
    50 |      * * *     *
    40 |    * * * * *  * *
    30 |   * * * * * * * * *
    20 |  * * * * * * * * * *
    10 | * * * * * * * * * * *
     0 ─────────────────────────────────
       Mon Tue Wed Thu Fri Sat Sun Mon

Insights:
- Peak activity: Wednesday 10am-12pm EST (68 opps/hour)
- Lowest activity: Saturday 3am-5am EST (8 opps/hour)
- Average: 42 opps/hour
- Weekly pattern: Higher on weekdays, lower on weekends
```

##### 2. Time-of-Day Effects

```
Average Spread by Hour (EST)

Avg Spread %
    1.0 |        ███
    0.9 |      ███████
    0.8 |    █████████
    0.7 |  ███████████
    0.6 |█████████████████
    0.5 |███████████████████
        ─────────────────────────
        0  4  8  12 16 20 24
              Hour (EST)

Best Trading Hours:
- 9am-11am EST: 0.85% avg spread (market open volatility)
- 2pm-4pm EST: 0.78% avg spread (afternoon session)
- 8pm-10pm EST: 0.72% avg spread (Asian market open)

Worst Trading Hours:
- 3am-5am EST: 0.52% avg spread (low activity)
- 12pm-1pm EST: 0.58% avg spread (lunch lull)
```

##### 3. Performance by Symbol

```
Symbol Performance (Last 30 Days)

┌────────┬──────┬────────────┬────────────┬──────────┐
│ Symbol │ Opps │ Avg Spread │ Max Spread │ Win Rate │
├────────┼──────┼────────────┼────────────┼──────────┤
│ BTC    │ 142  │   0.73%    │   2.15%    │  75.4%   │
│ ETH    │ 108  │   0.68%    │   1.95%    │  72.2%   │
│ SOL    │  89  │   0.81%    │   3.42%    │  68.5%   │
└────────┴──────┴────────────┴────────────┴──────────┘

Box Plot Visualization:
        BTC          ETH          SOL
        │            │            │
   3% ─ ┘            │            *  ← Outlier
   2% ─              *            ┐
   1% ─ ┬────────┐   ┬────────┐  ├────────┐
      ─ │▓▓▓▓▓▓▓▓│   │▓▓▓▓▓▓▓▓│  │▓▓▓▓▓▓▓▓│
   0% ─ ┴────────┘   ┴────────┘  ┴────────┘

Insights:
- SOL: Highest avg spread (0.81%) but lower win rate (68.5%)
- BTC: Most reliable (75.4% win rate) with moderate spread
- ETH: Balanced performance (middle ground)

Recommendation:
- Conservative traders: Focus on BTC (highest win rate)
- Aggressive traders: Focus on SOL (highest profit potential)
- Balanced traders: Diversify across all three
```

---

### Analytics Dashboard Update Mechanism

**Callback:**
```python
@app.callback(
    [
        Output('spread-distribution', 'figure'),
        Output('duration-analysis', 'children'),
        Output('exchange-pair-performance', 'figure'),
        Output('volatility-chart', 'figure'),
        Output('correlation-heatmap', 'figure'),
        # ... more outputs
    ],
    [Input('interval-component', 'n_intervals')]
)
def update_analytics(n):
    # Fetch data (try detector first, fallback to CSV)
    try:
        opportunities = detector.get_all_opportunities()
        price_buffer = detector.get_price_buffer()
    except:
        opportunities = load_from_csv('captured_data/opportunities.csv')
        price_buffer = load_from_csv('captured_data/prices.csv')

    # Create visualizations
    spread_dist = create_spread_distribution(opportunities)
    duration = analyze_duration(opportunities)
    pair_perf = create_exchange_pair_performance(opportunities)
    volatility = create_volatility_chart(price_buffer)
    correlation = create_correlation_heatmap(price_buffer)

    return [spread_dist, duration, pair_perf, volatility, correlation, ...]
```

**Interval:**
```python
dcc.Interval(
    id='interval-component',
    interval=5000,  # Update every 5 seconds
    n_intervals=0
)
```

---

## Dashboard 3: 🤖 Arbitrage Bot Backtest Comparison

**File:** [backtest_dashboard.py](backtest_dashboard.py)
**Port:** 8052
**Purpose:** Compare ML bot vs Benchmark bot performance
**Update Frequency:** Static (loaded once at startup)

### Launch Command
```bash
python run_backtest.py
# Runs backtest simulation, then opens dashboard at http://localhost:8052
```

---

### 8 Visualization Components

#### 1. Performance Comparison Table

```
┌─────────────────────┬────────────┬──────────────┐
│      Metric         │   ML Bot   │ Benchmark Bot│
├─────────────────────┼────────────┼──────────────┤
│ Total Trades        │    104     │      87      │
│ Winning Trades      │     75     │      60      │
│ Losing Trades       │     29     │      27      │
│ Win Rate            │   72.1%    │    68.9%     │
│ Total Profit        │  $847.32   │   $623.18    │
│ Return %            │  +8.47%    │   +6.23%     │
│ Avg Trade Profit    │  $8.15     │   $7.16      │
│ Largest Win         │  $52.30    │   $48.12     │
│ Largest Loss        │ -$18.45    │  -$31.27     │
│ Sharpe Ratio        │   2.34     │    1.87      │
│ Sortino Ratio       │   3.12     │    2.45      │
│ Max Drawdown        │  -1.2%     │   -2.1%      │
│ Calmar Ratio        │   7.06     │    2.97      │
│ Profit Factor       │   2.87     │    2.31      │
└─────────────────────┴────────────┴──────────────┘

Winner: ML Bot
Improvement: +36% higher profit, +25% better Sharpe ratio
```

**Implementation:**
```python
def create_performance_table(ml_results, benchmark_results):
    data = [
        {'Metric': 'Total Trades', 'ML Bot': ml_results['total_trades'],
         'Benchmark': benchmark_results['total_trades']},
        {'Metric': 'Win Rate', 'ML Bot': f"{ml_results['win_rate']:.1f}%",
         'Benchmark': f"{benchmark_results['win_rate']:.1f}%"},
        # ... more metrics
    ]

    return dash_table.DataTable(
        columns=[{'name': col, 'id': col} for col in ['Metric', 'ML Bot', 'Benchmark']],
        data=data,
        style_data_conditional=[
            {
                'if': {
                    'filter_query': '{ML Bot} > {Benchmark}',
                    'column_id': 'ML Bot'
                },
                'backgroundColor': '#d4edda',  # Green
                'fontWeight': 'bold'
            }
        ]
    )
```

#### 2. Capital Curves (Portfolio Value Over Time)

```
Portfolio Value Over Time

Value ($)
$11,000 |                          ╱───── ML Bot
        |                        ╱
$10,500 |                      ╱
        |                    ╱  ╱───── Benchmark
$10,000 |──────────────────╱──╱
        |
 $9,500 |
        ─────────────────────────────────────────
        0min     30min    60min    90min   120min

Key Observations:
- ML Bot: Smoother growth curve (less volatile)
- Benchmark: More jagged (higher volatility)
- ML Bot final value: $10,847.32 (+8.47%)
- Benchmark final value: $10,623.18 (+6.23%)
- ML Bot never drops below $10,000 (no negative periods)
- Benchmark has 2 periods below starting capital
```

**Implementation:**
```python
def create_capital_curve(ml_trades, benchmark_trades):
    # Calculate cumulative capital
    ml_capital = [10000]  # Start with $10k
    for trade in ml_trades:
        ml_capital.append(ml_capital[-1] + trade['profit'])

    benchmark_capital = [10000]
    for trade in benchmark_trades:
        benchmark_capital.append(benchmark_capital[-1] + trade['profit'])

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=list(range(len(ml_capital))),
        y=ml_capital,
        mode='lines',
        name='ML Bot',
        line=dict(color='#2ca02c', width=3)
    ))
    fig.add_trace(go.Scatter(
        x=list(range(len(benchmark_capital))),
        y=benchmark_capital,
        mode='lines',
        name='Benchmark Bot',
        line=dict(color='#ff7f0e', width=3)
    ))

    fig.update_layout(
        title="Portfolio Value Over Time",
        xaxis_title="Trade Number",
        yaxis_title="Portfolio Value ($)",
        template='plotly_dark'
    )

    return fig
```

#### 3. Win Rate Comparison (Bar Chart)

```
Win Rate Comparison

100%|
    |
 80%|  ████          ████
    |  ████          ████
 60%|  ████          ████
    |  ████          ████
 40%|  ████          ████
    |  ████          ████
 20%|  ████          ████
    |  ████          ████
  0%|──────────────────────
      ML Bot    Benchmark

ML Bot: 72.1% (75 wins / 104 trades)
Benchmark: 68.9% (60 wins / 87 trades)
Difference: +3.2 percentage points
```

#### 4. Return Comparison (Bar Chart)

```
Total Return %

10% |
    |
 8% |  ████
    |  ████
 6% |  ████          ████
    |  ████          ████
 4% |  ████          ████
    |  ████          ████
 2% |  ████          ████
    |  ████          ████
 0% |──────────────────────
      ML Bot    Benchmark

ML Bot: +8.47% ($847.32 profit on $10k)
Benchmark: +6.23% ($623.18 profit on $10k)
Difference: +2.24 percentage points (+36% more profit)
```

#### 5. Profit Distribution (Histogram)

```
Distribution of Individual Trade Profits

Frequency
    30 |           █
       |          ███
    25 |         █████
       |        ███████
    20 |       █████████
       |      ███████████        █
    15 |     █████████████      ███
       |    ███████████████    █████
    10 |   █████████████████  ███████
       |  ███████████████████████████
     5 | █████████████████████████████
       |███████████████████████████████
     0 ─────────────────────────────────
      -$30  -$20  -$10   $0  +$10 +$20 +$30
                Trade Profit

Legend:
- Green bars: ML Bot (tighter distribution around mean)
- Orange bars: Benchmark Bot (wider spread)

ML Bot Statistics:
- Mean: $8.15
- Std Dev: $12.30 (lower risk)
- Range: -$18.45 to +$52.30

Benchmark Statistics:
- Mean: $7.16
- Std Dev: $18.75 (higher risk)
- Range: -$31.27 to +$48.12

Insight: ML bot has more consistent profits (lower variance)
```

**Implementation:**
```python
def create_profit_distribution(ml_trades, benchmark_trades):
    ml_profits = [t['profit'] for t in ml_trades]
    benchmark_profits = [t['profit'] for t in benchmark_trades]

    fig = go.Figure()
    fig.add_trace(go.Histogram(
        x=ml_profits,
        name='ML Bot',
        opacity=0.7,
        marker_color='#2ca02c',
        nbinsx=30
    ))
    fig.add_trace(go.Histogram(
        x=benchmark_profits,
        name='Benchmark Bot',
        opacity=0.7,
        marker_color='#ff7f0e',
        nbinsx=30
    ))

    fig.update_layout(
        title="Distribution of Trade Profits",
        xaxis_title="Profit per Trade ($)",
        yaxis_title="Frequency",
        barmode='overlay',
        template='plotly_dark'
    )

    return fig
```

#### 6. Sharpe Ratio Chart

```
Sharpe Ratio (Risk-Adjusted Return)

Higher is better (>2 is excellent)

3.0 |
    |
2.5 |  ████
    |  ████
2.0 |  ████          ████
    |  ████          ████
1.5 |  ████          ████
    |  ████          ████
1.0 |  ████          ████
    |  ████          ████
0.5 |  ████          ████
    |  ████          ████
0.0 |──────────────────────
      ML Bot    Benchmark

ML Bot: 2.34 (excellent)
Benchmark: 1.87 (good)
Difference: +25% better risk-adjusted returns

Formula: (Mean Return - Risk-Free Rate) / Std Dev of Returns
Risk-Free Rate: 0% (assumed)
```

**Sharpe Ratio Interpretation:**
- **<1.0:** Poor (not worth the risk)
- **1.0-2.0:** Good (acceptable risk/reward)
- **2.0-3.0:** Excellent (great risk/reward)
- **>3.0:** Exceptional (very rare)

#### 7. Maximum Drawdown Chart

```
Maximum Drawdown (Peak-to-Trough Decline)

Lower is better

 0% |──────────────────────
    |            ████
-1% |  ████      ████
    |  ████      ████
-2% |  ████      ████
    |  ████      ████
-3% |  ████      ████
    |──────────────────────
      ML Bot    Benchmark

ML Bot: -1.2% (less risky)
Benchmark: -2.1% (more risky)
Difference: 75% lower maximum drawdown

Interpretation:
- ML Bot: Worst losing streak was only 1.2% of capital
- Benchmark: Worst losing streak was 2.1% of capital
- ML Bot better protects against downside risk
```

**Drawdown Calculation:**
```python
def calculate_max_drawdown(capital_curve):
    peak = capital_curve[0]
    max_dd = 0

    for value in capital_curve:
        if value > peak:
            peak = value
        dd = (peak - value) / peak
        if dd > max_dd:
            max_dd = dd

    return max_dd * 100  # Convert to percentage
```

#### 8. Trade Timeline (Scatter Plot)

```
Individual Trades Over Time

Profit ($)
+$60|                    *
    |
+$40|              *  *     *
    |        *  *
+$20|  *  *  *  * *  *  *  *
    |────────────────────────────
  $0|────────────────────────────
    |     *        *
-$20|
    |
-$40|
    ─────────────────────────────
    0    20   40   60   80  100
          Trade Number

Legend:
🔵 Blue circles: ML Bot trades
🔴 Red triangles: Benchmark Bot trades

Observations:
- ML Bot: More clustered around positive profits
- Benchmark: More scattered (higher variance)
- ML Bot: Fewer large losses (better risk management)
- Benchmark: Has some large wins, but also large losses
```

**Implementation:**
```python
def create_trade_timeline(ml_trades, benchmark_trades):
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=list(range(len(ml_trades))),
        y=[t['profit'] for t in ml_trades],
        mode='markers',
        name='ML Bot',
        marker=dict(
            size=8,
            color='#2ca02c',
            symbol='circle'
        )
    ))

    fig.add_trace(go.Scatter(
        x=list(range(len(benchmark_trades))),
        y=[t['profit'] for t in benchmark_trades],
        mode='markers',
        name='Benchmark Bot',
        marker=dict(
            size=8,
            color='#ff7f0e',
            symbol='triangle-up'
        )
    ))

    # Add zero line
    fig.add_hline(y=0, line_dash="dash", line_color="white", opacity=0.5)

    fig.update_layout(
        title="Trade Timeline",
        xaxis_title="Trade Number",
        yaxis_title="Profit ($)",
        template='plotly_dark'
    )

    return fig
```

---

### Backtest Dashboard Data Flow

**Backtest Execution (run_backtest.py):**
```python
# 1. Load historical opportunities
opportunities = load_opportunities('captured_data/opportunities.csv')

# 2. Initialize bots
ml_bot = MLArbitrageBot(initial_capital=10000)
benchmark_bot = BenchmarkBot(initial_capital=10000)

# 3. Run backtest
for opp in opportunities:
    # ML Bot decision
    if ml_bot.should_execute(opp):
        ml_trade = backtest_engine.simulate_trade(opp, ml_bot)
        ml_trades.append(ml_trade)

    # Benchmark Bot decision
    if benchmark_bot.should_execute(opp):
        bench_trade = backtest_engine.simulate_trade(opp, benchmark_bot)
        benchmark_trades.append(bench_trade)

# 4. Calculate metrics
ml_results = calculate_metrics(ml_trades)
benchmark_results = calculate_metrics(benchmark_trades)

# 5. Save results
save_results('backtest_results/ml_bot_trades.csv', ml_trades)
save_results('backtest_results/benchmark_bot_trades.csv', benchmark_trades)

# 6. Launch dashboard
app = create_dashboard(ml_results, benchmark_results)
app.run_server(port=8052)
```

**Dashboard Loading:**
```python
def create_dashboard(ml_results, benchmark_results):
    app = dash.Dash(__name__)

    app.layout = html.Div([
        html.H1("Arbitrage Bot Backtest Comparison"),

        # Component 1: Performance Table
        html.Div(id='performance-table'),

        # Component 2-8: Charts
        dcc.Graph(id='capital-curve'),
        dcc.Graph(id='win-rate-chart'),
        dcc.Graph(id='return-chart'),
        dcc.Graph(id='profit-distribution'),
        dcc.Graph(id='sharpe-chart'),
        dcc.Graph(id='drawdown-chart'),
        dcc.Graph(id='trade-timeline')
    ])

    # Populate components with data
    # (No callbacks needed - static dashboard)

    return app
```

---

## Summary: Dashboard Quick Reference

### Dashboard 1: 🚀 Monitor (Port 8050)
- **Purpose:** Real-time tracking
- **Updates:** Every 1 second
- **Components:** 7 (Stats, Alert, Charts, Table, Heatmap, ML, Backtest)
- **Use Case:** Live trading monitoring

### Dashboard 2: 🔬 Analytics (Port 8051)
- **Purpose:** Strategy optimization
- **Updates:** Every 5 seconds
- **Components:** 4 tabs, 15+ visualizations
- **Use Case:** Parameter tuning, exchange health

### Dashboard 3: 🤖 Backtest (Port 8052)
- **Purpose:** Bot comparison
- **Updates:** Static (loaded once)
- **Components:** 8 (Table + 7 charts)
- **Use Case:** Strategy evaluation

---

## Common Dashboard Operations

### Exporting Data
```python
# From Monitor Dashboard
opportunities = detector.get_all_opportunities()
df = pd.DataFrame([o.__dict__ for o in opportunities])
df.to_csv('export.csv', index=False)

# From Analytics Dashboard
# Data is already in CSV format in captured_data/

# From Backtest Dashboard
# Data is in backtest_results/ as CSV + JSON
```

### Filtering by Time Range
```python
# Filter last N minutes
recent = detector.get_recent_opportunities(minutes=10)

# Filter by date range
start = datetime(2025, 11, 1)
end = datetime(2025, 11, 2)
filtered = [o for o in opportunities if start <= o.timestamp <= end]
```

### Customizing Update Frequency
```python
# In dashboard.py, change interval
dcc.Interval(
    id='interval-component',
    interval=500,  # 500ms = 2 updates/second (faster)
    # interval=2000,  # 2000ms = 0.5 updates/second (slower)
    n_intervals=0
)
```

### Adding Custom Metrics
```python
# In dashboard.py callback
@app.callback(...)
def update_dashboard(n):
    # Custom metric: Opportunities per minute
    opps_per_min = len(recent_opportunities) / 5  # Last 5 min

    # Custom metric: Average execution time
    avg_exec_time = np.mean([o.duration for o in opportunities])

    # Add to dashboard
    return [..., custom_metric_card]
```
