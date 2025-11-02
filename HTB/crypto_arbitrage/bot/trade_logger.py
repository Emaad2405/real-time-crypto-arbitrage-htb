"""Trade logging and persistence."""
import csv
import json
from pathlib import Path
from typing import List, Optional
from datetime import datetime
from loguru import logger

from .base_bot import Trade


class TradeLogger:
    """Logs trades to CSV and JSON files."""

    def __init__(self, log_dir: str = "backtest_results"):
        """
        Initialize trade logger.

        Args:
            log_dir: Directory to store trade logs
        """
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)

        # Create timestamped filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.csv_path = self.log_dir / f"trades_{timestamp}.csv"
        self.json_path = self.log_dir / f"trades_{timestamp}.json"

        self.trades: List[Trade] = []

        # Initialize CSV file with headers
        self._init_csv()

    def _init_csv(self):
        """Initialize CSV file with headers."""
        with open(self.csv_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                'timestamp',
                'bot_name',
                'symbol',
                'buy_exchange',
                'sell_exchange',
                'buy_price',
                'sell_price',
                'amount',
                'spread_pct',
                'predicted_profit_pct',
                'actual_profit_pct',
                'profit_usd',
                'fees_usd',
                'slippage_usd',
                'success',
                'execution_time_ms'
            ])

    def log_trade(self, trade: Trade):
        """
        Log a single trade.

        Args:
            trade: Trade to log
        """
        self.trades.append(trade)

        # Append to CSV
        with open(self.csv_path, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                trade.timestamp.isoformat(),
                trade.bot_name,
                trade.symbol,
                trade.buy_exchange,
                trade.sell_exchange,
                trade.buy_price,
                trade.sell_price,
                trade.amount,
                trade.spread_pct,
                trade.predicted_profit_pct,
                trade.actual_profit_pct,
                trade.profit_usd,
                trade.fees_usd,
                trade.slippage_usd,
                trade.success,
                trade.execution_time_ms
            ])

    def log_trades(self, trades: List[Trade]):
        """
        Log multiple trades.

        Args:
            trades: List of trades to log
        """
        for trade in trades:
            self.log_trade(trade)

    def save_summary(self, bot_metrics: dict):
        """
        Save summary metrics to JSON.

        Args:
            bot_metrics: Dictionary of bot performance metrics
        """
        # Convert all values to JSON-serializable types
        def make_serializable(obj):
            """Convert numpy/pandas types to Python native types."""
            import numpy as np
            if isinstance(obj, dict):
                return {k: make_serializable(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [make_serializable(item) for item in obj]
            elif isinstance(obj, (np.integer, np.floating)):
                return obj.item() if hasattr(obj, 'item') else float(obj)
            elif isinstance(obj, np.ndarray):
                return obj.tolist()
            elif isinstance(obj, np.bool_):
                return bool(obj)
            elif isinstance(obj, bool):
                return obj  # Already good
            elif isinstance(obj, (int, float, str)):
                return obj
            else:
                try:
                    # Fallback: try to convert via str (for datetime, etc.)
                    return str(obj)
                except:
                    return repr(obj)

        # Apply to bot_metrics
        clean_bot_metrics = make_serializable(bot_metrics)

        # Apply to each trade's dict
        clean_trades = [
            make_serializable(trade.to_dict())
            for trade in self.trades[:1000]
        ]

        summary = {
            'timestamp': datetime.now().isoformat(),
            'total_trades': len(self.trades),
            'bot_metrics': clean_bot_metrics,
            'trades': clean_trades
        }

        with open(self.json_path, 'w') as f:
            json.dump(summary, f, indent=2)

        logger.info(f"Trade summary saved to {self.json_path}")

    @staticmethod
    def load_trades_from_csv(csv_path: str) -> List[Trade]:
        """
        Load trades from a CSV file.

        Args:
            csv_path: Path to CSV file

        Returns:
            List of Trade objects
        """
        trades = []

        try:
            with open(csv_path, 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    trade = Trade(
                        timestamp=datetime.fromisoformat(row['timestamp']),
                        bot_name=row['bot_name'],
                        symbol=row['symbol'],
                        buy_exchange=row['buy_exchange'],
                        sell_exchange=row['sell_exchange'],
                        buy_price=float(row['buy_price']),
                        sell_price=float(row['sell_price']),
                        amount=float(row['amount']),
                        spread_pct=float(row['spread_pct']),
                        predicted_profit_pct=float(row['predicted_profit_pct']),
                        actual_profit_pct=float(row['actual_profit_pct']),
                        profit_usd=float(row['profit_usd']),
                        fees_usd=float(row['fees_usd']),
                        slippage_usd=float(row['slippage_usd']),
                        success=row['success'].lower() == 'true',
                        execution_time_ms=float(row['execution_time_ms'])
                    )
                    trades.append(trade)

            logger.info(f"Loaded {len(trades)} trades from {csv_path}")
            return trades

        except Exception as e:
            logger.error(f"Error loading trades from CSV: {e}")
            return []

    @staticmethod
    def load_summary_from_json(json_path: str) -> Optional[dict]:
        """
        Load trade summary from JSON file.

        Args:
            json_path: Path to JSON file

        Returns:
            Summary dictionary or None
        """
        try:
            with open(json_path, 'r') as f:
                summary = json.load(f)
            logger.info(f"Loaded summary from {json_path}")
            return summary
        except Exception as e:
            logger.error(f"Error loading summary from JSON: {e}")
            return None
