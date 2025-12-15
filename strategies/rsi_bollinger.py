"""
ST-02: RSI + Bollinger Band Mean Reversion Strategy

Mean reversion strategy that trades oversold/overbought conditions
identified by RSI and Bollinger Bands. Works best in sideways markets.
"""

import pandas as pd
import numpy as np
from typing import Dict, Optional
from .base_strategy import BaseStrategy


class RSIBollingerReversionStrategy(BaseStrategy):
    """
    RSI + Bollinger Band Mean Reversion Strategy (ST-02)

    This strategy exploits mean reversion by identifying extreme
    price conditions using both RSI (momentum) and Bollinger Bands
    (volatility) indicators.

    Entry Logic:
        - Long: Price < BB_lower AND RSI < buy_threshold (oversold)
        - Short: Price > BB_upper AND RSI > sell_threshold (overbought)

    Exit Logic:
        - Target: Price reaches BB_middle (mean reversion complete)
        - Stop loss: Price continues against us beyond band width

    Parameters:
        - rsi_period (int): RSI calculation period (9-21, default: 14)
        - rsi_buy_threshold (float): RSI level for long entry (20-35)
        - rsi_sell_threshold (float): RSI level for short entry (65-80)
        - bb_period (int): Bollinger Band SMA period (default: 20)
        - bb_stddev (float): BB standard deviation multiplier (1.8-2.5)
        - exit_at_midband (bool): Exit when price reaches BB middle
        - stop_loss_percent (float): Stop loss percentage (default: 2.0%)
        - take_profit_percent (float): Take profit percentage (default: 4.0%)

    Optimization Ranges:
        - rsi_period: [9, 14, 21]
        - rsi_buy_threshold: [20, 25, 30, 35]
        - rsi_sell_threshold: [65, 70, 75, 80]
        - bb_stddev: [1.8, 2.0, 2.2, 2.5]
    """

    def __init__(self, params: Optional[Dict] = None):
        """
        Initialize RSI + Bollinger Reversion Strategy.

        Args:
            params: Dictionary of strategy parameters
        """
        default_params = {
            'rsi_period': 14,
            'rsi_buy_threshold': 30,
            'rsi_sell_threshold': 70,
            'bb_period': 20,
            'bb_stddev': 2.0,
            'exit_at_midband': True,
            'stop_loss_percent': 2.0,
            'take_profit_percent': 4.0,
        }

        if params:
            default_params.update(params)

        super().__init__(name="RSI_Bollinger_Reversion", params=default_params)

    def add_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Add RSI and Bollinger Band indicators.

        Calculates:
        1. RSI (Relative Strength Index)
           - Measures momentum and identifies overbought/oversold
        2. Bollinger Bands (Upper, Middle, Lower)
           - Measures volatility and price extremes

        Args:
            df: OHLCV DataFrame

        Returns:
            DataFrame with added indicator columns
        """
        # Ensure we have required columns
        if 'close' not in df.columns:
            raise ValueError("Missing required column: close")

        # Calculate RSI
        rsi_period = self.params['rsi_period']
        df['rsi'] = self._calculate_rsi(df['close'], rsi_period)

        # Calculate Bollinger Bands
        bb_period = self.params['bb_period']
        bb_stddev = self.params['bb_stddev']

        df['bb_middle'] = df['close'].rolling(window=bb_period, min_periods=1).mean()
        bb_std = df['close'].rolling(window=bb_period, min_periods=1).std()

        df['bb_upper'] = df['bb_middle'] + (bb_std * bb_stddev)
        df['bb_lower'] = df['bb_middle'] - (bb_std * bb_stddev)

        # Calculate band width for reference
        df['bb_width'] = df['bb_upper'] - df['bb_lower']

        return df

    def _calculate_rsi(self, prices: pd.Series, period: int) -> pd.Series:
        """
        Calculate Relative Strength Index.

        RSI Formula:
        1. Calculate price changes (delta)
        2. Separate gains and losses
        3. Calculate average gain and average loss
        4. RS = average gain / average loss
        5. RSI = 100 - (100 / (1 + RS))

        Args:
            prices: Price series (typically close prices)
            period: RSI period (default: 14)

        Returns:
            RSI series (0-100 scale)
        """
        # Calculate price changes
        delta = prices.diff()

        # Separate gains and losses
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)

        # Calculate exponential moving average of gains and losses
        avg_gain = gain.rolling(window=period, min_periods=1).mean()
        avg_loss = loss.rolling(window=period, min_periods=1).mean()

        # Avoid division by zero
        avg_loss = avg_loss.replace(0, 1e-10)

        # Calculate RS and RSI
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))

        return rsi

    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Generate mean reversion signals.

        Signal Logic:
        1. Long Entry: Price < BB_lower AND RSI < buy_threshold
           (Market is oversold by both indicators)

        2. Short Entry: Price > BB_upper AND RSI > sell_threshold
           (Market is overbought by both indicators)

        3. Exit signals handled by backtester via SL/TP

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

        # Get threshold parameters
        rsi_buy = self.params['rsi_buy_threshold']
        rsi_sell = self.params['rsi_sell_threshold']

        # Long signal: Oversold by both RSI and Bollinger
        long_condition = (
            (df['close'] < df['bb_lower']) &
            (df['rsi'] < rsi_buy)
        )

        # Short signal: Overbought by both RSI and Bollinger
        short_condition = (
            (df['close'] > df['bb_upper']) &
            (df['rsi'] > rsi_sell)
        )

        # Assign signals
        df.loc[long_condition, 'signal'] = 1
        df.loc[short_condition, 'signal'] = -1

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

        Mean reversion trades can be more risky due to catching
        falling knives, so position sizing is conservative.

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

        For mean reversion, we primarily rely on:
        1. Take profit when price reaches BB middle (mean reversion target)
        2. Stop loss if price continues in extreme direction
        3. Time-based exit if mean reversion doesn't occur

        Args:
            current_price: Current market price
            entry_price: Entry price of position
            position_side: 'LONG' or 'SHORT'
            bars_held: Number of bars position has been held

        Returns:
            Tuple of (should_exit: bool, exit_reason: str)
        """
        # Time-based exit: Mean reversion should happen relatively quickly
        # Exit after 4 hours (240 minutes for 1m candles)
        max_hold_bars = 240  # 4 hours

        if bars_held >= max_hold_bars:
            return True, "time_exit_no_reversion"

        return False, ""

    def get_stop_loss_price(
        self,
        entry_price: float,
        side: str,
        stop_loss_percent: Optional[float] = None
    ) -> float:
        """
        Calculate stop loss price.

        For mean reversion, stop loss is tighter as we expect
        quick reversals.

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

        For mean reversion, take profit is typically when price
        returns to the mean (BB middle).

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
            f"RSIBollingerReversionStrategy("
            f"rsi_period={self.params['rsi_period']}, "
            f"rsi_thresholds=({self.params['rsi_buy_threshold']}/{self.params['rsi_sell_threshold']}), "
            f"bb_stddev={self.params['bb_stddev']}, "
            f"SL={self.params['stop_loss_percent']}%, "
            f"TP={self.params['take_profit_percent']}%)"
        )
