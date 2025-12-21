"""
ST-07: Keltner Channel Mean Reversion Strategy

ATR-based mean reversion strategy using Keltner Channels.
More stable than Bollinger Bands, works well in ranging markets.
"""

import pandas as pd
import numpy as np
from typing import Dict, Optional
from .base_strategy import BaseStrategy


class KeltnerChannelReversionStrategy(BaseStrategy):
    """
    Keltner Channel Mean Reversion Strategy (ST-07)

    Keltner Channels are volatility-based envelopes set above and below
    an EMA. Unlike Bollinger Bands (which use standard deviation), Keltner
    Channels use ATR, making them smoother and less prone to whipsaws.

    How Keltner Channels Work:
    1. Middle Line = EMA of close price
    2. Upper Channel = Middle Line + (ATR × multiplier)
    3. Lower Channel = Middle Line - (ATR × multiplier)

    Entry Logic (Mean Reversion):
        - Long: Price touches or breaks below Lower Channel (oversold)
          Price expected to revert back to middle line
        - Short: Price touches or breaks above Upper Channel (overbought)
          Price expected to revert back to middle line

    Exit Logic:
        - Target: Price returns to Middle Line (mean reversion complete)
        - Stop Loss: Price continues beyond channel (trend forming)

    Parameters:
        - ema_period (int): EMA period for middle line (default: 20)
        - atr_period (int): ATR calculation period (default: 10)
        - atr_multiplier (float): ATR multiplier for bands (default: 2.0)
        - require_price_outside (bool): Only enter when price is outside channel
        - use_rsi_filter (bool): Add RSI confirmation (default: False)
        - rsi_period (int): RSI period if filter enabled (default: 14)
        - rsi_buy_threshold (float): RSI buy level (default: 35)
        - rsi_sell_threshold (float): RSI sell level (default: 65)
        - stop_loss_percent (float): Stop loss percentage (default: 2.0%)
        - take_profit_percent (float): Take profit percentage (default: 3.0%)

    Optimization Ranges:
        - ema_period: [10, 20, 30]
        - atr_period: [10, 14, 20]
        - atr_multiplier: [1.5, 2.0, 2.5, 3.0]
        - use_rsi_filter: [True, False]
    """

    def __init__(self, params: Optional[Dict] = None):
        """
        Initialize Keltner Channel Mean Reversion Strategy.

        Args:
            params: Dictionary of strategy parameters
        """
        default_params = {
            'ema_period': 20,
            'atr_period': 10,
            'atr_multiplier': 2.0,
            'require_price_outside': True,
            'use_rsi_filter': False,
            'rsi_period': 14,
            'rsi_buy_threshold': 35,
            'rsi_sell_threshold': 65,
            'stop_loss_percent': 2.0,
            'take_profit_percent': 3.0,
        }

        if params:
            default_params.update(params)

        super().__init__(name="Keltner_Channel_Reversion", params=default_params)

    def calculate_atr(self, df: pd.DataFrame, period: int) -> pd.Series:
        """
        Calculate Average True Range (ATR).

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

    def calculate_rsi(self, prices: pd.Series, period: int) -> pd.Series:
        """
        Calculate Relative Strength Index.

        Args:
            prices: Price series (typically close)
            period: RSI period

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

    def add_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Add Keltner Channel indicators.

        Calculates:
        1. EMA (middle line)
        2. ATR (volatility measure)
        3. Upper and Lower Keltner Channels
        4. Channel width
        5. Optional: RSI for confirmation

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
        ema_period = self.params['ema_period']
        atr_period = self.params['atr_period']
        atr_multiplier = self.params['atr_multiplier']
        use_rsi_filter = self.params['use_rsi_filter']
        rsi_period = self.params['rsi_period']

        # Calculate EMA (middle line)
        df['kc_middle'] = df['close'].ewm(span=ema_period, adjust=False).mean()

        # Calculate ATR
        df['atr'] = self.calculate_atr(df, atr_period)

        # Calculate Keltner Channels
        df['kc_upper'] = df['kc_middle'] + (df['atr'] * atr_multiplier)
        df['kc_lower'] = df['kc_middle'] - (df['atr'] * atr_multiplier)

        # Calculate channel width (for reference)
        df['kc_width'] = df['kc_upper'] - df['kc_lower']

        # Calculate distance from middle (normalized by channel width)
        df['kc_position'] = (df['close'] - df['kc_middle']) / (df['kc_width'] / 2)

        # Optional: Add RSI filter
        if use_rsi_filter:
            df['rsi'] = self.calculate_rsi(df['close'], rsi_period)

        return df

    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Generate mean reversion signals based on Keltner Channels.

        Signal Logic:
        1. Long Entry: Price at or below Lower Channel (oversold)
           - Optional: RSI < buy_threshold (confirming oversold)
           - Expecting price to revert to middle

        2. Short Entry: Price at or above Upper Channel (overbought)
           - Optional: RSI > sell_threshold (confirming overbought)
           - Expecting price to revert to middle

        Args:
            df: OHLCV DataFrame

        Returns:
            DataFrame with 'signal' column:
                1 = Long entry (price at lower channel)
                -1 = Short entry (price at upper channel)
                0 = No position/hold
        """
        # Add indicators
        df = self.add_indicators(df)

        # Initialize signal column
        df['signal'] = 0

        # Get parameters
        require_outside = self.params['require_price_outside']
        use_rsi_filter = self.params['use_rsi_filter']
        rsi_buy = self.params['rsi_buy_threshold']
        rsi_sell = self.params['rsi_sell_threshold']

        # Define price touching/breaking channels
        if require_outside:
            # Price must be completely outside the channel
            touches_lower = df['close'] < df['kc_lower']
            touches_upper = df['close'] > df['kc_upper']
        else:
            # Price just needs to touch the channel
            touches_lower = df['low'] <= df['kc_lower']
            touches_upper = df['high'] >= df['kc_upper']

        # Long signal: Price at lower channel (oversold, expecting reversion up)
        long_condition = touches_lower

        # Short signal: Price at upper channel (overbought, expecting reversion down)
        short_condition = touches_upper

        # Apply RSI filter if enabled
        if use_rsi_filter:
            long_condition = long_condition & (df['rsi'] < rsi_buy)
            short_condition = short_condition & (df['rsi'] > rsi_sell)

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

        Mean reversion trades can fail if a trend forms,
        so position sizing is conservative.

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

        For mean reversion:
        1. Target exit: Price reaches middle line (handled externally)
        2. Stop loss: Price continues beyond channel (trend forming)
        3. Time exit: If reversion doesn't occur quickly

        Args:
            current_price: Current market price
            entry_price: Entry price of position
            position_side: 'LONG' or 'SHORT'
            bars_held: Number of bars position has been held

        Returns:
            Tuple of (should_exit: bool, exit_reason: str)
        """
        # Time-based exit: Mean reversion should happen quickly
        # Exit after 3 hours (180 minutes for 1m candles)
        max_hold_bars = 180  # 3 hours

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

        For Keltner Channel reversion, SL is placed beyond the
        opposite channel to protect against trend breakouts.

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

        For mean reversion, TP is typically at the middle line.
        This is approximated by take_profit_percent.

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
            f"KeltnerChannelReversionStrategy("
            f"ema={self.params['ema_period']}, "
            f"atr_period={self.params['atr_period']}, "
            f"multiplier={self.params['atr_multiplier']}, "
            f"rsi_filter={self.params['use_rsi_filter']}, "
            f"SL={self.params['stop_loss_percent']}%, "
            f"TP={self.params['take_profit_percent']}%)"
        )
