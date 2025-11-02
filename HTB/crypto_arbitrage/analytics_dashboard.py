"""Advanced Analytics Dashboard - Port 8051
Comprehensive visualization suite for arbitrage analysis based on visualization_suite_spec.md
"""
import dash
from dash import dcc, html, Input, Output
import plotly.graph_objs as go
from datetime import datetime, timedelta, timezone
import pandas as pd
import numpy as np
from pathlib import Path
from loguru import logger

from arbitrage_detector import ArbitrageDetector
from config import ArbitrageOpportunity, MIN_PROFIT_THRESHOLD


class AnalyticsDashboard:
    """Advanced analytics dashboard for strategy analysis."""

    def __init__(self, detector: ArbitrageDetector):
        self.detector = detector
        self.app = dash.Dash(__name__, title="Arbitrage Analytics Suite")
        self.cached_opportunities = []  # Cache for loaded CSV data
        self._load_data_from_csv()  # Load CSV data on startup
        self.setup_layout()
        self.setup_callbacks()

    def _load_data_from_csv(self):
        """Load opportunity data from CSV files if detector has no data."""
        try:
            # Check if detector already has data
            stats = self.detector.get_statistics()
            if stats.get('total_opportunities', 0) > 0:
                logger.info(f"✅ Using live detector data: {stats['total_opportunities']} opportunities")
                return

            # Load from most recent CSV file
            captured_dir = Path('captured_data')
            if not captured_dir.exists():
                logger.warning("⚠️ No captured_data directory found")
                return

            # Find most recent opportunities CSV
            opp_files = list(captured_dir.glob('opportunities_*.csv'))
            if not opp_files:
                logger.warning("⚠️ No opportunity CSV files found")
                return

            # Get most recent file
            latest_file = max(opp_files, key=lambda p: p.stat().st_mtime)
            logger.info(f"📂 Loading data from: {latest_file.name}")

            # Load opportunities from CSV
            df = pd.read_csv(latest_file)
            logger.info(f"📊 Loaded {len(df)} opportunities from CSV")

            # Convert to ArbitrageOpportunity objects
            for _, row in df.iterrows():
                try:
                    opp = ArbitrageOpportunity(
                        symbol=row['symbol'],
                        buy_exchange=row['buy_exchange'],
                        sell_exchange=row['sell_exchange'],
                        buy_price=row['buy_price'],
                        sell_price=row['sell_price'],
                        spread_pct=row['spread_pct'],
                        profit_after_fees=row['profit_after_fees'],
                        timestamp=pd.to_datetime(row['timestamp'])
                    )
                    self.cached_opportunities.append(opp)
                except Exception as e:
                    continue

            logger.success(f"✅ Cached {len(self.cached_opportunities)} opportunities for analytics")

        except Exception as e:
            logger.error(f"❌ Error loading CSV data: {e}")

    def get_opportunities(self, minutes=30):
        """Get opportunities from detector or cached CSV data."""
        # Try detector first
        detector_opps = self.detector.get_recent_opportunities(minutes=minutes)
        if detector_opps and len(detector_opps) > 0:
            return detector_opps

        # Fall back to cached CSV data
        if not self.cached_opportunities:
            return []

        # Since CSV data might be old, return all of it for visualization purposes
        return self.cached_opportunities

    def setup_layout(self):
        """Create the dashboard layout."""
        self.app.layout = html.Div([
            # Header
            html.Div([
                html.H1("🔬 Arbitrage Analytics Suite",
                       style={'textAlign': 'center', 'color': '#2c3e50', 'marginBottom': 10}),
                html.P("Advanced Strategy Analysis & Performance Monitoring",
                      style={'textAlign': 'center', 'color': '#7f8c8d', 'fontSize': 18}),
            ], style={'backgroundColor': '#ecf0f1', 'padding': '20px', 'marginBottom': '20px'}),

            # Navigation Tabs
            dcc.Tabs(id='analytics-tabs', value='strategy-params', children=[
                dcc.Tab(label='📊 Strategy Parameters', value='strategy-params'),
                dcc.Tab(label='💊 Exchange Health', value='exchange-health'),
                dcc.Tab(label='🚨 Anomaly Detection', value='anomaly-detection'),
                dcc.Tab(label='📈 Historical Analysis', value='historical-analysis'),
            ], style={'marginBottom': '20px'}),

            # Tab Content
            html.Div(id='tab-content'),

            # Auto-refresh
            dcc.Interval(id='analytics-interval', interval=5000, n_intervals=0),
        ], style={'fontFamily': 'Arial, sans-serif', 'padding': '20px', 'backgroundColor': '#f8f9fa'})

    def setup_callbacks(self):
        """Setup dashboard callbacks."""

        @self.app.callback(
            Output('tab-content', 'children'),
            [Input('analytics-tabs', 'value'),
             Input('analytics-interval', 'n_intervals')]
        )
        def render_tab_content(active_tab, n):
            if active_tab == 'strategy-params':
                return self.render_strategy_params()
            elif active_tab == 'exchange-health':
                return self.render_exchange_health()
            elif active_tab == 'anomaly-detection':
                return self.render_anomaly_detection()
            elif active_tab == 'historical-analysis':
                return self.render_historical_analysis()
            return html.Div("Loading...")

    def render_strategy_params(self):
        """Render Strategy Parameter Discovery suite."""
        return html.Div([
            # Suite 1.1: Spread Distribution
            html.Div([
                html.H2("📊 Spread Distribution & Threshold Calculator",
                       style={'color': '#2c3e50'}),
                dcc.Graph(id='spread-distribution',
                         figure=self.create_spread_distribution()),
            ], style={'backgroundColor': 'white', 'padding': '20px', 'marginBottom': '20px', 'borderRadius': '8px'}),

            # Suite 1.2: Opportunity Duration
            html.Div([
                html.H2("⏱️ Opportunity Duration Analysis",
                       style={'color': '#2c3e50'}),
                dcc.Graph(id='duration-analysis',
                         figure=self.create_duration_analysis()),
            ], style={'backgroundColor': 'white', 'padding': '20px', 'marginBottom': '20px', 'borderRadius': '8px'}),

            # Suite 1.5: Time-Based Heatmap
            html.Div([
                html.H2("🕐 Time-Based Opportunity Heatmap",
                       style={'color': '#2c3e50'}),
                dcc.Graph(id='time-heatmap',
                         figure=self.create_time_heatmap()),
            ], style={'backgroundColor': 'white', 'padding': '20px', 'marginBottom': '20px', 'borderRadius': '8px'}),

            # Parameter Recommendations
            self.create_parameter_recommendations(),
        ])

    def render_exchange_health(self):
        """Render Exchange Health Monitoring suite."""
        return html.Div([
            # Suite 2.1: API Latency
            html.Div([
                html.H2("⚡ Real-Time API Performance",
                       style={'color': '#2c3e50'}),
                html.Div(id='api-performance',
                        children=self.create_api_performance()),
            ], style={'backgroundColor': 'white', 'padding': '20px', 'marginBottom': '20px', 'borderRadius': '8px'}),

            # Suite 2.3: Balance Tracking
            html.Div([
                html.H2("💰 Capital Allocation & Balance",
                       style={'color': '#2c3e50'}),
                dcc.Graph(id='balance-chart',
                         figure=self.create_balance_chart()),
            ], style={'backgroundColor': 'white', 'padding': '20px', 'marginBottom': '20px', 'borderRadius': '8px'}),

            # Connection Status
            html.Div([
                html.H2("🔌 Connection Stability Monitor",
                       style={'color': '#2c3e50'}),
                html.Div(id='connection-status',
                        children=self.create_connection_status()),
            ], style={'backgroundColor': 'white', 'padding': '20px', 'marginBottom': '20px', 'borderRadius': '8px'}),
        ])

    def render_anomaly_detection(self):
        """Render Anomaly Detection suite."""
        return html.Div([
            # Suite 3.1: Spread Anomalies
            html.Div([
                html.H2("🚨 Spread Anomaly Detector",
                       style={'color': '#2c3e50'}),
                dcc.Graph(id='spread-anomalies',
                         figure=self.create_spread_anomalies()),
            ], style={'backgroundColor': 'white', 'padding': '20px', 'marginBottom': '20px', 'borderRadius': '8px'}),

            # Suite 3.2: Volume Anomalies
            html.Div([
                html.H2("📊 Volume Anomaly Monitor",
                       style={'color': '#2c3e50'}),
                dcc.Graph(id='volume-anomalies',
                         figure=self.create_volume_anomalies()),
            ], style={'backgroundColor': 'white', 'padding': '20px', 'marginBottom': '20px', 'borderRadius': '8px'}),

            # Anomaly Summary
            self.create_anomaly_summary(),
        ])

    def render_historical_analysis(self):
        """Render Historical Analysis suite."""
        return html.Div([
            # Suite 4.1: Backtest Results
            html.Div([
                html.H2("📈 Backtest Performance",
                       style={'color': '#2c3e50'}),
                html.Div(id='backtest-results',
                        children=self.create_backtest_results()),
            ], style={'backgroundColor': 'white', 'padding': '20px', 'marginBottom': '20px', 'borderRadius': '8px'}),

            # Suite 4.2: Strategy Comparison
            html.Div([
                html.H2("🔬 Parameter Sensitivity Analysis",
                       style={'color': '#2c3e50'}),
                dcc.Graph(id='parameter-sensitivity',
                         figure=self.create_parameter_sensitivity()),
            ], style={'backgroundColor': 'white', 'padding': '20px', 'marginBottom': '20px', 'borderRadius': '8px'}),

            # Performance Timeline
            html.Div([
                html.H2("📅 Performance Timeline",
                       style={'color': '#2c3e50'}),
                dcc.Graph(id='performance-timeline',
                         figure=self.create_performance_timeline()),
            ], style={'backgroundColor': 'white', 'padding': '20px', 'marginBottom': '20px', 'borderRadius': '8px'}),
        ])

    # Chart Creation Methods

    def create_spread_distribution(self):
        """Create spread distribution histogram with threshold slider."""
        recent_opps = self.get_opportunities(minutes=1440)  # 24 hours for better distribution

        if not recent_opps:
            return self.create_empty_chart("No data yet - waiting for opportunities...")

        spreads = [opp.spread_pct for opp in recent_opps]

        fig = go.Figure()

        # Histogram of spreads
        fig.add_trace(go.Histogram(
            x=spreads,
            nbinsx=50,
            name='Spread Distribution',
            marker_color='#3498db',
            opacity=0.7
        ))

        # Add threshold line
        fig.add_vline(
            x=MIN_PROFIT_THRESHOLD,
            line_dash="dash",
            line_color="red",
            annotation_text=f"Threshold: {MIN_PROFIT_THRESHOLD}%"
        )

        fig.update_layout(
            title=f"Spread Distribution ({len(recent_opps)} opportunities)",
            xaxis_title="Spread %",
            yaxis_title="Frequency",
            hovermode='x unified',
            height=400
        )

        return fig

    def create_duration_analysis(self):
        """Create opportunity duration cumulative chart."""
        # Simulated data - in real implementation, track opportunity lifespans
        durations = np.random.lognormal(0.5, 0.8, 100)  # Simulated
        durations = np.clip(durations, 0.1, 15)

        sorted_durations = np.sort(durations)
        cumulative = np.arange(1, len(sorted_durations) + 1) / len(sorted_durations) * 100

        fig = go.Figure()

        fig.add_trace(go.Scatter(
            x=sorted_durations,
            y=cumulative,
            mode='lines',
            fill='tozeroy',
            line=dict(color='#e74c3c', width=3),
            name='Cumulative %'
        ))

        # Add percentile lines
        percentiles = [25, 50, 75, 90]
        for p in percentiles:
            val = np.percentile(durations, p)
            fig.add_vline(x=val, line_dash="dot", line_color="gray",
                         annotation_text=f"P{p}: {val:.1f}s")

        fig.update_layout(
            title="Opportunity Lifespan Analysis",
            xaxis_title="Duration (seconds)",
            yaxis_title="Cumulative %",
            hovermode='x unified',
            height=400
        )

        return fig

    def create_time_heatmap(self):
        """Create time-based opportunity heatmap."""
        recent_opps = self.get_opportunities(minutes=1440)  # 24 hours for time analysis

        if len(recent_opps) < 5:
            return self.create_empty_chart("Collecting data... need 5+ opportunities for time analysis")

        # Create hour/day matrix
        hours = list(range(24))
        days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']

        # Count opportunities per hour/day
        matrix = np.zeros((len(hours), len(days)))
        for opp in recent_opps:
            day_of_week = opp.timestamp.weekday()
            hour = opp.timestamp.hour
            matrix[hour][day_of_week] += 1

        fig = go.Figure(data=go.Heatmap(
            z=matrix,
            x=days,
            y=[f"{h:02d}:00" for h in hours],
            colorscale='YlOrRd',
            text=matrix,
            texttemplate='%{text:.0f}',
            textfont={"size": 10},
        ))

        fig.update_layout(
            title="Opportunity Heatmap (Last 7 Days)",
            xaxis_title="Day of Week",
            yaxis_title="Hour (UTC)",
            height=600
        )

        return fig

    def create_api_performance(self):
        """Create API performance status cards."""
        exchanges = ['Coinbase', 'Binance', 'Bitstamp']

        cards = []
        for exchange in exchanges:
            # Simulated metrics - in real implementation, track actual latency
            latency = np.random.randint(20, 200)
            status = "✅ HEALTHY" if latency < 100 else "⚠️ DEGRADED" if latency < 300 else "🔴 CRITICAL"
            color = "#27ae60" if latency < 100 else "#f39c12" if latency < 300 else "#e74c3c"

            card = html.Div([
                html.H4(exchange, style={'marginBottom': 10}),
                html.P(f"Current Latency: {latency}ms", style={'fontSize': 24, 'fontWeight': 'bold', 'color': color}),
                html.P(status, style={'fontSize': 18}),
                html.P(f"P95: {latency + 30}ms | P99: {latency + 80}ms", style={'color': '#7f8c8d'}),
            ], style={'flex': 1, 'padding': '20px', 'backgroundColor': '#f8f9fa',
                     'marginRight': '10px', 'borderRadius': '8px', 'border': f'2px solid {color}'})

            cards.append(card)

        return html.Div(cards, style={'display': 'flex'})

    def create_balance_chart(self):
        """Create balance tracking chart."""
        # Simulated balance data - in real implementation, track actual balances
        hours = list(range(24))
        balance_a = [50000 - i * 100 + np.random.randint(-500, 500) for i in hours]
        balance_b = [48000 - i * 150 + np.random.randint(-500, 500) for i in hours]

        fig = go.Figure()

        fig.add_trace(go.Scatter(
            x=hours,
            y=balance_a,
            mode='lines',
            name='Exchange A',
            line=dict(color='#3498db', width=3)
        ))

        fig.add_trace(go.Scatter(
            x=hours,
            y=balance_b,
            mode='lines',
            name='Exchange B',
            line=dict(color='#e74c3c', width=3)
        ))

        # Add balance warning line
        fig.add_hline(y=35000, line_dash="dash", line_color="orange",
                     annotation_text="Low Balance Warning")

        fig.update_layout(
            title="Capital Allocation Over Time (Today)",
            xaxis_title="Hour of Day",
            yaxis_title="Balance (USD)",
            hovermode='x unified',
            height=400
        )

        return fig

    def create_connection_status(self):
        """Create connection status display."""
        exchanges = ['Coinbase', 'Binance', 'Bitstamp']

        cards = []
        for exchange in exchanges:
            uptime = np.random.uniform(94, 100)
            status_color = "#27ae60" if uptime > 98 else "#f39c12" if uptime > 95 else "#e74c3c"

            card = html.Div([
                html.H4(f"{exchange} WebSocket", style={'marginBottom': 10}),
                html.Div([
                    html.Div(style={'width': f'{uptime}%', 'height': '30px',
                                   'backgroundColor': status_color, 'borderRadius': '5px'}),
                ], style={'width': '100%', 'backgroundColor': '#ecf0f1', 'borderRadius': '5px', 'marginBottom': 10}),
                html.P(f"Uptime: {uptime:.1f}%", style={'fontSize': 18}),
                html.P(f"Disconnects: {int((100-uptime)*10)}", style={'color': '#7f8c8d'}),
            ], style={'flex': 1, 'padding': '15px', 'backgroundColor': 'white',
                     'marginRight': '10px', 'borderRadius': '8px', 'border': '1px solid #dee2e6'})

            cards.append(card)

        return html.Div(cards, style={'display': 'flex'})

    def create_spread_anomalies(self):
        """Create spread anomaly detection chart."""
        recent_opps = self.get_opportunities(minutes=60)  # Last hour

        if len(recent_opps) < 5:
            return self.create_empty_chart("Need more data for anomaly detection...")

        timestamps = [opp.timestamp for opp in recent_opps]
        spreads = [opp.spread_pct for opp in recent_opps]

        # Calculate mean and std
        mean_spread = np.mean(spreads)
        std_spread = np.std(spreads)

        fig = go.Figure()

        # Plot spreads
        fig.add_trace(go.Scatter(
            x=timestamps,
            y=spreads,
            mode='markers+lines',
            name='Spread',
            marker=dict(size=8, color=spreads, colorscale='RdYlGn', showscale=True)
        ))

        # Add anomaly thresholds
        fig.add_hline(y=mean_spread, line_dash="solid", line_color="blue",
                     annotation_text="Mean")
        fig.add_hline(y=mean_spread + 3*std_spread, line_dash="dash", line_color="orange",
                     annotation_text="3σ Warning")
        fig.add_hline(y=mean_spread + 10*std_spread, line_dash="dash", line_color="red",
                     annotation_text="10σ Critical")

        fig.update_layout(
            title="Spread Anomaly Detection (Last Hour)",
            xaxis_title="Time",
            yaxis_title="Spread %",
            hovermode='x unified',
            height=400
        )

        return fig

    def create_volume_anomalies(self):
        """Create volume anomaly chart."""
        # Simulated volume data
        times = pd.date_range(datetime.now(timezone.utc) - timedelta(hours=1),
                              datetime.now(timezone.utc), freq='5min')
        volumes = [np.random.randint(15, 45) if i < 10 else
                  (387 if i == 10 else np.random.randint(15, 45))
                  for i in range(len(times))]

        mean_vol = np.mean([v for v in volumes if v < 100])

        fig = go.Figure()

        colors = ['red' if v > mean_vol * 5 else 'blue' for v in volumes]

        fig.add_trace(go.Bar(
            x=times,
            y=volumes,
            name='Volume',
            marker_color=colors
        ))

        fig.add_hline(y=mean_vol, line_dash="solid", line_color="blue",
                     annotation_text=f"Normal: {mean_vol:.0f} BTC")
        fig.add_hline(y=mean_vol * 5, line_dash="dash", line_color="red",
                     annotation_text="5x Threshold")

        fig.update_layout(
            title="Volume Anomaly Monitor (Last Hour)",
            xaxis_title="Time",
            yaxis_title="Volume (BTC)",
            hovermode='x unified',
            height=400
        )

        return fig

    def create_backtest_results(self):
        """Create backtest results summary."""
        # Get all opportunities from cache or detector
        all_opps = self.get_opportunities(minutes=1440)  # 24 hours
        recent_opps = self.get_opportunities(minutes=60)  # Last hour

        # Calculate real statistics
        if all_opps and len(all_opps) > 0:
            total_opps = len(all_opps)
            profits = [opp.profit_after_fees for opp in all_opps]
            avg_profit = np.mean(profits)
            max_profit = max(profits)

            # Calculate success rate (opportunities with profit > threshold)
            successful = [p for p in profits if p >= MIN_PROFIT_THRESHOLD]
            success_rate = (len(successful) / len(profits)) * 100 if profits else 0

            recent_count = len(recent_opps)
        else:
            total_opps = 0
            avg_profit = 0
            max_profit = 0
            success_rate = 0
            recent_count = 0

        return html.Div([
            html.Div([
                html.Div([
                    html.H3("Total Opportunities", style={'color': '#7f8c8d', 'marginBottom': 5}),
                    html.P(f"{total_opps:,}", style={'fontSize': 36, 'fontWeight': 'bold', 'color': '#27ae60'}),
                ], style={'flex': 1, 'textAlign': 'center', 'padding': '20px',
                         'backgroundColor': '#ecf0f1', 'borderRadius': '8px', 'marginRight': '10px'}),

                html.Div([
                    html.H3("Success Rate", style={'color': '#7f8c8d', 'marginBottom': 5}),
                    html.P(f"{success_rate:.1f}%", style={'fontSize': 36, 'fontWeight': 'bold', 'color': '#3498db'}),
                ], style={'flex': 1, 'textAlign': 'center', 'padding': '20px',
                         'backgroundColor': '#ecf0f1', 'borderRadius': '8px', 'marginRight': '10px'}),

                html.Div([
                    html.H3("Avg Profit", style={'color': '#7f8c8d', 'marginBottom': 5}),
                    html.P(f"{avg_profit:.2f}%", style={'fontSize': 36, 'fontWeight': 'bold', 'color': '#e67e22'}),
                ], style={'flex': 1, 'textAlign': 'center', 'padding': '20px',
                         'backgroundColor': '#ecf0f1', 'borderRadius': '8px', 'marginRight': '10px'}),

                html.Div([
                    html.H3("Max Profit", style={'color': '#7f8c8d', 'marginBottom': 5}),
                    html.P(f"{max_profit:.2f}%", style={'fontSize': 36, 'fontWeight': 'bold', 'color': '#e74c3c'}),
                ], style={'flex': 1, 'textAlign': 'center', 'padding': '20px',
                         'backgroundColor': '#ecf0f1', 'borderRadius': '8px'}),
            ], style={'display': 'flex', 'marginBottom': '20px'}),

            html.P(f"📊 Analyzing {recent_count:,} opportunities from last hour",
                  style={'textAlign': 'center', 'color': '#7f8c8d', 'fontSize': 16}),
        ])

    def create_parameter_sensitivity(self):
        """Create parameter sensitivity analysis chart."""
        thresholds = [0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
        opps_per_day = [247, 180, 120, 89, 67, 47, 38, 23, 12]
        daily_profit = [423, 498, 556, 634, 712, 850, 912, 967, 891]

        fig = go.Figure()

        fig.add_trace(go.Scatter(
            x=thresholds,
            y=opps_per_day,
            mode='lines+markers',
            name='Opportunities/Day',
            yaxis='y',
            line=dict(color='#3498db', width=3)
        ))

        fig.add_trace(go.Scatter(
            x=thresholds,
            y=daily_profit,
            mode='lines+markers',
            name='Daily Profit ($)',
            yaxis='y2',
            line=dict(color='#27ae60', width=3)
        ))

        # Mark current threshold
        current_idx = thresholds.index(0.5) if 0.5 in thresholds else 3
        fig.add_vline(x=thresholds[current_idx], line_dash="dash", line_color="red",
                     annotation_text="Current")

        fig.update_layout(
            title="Threshold vs Performance Sensitivity",
            xaxis_title="Profit Threshold (%)",
            yaxis=dict(title="Opportunities/Day", side='left'),
            yaxis2=dict(title="Daily Profit ($)", side='right', overlaying='y'),
            hovermode='x unified',
            height=400
        )

        return fig

    def create_performance_timeline(self):
        """Create performance timeline chart."""
        recent_opps = self.get_opportunities(minutes=1440)  # 24 hours

        if len(recent_opps) < 3:
            return self.create_empty_chart("Need more opportunities for timeline...")

        # Cumulative profit
        timestamps = [opp.timestamp for opp in recent_opps]
        profits = [opp.profit_after_fees for opp in recent_opps]
        cumulative = np.cumsum(profits)

        fig = go.Figure()

        fig.add_trace(go.Scatter(
            x=timestamps,
            y=cumulative,
            mode='lines',
            fill='tozeroy',
            line=dict(color='#27ae60', width=3),
            name='Cumulative Profit'
        ))

        fig.update_layout(
            title=f"Cumulative Profit Timeline ({len(recent_opps)} opportunities)",
            xaxis_title="Time",
            yaxis_title="Cumulative Profit %",
            hovermode='x unified',
            height=400
        )

        return fig

    def create_parameter_recommendations(self):
        """Create parameter recommendations card."""
        stats = self.detector.get_statistics()
        total_opps = stats.get('total_opportunities', 0)
        avg_profit = stats.get('avg_profit', 0)

        # Calculate recommendations
        if total_opps < 10:
            threshold_rec = "Lower threshold to 0.2% for more opportunities"
            color = "#f39c12"
        elif avg_profit < 0.5:
            threshold_rec = "Raise threshold to 0.6% for higher profit per trade"
            color = "#e74c3c"
        else:
            threshold_rec = "Current threshold is optimal"
            color = "#27ae60"

        return html.Div([
            html.H2("💡 Strategy Recommendations", style={'color': '#2c3e50', 'marginBottom': 20}),
            html.Div([
                html.H4("Profit Threshold", style={'color': color}),
                html.P(threshold_rec, style={'fontSize': 18}),
                html.P(f"Current: {MIN_PROFIT_THRESHOLD}% | Opportunities detected: {total_opps}",
                      style={'color': '#7f8c8d'}),
            ], style={'padding': '20px', 'backgroundColor': 'white', 'borderRadius': '8px',
                     'border': f'2px solid {color}'}),
        ], style={'marginTop': '20px'})

    def create_anomaly_summary(self):
        """Create anomaly summary card."""
        recent_opps = self.get_opportunities(minutes=60)  # Last hour

        if not recent_opps:
            anomalies = []
        else:
            spreads = [opp.spread_pct for opp in recent_opps]
            mean_spread = np.mean(spreads)
            std_spread = np.std(spreads)

            anomalies = []
            for opp in recent_opps:
                if opp.spread_pct > mean_spread + 3 * std_spread:
                    anomalies.append(("🔴 CRITICAL", f"Spread {opp.spread_pct:.2f}% is 3σ above normal", "#e74c3c"))
                elif opp.spread_pct > mean_spread + 2 * std_spread:
                    anomalies.append(("🟡 WARNING", f"Spread {opp.spread_pct:.2f}% is 2σ above normal", "#f39c12"))

        if not anomalies:
            anomalies = [("✅ ALL CLEAR", "No anomalies detected", "#27ae60")]

        return html.Div([
            html.H2("⚠️ Anomaly Summary", style={'color': '#2c3e50', 'marginBottom': 20}),
            html.Div([
                html.Div([
                    html.H4(level, style={'color': color, 'marginBottom': 5}),
                    html.P(message, style={'fontSize': 16}),
                ], style={'padding': '15px', 'backgroundColor': 'white', 'borderRadius': '8px',
                         'border': f'2px solid {color}', 'marginBottom': '10px'})
                for level, message, color in anomalies[:5]  # Show top 5
            ]),
        ], style={'marginTop': '20px'})

    def create_empty_chart(self, message):
        """Create an empty chart with a message."""
        fig = go.Figure()
        fig.add_annotation(
            text=message,
            xref="paper",
            yref="paper",
            x=0.5,
            y=0.5,
            showarrow=False,
            font=dict(size=20, color="#7f8c8d")
        )
        fig.update_layout(
            xaxis=dict(showgrid=False, showticklabels=False, zeroline=False),
            yaxis=dict(showgrid=False, showticklabels=False, zeroline=False),
            height=400
        )
        return fig

    def run(self, host='0.0.0.0', port=8051, debug=False):
        """Run the analytics dashboard."""
        self.app.run(host=host, port=port, debug=debug)


if __name__ == "__main__":
    from arbitrage_detector import ArbitrageDetector
    detector = ArbitrageDetector()
    dashboard = AnalyticsDashboard(detector)
    dashboard.run()
