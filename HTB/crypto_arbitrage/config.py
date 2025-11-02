"""Configuration and data models for crypto arbitrage system."""
from dataclasses import dataclass, field
from typing import Dict, List
from datetime import datetime, timezone
from enum import Enum


class Exchange(Enum):
    """Supported exchanges."""
    COINBASE = "coinbase"
    BINANCE = "binance"
    BITSTAMP = "bitstamp"


@dataclass
class PriceData:
    """Normalized price data from any exchange."""
    exchange: str
    symbol: str  # Normalized: BTC-USD
    price: float
    volume: float
    timestamp: datetime
    bid: float = 0.0
    ask: float = 0.0

    def __post_init__(self):
        """Ensure timestamp is datetime object with timezone."""
        if isinstance(self.timestamp, (int, float)):
            self.timestamp = datetime.fromtimestamp(self.timestamp / 1000, tz=timezone.utc)
        elif isinstance(self.timestamp, datetime) and self.timestamp.tzinfo is None:
            # Make naive datetime timezone-aware
            self.timestamp = self.timestamp.replace(tzinfo=timezone.utc)


@dataclass
class ArbitrageOpportunity:
    """Detected arbitrage opportunity."""
    buy_exchange: str
    sell_exchange: str
    symbol: str
    buy_price: float
    sell_price: float
    spread_pct: float
    profit_after_fees: float
    timestamp: datetime
    confidence_score: float = 0.0  # ML prediction confidence

    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return {
            'buy_exchange': self.buy_exchange,
            'sell_exchange': self.sell_exchange,
            'symbol': self.symbol,
            'buy_price': self.buy_price,
            'sell_price': self.sell_price,
            'spread_pct': self.spread_pct,
            'profit_after_fees': self.profit_after_fees,
            'timestamp': self.timestamp.isoformat(),
            'confidence_score': self.confidence_score
        }


@dataclass
class ExchangeConfig:
    """Configuration for each exchange."""
    name: str
    websocket_url: str
    fee_pct: float
    symbols: List[str] = field(default_factory=list)


# Exchange configurations
EXCHANGE_CONFIGS = {
    Exchange.COINBASE: ExchangeConfig(
        name="Coinbase",
        websocket_url="wss://ws-feed.exchange.coinbase.com",
        fee_pct=0.6,  # 0.6% taker fee
        symbols=["BTC-USD", "ETH-USD", "SOL-USD"]
    ),
    Exchange.BINANCE: ExchangeConfig(
        name="Binance",
        websocket_url="wss://stream.binance.us:9443/ws",
        fee_pct=0.1,  # 0.1% taker fee
        symbols=["BTCUSDT", "ETHUSDT", "SOLUSDT"]
    ),
    Exchange.BITSTAMP: ExchangeConfig(
        name="Bitstamp",
        websocket_url="wss://ws.bitstamp.net",
        fee_pct=0.5,  # 0.5% taker fee
        symbols=["btcusd", "ethusd", "solusd"]
    )
}


# Symbol normalization mappings
SYMBOL_MAPPINGS = {
    # Binance → Standard
    "BTCUSDT": "BTC-USD",
    "ETHUSDT": "ETH-USD",
    "SOLUSDT": "SOL-USD",
    # Bitstamp → Standard
    "btcusd": "BTC-USD",
    "ethusd": "ETH-USD",
    "solusd": "SOL-USD",
    # Coinbase already uses standard format
    "BTC-USD": "BTC-USD",
    "ETH-USD": "ETH-USD",
    "SOL-USD": "SOL-USD"
}


# Trading configuration
MIN_PROFIT_THRESHOLD = -2.0  # Capture ALL spreads including unprofitable (for ML training)
MAX_SPREAD_AGE_SECONDS = 5  # Ignore old price data
DATA_BUFFER_SIZE = 10000  # Keep last N price points for ML (2 hours = ~1080 updates per symbol)
