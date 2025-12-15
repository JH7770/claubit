"""
ST-03: Volume Weighted Moving Average Cross Strategy

MA crossover strategy with volume confirmation to filter out
low-confidence signals and reduce whipsaws.
"""

import pandas as pd
import numpy as np
from typing import Dict, Optional
from .base_strategy import BaseStrategy


class VolumeWeightedMACrossStrategy(BaseStrategy):
    """
    Volume Weighted MA Cross Strategy (ST-03)

    This strategy combines the classic moving average crossover
    with volume confirmation. Only takes trades when crossovers
    occur with significantly elevated volume, indicating strong
    momentum and reducing false signals.

    Entry Logic:
        - Golden Cross (bullish): Fast MA crosses above Slow MA
          AND volume > average volume × multiplier
        - Death Cross (bearish): Fast MA crosses below Slow MA
          AND volume > average volume × multiplier

    Exit Logic:
        - Opposite crossover signal
        - Stop loss / Take profit

    Parameters:
        - short_window (int): Fast MA period (5-20, default: 10)
        - long_window (int): Slow MA period (20-60, default: 30)
        - vol_lookback (int): Period for average volume (default: 20)
        - vol_multiplier (float): Volume threshold multiplier (1.2-3.0)
        - stop_loss_percent (float): Stop loss percentage (default: 2.0%)
        - take_profit_percent (float): Take profit percentage (default: 4.0%)

    Optimization Ranges:
        - short_window: [5, 10, 15, 20]
        - long_window: [20, 30, 40, 60]
        - vol_multiplier: [1.2, 1.5, 2.0, 2.5, 3.0]
    """

    def __init__(self, params: Optional[Dict] = None):
        """
        Initialize Volume Weighted MA Cross Strategy.

        Args:
            params: Dictionary of strategy parameters
        """
        default_params = {
            'short_window': 10,
            'long_window': 30,
            'vol_lookback': 20,
            'vol_multiplier': 2.0,
            'stop_loss_percent': 2.0,
            'take_profit_percent': 4.0,
        }

        if params:
            default_params.update(params)

        super().__init__(name="Volume_MA_Cross", params=default_params)

    def add_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Add moving average and volume indicators.

        Calculates:
        1. Fast (short) moving average
        2. Slow (long) moving average
        3. Average volume over lookback period
        4. Volume ratio (current volume / average volume)

        Args:
            df: OHLCV DataFrame

        Returns:
            DataFrame with added indicator columns
        """
        # Ensure we have required columns
        required_cols = ['close', 'volume']
        for col in required_cols:
            if col not in df.columns:
                raise ValueError(f"Missing required column: {col}")

        # Calculate moving averages
        short_window = self.params['short_window']
        long_window = self.params['long_window']

        df['ma_short'] = df['close'].rolling(window=short_window, min_periods=1).mean()
        df['ma_long'] = df['close'].rolling(window=long_window, min_periods=1).mean()

        # Calculate volume metrics
        vol_lookback = self.params['vol_lookback']
        df['avg_volume'] = df['volume'].rolling(window=vol_lookback, min_periods=1).mean()

        # Volume ratio (current volume relative to average)
        # Avoid division by zero
        df['vol_ratio'] = df['volume'] / df['avg_volume'].replace(0, 1)

        return df

    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Generate crossover signals with volume confirmation.

        Signal Logic:
        1. Detect MA crossovers:
           - Golden Cross: Fast MA crosses above Slow MA
           - Death Cross: Fast MA crosses below Slow MA

        2. Apply volume filter:
           - Only take signals when vol_ratio > vol_multiplier

        3. Final signal = crossover AND high_volume

        Args:
            df: OHLCV DataFrame

        Returns:
            DataFrame with 'signal' column:
                1 = Long entry (golden cross with volume)
                -1 = Short entry (death cross with volume)
                0 = No position/hold
        """
        # Add indicators
        df = self.add_indicators(df)

        # Initialize signal column
        df['signal'] = 0

        # Detect crossovers
        # Golden Cross: Fast MA crosses above Slow MA
        # (current: fast > slow, previous: fast <= slow)
        golden_cross = (
            (df['ma_short'] > df['ma_long']) &
            (df['ma_short'].shift(1) <= df['ma_long'].shift(1))
        )

        # Death Cross: Fast MA crosses below Slow MA
        # (current: fast < slow, previous: fast >= slow)
        death_cross = (
            (df['ma_short'] < df['ma_long']) &
            (df['ma_short'].shift(1) >= df['ma_long'].shift(1))
        )

        # Volume filter: Only trade when volume is elevated
        vol_multiplier = self.params['vol_multiplier']
        high_volume = df['vol_ratio'] > vol_multiplier

        # Combine crossover with volume confirmation
        long_signal = golden_cross & high_volume
        short_signal = death_cross & high_volume

        # Assign signals
        df.loc[long_signal, 'signal'] = 1
        df.loc[short_signal, 'signal'] = -1

        # Shift signals by 1 to avoid look-ahead bias
        df['signal'] = df['signal'].shift(1).fillna(0)

        return df

    def calculate_position_size(
        self,
        signal: int,
        price: float,
        balance: float,
        risk_percent: float = 1.0
    ) -> float:
        """
        Calculate position size based on risk management.

        Volume-confirmed signals are generally more reliable,
        so we can use standard position sizing.

        Args:
            signal: 1 for long, -1 for short
            price: Current price
            balance: Account balance
            risk_percent: Percentage of balance to risk (default: 1.0%)

        Returns:
            Position size in base currency
        """
        if signal == 0:
            return 0.0

        # Calculate stop loss price
        stop_loss_pct = self.params['stop_loss_percent']
        if signal == 1:  # Long
            stop_loss_price = self.get_stop_loss_price(price, 'LONG', stop_loss_pct)
        else:  # Short
            stop_loss_price = self.get_stop_loss_price(price, 'SHORT', stop_loss_pct)

        # Calculate risk amount per trade
        risk_amount = balance * (risk_percent / 100)

        # Calculate price distance to stop loss
        price_diff = abs(price - stop_loss_price)
        if price_diff == 0:
            return 0.0

        # Position size = risk_amount / price_diff
        position_size = risk_amount / price_diff

        return position_size

    def should_exit(
        self,
        current_price: float,
        entry_price: float,
        position_side: str,
        bars_held: int
    ) -> tuple[bool, str]:
        """
        Determine if position should be exited.

        For MA crossover strategies:
        1. Primary exit: Opposite crossover signal (handled by backtester)
        2. Stop loss / Take profit (handled by backtester)
        3. Time-based exit: If trend doesn't develop

        Args:
            current_price: Current market price
            entry_price: Entry price of position
            position_side: 'LONG' or 'SHORT'
            bars_held: Number of bars position has been held

        Returns:
            Tuple of (should_exit: bool, exit_reason: str)
        """
        # Time-based exit: Exit if position held too long without profit
        # Crossover strategies need time for trend to develop
        max_hold_bars = 720  # 12 hours in 1-minute bars

        if bars_held >= max_hold_bars:
            return True, "time_exit_no_trend"

        return False, ""

    def get_stop_loss_price(
        self,
        entry_price: float,
        side: str,
        stop_loss_percent: Optional[float] = None
    ) -> float:
        """
        Calculate stop loss price.

        Args:
            entry_price: Position entry price
            side: 'LONG' or 'SHORT'
            stop_loss_percent: SL percentage (uses param if not provided)

        Returns:
            Stop loss price
        """
        if stop_loss_percent is None:
            stop_loss_percent = self.params['stop_loss_percent']

        if side == 'LONG':
            return entry_price * (1 - stop_loss_percent / 100)
        else:  # SHORT
            return entry_price * (1 + stop_loss_percent / 100)

    def get_take_profit_price(
        self,
        entry_price: float,
        side: str,
        take_profit_percent: Optional[float] = None
    ) -> float:
        """
        Calculate take profit price.

        Args:
            entry_price: Position entry price
            side: 'LONG' or 'SHORT'
            take_profit_percent: TP percentage (uses param if not provided)

        Returns:
            Take profit price
        """
        if take_profit_percent is None:
            take_profit_percent = self.params['take_profit_percent']

        if side == 'LONG':
            return entry_price * (1 + take_profit_percent / 100)
        else:  # SHORT
            return entry_price * (1 - take_profit_percent / 100)

    def __repr__(self) -> str:
        """String representation of strategy."""
        return (
            f"VolumeWeightedMACrossStrategy("
            f"short_window={self.params['short_window']}, "
            f"long_window={self.params['long_window']}, "
            f"vol_multiplier={self.params['vol_multiplier']}, "
            f"SL={self.params['stop_loss_percent']}%, "
            f"TP={self.params['take_profit_percent']}%)"
        )
