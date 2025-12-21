"""
ST-05: MACD Momentum Strategy

Trend-following momentum strategy using MACD (Moving Average Convergence Divergence).
Captures trend direction and strength, works well in trending markets.
"""

import pandas as pd
import numpy as np
from typing import Dict, Optional
from .base_strategy import BaseStrategy


class MACDMomentumStrategy(BaseStrategy):
    """
    MACD Momentum Strategy (ST-05)

    Uses MACD indicator to identify momentum and trend direction.
    MACD measures the relationship between two EMAs and provides
    signals through line crossovers and histogram changes.

    Entry Logic:
        - Long: MACD line crosses above Signal line (bullish crossover)
          AND MACD histogram is positive and increasing
        - Short: MACD line crosses below Signal line (bearish crossover)
          AND MACD histogram is negative and decreasing

    Optional Filters:
        - Zero line filter: Only long above 0, only short below 0
        - Histogram strength filter: Require minimum histogram value

    Exit Logic:
        - Opposite MACD crossover
        - Stop loss / Take profit
        - Histogram weakening (optional)

    Parameters:
        - fast_period (int): Fast EMA period (default: 12)
        - slow_period (int): Slow EMA period (default: 26)
        - signal_period (int): Signal line period (default: 9)
        - use_zero_filter (bool): Filter trades by MACD zero line
        - use_histogram_filter (bool): Require histogram strength
        - histogram_threshold (float): Min histogram value (default: 0.0)
        - stop_loss_percent (float): Stop loss percentage (default: 2.0%)
        - take_profit_percent (float): Take profit percentage (default: 4.0%)

    Optimization Ranges:
        - fast_period: [8, 12, 15]
        - slow_period: [21, 26, 30]
        - signal_period: [7, 9, 11]
        - use_zero_filter: [True, False]
    """

    def __init__(self, params: Optional[Dict] = None):
        """
        Initialize MACD Momentum Strategy.

        Args:
            params: Dictionary of strategy parameters
        """
        default_params = {
            'fast_period': 12,
            'slow_period': 26,
            'signal_period': 9,
            'use_zero_filter': False,
            'use_histogram_filter': True,
            'histogram_threshold': 0.0,
            'stop_loss_percent': 2.0,
            'take_profit_percent': 4.0,
        }

        if params:
            default_params.update(params)

        super().__init__(name="MACD_Momentum", params=default_params)

    def calculate_macd(
        self,
        prices: pd.Series,
        fast: int,
        slow: int,
        signal: int
    ) -> tuple[pd.Series, pd.Series, pd.Series]:
        """
        Calculate MACD indicator components.

        MACD = Fast EMA - Slow EMA
        Signal Line = EMA of MACD
        Histogram = MACD - Signal Line

        Args:
            prices: Price series (typically close)
            fast: Fast EMA period
            slow: Slow EMA period
            signal: Signal line EMA period

        Returns:
            Tuple of (macd_line, signal_line, histogram)
        """
        # Calculate EMAs
        ema_fast = prices.ewm(span=fast, adjust=False).mean()
        ema_slow = prices.ewm(span=slow, adjust=False).mean()

        # Calculate MACD line
        macd_line = ema_fast - ema_slow

        # Calculate Signal line (EMA of MACD)
        signal_line = macd_line.ewm(span=signal, adjust=False).mean()

        # Calculate Histogram
        histogram = macd_line - signal_line

        return macd_line, signal_line, histogram

    def add_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Add MACD indicators to DataFrame.

        Calculates:
        1. MACD line (fast EMA - slow EMA)
        2. Signal line (EMA of MACD)
        3. Histogram (MACD - Signal)
        4. Histogram momentum (rate of change)

        Args:
            df: OHLCV DataFrame

        Returns:
            DataFrame with added indicator columns
        """
        # Ensure we have required columns
        if 'close' not in df.columns:
            raise ValueError("Missing required column: close")

        # Get parameters
        fast_period = self.params['fast_period']
        slow_period = self.params['slow_period']
        signal_period = self.params['signal_period']

        # Calculate MACD components
        df['macd'], df['macd_signal'], df['macd_hist'] = self.calculate_macd(
            df['close'], fast_period, slow_period, signal_period
        )

        # Calculate histogram momentum (change in histogram)
        df['hist_momentum'] = df['macd_hist'].diff()

        # Calculate zero line distance (for reference)
        df['macd_distance_from_zero'] = df['macd'].abs()

        return df

    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Generate trading signals based on MACD crossovers.

        Signal Logic:
        1. Bullish Crossover: MACD crosses above Signal line
           - Optional: MACD above zero line
           - Optional: Histogram above threshold and increasing

        2. Bearish Crossover: MACD crosses below Signal line
           - Optional: MACD below zero line
           - Optional: Histogram below -threshold and decreasing

        Args:
            df: OHLCV DataFrame

        Returns:
            DataFrame with 'signal' column:
                1 = Long entry (bullish MACD crossover)
                -1 = Short entry (bearish MACD crossover)
                0 = No position/hold
        """
        # Add indicators
        df = self.add_indicators(df)

        # Initialize signal column
        df['signal'] = 0

        # Get parameters
        use_zero_filter = self.params['use_zero_filter']
        use_histogram_filter = self.params['use_histogram_filter']
        hist_threshold = self.params['histogram_threshold']

        # Detect MACD crossovers
        # Bullish: MACD crosses above Signal
        bullish_cross = (
            (df['macd'] > df['macd_signal']) &
            (df['macd'].shift(1) <= df['macd_signal'].shift(1))
        )

        # Bearish: MACD crosses below Signal
        bearish_cross = (
            (df['macd'] < df['macd_signal']) &
            (df['macd'].shift(1) >= df['macd_signal'].shift(1))
        )

        # Apply zero line filter if enabled
        if use_zero_filter:
            # Only long when MACD is above zero (bullish territory)
            bullish_cross = bullish_cross & (df['macd'] > 0)
            # Only short when MACD is below zero (bearish territory)
            bearish_cross = bearish_cross & (df['macd'] < 0)

        # Apply histogram filter if enabled
        if use_histogram_filter:
            # Long: Histogram positive and increasing
            bullish_cross = bullish_cross & (
                (df['macd_hist'] > hist_threshold) &
                (df['hist_momentum'] > 0)
            )
            # Short: Histogram negative and decreasing
            bearish_cross = bearish_cross & (
                (df['macd_hist'] < -hist_threshold) &
                (df['hist_momentum'] < 0)
            )

        # Assign signals
        df.loc[bullish_cross, 'signal'] = 1
        df.loc[bearish_cross, 'signal'] = -1

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

        MACD signals are generally reliable in trending markets,
        so we use standard position sizing.

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

        For MACD strategy:
        1. Primary exit: Opposite crossover (handled by backtester)
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
        # Time-based exit: MACD trends can run, but exit if too long
        max_hold_bars = 960  # 16 hours in 1-minute bars

        if bars_held >= max_hold_bars:
            return True, "time_exit_max_hold"

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
            f"MACDMomentumStrategy("
            f"fast={self.params['fast_period']}, "
            f"slow={self.params['slow_period']}, "
            f"signal={self.params['signal_period']}, "
            f"zero_filter={self.params['use_zero_filter']}, "
            f"SL={self.params['stop_loss_percent']}%, "
            f"TP={self.params['take_profit_percent']}%)"
        )
