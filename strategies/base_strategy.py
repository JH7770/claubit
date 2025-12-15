"""
Base Strategy Class
Abstract base class that all trading strategies must inherit from.
"""

from abc import ABC, abstractmethod
import pandas as pd
from typing import Dict, Optional, Tuple, List
from datetime import datetime


class BaseStrategy(ABC):
    """
    Abstract base class for all trading strategies.

    All strategies must implement:
    - generate_signals(): Generate buy/sell signals
    - calculate_position_size(): Determine position sizing
    """

    def __init__(self, name: str, params: Optional[Dict] = None):
        """
        Initialize the strategy.

        Args:
            name: Strategy name
            params: Strategy parameters dictionary
        """
        self.name = name
        self.params = params or {}
        self.signals = None
        self.positions = None

    @abstractmethod
    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Generate trading signals based on market data.

        Args:
            df: DataFrame with OHLCV data and indicators

        Returns:
            DataFrame with added 'signal' column where:
            - 1 = Buy/Long signal
            - -1 = Sell/Short signal
            - 0 = No signal/Hold
        """
        pass

    @abstractmethod
    def calculate_position_size(
        self,
        signal: int,
        current_price: float,
        account_balance: float,
        risk_percent: float = 1.0
    ) -> float:
        """
        Calculate position size based on risk management rules.

        Args:
            signal: Trading signal (1 or -1)
            current_price: Current asset price
            account_balance: Available account balance
            risk_percent: Percentage of account to risk per trade

        Returns:
            Position size in base currency
        """
        pass

    def add_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Add technical indicators to the dataframe.
        Override this method in child classes to add strategy-specific indicators.

        Args:
            df: DataFrame with OHLCV data

        Returns:
            DataFrame with added indicators
        """
        return df

    def validate_signal(
        self,
        signal: int,
        current_position: Optional[Dict] = None,
        market_data: Optional[pd.DataFrame] = None
    ) -> bool:
        """
        Validate if a signal should be executed.
        Override to add custom validation logic.

        Args:
            signal: Trading signal
            current_position: Current open position info
            market_data: Recent market data

        Returns:
            True if signal is valid, False otherwise
        """
        # Default validation: don't open new position if one exists
        if current_position and signal != 0:
            return False

        return signal != 0

    def get_stop_loss_price(
        self,
        entry_price: float,
        side: str,
        atr: Optional[float] = None
    ) -> float:
        """
        Calculate stop loss price.
        Override to implement custom stop loss logic.

        Args:
            entry_price: Entry price
            side: 'long' or 'short'
            atr: Average True Range (optional)

        Returns:
            Stop loss price
        """
        # Default: 2% stop loss
        stop_loss_percent = self.params.get('stop_loss_percent', 2.0)

        if side.lower() == 'long':
            return entry_price * (1 - stop_loss_percent / 100)
        else:  # short
            return entry_price * (1 + stop_loss_percent / 100)

    def get_take_profit_price(
        self,
        entry_price: float,
        side: str,
        atr: Optional[float] = None
    ) -> float:
        """
        Calculate take profit price.
        Override to implement custom take profit logic.

        Args:
            entry_price: Entry price
            side: 'long' or 'short'
            atr: Average True Range (optional)

        Returns:
            Take profit price
        """
        # Default: 4% take profit (2:1 risk-reward ratio)
        take_profit_percent = self.params.get('take_profit_percent', 4.0)

        if side.lower() == 'long':
            return entry_price * (1 + take_profit_percent / 100)
        else:  # short
            return entry_price * (1 - take_profit_percent / 100)

    def should_exit(
        self,
        position: Dict,
        current_price: float,
        market_data: pd.DataFrame
    ) -> Tuple[bool, str]:
        """
        Determine if an open position should be exited.
        Override to implement custom exit logic.

        Args:
            position: Current position information
            current_price: Current market price
            market_data: Recent market data

        Returns:
            Tuple of (should_exit: bool, reason: str)
        """
        # Default: No early exit, rely on SL/TP
        return False, ""

    def get_params_dict(self) -> Dict:
        """Get strategy parameters as dictionary."""
        return {
            'name': self.name,
            'params': self.params
        }

    def set_params(self, params: Dict):
        """Update strategy parameters."""
        self.params.update(params)

    def get_name(self) -> str:
        """Get strategy name."""
        return self.name

    def __str__(self):
        """String representation of the strategy."""
        return f"{self.name}(params={self.params})"

    def __repr__(self):
        """Repr of the strategy."""
        return self.__str__()


class SimpleMovingAverageCrossStrategy(BaseStrategy):
    """
    Example implementation: Simple Moving Average Crossover Strategy.
    This serves as a reference for implementing custom strategies.
    """

    def __init__(self, params: Optional[Dict] = None):
        """
        Initialize SMA Cross strategy.

        Default params:
            - fast_period: Fast SMA period (default: 10)
            - slow_period: Slow SMA period (default: 20)
        """
        default_params = {
            'fast_period': 10,
            'slow_period': 20,
            'stop_loss_percent': 2.0,
            'take_profit_percent': 4.0
        }

        if params:
            default_params.update(params)

        super().__init__(name="SMA_Cross", params=default_params)

    def add_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add SMA indicators."""
        df = df.copy()

        fast_period = self.params['fast_period']
        slow_period = self.params['slow_period']

        df['sma_fast'] = df['close'].rolling(window=fast_period).mean()
        df['sma_slow'] = df['close'].rolling(window=slow_period).mean()

        return df

    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Generate signals based on SMA crossover.

        Buy when fast SMA crosses above slow SMA.
        Sell when fast SMA crosses below slow SMA.
        """
        df = self.add_indicators(df)

        # Initialize signal column
        df['signal'] = 0

        # Buy signal: fast crosses above slow
        df.loc[
            (df['sma_fast'] > df['sma_slow']) &
            (df['sma_fast'].shift(1) <= df['sma_slow'].shift(1)),
            'signal'
        ] = 1

        # Sell signal: fast crosses below slow
        df.loc[
            (df['sma_fast'] < df['sma_slow']) &
            (df['sma_fast'].shift(1) >= df['sma_slow'].shift(1)),
            'signal'
        ] = -1

        return df

    def calculate_position_size(
        self,
        signal: int,
        current_price: float,
        account_balance: float,
        risk_percent: float = 1.0
    ) -> float:
        """
        Calculate position size based on risk percentage.

        Args:
            signal: Trading signal
            current_price: Current price
            account_balance: Available balance
            risk_percent: Risk per trade as percentage

        Returns:
            Position size in base currency
        """
        if signal == 0:
            return 0.0

        # Calculate position size based on risk
        risk_amount = account_balance * (risk_percent / 100)

        # Assuming 2% stop loss
        stop_loss_percent = self.params.get('stop_loss_percent', 2.0)
        position_value = risk_amount / (stop_loss_percent / 100)

        # Convert to base currency amount
        position_size = position_value / current_price

        return position_size


if __name__ == "__main__":
    # Test the strategy
    print("Testing BaseStrategy with SMA Cross example...")

    # Create sample data
    import numpy as np

    dates = pd.date_range(start='2024-01-01', periods=100, freq='1H')
    data = {
        'timestamp': dates,
        'open': np.random.randn(100).cumsum() + 100,
        'high': np.random.randn(100).cumsum() + 101,
        'low': np.random.randn(100).cumsum() + 99,
        'close': np.random.randn(100).cumsum() + 100,
        'volume': np.random.randint(1000, 10000, 100)
    }
    df = pd.DataFrame(data)

    # Initialize strategy
    strategy = SimpleMovingAverageCrossStrategy()
    print(f"\nStrategy: {strategy}")
    print(f"Parameters: {strategy.get_params_dict()}")

    # Generate signals
    df_with_signals = strategy.generate_signals(df)
    print(f"\nGenerated {len(df_with_signals)} rows of data")
    print(f"Buy signals: {(df_with_signals['signal'] == 1).sum()}")
    print(f"Sell signals: {(df_with_signals['signal'] == -1).sum()}")

    # Test position sizing
    position_size = strategy.calculate_position_size(
        signal=1,
        current_price=50000,
        account_balance=10000,
        risk_percent=1.0
    )
    print(f"\nPosition size for $10,000 balance: {position_size:.6f}")

    # Test SL/TP calculation
    entry_price = 50000
    sl = strategy.get_stop_loss_price(entry_price, 'long')
    tp = strategy.get_take_profit_price(entry_price, 'long')
    print(f"\nFor entry at ${entry_price}:")
    print(f"Stop Loss: ${sl:.2f}")
    print(f"Take Profit: ${tp:.2f}")
