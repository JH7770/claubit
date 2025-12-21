"""
ST-08: Stochastic Momentum Strategy

Momentum strategy using Stochastic Oscillator to identify overbought/oversold
conditions and momentum shifts. Complements RSI with different characteristics.
"""

import pandas as pd
import numpy as np
from typing import Dict, Optional
from .base_strategy import BaseStrategy


class StochasticMomentumStrategy(BaseStrategy):
    """
    Stochastic Momentum Strategy (ST-08)

    The Stochastic Oscillator compares a closing price to its price range
    over a given time period. It identifies overbought/oversold conditions
    and momentum shifts through %K and %D line crossovers.

    How Stochastic Works:
    1. %K (Fast Stochastic) = 100 × (Current Close - Lowest Low) / (Highest High - Lowest Low)
    2. %D (Slow Stochastic) = 3-period SMA of %K
    3. Values range from 0 to 100
       - Above 80: Overbought
       - Below 20: Oversold

    Entry Logic:
        - Long: %K crosses above %D in oversold territory (< 20-30)
          Indicates momentum shift from oversold to bullish
        - Short: %K crosses below %D in overbought territory (> 70-80)
          Indicates momentum shift from overbought to bearish

    Optional Filters:
        - Trend filter: Only trade with the trend (using EMA)
        - Divergence detection: Price vs Stochastic divergence

    Parameters:
        - k_period (int): %K lookback period (default: 14)
        - k_smooth (int): %K smoothing period (default: 3)
        - d_period (int): %D smoothing period (default: 3)
        - oversold_level (int): Oversold threshold (default: 20)
        - overbought_level (int): Overbought threshold (default: 80)
        - use_trend_filter (bool): Add EMA trend filter (default: False)
        - ema_period (int): EMA period for trend (default: 50)
        - require_extreme_zone (bool): Only trade from extreme zones (default: True)
        - stop_loss_percent (float): Stop loss percentage (default: 2.0%)
        - take_profit_percent (float): Take profit percentage (default: 4.0%)

    Optimization Ranges:
        - k_period: [9, 14, 21]
        - oversold_level: [15, 20, 25, 30]
        - overbought_level: [70, 75, 80, 85]
        - use_trend_filter: [True, False]
    """

    def __init__(self, params: Optional[Dict] = None):
        """
        Initialize Stochastic Momentum Strategy.

        Args:
            params: Dictionary of strategy parameters
        """
        default_params = {
            'k_period': 14,
            'k_smooth': 3,
            'd_period': 3,
            'oversold_level': 20,
            'overbought_level': 80,
            'use_trend_filter': False,
            'ema_period': 50,
            'require_extreme_zone': True,
            'stop_loss_percent': 2.0,
            'take_profit_percent': 4.0,
        }

        if params:
            default_params.update(params)

        super().__init__(name="Stochastic_Momentum", params=default_params)

    def calculate_stochastic(
        self,
        df: pd.DataFrame,
        k_period: int,
        k_smooth: int,
        d_period: int
    ) -> tuple[pd.Series, pd.Series]:
        """
        Calculate Stochastic Oscillator (%K and %D).

        %K Formula:
        1. Find highest high and lowest low over k_period
        2. %K = 100 × (Close - Lowest Low) / (Highest High - Lowest Low)
        3. Apply smoothing to %K

        %D = SMA of %K over d_period

        Args:
            df: OHLCV DataFrame
            k_period: Lookback period for %K
            k_smooth: Smoothing period for %K
            d_period: Smoothing period for %D

        Returns:
            Tuple of (%K, %D)
        """
        # Calculate rolling highest high and lowest low
        highest_high = df['high'].rolling(window=k_period, min_periods=1).max()
        lowest_low = df['low'].rolling(window=k_period, min_periods=1).min()

        # Calculate raw %K (Fast Stochastic)
        # Avoid division by zero
        price_range = highest_high - lowest_low
        price_range = price_range.replace(0, 1e-10)

        k_raw = 100 * (df['close'] - lowest_low) / price_range

        # Apply smoothing to %K
        if k_smooth > 1:
            k = k_raw.rolling(window=k_smooth, min_periods=1).mean()
        else:
            k = k_raw

        # Calculate %D (Slow Stochastic - SMA of %K)
        d = k.rolling(window=d_period, min_periods=1).mean()

        return k, d

    def add_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Add Stochastic Oscillator indicators.

        Calculates:
        1. %K (Fast Stochastic)
        2. %D (Slow Stochastic)
        3. Optional: EMA for trend filter
        4. Momentum direction (rising/falling %K)

        Args:
            df: OHLCV DataFrame

        Returns:
            DataFrame with added indicator columns
        """
        # Ensure we have required columns
        required_cols = ['high', 'low', 'close']
        for col in required_cols:
            if col not in df.columns:
                raise ValueError(f"Missing required column: {col}")

        # Get parameters
        k_period = self.params['k_period']
        k_smooth = self.params['k_smooth']
        d_period = self.params['d_period']
        use_trend_filter = self.params['use_trend_filter']
        ema_period = self.params['ema_period']

        # Calculate Stochastic Oscillator
        df['stoch_k'], df['stoch_d'] = self.calculate_stochastic(
            df, k_period, k_smooth, d_period
        )

        # Calculate %K momentum (rate of change)
        df['stoch_momentum'] = df['stoch_k'].diff()

        # Optional: Add EMA for trend filter
        if use_trend_filter:
            df['ema'] = df['close'].ewm(span=ema_period, adjust=False).mean()

        return df

    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Generate trading signals based on Stochastic crossovers.

        Signal Logic:
        1. Long Entry: %K crosses above %D in oversold zone
           - %K was below oversold_level (in oversold zone)
           - %K crosses above %D (momentum shift to bullish)
           - Optional: Price above EMA (confirming uptrend)

        2. Short Entry: %K crosses below %D in overbought zone
           - %K was above overbought_level (in overbought zone)
           - %K crosses below %D (momentum shift to bearish)
           - Optional: Price below EMA (confirming downtrend)

        Args:
            df: OHLCV DataFrame

        Returns:
            DataFrame with 'signal' column:
                1 = Long entry (bullish Stochastic crossover from oversold)
                -1 = Short entry (bearish Stochastic crossover from overbought)
                0 = No position/hold
        """
        # Add indicators
        df = self.add_indicators(df)

        # Initialize signal column
        df['signal'] = 0

        # Get parameters
        oversold = self.params['oversold_level']
        overbought = self.params['overbought_level']
        use_trend_filter = self.params['use_trend_filter']
        require_extreme = self.params['require_extreme_zone']

        # Detect Stochastic crossovers
        # Bullish crossover: %K crosses above %D
        bullish_cross = (
            (df['stoch_k'] > df['stoch_d']) &
            (df['stoch_k'].shift(1) <= df['stoch_d'].shift(1))
        )

        # Bearish crossover: %K crosses below %D
        bearish_cross = (
            (df['stoch_k'] < df['stoch_d']) &
            (df['stoch_k'].shift(1) >= df['stoch_d'].shift(1))
        )

        # Apply zone filters
        if require_extreme:
            # For longs: Must be coming from oversold zone
            # Check if %K was recently (within last 3 bars) in oversold zone
            was_oversold = (
                (df['stoch_k'].shift(1) < oversold) |
                (df['stoch_k'].shift(2) < oversold) |
                (df['stoch_k'].shift(3) < oversold)
            )
            bullish_cross = bullish_cross & was_oversold

            # For shorts: Must be coming from overbought zone
            # Check if %K was recently (within last 3 bars) in overbought zone
            was_overbought = (
                (df['stoch_k'].shift(1) > overbought) |
                (df['stoch_k'].shift(2) > overbought) |
                (df['stoch_k'].shift(3) > overbought)
            )
            bearish_cross = bearish_cross & was_overbought

        # Apply trend filter if enabled
        if use_trend_filter:
            # Only long when price is above EMA (uptrend)
            bullish_cross = bullish_cross & (df['close'] > df['ema'])
            # Only short when price is below EMA (downtrend)
            bearish_cross = bearish_cross & (df['close'] < df['ema'])

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

        Stochastic signals from extreme zones are generally reliable,
        allowing for standard position sizing.

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

        For Stochastic strategy:
        1. Primary exit: Opposite crossover (handled by backtester)
        2. Stop loss / Take profit (handled by backtester)
        3. Time-based exit: If momentum doesn't materialize

        Args:
            current_price: Current market price
            entry_price: Entry price of position
            position_side: 'LONG' or 'SHORT'
            bars_held: Number of bars position has been held

        Returns:
            Tuple of (should_exit: bool, exit_reason: str)
        """
        # Time-based exit: Exit if position held too long without profit
        # Stochastic momentum moves should happen relatively quickly
        max_hold_bars = 360  # 6 hours in 1-minute bars

        if bars_held >= max_hold_bars:
            return True, "time_exit_momentum_faded"

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
            f"StochasticMomentumStrategy("
            f"k_period={self.params['k_period']}, "
            f"levels=({self.params['oversold_level']}/{self.params['overbought_level']}), "
            f"trend_filter={self.params['use_trend_filter']}, "
            f"SL={self.params['stop_loss_percent']}%, "
            f"TP={self.params['take_profit_percent']}%)"
        )
