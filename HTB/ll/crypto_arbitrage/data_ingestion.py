"""WebSocket clients for multiple crypto exchanges."""
import json
import asyncio
import websockets
from datetime import datetime, timezone
from typing import Callable, Optional
from loguru import logger
from config import PriceData, Exchange, EXCHANGE_CONFIGS, SYMBOL_MAPPINGS


class BaseExchangeClient:
    """Base class for exchange WebSocket clients."""

    def __init__(self, exchange: Exchange, callback: Callable[[PriceData], None]):
        self.exchange = exchange
        self.config = EXCHANGE_CONFIGS[exchange]
        self.callback = callback
        self.websocket: Optional[websockets.WebSocketClientProtocol] = None
        self.running = False

    async def connect(self):
        """Connect to exchange WebSocket."""
        try:
            self.websocket = await websockets.connect(self.config.websocket_url)
            logger.info(f"Connected to {self.config.name}")
            self.running = True
        except Exception as e:
            logger.error(f"Failed to connect to {self.config.name}: {e}")
            raise

    async def disconnect(self):
        """Disconnect from exchange."""
        self.running = False
        if self.websocket:
            await self.websocket.close()
            logger.info(f"Disconnected from {self.config.name}")

    def normalize_symbol(self, symbol: str) -> str:
        """Convert exchange-specific symbol to standard format."""
        return SYMBOL_MAPPINGS.get(symbol, symbol)
    
    async def subscribe(self):
        """Subscribe to relevant channels (implement in subclass)."""
        raise NotImplementedError

    async def handle_message(self, message: dict):
        """Parse message and create PriceData (implement in subclass)."""
        raise NotImplementedError

    async def run(self):
        """Main message loop with auto-reconnect."""
        retry_count = 0
        max_retries = 5

        while retry_count < max_retries:
            try:
                await self.connect()
                await self.subscribe()

                async for message in self.websocket:
                    try:
                        data = json.loads(message)
                        await self.handle_message(data)
                    except json.JSONDecodeError as e:
                        logger.warning(f"Invalid JSON from {self.config.name}: {e}")
                    except Exception as e:
                        logger.error(f"Error handling message from {self.config.name}: {e}")

            except websockets.exceptions.ConnectionClosed:
                logger.warning(f"Connection to {self.config.name} closed, reconnecting...")
                retry_count += 1
                await asyncio.sleep(2 ** retry_count)  # Exponential backoff
            except Exception as e:
                logger.error(f"Error in {self.config.name} client: {e}")
                retry_count += 1
                await asyncio.sleep(2 ** retry_count)

        logger.error(f"Max retries reached for {self.config.name}")


class CoinbaseClient(BaseExchangeClient):
    """Coinbase WebSocket client."""

    def __init__(self, callback: Callable[[PriceData], None]):
        super().__init__(Exchange.COINBASE, callback)

    async def subscribe(self):
        """Subscribe to ticker channel."""
        subscribe_message = {
            "type": "subscribe",
            "product_ids": self.config.symbols,
            "channels": ["ticker"]
        }
        await self.websocket.send(json.dumps(subscribe_message))
        logger.info(f"Subscribed to Coinbase symbols: {self.config.symbols}")

    async def handle_message(self, message: dict):
        """Parse Coinbase ticker message."""
        if message.get("type") != "ticker":
            return

        try:
            price_data = PriceData(
                exchange=self.config.name,
                symbol=self.normalize_symbol(message["product_id"]),
                price=float(message["price"]),
                volume=float(message.get("volume_24h", 0)),
                timestamp=datetime.fromisoformat(message["time"].replace("Z", "+00:00")),
                bid=float(message.get("best_bid", 0)),
                ask=float(message.get("best_ask", 0))
            )
            self.callback(price_data)
        except (KeyError, ValueError) as e:
            logger.warning(f"Failed to parse Coinbase message: {e}")


class BinanceClient(BaseExchangeClient):
    """Binance WebSocket client."""

    def __init__(self, callback: Callable[[PriceData], None]):
        super().__init__(Exchange.BINANCE, callback)

    async def connect(self):
        """Connect to Binance with stream-specific URL."""
        # Binance uses stream names in URL
        streams = [f"{s.lower()}@ticker" for s in self.config.symbols]
        stream_url = f"{self.config.websocket_url}/{'/'.join(streams)}"

        try:
            self.websocket = await websockets.connect(stream_url)
            logger.info(f"Connected to {self.config.name}")
            self.running = True
        except Exception as e:
            logger.error(f"Failed to connect to {self.config.name}: {e}")
            raise

    async def subscribe(self):
        """No explicit subscribe needed for Binance (done via URL)."""
        pass

    async def handle_message(self, message: dict):
        """Parse Binance ticker message."""
        if "e" not in message or message["e"] != "24hrTicker":
            return

        try:
            price_data = PriceData(
                exchange=self.config.name,
                symbol=self.normalize_symbol(message["s"]),
                price=float(message["c"]),  # Current price
                volume=float(message["v"]),  # Volume
                timestamp=datetime.fromtimestamp(message["E"] / 1000),
                bid=float(message.get("b", 0)),
                ask=float(message.get("a", 0))
            )
            self.callback(price_data)
        except (KeyError, ValueError) as e:
            logger.warning(f"Failed to parse Binance message: {e}")


class BitstampClient(BaseExchangeClient):
    """Bitstamp WebSocket client."""

    def __init__(self, callback: Callable[[PriceData], None]):
        super().__init__(Exchange.BITSTAMP, callback)

    async def subscribe(self):
        """Subscribe to live trades for each symbol."""
        for symbol in self.config.symbols:
            subscribe_message = {
                "event": "bts:subscribe",
                "data": {
                    "channel": f"live_trades_{symbol}"
                }
            }
            await self.websocket.send(json.dumps(subscribe_message))
        logger.info(f"Subscribed to Bitstamp symbols: {self.config.symbols}")

    async def handle_message(self, message: dict):
        """Parse Bitstamp trade message."""
        try:
            # Bitstamp sends: {"event": "trade", "channel": "live_trades_btcusd", "data": {...}}
            if message.get("event") == "trade":
                channel = message.get("channel", "")
                # Extract symbol from channel name (e.g., "live_trades_btcusd" -> "btcusd")
                symbol = channel.replace("live_trades_", "")

                if symbol in self.config.symbols:
                    data = message.get("data", {})
                    price_data = PriceData(
                        exchange=self.config.name,
                        symbol=self.normalize_symbol(symbol),
                        price=float(data.get("price", 0)),
                        volume=float(data.get("amount", 0)),
                        timestamp=datetime.fromtimestamp(int(data.get("timestamp", 0)), tz=timezone.utc),
                        bid=0.0,  # Bitstamp doesn't provide bid/ask in trade stream
                        ask=0.0
                    )
                    self.callback(price_data)
        except (KeyError, ValueError, TypeError) as e:
            logger.warning(f"Failed to parse Bitstamp message: {e}")


class MultiExchangeAggregator:
    """Aggregates data from multiple exchanges."""

    def __init__(self, callback: Callable[[PriceData], None]):
        self.callback = callback
        self.clients = [
            CoinbaseClient(self.on_price_update),
            BinanceClient(self.on_price_update),
            BitstampClient(self.on_price_update)
        ]
        self.latest_prices = {}  # {(exchange, symbol): PriceData}

    def on_price_update(self, price_data: PriceData):
        """Handle price updates from any exchange."""
        key = (price_data.exchange, price_data.symbol)
        self.latest_prices[key] = price_data
        self.callback(price_data)

    async def start(self):
        """Start all exchange clients concurrently."""
        logger.info("Starting multi-exchange aggregator...")
        tasks = [client.run() for client in self.clients]
        await asyncio.gather(*tasks, return_exceptions=True)

    async def stop(self):
        """Stop all exchange clients."""
        logger.info("Stopping multi-exchange aggregator...")
        for client in self.clients:
            await client.disconnect()

    def get_latest_prices(self, symbol: str) -> dict:
        """Get latest prices for a symbol across all exchanges."""
        return {
            exchange: price_data
            for (exchange, sym), price_data in self.latest_prices.items()
            if sym == symbol
        }
