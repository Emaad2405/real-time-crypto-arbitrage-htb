"""Interactive dashboard for comparing bot performance."""
import dash
from dash import dcc, html, Input, Output
import plotly.graph_objs as go
import plotly.express as px
import pandas as pd
from datetime import datetime
from typing import Optional

from bot.backtest_engine import BacktestEngine


class BacktestDashboard:
    """
    Interactive Dash dashboard for bot comparison.

    Displays:
    - Performance comparison table
    - Capital curves
    - Trade distribution
    - Win rate comparison
    - Profit distribution
    - Drawdown analysis
    """

    def __init__(self, backtest_engine: BacktestEngine):
        """
        Initialize dashboard.

        Args:
            backtest_engine: Completed backtest engine with results
        """
        self.engine = backtest_engine
        self.app = dash.Dash(__name__, title="Bot Backtest Comparison")

        self._setup_layout()
        self._setup_callbacks()

    def _setup_layout(self):
        """Setup dashboard layout."""
        self.app.layout = html.Div([
            html.Div([
                html.H1("🤖 Arbitrage Bot Backtest Comparison",
                       style={'textAlign': 'center', 'color': '#2c3e50'}),
                html.P(f"Backtest Results - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                      style={'textAlign': 'center', 'color': '#7f8c8d'}),
            ], style={'padding': '20px', 'backgroundColor': '#ecf0f1'}),

            # Performance Comparison Table
            html.Div([
                html.H2("📊 Performance Comparison", style={'color': '#2c3e50'}),
                html.Div(id='performance-table'),
            ], style={'padding': '20px'}),

            # Capital Curves
            html.Div([
                html.H2("💰 Capital Curves", style={'color': '#2c3e50'}),
                dcc.Graph(id='capital-curves'),
            ], style={'padding': '20px'}),

            # Row with two charts
            html.Div([
                # Win Rate Comparison
                html.Div([
                    html.H3("🎯 Win Rate Comparison", style={'color': '#2c3e50'}),
                    dcc.Graph(id='win-rate-chart'),
                ], style={'width': '48%', 'display': 'inline-block', 'padding': '10px'}),

                # Return Comparison
                html.Div([
                    html.H3("📈 Return Comparison", style={'color': '#2c3e50'}),
                    dcc.Graph(id='return-chart'),
                ], style={'width': '48%', 'display': 'inline-block', 'padding': '10px'}),
            ]),

            # Trade Distribution
            html.Div([
                html.H2("📉 Profit Distribution", style={'color': '#2c3e50'}),
                dcc.Graph(id='profit-distribution'),
            ], style={'padding': '20px'}),

            # Row with Sharpe and Drawdown
            html.Div([
                # Sharpe Ratio
                html.Div([
                    html.H3("📊 Sharpe Ratio", style={'color': '#2c3e50'}),
                    dcc.Graph(id='sharpe-chart'),
                ], style={'width': '48%', 'display': 'inline-block', 'padding': '10px'}),

                # Max Drawdown
                html.Div([
                    html.H3("📉 Maximum Drawdown", style={'color': '#2c3e50'}),
                    dcc.Graph(id='drawdown-chart'),
                ], style={'width': '48%', 'display': 'inline-block', 'padding': '10px'}),
            ]),

            # Trade Timeline
            html.Div([
                html.H2("⏰ Trade Timeline", style={'color': '#2c3e50'}),
                dcc.Graph(id='trade-timeline'),
            ], style={'padding': '20px'}),

            # Auto-refresh (disabled by default)
            dcc.Interval(
                id='interval-component',
                interval=30*1000,  # 30 seconds
                n_intervals=0,
                disabled=True  # No refresh needed for backtest
            ),

        ], style={'fontFamily': 'Arial, sans-serif', 'backgroundColor': '#f5f5f5'})

    def _setup_callbacks(self):
        """Setup dashboard callbacks."""

        @self.app.callback(
            [
                Output('performance-table', 'children'),
                Output('capital-curves', 'figure'),
                Output('win-rate-chart', 'figure'),
                Output('return-chart', 'figure'),
                Output('profit-distribution', 'figure'),
                Output('sharpe-chart', 'figure'),
                Output('drawdown-chart', 'figure'),
                Output('trade-timeline', 'figure'),
            ],
            [Input('interval-component', 'n_intervals')]
        )
        def update_dashboard(n):
            """Update all dashboard components."""
            return (
                self._create_performance_table(),
                self._create_capital_curves(),
                self._create_win_rate_chart(),
                self._create_return_chart(),
                self._create_profit_distribution(),
                self._create_sharpe_chart(),
                self._create_drawdown_chart(),
                self._create_trade_timeline(),
            )

    def _create_performance_table(self):
        """Create performance comparison table."""
        comparison_df = self.engine.compare_bots()

        if comparison_df.empty:
            return html.P("No data available")

        # Create HTML table
        return html.Table([
            html.Thead(
                html.Tr([html.Th(col) for col in comparison_df.columns])
            ),
            html.Tbody([
                html.Tr([
                    html.Td(comparison_df.iloc[i][col])
                    for col in comparison_df.columns
                ]) for i in range(len(comparison_df))
            ])
        ], style={
            'width': '100%',
            'borderCollapse': 'collapse',
            'border': '1px solid #ddd',
            'backgroundColor': 'white'
        })

    def _create_capital_curves(self):
        """Create capital curve comparison."""
        fig = go.Figure()

        for bot in self.engine.bots:
            capital_df = self.engine.get_capital_curve(bot.name)

            if not capital_df.empty:
                fig.add_trace(go.Scatter(
                    x=capital_df['timestamp'],
                    y=capital_df['capital'],
                    mode='lines',
                    name=bot.name,
                    line=dict(width=2)
                ))

        fig.update_layout(
            xaxis_title="Time",
            yaxis_title="Capital ($)",
            hovermode='x unified',
            template='plotly_white',
            height=400
        )

        return fig

    def _create_win_rate_chart(self):
        """Create win rate comparison bar chart."""
        comparison_df = self.engine.compare_bots()

        fig = go.Figure(data=[
            go.Bar(
                x=comparison_df['Bot'],
                y=comparison_df['Win Rate (%)'],
                text=comparison_df['Win Rate (%)'].apply(lambda x: f"{x:.1f}%"),
                textposition='auto',
                marker_color=['#3498db', '#e74c3c']
            )
        ])

        fig.update_layout(
            yaxis_title="Win Rate (%)",
            template='plotly_white',
            height=300,
            showlegend=False
        )

        return fig

    def _create_return_chart(self):
        """Create return comparison bar chart."""
        comparison_df = self.engine.compare_bots()

        fig = go.Figure(data=[
            go.Bar(
                x=comparison_df['Bot'],
                y=comparison_df['Return (%)'],
                text=comparison_df['Return (%)'].apply(lambda x: f"{x:.2f}%"),
                textposition='auto',
                marker_color=['#2ecc71', '#95a5a6']
            )
        ])

        fig.update_layout(
            yaxis_title="Return (%)",
            template='plotly_white',
            height=300,
            showlegend=False
        )

        return fig

    def _create_profit_distribution(self):
        """Create profit distribution histogram."""
        fig = go.Figure()

        for bot in self.engine.bots:
            trades = self.engine.get_trade_history(bot.name)
            if trades:
                profits = [t.profit_usd for t in trades]

                fig.add_trace(go.Histogram(
                    x=profits,
                    name=bot.name,
                    opacity=0.7,
                    nbinsx=50
                ))

        fig.update_layout(
            xaxis_title="Profit per Trade ($)",
            yaxis_title="Frequency",
            barmode='overlay',
            template='plotly_white',
            height=400
        )

        return fig

    def _create_sharpe_chart(self):
        """Create Sharpe ratio comparison."""
        comparison_df = self.engine.compare_bots()

        fig = go.Figure(data=[
            go.Bar(
                x=comparison_df['Bot'],
                y=comparison_df['Sharpe Ratio'],
                text=comparison_df['Sharpe Ratio'].apply(lambda x: f"{x:.3f}"),
                textposition='auto',
                marker_color=['#9b59b6', '#34495e']
            )
        ])

        fig.update_layout(
            yaxis_title="Sharpe Ratio",
            template='plotly_white',
            height=300,
            showlegend=False
        )

        return fig

    def _create_drawdown_chart(self):
        """Create maximum drawdown comparison."""
        comparison_df = self.engine.compare_bots()

        fig = go.Figure(data=[
            go.Bar(
                x=comparison_df['Bot'],
                y=comparison_df['Max Drawdown (%)'],
                text=comparison_df['Max Drawdown (%)'].apply(lambda x: f"{x:.2f}%"),
                textposition='auto',
                marker_color=['#e67e22', '#1abc9c']
            )
        ])

        fig.update_layout(
            yaxis_title="Max Drawdown (%)",
            template='plotly_white',
            height=300,
            showlegend=False
        )

        return fig

    def _create_trade_timeline(self):
        """Create trade timeline scatter plot."""
        fig = go.Figure()

        for bot in self.engine.bots:
            trades = self.engine.get_trade_history(bot.name)
            if trades:
                timestamps = [t.timestamp for t in trades]
                profits = [t.profit_usd for t in trades]
                colors = ['green' if t.success else 'red' for t in trades]

                fig.add_trace(go.Scatter(
                    x=timestamps,
                    y=profits,
                    mode='markers',
                    name=bot.name,
                    marker=dict(size=8, opacity=0.6),
                    text=[f"${p:.2f}" for p in profits],
                    hovertemplate='%{text}<extra></extra>'
                ))

        fig.update_layout(
            xaxis_title="Time",
            yaxis_title="Profit per Trade ($)",
            hovermode='closest',
            template='plotly_white',
            height=400
        )

        # Add horizontal line at y=0
        fig.add_hline(y=0, line_dash="dash", line_color="gray", opacity=0.5)

        return fig

    def run(self, host='0.0.0.0', port=8052, debug=False):
        """
        Run the dashboard server.

        Args:
            host: Host address
            port: Port number
            debug: Debug mode
        """
        self.app.run(host=host, port=port, debug=debug)
