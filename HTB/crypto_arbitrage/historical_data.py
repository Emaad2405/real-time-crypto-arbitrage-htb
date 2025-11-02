"""Historical data fetching and training for ML models."""
import os
import json
import requests
import pandas as pd
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Tuple
from pathlib import Path
from loguru import logger
import time

from config import Exchange, EXCHANGE_CONFIGS, SYMBOL_MAPPINGS


class HistoricalDataFetcher:
    """Fetch historical OHLCV data from multiple exchanges."""

    def __init__(self, data_dir: str = "historical_data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)

    def fetch_coinbase_history(self, symbol: str, days: int = 30) -> pd.DataFrame:
        """Fetch historical data from Coinbase Pro."""
        # Coinbase uses product_id format: BTC-USD
        product_id = symbol if "-" in symbol else SYMBOL_MAPPINGS.get(symbol, symbol)

        end_time = datetime.now(timezone.utc)
        start_time = end_time - timedelta(days=days)

        # Coinbase API: 300 candles per request, 1 minute granularity
        # For 30 days = 43,200 minutes, need multiple requests
        granularity = 60  # 1 minute

        all_data = []
        current_start = start_time

        logger.info(f"Fetching Coinbase {product_id} history for {days} days...")

        while current_start < end_time:
            current_end = min(current_start + timedelta(minutes=300), end_time)

            url = f"https://api.exchange.coinbase.com/products/{product_id}/candles"
            params = {
                'start': current_start.isoformat(),
                'end': current_end.isoformat(),
                'granularity': granularity
            }

            try:
                response = requests.get(url, params=params, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    if data:
                        all_data.extend(data)
                        logger.debug(f"Fetched {len(data)} candles from Coinbase")
                else:
                    logger.warning(f"Coinbase API returned {response.status_code}")

                time.sleep(0.5)  # Rate limiting

            except Exception as e:
                logger.error(f"Error fetching Coinbase data: {e}")

            current_start = current_end

        if not all_data:
            logger.warning(f"No data fetched for {product_id}")
            return pd.DataFrame()

        # Convert to DataFrame
        # Format: [timestamp, low, high, open, close, volume]
        df = pd.DataFrame(all_data, columns=['timestamp', 'low', 'high', 'open', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s', utc=True)
        df['exchange'] = 'Coinbase'
        df['symbol'] = SYMBOL_MAPPINGS.get(product_id, product_id)

        logger.success(f"Fetched {len(df)} candles from Coinbase for {product_id}")
        return df

    def fetch_binance_history(self, symbol: str, days: int = 30) -> pd.DataFrame:
        """Fetch historical data from Binance US."""
        # Binance uses symbol format: BTCUSDT
        binance_symbol = symbol.replace("-", "").upper()
        if not binance_symbol.endswith("USDT"):
            if binance_symbol.endswith("USD"):
                binance_symbol = binance_symbol[:-3] + "USDT"

        # Map to Binance format
        symbol_map = {"BTCUSD": "BTCUSDT", "ETHUSD": "ETHUSDT", "SOLUSD": "SOLUSDT"}
        binance_symbol = symbol_map.get(binance_symbol, binance_symbol)

        end_time = datetime.now(timezone.utc)
        start_time = end_time - timedelta(days=days)

        # Binance API: 1000 candles per request, 1 minute interval
        interval = "1m"

        all_data = []
        current_start = start_time

        logger.info(f"Fetching Binance {binance_symbol} history for {days} days...")

        while current_start < end_time:
            current_end = min(current_start + timedelta(minutes=1000), end_time)

            url = "https://api.binance.us/api/v3/klines"
            params = {
                'symbol': binance_symbol,
                'interval': interval,
                'startTime': int(current_start.timestamp() * 1000),
                'endTime': int(current_end.timestamp() * 1000),
                'limit': 1000
            }

            try:
                response = requests.get(url, params=params, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    if data:
                        all_data.extend(data)
                        logger.debug(f"Fetched {len(data)} candles from Binance")
                else:
                    logger.warning(f"Binance API returned {response.status_code}")

                time.sleep(0.5)  # Rate limiting

            except Exception as e:
                logger.error(f"Error fetching Binance data: {e}")

            current_start = current_end

        if not all_data:
            logger.warning(f"No data fetched for {binance_symbol}")
            return pd.DataFrame()

        # Convert to DataFrame
        # Format: [timestamp, open, high, low, close, volume, close_time, ...]
        df = pd.DataFrame(all_data, columns=[
            'timestamp', 'open', 'high', 'low', 'close', 'volume',
            'close_time', 'quote_volume', 'trades', 'taker_base', 'taker_quote', 'ignore'
        ])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms', utc=True)
        df = df[['timestamp', 'open', 'high', 'low', 'close', 'volume']]
        df['exchange'] = 'Binance'

        # Map back to standard symbol
        standard_symbol = symbol.upper() if "-" in symbol else f"{symbol[:3]}-USD"
        df['symbol'] = SYMBOL_MAPPINGS.get(binance_symbol, standard_symbol)

        logger.success(f"Fetched {len(df)} candles from Binance for {binance_symbol}")
        return df

    def fetch_bitstamp_history(self, symbol: str, days: int = 30) -> pd.DataFrame:
        """Fetch historical data from Bitstamp."""
        # Bitstamp uses lowercase: btcusd
        bitstamp_symbol = symbol.lower().replace("-", "")

        end_time = datetime.now(timezone.utc)
        start_time = end_time - timedelta(days=days)

        # Bitstamp API: OHLC data, 1000 candles max, 60 second step
        step = 60  # 1 minute
        limit = 1000

        all_data = []
        current_start = start_time

        logger.info(f"Fetching Bitstamp {bitstamp_symbol} history for {days} days...")

        while current_start < end_time:
            url = f"https://www.bitstamp.net/api/v2/ohlc/{bitstamp_symbol}/"
            params = {
                'step': step,
                'limit': limit,
                'start': int(current_start.timestamp())
            }

            try:
                response = requests.get(url, params=params, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    if data and 'data' in data and 'ohlc' in data['data']:
                        candles = data['data']['ohlc']
                        if candles:
                            all_data.extend(candles)
                            logger.debug(f"Fetched {len(candles)} candles from Bitstamp")

                            # Move to next batch
                            last_timestamp = int(candles[-1]['timestamp'])
                            current_start = datetime.fromtimestamp(last_timestamp, tz=timezone.utc)
                        else:
                            break
                else:
                    logger.warning(f"Bitstamp API returned {response.status_code}")
                    break

                time.sleep(0.5)  # Rate limiting

            except Exception as e:
                logger.error(f"Error fetching Bitstamp data: {e}")
                break

            # Prevent infinite loops
            if len(all_data) > days * 1440:  # More than expected
                break

        if not all_data:
            logger.warning(f"No data fetched for {bitstamp_symbol}")
            return pd.DataFrame()

        # Convert to DataFrame
        df = pd.DataFrame(all_data)
        df['timestamp'] = pd.to_datetime(df['timestamp'].astype(int), unit='s', utc=True)
        df = df.rename(columns={'timestamp': 'timestamp'})
        df = df[['timestamp', 'open', 'high', 'low', 'close', 'volume']]
        df['exchange'] = 'Bitstamp'

        # Map to standard symbol
        standard_symbol = SYMBOL_MAPPINGS.get(bitstamp_symbol, f"{symbol[:3].upper()}-USD")
        df['symbol'] = standard_symbol

        logger.success(f"Fetched {len(df)} candles from Bitstamp for {bitstamp_symbol}")
        return df

    def fetch_all_exchanges(self, symbol: str, days: int = 30) -> Dict[str, pd.DataFrame]:
        """Fetch historical data from all exchanges for a symbol."""
        data = {}

        # Fetch from each exchange
        df_coinbase = self.fetch_coinbase_history(symbol, days)
        if not df_coinbase.empty:
            data['Coinbase'] = df_coinbase

        df_binance = self.fetch_binance_history(symbol, days)
        if not df_binance.empty:
            data['Binance'] = df_binance

        df_bitstamp = self.fetch_bitstamp_history(symbol, days)
        if not df_bitstamp.empty:
            data['Bitstamp'] = df_bitstamp

        return data

    def save_data(self, symbol: str, exchange_data: Dict[str, pd.DataFrame]):
        """Save historical data to disk."""
        symbol_clean = symbol.replace("-", "_").lower()

        for exchange, df in exchange_data.items():
            filename = self.data_dir / f"{exchange.lower()}_{symbol_clean}_history.csv"
            df.to_csv(filename, index=False)
            logger.info(f"Saved {len(df)} records to {filename}")

    def load_data(self, symbol: str) -> Dict[str, pd.DataFrame]:
        """Load historical data from disk."""
        symbol_clean = symbol.replace("-", "_").lower()
        data = {}

        for exchange in ['Coinbase', 'Binance', 'Bitstamp']:
            filename = self.data_dir / f"{exchange.lower()}_{symbol_clean}_history.csv"
            if filename.exists():
                df = pd.read_csv(filename)
                df['timestamp'] = pd.to_datetime(df['timestamp'], utc=True)
                data[exchange] = df
                logger.info(f"Loaded {len(df)} records from {filename}")

        return data

    def calculate_spread_features(self, exchange_data: Dict[str, pd.DataFrame]) -> pd.DataFrame:
        """Calculate spread features for ML training."""
        if len(exchange_data) < 2:
            logger.warning("Need at least 2 exchanges to calculate spreads")
            return pd.DataFrame()

        # Merge all exchange data on timestamp (nearest match)
        dfs = []
        for exchange, df in exchange_data.items():
            df_copy = df.copy()
            df_copy = df_copy.rename(columns={
                'close': f'{exchange}_price',
                'volume': f'{exchange}_volume'
            })
            df_copy = df_copy[['timestamp', f'{exchange}_price', f'{exchange}_volume']]
            dfs.append(df_copy)

        # Merge on timestamp with 1-minute tolerance
        merged = dfs[0]
        for df in dfs[1:]:
            merged = pd.merge_asof(
                merged.sort_values('timestamp'),
                df.sort_values('timestamp'),
                on='timestamp',
                direction='nearest',
                tolerance=pd.Timedelta('1min')
            )

        # Calculate spreads between all pairs
        exchanges = list(exchange_data.keys())
        for i, ex1 in enumerate(exchanges):
            for ex2 in exchanges[i+1:]:
                price1_col = f'{ex1}_price'
                price2_col = f'{ex2}_price'

                if price1_col in merged.columns and price2_col in merged.columns:
                    # Spread percentage
                    merged[f'spread_{ex1}_{ex2}'] = (
                        (merged[price2_col] - merged[price1_col]) / merged[price1_col] * 100
                    )

        # Drop rows with missing data
        merged = merged.dropna()

        logger.success(f"Calculated spread features: {len(merged)} records")
        return merged


def fetch_and_prepare_training_data(days: int = 30, symbols: List[str] = None) -> pd.DataFrame:
    """
    Fetch historical data and prepare for ML training.

    Args:
        days: Number of days of historical data (default 30)
        symbols: List of symbols to fetch (default: BTC-USD, ETH-USD, SOL-USD)

    Returns:
        DataFrame with spread features for all symbols
    """
    if symbols is None:
        symbols = ['BTC-USD', 'ETH-USD', 'SOL-USD']

    fetcher = HistoricalDataFetcher()
    all_spread_data = []

    for symbol in symbols:
        logger.info(f"\n{'='*60}")
        logger.info(f"Processing {symbol}")
        logger.info(f"{'='*60}")

        # Try to load cached data first
        exchange_data = fetcher.load_data(symbol)

        # If not cached, fetch from APIs
        if not exchange_data:
            logger.info(f"No cached data found, fetching from APIs...")
            exchange_data = fetcher.fetch_all_exchanges(symbol, days)
            if exchange_data:
                fetcher.save_data(symbol, exchange_data)

        # Calculate spread features
        if exchange_data:
            spread_df = fetcher.calculate_spread_features(exchange_data)
            if not spread_df.empty:
                spread_df['symbol'] = symbol
                all_spread_data.append(spread_df)

    if not all_spread_data:
        logger.error("No historical data fetched!")
        return pd.DataFrame()

    # Combine all symbols
    combined = pd.concat(all_spread_data, ignore_index=True)

    logger.success(f"\n{'='*60}")
    logger.success(f"TOTAL TRAINING DATA: {len(combined)} records")
    logger.success(f"Date range: {combined['timestamp'].min()} to {combined['timestamp'].max()}")
    logger.success(f"Symbols: {combined['symbol'].unique()}")
    logger.success(f"{'='*60}\n")

    return combined


if __name__ == "__main__":
    # Test fetching
    logger.info("Fetching 30 days of historical data...")
    data = fetch_and_prepare_training_data(days=30)

    if not data.empty:
        print("\n=== DATA SUMMARY ===")
        print(f"Total records: {len(data)}")
        print(f"\nColumns: {list(data.columns)}")
        print(f"\nFirst few rows:")
        print(data.head())
        print(f"\nSpread statistics:")
        spread_cols = [col for col in data.columns if col.startswith('spread_')]
        print(data[spread_cols].describe())
