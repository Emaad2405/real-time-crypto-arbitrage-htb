# """Real-time Plotly Dash dashboard for arbitrage monitoring."""
# import dash
# from dash import dcc, html, Input, Output, State
# import dash_bootstrap_components as dbc
# import plotly.graph_objs as go
# from datetime import datetime, timedelta
# import pandas as pd
# from collections import deque
# from loguru import logger


# class ArbitrageDashboard:
#     """Real-time dashboard for monitoring arbitrage opportunities."""

#     # def __init__(self, detector, ml_predictor=None):
#     #     self.detector = detector
#     #     self.ml_predictor = ml_predictor
#     def __init__(self, detector, spread_predictor=None, opportunity_scorer=None):
#         self.detector = detector
#         self.spread_predictor = spread_predictor          # <-- renamed
#         self.opportunity_scorer = opportunity_scorer

#         # Initialize Dash app with Bootstrap theme
#         self.app = dash.Dash(
#             __name__,
#             external_stylesheets=[dbc.themes.CYBORG],
#             title="Crypto Arbitrage Monitor"
#         )

#         # Data storage for time series
#         self.price_history = {
#             'BTC-USD': deque(maxlen=200),
#             'ETH-USD': deque(maxlen=200),
#             'SOL-USD': deque(maxlen=200)
#         }

#         self.opportunity_history = deque(maxlen=100)

#         # Setup layout
#         self._setup_layout()
#         self._setup_callbacks()

#     def _setup_layout(self):
#         """Create dashboard layout."""
#         self.app.layout = dbc.Container([
#             # Header
#             dbc.Row([
#                 dbc.Col([
#                     html.H1("🚀 Crypto Arbitrage Monitor", className="text-center mb-4"),
#                     html.P(
#                         "Real-time arbitrage detection across Coinbase, Binance, and Bitstamp",
#                         className="text-center text-muted"
#                     )
#                 ])
#             ]),

#             html.Hr(),

#             # Statistics Cards
#             dbc.Row([
#                 dbc.Col([
#                     dbc.Card([
#                         dbc.CardBody([
#                             html.H4("Total Opportunities", className="card-title"),
#                             html.H2(id="total-opps", children="0", className="text-success")
#                         ])
#                     ], color="dark", outline=True)
#                 ], width=3),

#                 dbc.Col([
#                     dbc.Card([
#                         dbc.CardBody([
#                             html.H4("Avg Profit", className="card-title"),
#                             html.H2(id="avg-profit", children="0.00%", className="text-info")
#                         ])
#                     ], color="dark", outline=True)
#                 ], width=3),

#                 dbc.Col([
#                     dbc.Card([
#                         dbc.CardBody([
#                             html.H4("Max Profit", className="card-title"),
#                             html.H2(id="max-profit", children="0.00%", className="text-warning")
#                         ])
#                     ], color="dark", outline=True)
#                 ], width=3),

#                 dbc.Col([
#                     dbc.Card([
#                         dbc.CardBody([
#                             html.H4("Recent (5min)", className="card-title"),
#                             html.H2(id="recent-count", children="0", className="text-danger")
#                         ])
#                     ], color="dark", outline=True)
#                 ], width=3),
#             ], className="mb-4"),

#             # Best Current Opportunity Alert
#             dbc.Row([
#                 dbc.Col([
#                     html.Div(id="best-opportunity-alert")
#                 ])
#             ], className="mb-4"),

#             # Live Price Charts
#             dbc.Row([
#                 dbc.Col([
#                     dbc.Card([
#                         dbc.CardHeader("📈 Live Price Feeds"),
#                         dbc.CardBody([
#                             dcc.Graph(id="price-chart", config={'displayModeBar': False})
#                         ])
#                     ], color="light")
#                 ])
#             ], className="mb-4"),

#             # Opportunities Table
#             dbc.Row([
#                 dbc.Col([
#                     dbc.Card([
#                         dbc.CardHeader("💰 Recent Arbitrage Opportunities"),
#                         dbc.CardBody([
#                             html.Div(id="opportunities-table")
#                         ])
#                     ], color="light")
#                 ], width=8),

#                 # Spread Heatmap
#                 dbc.Col([
#                     dbc.Card([
#                         dbc.CardHeader("🔥 Spread Heatmap"),
#                         dbc.CardBody([
#                             dcc.Graph(id="spread-heatmap", config={'displayModeBar': False})
#                         ])
#                     ], color="light")
#                 ], width=4),
#             ], className="mb-4"),

#             # ML Predictions (if available)
#             dbc.Row([
#                 dbc.Col([
#                     dbc.Card([
#                         dbc.CardHeader("🤖 ML Spread Predictions"),
#                         dbc.CardBody([
#                             html.Div(id="ml-predictions")
#                         ])
#                     ], color="light")
#                 ])
#             ], className="mb-4"),

#             # Backtest Results
#             dbc.Row([
#                 dbc.Col([
#                     dbc.Card([
#                         dbc.CardHeader("📊 Backtest Performance"),
#                         dbc.CardBody([
#                             html.Div(id="backtest-results")
#                         ])
#                     ], color="light")
#                 ])
#             ]),

#             # Auto-refresh interval
#             dcc.Interval(
#                 id='interval-component',
#                 interval=1000,  # Update every 1 second
#                 n_intervals=0
#             )

#         ], fluid=True, className="p-4")

#     def _setup_callbacks(self):
#         """Setup dashboard callbacks."""

#         @self.app.callback(
#             [
#                 Output("total-opps", "children"),
#                 Output("avg-profit", "children"),
#                 Output("max-profit", "children"),
#                 Output("recent-count", "children"),
#             ],
#             Input("interval-component", "n_intervals")
#         )
#         def update_stats(n):
#             stats = self.detector.get_statistics()

#             return (
#                 f"{stats['total_opportunities']:,}",
#                 f"{stats['avg_profit']:.2f}%",
#                 f"{stats['max_profit']:.2f}%",
#                 str(stats['recent_count'])
#             )

#         @self.app.callback(
#             Output("best-opportunity-alert", "children"),
#             Input("interval-component", "n_intervals")
#         )
#         def update_best_opportunity(n):
#             best = self.detector.get_best_opportunity()

#             if not best:
#                 return dbc.Alert(
#                     "⏳ Monitoring exchanges... No opportunities detected yet.",
#                     color="secondary"
#                 )

#             return dbc.Alert([
#                 html.H4("🎯 BEST OPPORTUNITY", className="alert-heading"),
#                 html.Hr(),
#                 html.P([
#                     html.Strong(f"{best.symbol}: "),
#                     f"Buy on {best.buy_exchange} @ ${best.buy_price:.2f} → ",
#                     f"Sell on {best.sell_exchange} @ ${best.sell_price:.2f}"
#                 ]),
#                 html.P([
#                     html.Strong("Profit after fees: "),
#                     html.Span(f"{best.profit_after_fees:.2f}%", className="text-light fs-4"),
#                     f" (spread: {best.spread_pct:.2f}%)"
#                 ]),
#                 html.Small(f"Detected: {best.timestamp.strftime('%H:%M:%S')}")
#             ], color="success", className="mb-0")

#         @self.app.callback(
#             Output("price-chart", "figure"),
#             Input("interval-component", "n_intervals")
#         )
#         def update_price_chart(n):
#             fig = go.Figure()

#             symbols = ['BTC-USD', 'ETH-USD', 'SOL-USD']
#             colors = {'Coinbase': '#0052FF', 'Binance': '#F3BA2F', 'Bitstamp': '#00D43A'}

#             for symbol in symbols:
#                 # Get latest prices for this symbol
#                 prices = self.detector.get_latest_prices(symbol)

#                 for exchange, price_data in prices.items():
#                     # Store in history
#                     if symbol not in self.price_history:
#                         self.price_history[symbol] = deque(maxlen=200)

#                     self.price_history[symbol].append({
#                         'timestamp': price_data.timestamp,
#                         'exchange': exchange,
#                         'price': price_data.price
#                     })

#             # Plot each symbol
#             for symbol in symbols:
#                 if symbol in self.price_history and len(self.price_history[symbol]) > 0:
#                     df = pd.DataFrame(list(self.price_history[symbol]))

#                     for exchange in df['exchange'].unique():
#                         ex_df = df[df['exchange'] == exchange]

#                         fig.add_trace(go.Scatter(
#                             x=ex_df['timestamp'],
#                             y=ex_df['price'],
#                             mode='lines',
#                             name=f"{symbol} - {exchange}",
#                             line=dict(color=colors.get(exchange, '#FFFFFF'), width=2),
#                             hovertemplate=f"<b>{exchange}</b><br>" +
#                                         "Price: $%{y:.2f}<br>" +
#                                         "<extra></extra>"
#                         ))

#             fig.update_layout(
#                 template="plotly_dark",
#                 height=400,
#                 xaxis_title="Time",
#                 yaxis_title="Price (USD)",
#                 hovermode='x unified',
#                 legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
#             )

#             return fig

#         @self.app.callback(
#             Output("opportunities-table", "children"),
#             Input("interval-component", "n_intervals")
#         )
#         def update_opportunities_table(n):
#             recent_opps = self.detector.get_recent_opportunities(minutes=5)

#             if not recent_opps:
#                 return html.P("No opportunities detected yet...", className="text-muted")

#             # Sort by profit
#             recent_opps = sorted(
#                 recent_opps,
#                 key=lambda x: x.profit_after_fees,
#                 reverse=True
#             )[:20]  # Top 20

#             table_header = [
#                 html.Thead(html.Tr([
#                     html.Th("Time"),
#                     html.Th("Symbol"),
#                     html.Th("Buy"),
#                     html.Th("Sell"),
#                     html.Th("Spread"),
#                     html.Th("Profit"),
#                 ]))
#             ]

#             rows = []
#             for opp in recent_opps:
#                 rows.append(html.Tr([
#                     html.Td(opp.timestamp.strftime("%H:%M:%S")),
#                     html.Td(opp.symbol),
#                     html.Td(f"{opp.buy_exchange} ${opp.buy_price:.2f}"),
#                     html.Td(f"{opp.sell_exchange} ${opp.sell_price:.2f}"),
#                     html.Td(f"{opp.spread_pct:.2f}%"),
#                     html.Td(
#                         f"{opp.profit_after_fees:.2f}%",
#                         className="text-success fw-bold"
#                     ),
#                 ]))

#             table_body = [html.Tbody(rows)]

#             return dbc.Table(
#                 table_header + table_body,
#                 bordered=True,
#                 hover=True,
#                 responsive=True,
#                 striped=True,
#                 className="mb-0"
#             )

#         @self.app.callback(
#             Output("spread-heatmap", "figure"),
#             Input("interval-component", "n_intervals")
#         )
#         def update_spread_heatmap(n):
#             """Create heatmap of spreads between exchanges."""
#             symbols = ['BTC-USD', 'ETH-USD', 'SOL-USD']
#             exchanges = ['Coinbase', 'Binance', 'Bitstamp']

#             # Calculate current spreads
#             spread_matrix = []

#             for symbol in symbols:
#                 spreads = self.detector.calculate_spread_metrics(symbol)
#                 row = []

#                 for ex1 in exchanges:
#                     for ex2 in exchanges:
#                         if ex1 == ex2:
#                             row.append(0)
#                         else:
#                             key = f"{ex1}->{ex2}"
#                             if key in spreads:
#                                 row.append(spreads[key].get('current', 0))
#                             else:
#                                 row.append(0)
#                 spread_matrix.append(row)

#             fig = go.Figure(data=go.Heatmap(
#                 z=spread_matrix,
#                 x=exchanges * len(exchanges),
#                 y=symbols,
#                 colorscale='RdYlGn',
#                 zmid=0,
#                 text=[[f"{val:.2f}%" for val in row] for row in spread_matrix],
#                 texttemplate="%{text}",
#                 textfont={"size": 10},
#                 hovertemplate="<b>%{y}</b><br>Spread: %{z:.2f}%<extra></extra>"
#             ))

#             fig.update_layout(
#                 template="plotly_dark",
#                 height=300,
#                 xaxis_title="Exchange",
#                 yaxis_title="Symbol"
#             )

#             return fig

#         @self.app.callback(
#             Output("ml-predictions", "children"),
#             Input("interval-component", "n_intervals")
#         )
#         def update_ml_predictions(n):
#             if not self.spread_predictor or not self.spread_predictor.is_trained:
#                 return html.P(
#                     "⚙️ ML model training in progress... (need ~5 min of data)",
#                     className="text-muted"
#                 )

#             predictions = []
#             symbols = ['BTC-USD', 'ETH-USD', 'SOL-USD']

#             for symbol in symbols:
#                 df = self.detector.get_historical_data(symbol)
#                 if not df.empty:
#                     pred = self.spread_predictor.predict_spread(df)
#                     if pred is not None:
#                         predictions.append(
#                             dbc.ListGroupItem([
#                                 html.Strong(f"{symbol}: "),
#                                 f"Predicted spread in 30s: ",
#                                 html.Span(
#                                     f"{pred:.2f}%",
#                                     className="text-success" if pred > 0.5 else "text-danger"
#                                 )
#                             ])
#                         )

#             if not predictions:
#                 return html.P("No predictions available yet...", className="text-muted")

#             return dbc.ListGroup(predictions)

#         @self.app.callback(
#             Output("backtest-results", "children"),
#             Input("interval-component", "n_intervals")
#         )
#         def update_backtest_results(n):
#             """Run backtest on recent opportunities."""
#             from arbitrage_detector import BacktestEngine

#             backtest = BacktestEngine(initial_capital=10000)
#             recent_opps = self.detector.get_recent_opportunities(minutes=30)  # 30 minutes for live training

#             for opp in recent_opps:
#                 backtest.execute_opportunity(opp)

#             results = backtest.get_results()

#             if results['total_trades'] == 0:
#                 return html.P("No trades to backtest yet...", className="text-muted")

#             return dbc.Row([
#                 dbc.Col([
#                     html.P([
#                         html.Strong("Total Trades: "),
#                         str(results['total_trades'])
#                     ]),
#                     html.P([
#                         html.Strong("Win Rate: "),
#                         f"{results['win_rate']:.1f}%"
#                     ]),
#                 ]),
#                 dbc.Col([
#                     html.P([
#                         html.Strong("Total Return: "),
#                         html.Span(
#                             f"${results['total_return']:.2f} ({results['total_return_pct']:.2f}%)",
#                             className="text-success" if results['total_return'] > 0 else "text-danger"
#                         )
#                     ]),
#                     html.P([
#                         html.Strong("Avg Profit/Trade: "),
#                         f"${results['avg_profit_per_trade']:.2f}"
#                     ]),
#                 ]),
#             ])

#     def run(self, host='0.0.0.0', port=8050, debug=False):
#         """Start the dashboard server."""
#         logger.info(f"Starting dashboard on http://{host}:{port}")
#         self.app.run(host=host, port=port, debug=debug)





"""Real-time Plotly Dash dashboard for arbitrage monitoring."""
import dash
from dash import dcc, html, Input, Output
import dash_bootstrap_components as dbc
import plotly.graph_objs as go
from datetime import datetime
import pandas as pd
from collections import deque
from loguru import logger


class ArbitrageDashboard:
    """Real-time dashboard for monitoring arbitrage opportunities."""

    def __init__(self, detector, spread_predictor=None, opportunity_scorer=None):
        self.detector = detector
        self.spread_predictor = spread_predictor
        self.opportunity_scorer = opportunity_scorer

        # Initialize Dash app with Bootstrap theme
        self.app = dash.Dash(
            __name__,
            external_stylesheets=[dbc.themes.CYBORG],
            title="Crypto Arbitrage Monitor"
        )

        # Data storage for time series (for live price feed)
        self.price_history = {
            'BTC-USD': deque(maxlen=200),
            'ETH-USD': deque(maxlen=200),
            'SOL-USD': deque(maxlen=200)
        }

        # Normalized price history for mini charts
        self.normalized_history = {}
        self.last_update_time = {}
        symbols = ['BTC-USD', 'ETH-USD', 'SOL-USD']
        for sym in symbols:
            self.normalized_history[sym] = deque(maxlen=200)
            self.last_update_time[sym] = None

        self.opportunity_history = deque(maxlen=100)

        # Setup layout
        self._setup_layout()
        self._setup_callbacks()

    def _setup_layout(self):
        """Create dashboard layout."""
        self.app.layout = dbc.Container([
            # Header
            dbc.Row([
                dbc.Col([
                    html.H1("🚀 Crypto Arbitrage Monitor", className="text-center mb-4"),
                    html.P(
                        "Real-time arbitrage detection across Coinbase, Binance, and Bitstamp",
                        className="text-center text-muted"
                    )
                ])
            ]),

            html.Hr(),

            # Statistics Cards
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H4("Total Opportunities", className="card-title"),
                            html.H2(id="total-opps", children="0", className="text-success")
                        ])
                    ], color="dark", outline=True)
                ], width=3),

                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H4("Avg Profit", className="card-title"),
                            html.H2(id="avg-profit", children="0.00%", className="text-info")
                        ])
                    ], color="dark", outline=True)
                ], width=3),

                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H4("Max Profit", className="card-title"),
                            html.H2(id="max-profit", children="0.00%", className="text-warning")
                        ])
                    ], color="dark", outline=True)
                ], width=3),

                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H4("Recent (5min)", className="card-title"),
                            html.H2(id="recent-count", children="0", className="text-danger")
                        ])
                    ], color="dark", outline=True)
                ], width=3),
            ], className="mb-4"),

            # Best Current Opportunity Alert
            dbc.Row([
                dbc.Col([
                    html.Div(id="best-opportunity-alert")
                ])
            ], className="mb-4"),

            # Live Price Feed (Original - All symbols on one chart)
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader("📈 Live Price Feeds (Absolute Prices)"),
                        dbc.CardBody([
                            dcc.Graph(id="price-chart", config={'displayModeBar': False})
                        ])
                    ], color="light")
                ])
            ], className="mb-4"),

            # 3 Mini Normalized Charts (Percentage Change)
            dbc.Row([
                dbc.Col([
                    html.H5("📊 Normalized Price Changes (% from baseline)", className="text-center mb-3")
                ])
            ]),
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader("BTC-USD"),
                        dbc.CardBody([
                            dcc.Graph(id="chart-btc-usd", config={'displayModeBar': False})
                        ])
                    ], color="light")
                ], width=4),
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader("ETH-USD"),
                        dbc.CardBody([
                            dcc.Graph(id="chart-eth-usd", config={'displayModeBar': False})
                        ])
                    ], color="light")
                ], width=4),
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader("SOL-USD"),
                        dbc.CardBody([
                            dcc.Graph(id="chart-sol-usd", config={'displayModeBar': False})
                        ])
                    ], color="light")
                ], width=4),
            ], className="mb-4"),

            # Opportunities Table + Spread Heatmap
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader("💰 Recent Arbitrage Opportunities"),
                        dbc.CardBody([
                            html.Div(id="opportunities-table")
                        ])
                    ], color="light")
                ], width=8),

                # Spread Heatmap (Fixed)
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader("🔥 Live Spread Matrix"),
                        dbc.CardBody([
                            dcc.Graph(id="spread-heatmap", config={'displayModeBar': False})
                        ])
                    ], color="light")
                ], width=4),
            ], className="mb-4"),

            # ML Predictions (if available)
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader("🤖 ML Spread Predictions"),
                        dbc.CardBody([
                            html.Div(id="ml-predictions")
                        ])
                    ], color="light")
                ])
            ], className="mb-4"),

            # Backtest Results
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader("📊 Backtest Performance"),
                        dbc.CardBody([
                            html.Div(id="backtest-results")
                        ])
                    ], color="light")
                ])
            ]),

            # Auto-refresh interval
            dcc.Interval(
                id='interval-component',
                interval=1000,  # Update every 1 second
                n_intervals=0
            )

        ], fluid=True, className="p-4")

    def _setup_callbacks(self):
        """Setup dashboard callbacks."""

        @self.app.callback(
            [
                Output("total-opps", "children"),
                Output("avg-profit", "children"),
                Output("max-profit", "children"),
                Output("recent-count", "children"),
            ],
            Input("interval-component", "n_intervals")
        )
        def update_stats(n):
            try:
                stats = self.detector.get_statistics()
                return (
                    f"{stats['total_opportunities']:,}",
                    f"{stats['avg_profit']:.2f}%",
                    f"{stats['max_profit']:.2f}%",
                    str(stats['recent_count'])
                )
            except Exception as e:
                logger.error(f"Error updating stats: {e}")
                return "0", "0.00%", "0.00%", "0"

        @self.app.callback(
            Output("best-opportunity-alert", "children"),
            Input("interval-component", "n_intervals")
        )
        def update_best_opportunity(n):
            try:
                best = self.detector.get_best_opportunity()

                if not best:
                    return dbc.Alert(
                        "⏳ Monitoring exchanges... No opportunities detected yet.",
                        color="secondary"
                    )

                return dbc.Alert([
                    html.H4("🎯 BEST OPPORTUNITY", className="alert-heading"),
                    html.Hr(),
                    html.P([
                        html.Strong(f"{best.symbol}: "),
                        f"Buy on {best.buy_exchange} @ ${best.buy_price:.2f} → ",
                        f"Sell on {best.sell_exchange} @ ${best.sell_price:.2f}"
                    ]),
                    html.P([
                        html.Strong("Profit after fees: "),
                        html.Span(f"{best.profit_after_fees:.2f}%", className="text-white fs-4"),
                        f" (spread: {best.spread_pct:.2f}%)"
                    ]),
                    html.Small(f"Detected: {best.timestamp.strftime('%H:%M:%S')}")
                ], color="light", className="mb-0")
            except Exception as e:
                logger.error(f"Error updating best opportunity: {e}")
                return dbc.Alert("Error loading opportunity data", color="danger")

        @self.app.callback(
            Output("price-chart", "figure"),
            Input("interval-component", "n_intervals")
        )
        def update_price_chart(n):
            """Update the main live price feed chart (absolute prices)."""
            try:
                fig = go.Figure()

                symbols = ['BTC-USD', 'ETH-USD', 'SOL-USD']
                colors = {'Coinbase': '#0052FF', 'Binance': '#F3BA2F', 'Bitstamp': '#00D43A'}

                for symbol in symbols:
                    # Get latest prices for this symbol
                    prices = self.detector.get_latest_prices(symbol)

                    for exchange, price_data in prices.items():
                        # Store in history
                        if symbol not in self.price_history:
                            self.price_history[symbol] = deque(maxlen=200)

                        self.price_history[symbol].append({
                            'timestamp': price_data.timestamp,
                            'exchange': exchange,
                            'price': price_data.price
                        })

                # Plot each symbol
                for symbol in symbols:
                    if symbol in self.price_history and len(self.price_history[symbol]) > 0:
                        df = pd.DataFrame(list(self.price_history[symbol]))

                        for exchange in df['exchange'].unique():
                            ex_df = df[df['exchange'] == exchange]

                            fig.add_trace(go.Scatter(
                                x=ex_df['timestamp'],
                                y=ex_df['price'],
                                mode='lines',
                                name=f"{symbol} - {exchange}",
                                line=dict(color=colors.get(exchange, '#FFFFFF'), width=2),
                                hovertemplate=f"<b>{exchange}</b><br>" +
                                            "Price: $%{y:.2f}<br>" +
                                            "<extra></extra>"
                            ))

                fig.update_layout(
                    template="plotly_dark",
                    height=400,
                    xaxis_title="Time",
                    yaxis_title="Price (USD)",
                    hovermode='x unified',
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
                )

                return fig
            except Exception as e:
                logger.error(f"Error updating price chart: {e}")
                fig = go.Figure()
                fig.add_annotation(text=f"Error: {str(e)}", x=0.5, y=0.5, showarrow=False, xref="paper", yref="paper")
                fig.update_layout(template="plotly_dark", height=400)
                return fig

        # === 3 MINI NORMALIZED CHARTS ===
        def make_chart_callback(symbol):
            """Factory function to create chart callbacks with proper closure."""
            def chart_updater(n):
                return self._make_normalized_chart(symbol)
            return chart_updater
        
        for symbol in ['BTC-USD', 'ETH-USD', 'SOL-USD']:
            self.app.callback(
                Output(f"chart-{symbol.lower()}", "figure"),
                Input("interval-component", "n_intervals")
            )(make_chart_callback(symbol))

        @self.app.callback(
            Output("opportunities-table", "children"),
            Input("interval-component", "n_intervals")
        )
        def update_opportunities_table(n):
            try:
                recent_opps = self.detector.get_recent_opportunities(minutes=5)

                if not recent_opps:
                    return html.P("⏳ No opportunities detected yet...", className="text-muted")

                # Sort by profit
                recent_opps = sorted(
                    recent_opps,
                    key=lambda x: x.profit_after_fees,
                    reverse=True
                )[:20]  # Top 20

                table_header = [
                    html.Thead(html.Tr([
                        html.Th("Time"),
                        html.Th("Symbol"),
                        html.Th("Buy"),
                        html.Th("Sell"),
                        html.Th("Spread"),
                        html.Th("Profit"),
                    ]))
                ]

                rows = []
                for opp in recent_opps:
                    rows.append(html.Tr([
                        html.Td(opp.timestamp.strftime("%H:%M:%S")),
                        html.Td(opp.symbol),
                        html.Td(f"{opp.buy_exchange} ${opp.buy_price:.2f}"),
                        html.Td(f"{opp.sell_exchange} ${opp.sell_price:.2f}"),
                        html.Td(f"{opp.spread_pct:.2f}%"),
                        html.Td(
                            f"{opp.profit_after_fees:.2f}%",
                            className="text-success fw-bold"
                        ),
                    ]))

                table_body = [html.Tbody(rows)]

                return dbc.Table(
                    table_header + table_body,
                    bordered=True,
                    hover=True,
                    responsive=True,
                    striped=True,
                    className="mb-0"
                )
            except Exception as e:
                logger.error(f"Error updating opportunities table: {e}")
                return html.P(f"❌ Error: {str(e)}", className="text-danger")

        @self.app.callback(
            Output("spread-heatmap", "figure"),
            Input("interval-component", "n_intervals")
        )
        def update_spread_heatmap(n):
            """Create heatmap of spreads between exchanges (FIXED VERSION)."""
            try:
                exchanges = ['Coinbase', 'Binance', 'Bitstamp']
                z, text = [], []
                latest = self.detector.latest_prices

                for ex1 in exchanges:
                    row, row_text = [], []
                    for ex2 in exchanges:
                        if ex1 == ex2:
                            row.append(0)
                            row_text.append("-")
                            continue
                        
                        # Calculate spread for BTC-USD
                        p1 = p2 = None
                        for (ex, sym), price_data in latest.items():
                            if sym == 'BTC-USD':
                                if ex == ex1: 
                                    p1 = price_data.price
                                if ex == ex2: 
                                    p2 = price_data.price
                        
                        # Spread: (sell_price - buy_price) / buy_price * 100
                        spread = ((p2 - p1) / p1 * 100) if (p1 and p2 and p1 > 0) else 0
                        row.append(spread)
                        row_text.append(f"{spread:+.2f}%")
                    
                    z.append(row)
                    text.append(row_text)

                fig = go.Figure(data=go.Heatmap(
                    z=z, 
                    x=exchanges, 
                    y=exchanges,
                    colorscale='RdYlGn', 
                    zmid=0,
                    text=text, 
                    texttemplate="%{text}", 
                    textfont={"size": 11},
                    hovertemplate="<b>Buy: %{y} → Sell: %{x}</b><br>Spread: %{z:.2f}%<extra></extra>"
                ))
                
                fig.update_layout(
                    title="Live Spread Matrix (BTC-USD)", 
                    height=300, 
                    template="plotly_dark",
                    xaxis_title="Sell Exchange",
                    yaxis_title="Buy Exchange"
                )
                return fig
            except Exception as e:
                logger.error(f"Error updating heatmap: {e}")
                fig = go.Figure()
                fig.add_annotation(
                    text=f"Error: {str(e)}", 
                    x=0.5, y=0.5, 
                    showarrow=False, 
                    xref="paper", yref="paper"
                )
                fig.update_layout(template="plotly_dark", height=300)
                return fig

        @self.app.callback(
            Output("ml-predictions", "children"),
            Input("interval-component", "n_intervals")
        )
        def update_ml_predictions(n):
            try:
                if not self.spread_predictor:
                    return html.P("❌ Spread predictor not initialized", className="text-danger")
                
                if not self.spread_predictor.is_trained:
                    return html.P(
                        "⚙️ ML model training in progress... (need ~5 min of data)",
                        className="text-muted"
                    )

                predictions = []
                symbols = ['BTC-USD', 'ETH-USD', 'SOL-USD']

                for symbol in symbols:
                    df = self.detector.get_historical_data(symbol)
                    if df is not None and not df.empty:
                        pred = self.spread_predictor.predict_spread(df)
                        if pred is not None:
                            predictions.append(
                                dbc.ListGroupItem([
                                    html.Strong(f"{symbol}: "),
                                    f"Predicted spread in 30s: ",
                                    html.Span(
                                        f"{pred:.2f}%",
                                        className="text-dark" if pred > 0.5 else "text-danger"
                                    )
                                ])
                            )

                if not predictions:
                    return html.P("⏳ No predictions available yet...", className="text-muted")

                return dbc.ListGroup(predictions)
            except Exception as e:
                logger.error(f"Error updating ML predictions: {e}")
                return html.P(f"❌ Error: {str(e)}", className="text-danger")

        @self.app.callback(
            Output("backtest-results", "children"),
            Input("interval-component", "n_intervals")
        )
        def update_backtest_results(n):
            """Run backtest on recent opportunities."""
            try:
                from arbitrage_detector import BacktestEngine

                backtest = BacktestEngine(initial_capital=10000)
                recent_opps = self.detector.get_recent_opportunities(minutes=30)

                for opp in recent_opps:
                    backtest.execute_opportunity(opp)

                results = backtest.get_results()

                if results['total_trades'] == 0:
                    return html.P("⏳ No trades to backtest yet...", className="text-muted")

                return dbc.Row([
                    dbc.Col([
                        html.P([
                            html.Strong("Total Trades: "),
                            str(results['total_trades'])
                        ]),
                        html.P([
                            html.Strong("Win Rate: "),
                            f"{results['win_rate']:.1f}%"
                        ]),
                    ]),
                    dbc.Col([
                        html.P([
                            html.Strong("Total Return: "),
                            html.Span(
                                f"${results['total_return']:.2f} ({results['total_return_pct']:.2f}%)",
                                className="text-success" if results['total_return'] > 0 else "text-danger"
                            )
                        ]),
                        html.P([
                            html.Strong("Avg Profit/Trade: "),
                            f"${results['avg_profit_per_trade']:.2f}"
                        ]),
                    ]),
                ])
            except Exception as e:
                logger.error(f"Error updating backtest: {e}")
                return html.P(f"❌ Error: {str(e)}", className="text-danger")

    def _make_normalized_chart(self, symbol: str):
        """Create normalized % change chart for one symbol."""
        try:
            fig = go.Figure()
            
            # Get latest prices
            prices = self.detector.get_latest_prices(symbol)
            history = self.normalized_history[symbol]
            
            # Only update if we have new data
            if prices:
                latest_timestamp = max(price_data.timestamp for price_data in prices.values())
                
                # Check if this is genuinely new data
                if (not self.last_update_time[symbol] or 
                    latest_timestamp > self.last_update_time[symbol]):
                    
                    for ex, price_data in prices.items():
                        history.append({
                            't': price_data.timestamp, 
                            'p': price_data.price, 
                            'ex': ex
                        })
                    
                    self.last_update_time[symbol] = latest_timestamp

            # Need at least 2 data points to show percentage change
            if len(history) < 2:
                fig.add_annotation(
                    text="⏳ Waiting for data...", 
                    x=0.5, y=0.5, 
                    showarrow=False, 
                    xref="paper", yref="paper",
                    font=dict(size=16, color="gray")
                )
                fig.update_layout(template="plotly_dark", height=280)
                return fig

            # Convert to DataFrame
            df = pd.DataFrame(list(history))
            
            # Calculate percentage change from first price
            first_price = df['p'].iloc[0]
            colors = {'Coinbase': '#0052FF', 'Binance': '#F3BA2F', 'Bitstamp': '#00D43A'}

            for ex in df['ex'].unique():
                ex_df = df[df['ex'] == ex].copy()
                ex_df['pct'] = (ex_df['p'] / first_price - 1) * 100
                
                fig.add_trace(go.Scatter(
                    x=ex_df['t'], 
                    y=ex_df['pct'], 
                    mode='lines', 
                    name=ex,
                    line=dict(color=colors.get(ex, '#FFFFFF'), width=2),
                    hovertemplate=(
                        f"<b>{ex}</b><br>"
                        "Δ: %{y:.3f}%<br>"
                        "Price: $%{customdata[0]:.2f}"
                        "<extra></extra>"
                    ),
                    customdata=ex_df[['p']]
                ))

            fig.update_layout(
                template="plotly_dark",
                height=280,
                margin=dict(t=40, b=20, l=40, r=20),
                yaxis=dict(range=[-1.5, 1.5], title="Δ%", zeroline=True, zerolinewidth=2, zerolinecolor='gray'),
                xaxis_title=None,
                hovermode='x unified',
                showlegend=True,
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="right",
                    x=1
                )
            )
            return fig
            
        except Exception as e:
            logger.error(f"Error creating normalized chart for {symbol}: {e}")
            fig = go.Figure()
            fig.add_annotation(
                text=f"Error: {str(e)}", 
                x=0.5, y=0.5, 
                showarrow=False, 
                xref="paper", yref="paper"
            )
            fig.update_layout(template="plotly_dark", height=280)
            return fig

    def run(self, host='0.0.0.0', port=8050, debug=False):
        """Start the dashboard server."""
        logger.info(f"Starting dashboard on http://{host}:{port}")
        self.app.run(host=host, port=port, debug=debug)