# Arbitrage Visualization Suite Specification

## Overview

A comprehensive dashboard suite for understanding arbitrage market state between three crypto exchanges, designed for:
1. **Bot builders** - Determining optimal parameters
2. **Bot managers** - Monitoring for anomalies requiring intervention

---

## Suite Organization

```
┌─────────────────────────────────────────┐
│         MAIN DASHBOARD                  │
│  (At-a-glance health & key metrics)     │
└─────────────────────────────────────────┘
           │
    ┌──────┴──────┬──────────┬──────────┐
    ▼             ▼          ▼          ▼
STRATEGY     EXCHANGE    ANOMALY    HISTORICAL
PARAMETERS   HEALTH      DETECTION  ANALYSIS
```

---

## SUITE 1: STRATEGY PARAMETER DISCOVERY

*Purpose: Help bot builders determine optimal configuration*

### 1.1 Spread Distribution & Threshold Calculator

**Visualization:**
```
SPREAD DISTRIBUTION (30-day)

Frequency
3000│         ████
    │         ████
2500│         ████
    │      ██ ████
2000│      ██ ████
    │      ██ ████  ██
1500│   ██ ██ ████  ██
    │   ██ ██ ████  ██  █
1000│   ██ ██ ████  ██  █
    │█  ██ ██ ████  ██  █  █
 500│█  ██ ██ ████  ██  █  █
    │█  ██ ██ ████  ██  █  █
   0└─────────────────────────────────→
    0% 0.2% 0.5% 0.8% 1.0% 1.2% 1.5%
                ↑
         Current fees: 0.76%

INTERACTIVE THRESHOLD SLIDER:
[━━━━━━●━━━━━━━━━━━] 0.76%

Statistics at 0.76% threshold:
- Opportunities per day: 47
- % of time profitable: 3.2%
- Expected daily profit: $850 (@ 1 BTC/trade)
- Monthly ROI: 25.5% (on $100K capital)

Adjust threshold to see:
→ Lower: More opportunities, lower profit per trade
→ Higher: Fewer opportunities, higher profit per trade
```

**Bot Parameter Output:**
```python
MIN_PROFITABLE_SPREAD = 0.0076  # 0.76%
EXPECTED_DAILY_TRADES = 47
```

**Anomalies Detected:**
- 🔴 Spread distribution shifts suddenly (market regime change)
- 🔴 Opportunities drop below 10/day (market too efficient)
- 🟡 Spread pattern changes (adjust threshold)

---

### 1.2 Opportunity Duration Analysis

**Visualization:**
```
OPPORTUNITY LIFESPAN (30-day)

Cumulative %
100%│                        ████
    │                    ████
 90%│                ████
    │            ████
 75%│        ████  ← 75% close within 3.2s
    │    ████
 50%│ ███  ← 50% close within 1.8s
    │██
 25%│█
    │
   0└──────────────────────────────→
    0s  1s  2s  3s  4s  5s  6s  7s

Key Percentiles:
P25: 0.9s
P50: 1.8s  ← MEDIAN
P75: 3.2s
P90: 5.8s
P99: 12.3s

Execution Speed Requirements:
- Miss 25% if slower than: 0.9s ⚠️
- Miss 50% if slower than: 1.8s ❌
- Capture 90% if faster than: 0.9s ✅

Your bot latency: [INPUT] ms
→ Expected capture rate: XX%
```

**Bot Parameter Output:**
```python
MAX_EXECUTION_TIME = 900  # milliseconds
TARGET_LATENCY = 500  # to capture >50%
```

**Anomalies Detected:**
- 🔴 Duration suddenly drops (bots getting faster - arms race)
- 🔴 Duration increases (opportunity to optimize)
- 🟡 Your bot capture rate declining (competitor bots faster)

---

### 1.3 Optimal Trade Size Calculator

**Visualization:**
```
LIQUIDITY DEPTH AT PROFITABLE SPREADS

Available Volume When Spread >0.76%:

       Exchange A         Exchange B
$1M │     10 BTC            8 BTC
    │
$500K│    25 BTC ████      18 BTC ███
    │
$200K│    45 BTC ████████  32 BTC ██████
    │
$100K│    72 BTC ██████████ 58 BTC █████████
    │
$50K │   120 BTC ████████████ 95 BTC ██████████████
    │
    └─────────────────────────────────

Slippage Analysis:
Trade Size   Avg Slippage   Still Profitable?
0.1 BTC      $3 (0.003%)    ✅ Yes
0.5 BTC      $12 (0.011%)   ✅ Yes
1.0 BTC      $38 (0.035%)   ✅ Marginal
2.0 BTC      $127 (0.115%)  ❌ No
5.0 BTC      $445 (0.405%)  ❌ No

RECOMMENDED MAX POSITION: 0.5 BTC
Capital needed: $55,000 per exchange
```

**Bot Parameter Output:**
```python
MAX_TRADE_SIZE = 0.5  # BTC
REQUIRED_CAPITAL_PER_EXCHANGE = 55000  # USD
```

**Anomalies Detected:**
- 🔴 Liquidity drops suddenly (reduce position size)
- 🔴 Slippage increasing (order books thinning)
- 🟡 Large orders appearing (potential manipulation)

---

### 1.4 Fee Tier Impact Matrix

**Visualization:**
```
FEE OPTIMIZATION ANALYSIS

Current Fees:
Exchange A: 0.10% taker
Exchange B: 0.60% taker
Total: 0.70% per round trip

Breakeven spread: 0.76% (including other costs)
Opportunities/day: 47
Expected monthly profit: $25,500

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

UPGRADE SCENARIO 1: VIP Tier (requires $2M/month volume)
Exchange A: 0.08% taker (-20%)
Exchange B: 0.50% taker (-17%)
Total: 0.58% per round trip

New breakeven: 0.64%
Opportunities/day: 89 (+89%)
Expected monthly profit: $48,300 (+89%)

Cost to reach: Trade $2M/month
Payback period: 1.2 months

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

UPGRADE SCENARIO 2: Market Maker Program
Exchange A: 0.05% maker, 0.10% taker
Exchange B: 0.40% maker, 0.60% taker

Using maker orders (requires limit orders):
Total: 0.45% per round trip
New breakeven: 0.51%
Opportunities/day: 178 (+279%)
Expected monthly profit: $89,400 (+251%)

Risk: Partial fills, execution uncertainty
```

**Bot Parameter Output:**
```python
FEE_EXCHANGE_A = 0.0010
FEE_EXCHANGE_B = 0.0060
USE_MAKER_ORDERS = False  # or True with risk
```

**Anomalies Detected:**
- 🔴 Fees increased without notice
- 🔴 Volume requirements for VIP changed
- 🟡 New fee tier available

---

### 1.5 Time-Based Opportunity Heatmap

**Visualization:**
```
WHEN TO RUN BOT (UTC) - 30 Day Average

Hour │Mon│Tue│Wed│Thu│Fri│Sat│Sun│ Opportunities/Day
─────┼───┼───┼───┼───┼───┼───┼───┼──────────────────
00:00│ 2 │ 1 │ 2 │ 1 │ 2 │ 4 │ 5 │  2.4
02:00│ 3 │ 2 │ 3 │ 3 │ 4 │ 7 │ 8 │  4.3 ⚠️
04:00│ 4 │ 3 │ 4 │ 4 │ 5 │ 9 │10 │  5.6 ⚠️
06:00│ 3 │ 3 │ 3 │ 4 │ 4 │ 5 │ 6 │  4.0
08:00│ 5 │ 6 │ 5 │ 6 │ 6 │ 3 │ 2 │  4.7
10:00│ 7 │ 8 │ 7 │ 8 │ 9 │ 2 │ 2 │  6.1
12:00│ 9 │10 │ 9 │10 │11 │ 3 │ 2 │  7.7 ⭐
14:00│11 │12 │11 │12 │13 │ 3 │ 2 │  9.1 ⭐⭐
16:00│ 9 │10 │ 9 │10 │11 │ 4 │ 3 │  8.0 ⭐
18:00│ 6 │ 7 │ 6 │ 7 │ 8 │ 5 │ 4 │  6.1
20:00│ 4 │ 5 │ 4 │ 5 │ 5 │ 6 │ 5 │  4.9
22:00│ 3 │ 3 │ 3 │ 3 │ 3 │ 5 │ 6 │  3.7

Peak Hours:    12:00-18:00 UTC (US trading hours)
Off-Peak:      00:00-06:00 UTC (Low liquidity)
Weekend Risk:  Sat/Sun 12:00-20:00 (Very low volume)

RECOMMENDATIONS:
✓ Run 24/7 but allocate capital for peak hours
✓ Reduce position size during off-peak
⚠️ Consider pausing Sat 12:00-20:00 (high risk, low reward)
```

**Bot Parameter Output:**
```python
PEAK_HOURS = [12, 13, 14, 15, 16, 17]  # UTC
REDUCE_SIZE_HOURS = [0, 1, 2, 3, 4, 5]
PAUSE_WINDOWS = [
    ("Saturday", 12, 20),
    ("Sunday", 12, 20)
]
```

**Anomalies Detected:**
- 🔴 Pattern shifts (regulatory change, market hours change)
- 🔴 Unexpected activity spike (news event, manipulation)
- 🟡 Weekend patterns changing

---

## SUITE 2: EXCHANGE HEALTH MONITORING

*Purpose: Ensure infrastructure is performing correctly*

### 2.1 Real-Time API Latency Dashboard

**Visualization:**
```
API PERFORMANCE MONITOR

Exchange A - WebSocket:
Current: 34ms ✅
1-hour avg: 38ms
P95: 67ms
P99: 124ms
Status: HEALTHY

Exchange A - REST API:
Current: 89ms ✅
1-hour avg: 94ms
P95: 156ms
P99: 234ms
Status: HEALTHY

Exchange B - WebSocket:
Current: 187ms ⚠️
1-hour avg: 156ms
P95: 298ms
P99: 445ms
Status: DEGRADED

Exchange B - REST API:
Current: 356ms ⚠️
1-hour avg: 312ms
P95: 523ms
P99: 789ms
Status: DEGRADED

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

LATENCY TREND (Last 6 hours):
 500ms│
      │
 400ms│                    ╱╲
      │                   ╱  ╲
 300ms│              ╱╲__╱    ╲
      │         ____╱           ╲
 200ms│    ____╱                 ╲___
      │___╱
 100ms│
      │
   0ms└─────────────────────────────→
      09:00  10:00  11:00  12:00  Now

⚠️ Exchange B latency increasing
   Missed opportunities: 8 (last hour)
   Impact: -$340 estimated loss
```

**Anomalies Detected:**
- 🔴 Latency >500ms (severe degradation)
- 🔴 Latency trend increasing (connection issues)
- 🟡 Latency spikes (temporary issues)
- 🔴 WebSocket disconnections

**Manager Actions:**
- Check exchange status page
- Switch to backup connection
- Reduce trade frequency
- Contact exchange support

---

### 2.2 Order Book Synchronization Quality

**Visualization:**
```
ORDER BOOK HEALTH

Exchange A:
Last snapshot: 2 min ago ✅
Updates received: 1,247
Missed sequences: 0
Confidence: 100.0% ✅

Exchange B:
Last snapshot: 45 sec ago ✅
Updates received: 892
Missed sequences: 7 ⚠️
Confidence: 97.3% ⚠️
Last resync: 3 min ago

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

SYNC QUALITY (Last hour)
100%│████████████████████████████
    │████████████████████████████ Exch A
 98%│███████░░░██████░░░░████████ Exch B
    │
 95%│
    └────────────────────────────→
    14:00                    15:00

⚠️ Exchange B missing order book updates
   Possible phantom opportunities: 3
   Recommend: Force resync or pause trading
```

**Anomalies Detected:**
- 🔴 Confidence <95% (trading on stale data)
- 🔴 High sequence gaps (missing critical updates)
- 🔴 No snapshot in >5 minutes (connection dead)

**Manager Actions:**
- Force order book resync
- Pause trading until quality improves
- Investigate network issues

---

### 2.3 Balance & Capital Tracking

**Visualization:**
```
CAPITAL ALLOCATION

Exchange A:
Available: $48,234 / $50,000 (96.5%) ✅
In orders: $1,234 (2.5%)
In transit: $532 (1.0%)
Status: HEALTHY

Exchange B:
Available: $32,891 / $50,000 (65.8%) ⚠️
In orders: $2,456 (4.9%)
In transit: $14,653 (29.3%) ⚠️
Status: LOW BALANCE

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

BALANCE OVER TIME (Today)
 $60k│
     │
 $50k│██████████████████░░░░░░░░ Exch A
     │
 $40k│██████████████░░░░░░░░░░░░ Exch B
     │                        ↓
 $30k│                     LOW! ⚠️
     │
 $20k│
     └────────────────────────────→
     00:00  06:00  12:00  18:00  Now

⚠️ ALERT: Exchange B balance below 70%
   Action required: Rebalance or pause
   
Pending transfers:
• $14,653 from B→A (started 2h ago) ⏳
  Expected arrival: 45 min
```

**Anomalies Detected:**
- 🔴 Balance <50% on either exchange (can't execute)
- 🔴 Imbalance >30% difference (need rebalancing)
- 🔴 Transfer stuck >3 hours (investigate)
- 🟡 Unexpected balance change (unauthorized trade?)

**Manager Actions:**
- Initiate rebalancing transfer
- Pause trading until balanced
- Check for stuck transactions
- Verify no unauthorized access

---

### 2.4 Connection Stability Monitor

**Visualization:**
```
CONNECTION UPTIME (24 hours)

Exchange A - WebSocket:
████████████████████████████████ 100.0% ✅
Disconnects: 0
Reconnects: 0
Uptime: 24h 0m

Exchange A - REST API:
████████████████████████████████ 100.0% ✅
Failed requests: 2 (0.01%)
Timeout rate: 0.0%

Exchange B - WebSocket:
██████████████░░██████████████░░ 94.2% ⚠️
Disconnects: 4
Reconnects: 4
Longest outage: 23 min ⚠️

Exchange B - REST API:
████████████████████████░░░░░░░░ 87.1% ⚠️
Failed requests: 47 (2.3%)
Timeout rate: 1.8%

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

RECENT INCIDENTS:
🔴 14:32 - Exchange B WS disconnected (23 min)
   Missed opportunities: 12 est.
   Loss: ~$580

🟡 13:18 - Exchange B REST timeout spike
   Duration: 8 minutes
   Impact: 3 failed trades

✅ 12:05 - All connections stable
```

**Anomalies Detected:**
- 🔴 Uptime <95% (unreliable)
- 🔴 Disconnect >5 minutes (significant loss)
- 🔴 Failed request rate >5% (API issues)
- 🟡 Repeated disconnects (investigate)

**Manager Actions:**
- Switch to backup API endpoint
- Contact exchange support
- Consider temporary pause
- Review co-location options

---

## SUITE 3: ANOMALY DETECTION

*Purpose: Identify unusual market conditions requiring intervention*

### 3.1 Spread Anomaly Detector

**Visualization:**
```
SPREAD ANOMALY DETECTION

Normal Range (30-day): $2-$25 (0.002%-0.023%)
Current spread: $847 (0.770%) 🔴

                      Current ↓
 $1000│                     ●
      │
  $500│
      │
  $100│
      │
   $50│
      │
   $25│█ ═══════════════════
      │█
   $10│█  ● ●  ●  ● ●    Normal range
      │█ ●  ● ● ● ●  ●
    $2│█─────────────────────
      │
    $0└──────────────────────────→
      14:00            14:55  Now

🔴 ALERT: Spread 34x normal!

Possible causes:
1. Exchange B API failure (check connection)
2. Exchange B halted trading (check status)
3. Flash crash / manipulation
4. Network split (prices diverged)

RECOMMENDATION:
⚠️ DO NOT TRADE - verify data accuracy
⚠️ Check exchange status pages
⚠️ Verify order books are real
✅ Wait for spread to normalize
```

**Anomalies Detected:**
- 🔴 Spread >3σ above mean (investigate before trading)
- 🔴 Spread >10σ (likely data error, do not trade)
- 🟡 Spread pattern change (new market regime)

**Manager Actions:**
- PAUSE trading immediately
- Verify data accuracy
- Check exchange status
- Investigate manually before resuming

---

### 3.2 Volume Anomaly Detection

**Visualization:**
```
VOLUME ANOMALY MONITOR

Normal 5-min volume: 15-45 BTC
Current 5-min volume: 387 BTC 🔴

 Volume (BTC)
  500│              ●
     │
  400│              │
     │              │
  300│              │
     │              │  ← Abnormal!
  200│              │
     │              │
  100│              │
     │  ● ●   ●  ● │  ●  ● ● ●
   50│●   ● ● ● ●  │ ● ●
     │─────────────┴────────────
     │
    0└──────────────────────────→
     14:40      14:52  14:55 Now

🔴 ALERT: Volume spike 8.6x normal!

Breakdown:
• Exchange A: 198 BTC (normal: 25 BTC)
• Exchange B: 189 BTC (normal: 20 BTC)
• Both spiked simultaneously

Possible causes:
1. Large institutional order
2. News event (check Twitter/news)
3. Liquidation cascade
4. Coordinated pump/dump

Volume distribution:
Orders >10 BTC: 8 (unusual - normally 0-1)
Largest order: 47 BTC

RECOMMENDATION:
⚠️ Reduce position size (high volatility expected)
⚠️ Widen spread threshold temporarily
✅ Monitor for manipulation
```

**Anomalies Detected:**
- 🔴 Volume >5x normal (unusual activity)
- 🔴 Volume <0.2x normal (liquidity dried up)
- 🟡 Large orders appearing (>10 BTC)
- 🔴 Volume spike on one exchange only (data issue?)

**Manager Actions:**
- Reduce position size
- Increase spread threshold
- Check news/Twitter
- Monitor for manipulation

---

### 3.3 Correlation Break Monitor

**Visualization:**
```
PRICE CORRELATION TRACKER

Normal correlation: 0.95-0.99
Current correlation: 0.78 🔴

 Correlation
 1.00│████████████████████
     │████████████████████
 0.95│████████████████████
     │████████████████████
 0.90│█████████░░░████████
     │█████████░░░████████
 0.85│█████████░░░████████
     │█████████░░░████████
 0.80│█████████░░░████████
     │█████████░  ●
 0.75│█████████    ↑
     │          Current
 0.70│
     └──────────────────────────→
     12:00      14:00       Now

🔴 ALERT: Correlation breakdown!

Price divergence:
Exchange A: $110,245 → $110,890 (+0.59%)
Exchange B: $110,253 → $110,156 (-0.09%)
Divergence: $734 (0.67%)

Historical context:
Last correlation <0.85: 12 days ago
Duration: 45 minutes
Result: Returned to normal

Opportunities during low correlation:
- Last event: 37 trades, $2,840 profit
- Risk: Higher volatility, larger drawdowns

RECOMMENDATION:
✅ Opportunities will increase
⚠️ Higher risk - reduce position size 50%
⚠️ Widen stop losses
✅ Monitor closely for normalization
```

**Anomalies Detected:**
- 🔴 Correlation <0.85 (unusual divergence)
- 🔴 Negative correlation (something broken)
- 🟡 Correlation declining trend (market changing)

**Manager Actions:**
- Increase monitoring
- Reduce risk exposure
- Prepare for volatility
- Check for exchange-specific news

---

### 3.4 Order Book Manipulation Detector

**Visualization:**
```
SUSPICIOUS ORDER ACTIVITY

Order Book Wall Detection:

Exchange A - BID side:
$110,200: 0.5 BTC
$110,150: 1.2 BTC
$110,100: 2.1 BTC
$110,050: 3.4 BTC ← Accumulating
$110,000: 45.7 BTC 🔴 WALL! (15x avg size)

Exchange B - ASK side:
$110,300: 0.8 BTC
$110,350: 1.5 BTC
$110,400: 2.3 BTC
$110,450: 52.3 BTC 🔴 WALL! (17x avg size)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

WALL BEHAVIOR (Last 30 minutes):
• Buy wall at $110,000 appeared 14:23
• Size fluctuates: 45→58→42→45 BTC
• Price tested wall 3 times
• Wall hasn't moved (likely fake/spoofing)

• Sell wall at $110,450 appeared 14:25
• Size stable: 52 BTC
• No tests yet
• Appeared after buy wall (coordinated?)

INTERPRETATION:
⚠️ Possible spoofing/manipulation
⚠️ Walls preventing arbitrage
⚠️ Range: $110,000-$110,450 (artificial)

RECOMMENDATION:
⚠️ Avoid trading near walls
✅ Wait for walls to be removed/filled
⚠️ Be ready for price jump when walls pulled
```

**Anomalies Detected:**
- 🔴 Order >10x average size (potential spoofing)
- 🔴 Wall appearing/disappearing (manipulation)
- 🔴 Coordinated walls on both exchanges (market making or manipulation)
- 🟡 Orders pulled before being filled (fake liquidity)

**Manager Actions:**
- Avoid trading near manipulation
- Wait for walls to clear
- Document for exchange report (if manipulation)
- Adjust bot to avoid spoofed areas

---

## SUITE 4: HISTORICAL ANALYSIS

*Purpose: Long-term strategy evaluation and optimization*

### 4.1 Backtest Results Dashboard

**Visualization:**
```
STRATEGY BACKTEST (90 days)

Strategy: 0.76% threshold, 0.5 BTC size

Performance Summary:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Total Opportunities:     4,140
Trades Executed:         3,894 (94.1%)
Successful:              3,623 (93.0%)
Failed:                    271 (7.0%)

Financial Results:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Gross Profit:          $47,832
Total Fees:           -$28,904
Net Profit:            $18,928
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ROI (quarterly):         18.9%
ROI (annualized):        75.6%
Sharpe Ratio:             1.87
Max Drawdown:           -$2,341
Win Rate:                93.0%

Daily P&L:
$1500│    ╱╲     ╱╲
     │   ╱  ╲   ╱  ╲    ╱╲
$1000│  ╱    ╲ ╱    ╲  ╱  ╲
     │ ╱      ╲╱      ╲╱    ╲
 $500│╱                      ╲
     │                        ╲___
   $0│────────────────────────────╲─
     │                             ╲
-$500│                              ╲
     └──────────────────────────────→
     Sep 1        Oct 1        Nov 1

Failure Analysis:
• Insufficient balance: 145 (53.5%)
• API timeout:           78 (28.8%)
• Price moved:           48 (17.7%)

OPTIMIZATION RECOMMENDATIONS:
✓ Better balance management → +$2,450
✓ Faster API connection → +$1,820
✓ Predictive pricing → +$890
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Potential total: $24,088 (+27%)
```

**Bot Parameter Validation:**
- Are current parameters optimal?
- What changes would improve performance?
- Is strategy viable long-term?

---

### 4.2 Strategy Comparison Matrix

**Visualization:**
```
PARAMETER SENSITIVITY ANALYSIS

Threshold vs Performance:

Threshold  Opps/day  Success%  Daily$  ROI/mo
0.50%        247      78%      $423    12.7%
0.60%        156      85%      $512    15.4%
0.70%         89      91%      $634    19.0%
0.76% ★       47      93%      $850    25.5% ← Current
0.80%         38      94%      $912    27.4%
0.90%         23      96%      $967    29.0%
1.00%         12      97%      $891    26.7%

Position Size vs Performance:

Size      Opps/day  Slippage  Daily$  ROI/mo
0.1 BTC     47       $3       $334    20.0%
0.3 BTC     47       $7       $724    21.7%
0.5 BTC ★   47       $12      $850    25.5% ← Current
0.7 BTC     47       $23      $743    22.3%
1.0 BTC     42       $38      $628    18.8%

OPTIMAL CONFIGURATION:
Threshold: 0.80% (+$62/day)
Size: 0.5 BTC (current is optimal)
Expected improvement: +7.3%
```

**Insights for Bot Builders:**
- Current vs optimal parameters
- Trade-offs between parameters
- Sensitivity analysis

---

### 4.3 Market Regime Classification

**Visualization:**
```
MARKET REGIME HISTORY (6 months)

Regime 1: High Efficiency (correlation >0.97)
Duration: 67% of time
Characteristics:
• Tight spreads (avg 0.08%)
• Rare opportunities (8/day)
• Low volatility
Strategy: Conservative, tight threshold

Regime 2: Moderate Efficiency (corr 0.93-0.97)
Duration: 28% of time
Characteristics:
• Medium spreads (avg 0.24%)
• Good opportunities (47/day) ★
• Normal volatility
Strategy: Standard arbitrage ← We are here

Regime 3: Low Efficiency (corr <0.93)
Duration: 5% of time
Characteristics:
• Wide spreads (avg 0.89%)
• Many opportunities (150+/day)
• High volatility, high risk
Strategy: Aggressive, wider threshold

Timeline:
May │ R1 R1 R1 R1 │ R1 R1 R2 R2
Jun │ R2 R2 R2 R1 │ R1 R1 R1 R2
Jul │ R2 R2 R3 R3 │ R2 R2 R2 R2
Aug │ R2 R1 R1 R1 │ R1 R2 R2 R2
Sep │ R2 R2 R2 R2 │ R3 R2 R2 R2
Oct │ R2 R2 R2 R1 │ R1 R1 R2 R2
    └──────────────────────────→

Current: Regime 2 (favorable)
Probability of regime change: 15% (next week)
```

**Strategic Insights:**
- Market conditions change over time
- Adapt strategy to regime
- Predict regime shifts

---

## DASHBOARD LAYOUTS

### Main Dashboard (Single Screen)

```
┌────────────────────┬─────────────────┬──────────────────┐
│ SYSTEM HEALTH      │ OPPORTUNITIES   │ CAPITAL          │
│                    │                 │                  │
│ APIs: ✅✅         │ Last hour: 5    │ Bal A: 96% ✅    │
│ Sync: ✅⚠️         │ Success: 4/5    │ Bal B: 66% ⚠️    │
│ Balance: ⚠️        │ Net: $187       │ Transfer: ⏳     │
│                    │                 │                  │
│ [Details]          │ [Details]       │ [Rebalance]      │
└────────────────────┴─────────────────┴──────────────────┘
┌───────────────────────────────────────────────────────┐
│ LIVE OPPORTUNITY FEED                                 │
│                                                       │
│ 15:02:34 BTC 0.82% 2.1s ✅ $34                       │
│ 15:01:18 BTC 0.91% 1.8s ✅ $67                       │
│ 14:59:45 ETH 0.74% 0.9s ❌ Too fast                  │
│                                                       │
└───────────────────────────────────────────────────────┘
┌──────────────────────┬────────────────────────────────┐
│ ANOMALY ALERTS       │ PERFORMANCE TODAY              │
│                      │                                │
│ ⚠️ Exchange B slow   │ Trades: 47                     │
│ 🟡 Low correlation   │ Success: 94%                   │
│                      │ Net: $1,247                    │
│ [View All]           │ [Details]                      │
└──────────────────────┴────────────────────────────────┘
```

---

## IMPLEMENTATION PRIORITIES

### Phase 1: Core Monitoring (Week 1)
1. Bot health dashboard
2. API latency monitor
3. Balance tracker
4. Live opportunity feed

### Phase 2: Strategy Parameters (Week 2)
5. Spread distribution
6. Duration analysis
7. Fee calculator
8. Liquidity analysis

### Phase 3: Anomaly Detection (Week 3)
9. Spread anomalies
10. Volume anomalies
11. Correlation monitor
12. Order book quality

### Phase 4: Historical Analysis (Week 4)
13. Backtest results
14. Parameter optimization
15. Regime classification
16. Performance trends

---

## TECHNICAL STACK RECOMMENDATIONS

```
Data Collection:
- WebSocket clients (persistent connections)
- PostgreSQL / TimescaleDB (time-series)
- Redis (real-time caching)

Backend:
- Python + FastAPI (REST endpoints)
- Pandas (data processing)
- NumPy (calculations)

Frontend:
- React + TypeScript
- Recharts / Chart.js (visualizations)
- TailwindCSS (styling)
- WebSocket client (live updates)

Monitoring:
- Prometheus (metrics)
- Grafana (operational dashboards)
- PagerDuty / alerts (anomaly notifications)
```

---

## SUCCESS METRICS

Dashboard is successful if:

1. **Bot builders** can determine:
   ✓ Whether to build the bot (viability)
   ✓ Optimal parameters (threshold, size, timing)
   ✓ Expected profitability (realistic ROI)

2. **Bot managers** can:
   ✓ Monitor health at a glance
   ✓ Detect anomalies requiring intervention
   ✓ Debug failures quickly
   ✓ Make informed decisions (pause/continue/optimize)

3. **Platform provides:**
   ✓ Real-time alerts for critical issues
   ✓ Historical context for decisions
   ✓ Clear actionable recommendations
   ✓ No false alarms (high signal-to-noise)

---

## ALERT CONFIGURATION

### Critical (Immediate Action)
🔴 Exchange API down
🔴 Balance <30%
🔴 Order book confidence <90%
🔴 Spread >10σ from normal
🔴 Correlation <0.80

### Warning (Check Soon)
🟡 Exchange API slow
🟡 Balance imbalance >30%
🟡 Volume 5x normal
🟡 Spread 3-10σ from normal
🟡 Correlation 0.80-0.90

### Info (Monitor)
🔵 Normal operation resumed
🔵 Rebalance completed
🔵 New regime detected
🔵 Performance milestone reached

---

END OF SPECIFICATION
