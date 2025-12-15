"""
Data Collector Module
Handles downloading and updating OHLCV data from exchanges using CCXT.
"""

import ccxt
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path
import time
from typing import Optional, List
import pytz


class DataCollector:
    """Collects OHLCV data from cryptocurrency exchanges."""

    def __init__(self, exchange_name: str = 'binance', api_key: str = '', api_secret: str = ''):
        """
        Initialize the data collector.

        Args:
            exchange_name: Name of the exchange (default: binance)
            api_key: API key for the exchange
            api_secret: API secret for the exchange
        """
        self.exchange_name = exchange_name
        self.exchange = self._initialize_exchange(exchange_name, api_key, api_secret)
        self.data_dir = Path('data')
        self.data_dir.mkdir(exist_ok=True)

    def _initialize_exchange(self, exchange_name: str, api_key: str, api_secret: str):
        """Initialize CCXT exchange instance."""
        exchange_class = getattr(ccxt, exchange_name)
        exchange = exchange_class({
            'apiKey': api_key,
            'secret': api_secret,
            'enableRateLimit': True,
            'options': {
                'defaultType': 'future',  # Use futures market
            }
        })
        return exchange

    def fetch_ohlcv(
        self,
        symbol: str,
        timeframe: str = '1m',
        since: Optional[datetime] = None,
        limit: int = 1000
    ) -> pd.DataFrame:
        """
        Fetch OHLCV data from the exchange.

        Args:
            symbol: Trading pair symbol (e.g., 'BTC/USDT')
            timeframe: Candle timeframe (e.g., '1m', '5m', '1h')
            since: Start datetime for fetching data
            limit: Maximum number of candles to fetch

        Returns:
            DataFrame with OHLCV data
        """
        try:
            if since:
                since_ms = int(since.timestamp() * 1000)
            else:
                since_ms = None

            ohlcv = self.exchange.fetch_ohlcv(symbol, timeframe, since_ms, limit)

            df = pd.DataFrame(
                ohlcv,
                columns=['timestamp', 'open', 'high', 'low', 'close', 'volume']
            )

            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.set_index('timestamp', inplace=True)

            return df

        except Exception as e:
            print(f"Error fetching OHLCV data: {e}")
            raise

    def download_historical_data(
        self,
        symbol: str,
        timeframe: str = '1m',
        days: int = 30,
        save_to_file: bool = True
    ) -> pd.DataFrame:
        """
        Download historical OHLCV data for a specified period.

        Args:
            symbol: Trading pair symbol
            timeframe: Candle timeframe
            days: Number of days to download
            save_to_file: Whether to save data to parquet file

        Returns:
            DataFrame with historical OHLCV data
        """
        print(f"Downloading {days} days of {timeframe} data for {symbol}...")

        end_time = datetime.now(pytz.UTC)
        start_time = end_time - timedelta(days=days)

        all_data = []
        current_time = start_time

        # Calculate approximate number of candles per request
        timeframe_minutes = self._timeframe_to_minutes(timeframe)
        candles_per_request = 1000

        while current_time < end_time:
            try:
                df = self.fetch_ohlcv(symbol, timeframe, current_time, candles_per_request)

                if df.empty:
                    break

                all_data.append(df)

                # Update current_time to the last candle timestamp
                current_time = df.index[-1] + timedelta(minutes=timeframe_minutes)

                # Rate limiting
                time.sleep(self.exchange.rateLimit / 1000)

                print(f"Downloaded up to {df.index[-1]}")

            except Exception as e:
                print(f"Error during download: {e}")
                time.sleep(5)
                continue

        if not all_data:
            print("No data downloaded")
            return pd.DataFrame()

        # Combine all data
        combined_df = pd.concat(all_data)
        combined_df = combined_df[~combined_df.index.duplicated(keep='last')]
        combined_df.sort_index(inplace=True)

        print(f"Downloaded {len(combined_df)} candles from {combined_df.index[0]} to {combined_df.index[-1]}")

        # Save to file
        if save_to_file:
            filename = self._generate_filename(symbol, timeframe)
            filepath = self.data_dir / filename
            combined_df.to_parquet(filepath)
            print(f"Saved to {filepath}")

        return combined_df

    def update_data(self, symbol: str, timeframe: str = '1m') -> pd.DataFrame:
        """
        Update existing data file with latest candles.

        Args:
            symbol: Trading pair symbol
            timeframe: Candle timeframe

        Returns:
            Updated DataFrame
        """
        filename = self._generate_filename(symbol, timeframe)
        filepath = self.data_dir / filename

        if filepath.exists():
            # Load existing data
            df_existing = pd.read_parquet(filepath)
            last_timestamp = df_existing.index[-1]

            print(f"Updating data from {last_timestamp}...")

            # Fetch new data
            df_new = self.fetch_ohlcv(
                symbol,
                timeframe,
                since=last_timestamp.to_pydatetime(),
                limit=1000
            )

            if not df_new.empty:
                # Combine and remove duplicates
                df_combined = pd.concat([df_existing, df_new])
                df_combined = df_combined[~df_combined.index.duplicated(keep='last')]
                df_combined.sort_index(inplace=True)

                # Save updated data
                df_combined.to_parquet(filepath)
                print(f"Updated {len(df_new)} new candles")

                return df_combined
            else:
                print("No new data available")
                return df_existing
        else:
            print(f"No existing data found. Downloading historical data...")
            return self.download_historical_data(symbol, timeframe, days=30)

    def load_data(self, symbol: str, timeframe: str = '1m') -> Optional[pd.DataFrame]:
        """
        Load data from file.

        Args:
            symbol: Trading pair symbol
            timeframe: Candle timeframe

        Returns:
            DataFrame with OHLCV data or None if file doesn't exist
        """
        filename = self._generate_filename(symbol, timeframe)
        filepath = self.data_dir / filename

        if filepath.exists():
            return pd.read_parquet(filepath)
        else:
            print(f"Data file not found: {filepath}")
            return None

    def get_latest_price(self, symbol: str) -> float:
        """
        Get the latest price for a symbol.

        Args:
            symbol: Trading pair symbol

        Returns:
            Latest price
        """
        ticker = self.exchange.fetch_ticker(symbol)
        return ticker['last']

    def get_orderbook(self, symbol: str, limit: int = 20) -> dict:
        """
        Get current orderbook (bid/ask).

        Args:
            symbol: Trading pair symbol
            limit: Depth of orderbook

        Returns:
            Orderbook data
        """
        return self.exchange.fetch_order_book(symbol, limit)

    @staticmethod
    def _timeframe_to_minutes(timeframe: str) -> int:
        """Convert timeframe string to minutes."""
        multipliers = {
            'm': 1,
            'h': 60,
            'd': 1440,
            'w': 10080
        }
        value = int(timeframe[:-1])
        unit = timeframe[-1]
        return value * multipliers.get(unit, 1)

    @staticmethod
    def _generate_filename(symbol: str, timeframe: str) -> str:
        """Generate filename for data storage."""
        symbol_clean = symbol.replace('/', '_')
        return f"{symbol_clean}_{timeframe}.parquet"


if __name__ == "__main__":
    # Test the collector
    collector = DataCollector('binance')

    # Download sample data
    df = collector.download_historical_data('BTC/USDT', timeframe='1m', days=1)
    print(df.head())
    print(f"\nTotal candles: {len(df)}")

    # Test latest price
    price = collector.get_latest_price('BTC/USDT')
    print(f"\nLatest BTC/USDT price: ${price:,.2f}")
