"""
ST-01: Volatility Breakout Strategy

Modified Larry Williams volatility breakout strategy adapted for scalping.
Trades breakouts based on the range of previous session.
"""

import pandas as pd
import numpy as np
from typing import Dict, Optional
from .base_strategy import BaseStrategy


class VolatilityBreakoutStrategy(BaseStrategy):
    """
    Volatility Breakout Strategy (ST-01)

    Inspired by Larry Williams' range breakout concept, this strategy
    identifies volatility expansion moments during US market hours and
    enters positions when price breaks out of the previous range.

    Entry Logic:
        - Long: Price > Open + (Range × k)
        - Short: Price < Open - (Range × k)
        Where Range = Previous session's High - Low

    Optional MA Filter:
        - Only take longs above MA
        - Only take shorts below MA

    Parameters:
        - k (float): Noise ratio for breakout threshold (0.3-0.8)
                    Lower = earlier entries but more whipsaws
                    Higher = fewer entries but more reliable
        - lookback_period (int): Hours to calculate range (4, 8, 12, 24)
        - ma_period (int): Moving average period for trend filter
        - use_ma_filter (bool): Enable MA trend filtering
        - stop_loss_percent (float): Stop loss percentage (default: 2.0%)
        - take_profit_percent (float): Take profit percentage (default: 4.0%)

    Optimization Ranges:
        - k: [0.3, 0.4, 0.5, 0.6, 0.7, 0.8]
        - lookback_period: [4, 8, 12, 24]
        - ma_period: [5, 10, 20, 50]
    """

    def __init__(self, params: Optional[Dict] = None):
        """
        Initialize Volatility Breakout Strategy.

        Args:
            params: Dictionary of strategy parameters
        """
        default_params = {
            'k': 0.5,
            'lookback_period': 24,
            'ma_period': 20,
            'use_ma_filter': False,
            'stop_loss_percent': 2.0,
            'take_profit_percent': 4.0,
        }

        if params:
            default_params.update(params)

        super().__init__(name="Volatility_Breakout", params=default_params)

    def add_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Add technical indicators for volatility breakout.

        Calculates:
        1. Rolling high/low over lookback period
        2. Range (High - Low)
        3. Breakout levels (Open ± Range × k)
        4. Optional: Moving average for trend filter

        Args:
            df: OHLCV DataFrame

        Returns:
            DataFrame with added indicator columns
        """
        # Ensure we have required columns
        required_cols = ['open', 'high', 'low', 'close']
        for col in required_cols:
            if col not in df.columns:
                raise ValueError(f"Missing required column: {col}")

        # Calculate rolling high and low (shifted by 1 to avoid look-ahead bias)
        lookback = self.params['lookback_period']
        df['rolling_high'] = df['high'].rolling(window=lookback, min_periods=1).max().shift(1)
        df['rolling_low'] = df['low'].rolling(window=lookback, min_periods=1).min().shift(1)

        # Calculate range
        df['range'] = df['rolling_high'] - df['rolling_low']

        # Calculate breakout levels
        k = self.params['k']
        df['long_breakout'] = df['open'] + (df['range'] * k)
        df['short_breakout'] = df['open'] - (df['range'] * k)

        # Optional: Add moving average for trend filter
        if self.params['use_ma_filter']:
            ma_period = self.params['ma_period']
            df['ma'] = df['close'].rolling(window=ma_period, min_periods=1).mean()

        return df

    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Generate trading signals based on volatility breakout.

        Signal Logic:
        1. Long signal: Close > long_breakout level
           (AND close > MA if filter enabled)
        2. Short signal: Close < short_breakout level
           (AND close < MA if filter enabled)
        3. Use shift(1) to avoid look-ahead bias

        Args:
            df: OHLCV DataFrame

        Returns:
            DataFrame with 'signal' column:
                1 = Long entry
                -1 = Short entry
                0 = No position/hold
        """
        # Add indicators
        df = self.add_indicators(df)

        # Initialize signal column
        df['signal'] = 0

        # Generate base breakout signals
        # Long: price breaks above upper threshold
        long_condition = df['close'] > df['long_breakout']

        # Short: price breaks below lower threshold
        short_condition = df['close'] < df['short_breakout']

        # Apply MA filter if enabled
        if self.params['use_ma_filter']:
            # Only long when above MA
            long_condition = long_condition & (df['close'] > df['ma'])
            # Only short when below MA
            short_condition = short_condition & (df['close'] < df['ma'])

        # Assign signals
        df.loc[long_condition, 'signal'] = 1
        df.loc[short_condition, 'signal'] = -1

        # Shift signals by 1 to avoid look-ahead bias
        # (we can only act on the next candle after signal appears)
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

        Uses fixed percentage of balance risked per trade.
        Position size accounts for leverage.

        Args:
            signal: 1 for long, -1 for short
            price: Current price
            balance: Account balance
            risk_percent: Percentage of balance to risk (default: 1.0%)

        Returns:
            Position size in base currency (e.g., BTC amount)
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
        # This ensures we risk exactly risk_amount if stop loss is hit
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
        Determine if position should be exited based on custom logic.

        For this strategy, exits are primarily handled by:
        1. Stop loss (handled by backtester)
        2. Take profit (handled by backtester)
        3. Opposite signal (handled by backtester)
        4. Time-based exit (implemented here)

        Args:
            current_price: Current market price
            entry_price: Entry price of position
            position_side: 'LONG' or 'SHORT'
            bars_held: Number of bars position has been held

        Returns:
            Tuple of (should_exit: bool, exit_reason: str)
        """
        # Time-based exit: Close position after max holding period
        # Default: Hold for maximum 8 hours (480 minutes for 1m candles)
        max_hold_bars = 480  # 8 hours in 1-minute bars

        if bars_held >= max_hold_bars:
            return True, "time_exit"

        return False, ""

    def get_stop_loss_price(
        self,
        entry_price: float,
        side: str,
        stop_loss_percent: Optional[float] = None
    ) -> float:
        """
        Calculate stop loss price based on entry price and side.

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
        Calculate take profit price based on entry price and side.

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
            f"VolatilityBreakoutStrategy("
            f"k={self.params['k']}, "
            f"lookback={self.params['lookback_period']}, "
            f"ma_filter={self.params['use_ma_filter']}, "
            f"SL={self.params['stop_loss_percent']}%, "
            f"TP={self.params['take_profit_percent']}%)"
        )
