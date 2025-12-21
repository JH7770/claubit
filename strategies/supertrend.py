"""
ST-06: Supertrend Strategy

ATR-based trend following strategy with clear visual signals.
Provides unambiguous entry/exit points and adapts to volatility.
"""

import pandas as pd
import numpy as np
from typing import Dict, Optional
from .base_strategy import BaseStrategy


class SupertrendStrategy(BaseStrategy):
    """
    Supertrend Strategy (ST-06)

    Supertrend is an ATR-based indicator that provides clear trend
    direction and entry/exit signals. The indicator plots above price
    in downtrends (resistance) and below price in uptrends (support).

    How Supertrend Works:
    1. Calculate ATR (Average True Range) for volatility
    2. Calculate basic bands:
       - Upper Band = (High + Low) / 2 + (Multiplier × ATR)
       - Lower Band = (High + Low) / 2 - (Multiplier × ATR)
    3. Track final bands with trend direction
    4. Signal when price crosses the Supertrend line

    Entry Logic:
        - Long: Price closes above Supertrend (trend flip to bullish)
        - Short: Price closes below Supertrend (trend flip to bearish)

    Exit Logic:
        - Long Exit: Price closes below Supertrend (trend flip to bearish)
        - Short Exit: Price closes above Supertrend (trend flip to bullish)
        - Stop loss / Take profit as backup

    Parameters:
        - atr_period (int): ATR calculation period (default: 10)
        - atr_multiplier (float): ATR multiplier for bands (default: 3.0)
        - use_ema_filter (bool): Add EMA trend filter (default: False)
        - ema_period (int): EMA period for trend filter (default: 50)
        - stop_loss_percent (float): Stop loss percentage (default: 2.5%)
        - take_profit_percent (float): Take profit percentage (default: 5.0%)

    Optimization Ranges:
        - atr_period: [7, 10, 14]
        - atr_multiplier: [2.0, 2.5, 3.0, 3.5]
        - use_ema_filter: [True, False]
        - ema_period: [20, 50, 100]
    """

    def __init__(self, params: Optional[Dict] = None):
        """
        Initialize Supertrend Strategy.

        Args:
            params: Dictionary of strategy parameters
        """
        default_params = {
            'atr_period': 10,
            'atr_multiplier': 3.0,
            'use_ema_filter': False,
            'ema_period': 50,
            'stop_loss_percent': 2.5,
            'take_profit_percent': 5.0,
        }

        if params:
            default_params.update(params)

        super().__init__(name="Supertrend", params=default_params)

    def calculate_atr(self, df: pd.DataFrame, period: int) -> pd.Series:
        """
        Calculate Average True Range (ATR).

        ATR measures market volatility.
        TR = max(high-low, abs(high-prev_close), abs(low-prev_close))
        ATR = EMA(TR, period)

        Args:
            df: OHLCV DataFrame
            period: ATR period

        Returns:
            Series with ATR values
        """
        high = df['high']
        low = df['low']
        close = df['close']

        # Calculate True Range
        tr1 = high - low
        tr2 = abs(high - close.shift())
        tr3 = abs(low - close.shift())

        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)

        # Calculate ATR using EMA
        atr = tr.ewm(span=period, adjust=False).mean()

        return atr

    def calculate_supertrend(
        self,
        df: pd.DataFrame,
        atr_period: int,
        multiplier: float
    ) -> tuple[pd.Series, pd.Series]:
        """
        Calculate Supertrend indicator.

        Args:
            df: OHLCV DataFrame
            atr_period: ATR period
            multiplier: ATR multiplier

        Returns:
            Tuple of (supertrend_line, trend_direction)
            - supertrend_line: The Supertrend line values
            - trend_direction: 1 for uptrend, -1 for downtrend
        """
        # Calculate ATR
        atr = self.calculate_atr(df, atr_period)

        # Calculate HL average
        hl_avg = (df['high'] + df['low']) / 2

        # Calculate basic upper and lower bands
        upper_band = hl_avg + (multiplier * atr)
        lower_band = hl_avg - (multiplier * atr)

        # Initialize final bands and trend
        final_upper = upper_band.copy()
        final_lower = lower_band.copy()
        supertrend = pd.Series(index=df.index, dtype=float)
        direction = pd.Series(index=df.index, dtype=int)

        # Calculate Supertrend line
        for i in range(len(df)):
            if i == 0:
                # Initialize
                final_upper.iloc[i] = upper_band.iloc[i]
                final_lower.iloc[i] = lower_band.iloc[i]
                supertrend.iloc[i] = 0
                direction.iloc[i] = 1
                continue

            # Update final bands
            # Upper band: use new band if price crossed above, else use min of current and previous
            if upper_band.iloc[i] < final_upper.iloc[i-1] or df['close'].iloc[i-1] > final_upper.iloc[i-1]:
                final_upper.iloc[i] = upper_band.iloc[i]
            else:
                final_upper.iloc[i] = final_upper.iloc[i-1]

            # Lower band: use new band if price crossed below, else use max of current and previous
            if lower_band.iloc[i] > final_lower.iloc[i-1] or df['close'].iloc[i-1] < final_lower.iloc[i-1]:
                final_lower.iloc[i] = lower_band.iloc[i]
            else:
                final_lower.iloc[i] = final_lower.iloc[i-1]

            # Determine trend direction
            if supertrend.iloc[i-1] == final_upper.iloc[i-1]:
                # Previous trend was down
                if df['close'].iloc[i] <= final_upper.iloc[i]:
                    supertrend.iloc[i] = final_upper.iloc[i]
                    direction.iloc[i] = -1
                else:
                    supertrend.iloc[i] = final_lower.iloc[i]
                    direction.iloc[i] = 1
            else:
                # Previous trend was up
                if df['close'].iloc[i] >= final_lower.iloc[i]:
                    supertrend.iloc[i] = final_lower.iloc[i]
                    direction.iloc[i] = 1
                else:
                    supertrend.iloc[i] = final_upper.iloc[i]
                    direction.iloc[i] = -1

        return supertrend, direction

    def add_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Add Supertrend and optional EMA indicators.

        Calculates:
        1. ATR for volatility
        2. Supertrend line and direction
        3. Optional: EMA for trend confirmation

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

        # Get parameters
        atr_period = self.params['atr_period']
        multiplier = self.params['atr_multiplier']
        use_ema_filter = self.params['use_ema_filter']
        ema_period = self.params['ema_period']

        # Calculate ATR
        df['atr'] = self.calculate_atr(df, atr_period)

        # Calculate Supertrend
        df['supertrend'], df['st_direction'] = self.calculate_supertrend(
            df, atr_period, multiplier
        )

        # Optional: Add EMA filter
        if use_ema_filter:
            df['ema'] = df['close'].ewm(span=ema_period, adjust=False).mean()

        return df

    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Generate trading signals based on Supertrend crossovers.

        Signal Logic:
        1. Long: Supertrend direction changes from -1 to 1 (trend flip to bullish)
           - Optional: Price above EMA (if filter enabled)

        2. Short: Supertrend direction changes from 1 to -1 (trend flip to bearish)
           - Optional: Price below EMA (if filter enabled)

        Args:
            df: OHLCV DataFrame

        Returns:
            DataFrame with 'signal' column:
                1 = Long entry (bullish trend flip)
                -1 = Short entry (bearish trend flip)
                0 = No position/hold
        """
        # Add indicators
        df = self.add_indicators(df)

        # Initialize signal column
        df['signal'] = 0

        # Get parameters
        use_ema_filter = self.params['use_ema_filter']

        # Detect trend changes
        # Bullish flip: direction changes from -1 to 1
        bullish_flip = (df['st_direction'] == 1) & (df['st_direction'].shift(1) == -1)

        # Bearish flip: direction changes from 1 to -1
        bearish_flip = (df['st_direction'] == -1) & (df['st_direction'].shift(1) == 1)

        # Apply EMA filter if enabled
        if use_ema_filter:
            # Only long when price is above EMA (confirming uptrend)
            bullish_flip = bullish_flip & (df['close'] > df['ema'])
            # Only short when price is below EMA (confirming downtrend)
            bearish_flip = bearish_flip & (df['close'] < df['ema'])

        # Assign signals
        df.loc[bullish_flip, 'signal'] = 1
        df.loc[bearish_flip, 'signal'] = -1

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

        Supertrend provides clear trend signals, allowing for
        confident position sizing.

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

        For Supertrend strategy:
        1. Primary exit: Trend flip (opposite Supertrend signal)
        2. Stop loss / Take profit (handled by backtester)
        3. No time-based exit (let trend run)

        Args:
            current_price: Current market price
            entry_price: Entry price of position
            position_side: 'LONG' or 'SHORT'
            bars_held: Number of bars position has been held

        Returns:
            Tuple of (should_exit: bool, exit_reason: str)
        """
        # Supertrend is designed to let trends run
        # Exit only on trend reversal signal (handled by backtester)
        return False, ""

    def get_stop_loss_price(
        self,
        entry_price: float,
        side: str,
        stop_loss_percent: Optional[float] = None
    ) -> float:
        """
        Calculate stop loss price.

        For Supertrend, SL can be wider since we're following the trend.

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

        For Supertrend, TP can be wider to let trends run.

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
            f"SupertrendStrategy("
            f"atr_period={self.params['atr_period']}, "
            f"multiplier={self.params['atr_multiplier']}, "
            f"ema_filter={self.params['use_ema_filter']}, "
            f"SL={self.params['stop_loss_percent']}%, "
            f"TP={self.params['take_profit_percent']}%)"
        )
