"""
ST-04: Dynamic Scalping Grid Strategy

Places grid of limit orders above/below current price with ATR-based spacing.
Designed for ranging markets, uses tight stops to exit when trends form.
"""

import pandas as pd
import numpy as np
from typing import Dict, Optional
from .base_strategy import BaseStrategy


class DynamicScalpingGridStrategy(BaseStrategy):
    """
    Dynamic Scalping Grid Strategy (ST-04)

    Places a grid of trading levels above and below current price.
    Grid spacing adapts to volatility using ATR (Average True Range).
    Designed to profit from price oscillations in ranging markets.

    Entry Logic:
        - BUY: Price touches lower grid levels (grid_buy_1, grid_buy_2, etc.)
        - SELL: Price touches upper grid levels (grid_sell_1, grid_sell_2, etc.)

    Exit Logic:
        - Take Profit: Next grid level (gap distance)
        - Stop Loss: Price breaks grid range (trend detected)

    Parameters:
        - grid_lines (int): Number of grid levels (3-5)
        - gap_percent (float): Base gap between grids (0.2-0.5%)
        - atr_period (int): ATR calculation period (14)
        - atr_multiplier (float): ATR multiplier for dynamic gap (0.5-2.0)
        - use_dynamic_gap (bool): Use ATR-based gap vs fixed percentage
        - stop_trigger_percent (float): Stop loss trigger beyond grid (1.0-3.0%)
        - stop_loss_percent (float): Actual stop loss distance (3.0%)
        - take_profit_percent (float): Take profit distance (0.3%, matches gap)

    Optimization Ranges:
        - grid_lines: [3, 4, 5]
        - gap_percent: [0.2, 0.3, 0.4, 0.5]
        - atr_multiplier: [0.5, 1.0, 1.5, 2.0]
        - stop_trigger_percent: [1.0, 1.5, 2.0, 2.5, 3.0]
    """

    def __init__(self, params: Optional[Dict] = None):
        """
        Initialize Dynamic Scalping Grid Strategy.

        Args:
            params: Dictionary of strategy parameters
        """
        default_params = {
            'grid_lines': 3,
            'gap_percent': 0.3,
            'atr_period': 14,
            'atr_multiplier': 1.0,
            'use_dynamic_gap': True,
            'stop_trigger_percent': 2.0,
            'stop_loss_percent': 3.0,
            'take_profit_percent': 0.3,
        }

        if params:
            default_params.update(params)

        super().__init__(name="Scalping_Grid", params=default_params)

    def calculate_atr(self, df: pd.DataFrame, period: int = 14) -> pd.Series:
        """
        Calculate Average True Range (ATR).

        ATR measures market volatility.
        TR = max(high-low, abs(high-prev_close), abs(low-prev_close))
        ATR = EMA(TR, period)

        Args:
            df: OHLCV DataFrame
            period: ATR period (default: 14)

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

    def add_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Add grid levels and ATR to DataFrame.

        Calculates:
        1. ATR for volatility measurement
        2. Gap size (ATR-based or fixed percentage)
        3. Grid buy levels (below price)
        4. Grid sell levels (above price)
        5. Stop trigger levels (grid boundaries)

        Args:
            df: OHLCV DataFrame

        Returns:
            DataFrame with indicators added
        """
        df = df.copy()

        # Get parameters
        grid_lines = self.params['grid_lines']
        gap_percent = self.params['gap_percent']
        atr_period = self.params['atr_period']
        atr_multiplier = self.params['atr_multiplier']
        use_dynamic_gap = self.params['use_dynamic_gap']
        stop_trigger_percent = self.params['stop_trigger_percent']

        # Calculate ATR
        df['atr'] = self.calculate_atr(df, period=atr_period)

        # Calculate gap size
        if use_dynamic_gap:
            # Dynamic gap based on ATR
            df['gap'] = df['atr'] * atr_multiplier
            df['gap_percent'] = (df['gap'] / df['close']) * 100
        else:
            # Fixed percentage gap
            df['gap'] = df['close'] * (gap_percent / 100)
            df['gap_percent'] = gap_percent

        # Calculate grid levels
        # Buy grids (below current price)
        for i in range(1, grid_lines + 1):
            df[f'grid_buy_{i}'] = df['close'] - (df['gap'] * i)

        # Sell grids (above current price)
        for i in range(1, grid_lines + 1):
            df[f'grid_sell_{i}'] = df['close'] + (df['gap'] * i)

        # Calculate stop triggers (grid boundaries)
        max_grid_distance = df['gap'] * grid_lines
        df['stop_lower'] = df['close'] - (df['close'] * (stop_trigger_percent / 100))
        df['stop_upper'] = df['close'] + (df['close'] * (stop_trigger_percent / 100))

        # Alternative: use grid boundaries as stops
        # df['stop_lower'] = df[f'grid_buy_{grid_lines}'] - df['gap']
        # df['stop_upper'] = df[f'grid_sell_{grid_lines}'] + df['gap']

        return df

    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Generate trading signals based on grid touches.

        Note: This is a simplified implementation for vectorized backtesting.
        Real grid trading uses limit orders at each level.

        BUY Signal (1):
        - Price touches or crosses below grid_buy levels

        SELL Signal (-1):
        - Price touches or crosses above grid_sell levels

        EXIT Signal (0):
        - Price breaks stop_lower or stop_upper (trend forming)

        Args:
            df: OHLCV DataFrame

        Returns:
            DataFrame with 'signal' column added
        """
        df = self.add_indicators(df)
        df['signal'] = 0

        grid_lines = self.params['grid_lines']

        # Detect grid touches using low/high of candles
        # BUY: Low touches any grid_buy level
        buy_touched = pd.Series(False, index=df.index)
        for i in range(1, grid_lines + 1):
            buy_touched |= (df['low'] <= df[f'grid_buy_{i}'].shift()) & (df['low'] > df[f'grid_buy_{i}'].shift() - df['gap'].shift())

        # SELL: High touches any grid_sell level
        sell_touched = pd.Series(False, index=df.index)
        for i in range(1, grid_lines + 1):
            sell_touched |= (df['high'] >= df[f'grid_sell_{i}'].shift()) & (df['high'] < df[f'grid_sell_{i}'].shift() + df['gap'].shift())

        # Stop triggers: Price breaks grid range
        stop_triggered = (df['low'] < df['stop_lower'].shift()) | (df['high'] > df['stop_upper'].shift())

        # Assign signals
        df.loc[buy_touched & ~stop_triggered, 'signal'] = 1
        df.loc[sell_touched & ~stop_triggered, 'signal'] = -1
        df.loc[stop_triggered, 'signal'] = 0  # Force exit on stop trigger

        # For backtesting: hold signal until opposite signal or stop
        # This is a simplified approach - real grid trading is more complex
        df['signal'] = df['signal'].replace(0, np.nan).ffill().fillna(0).astype(int)

        # Clear signals when stops are hit
        for idx in df[stop_triggered].index:
            # Find next index
            loc = df.index.get_loc(idx)
            if loc < len(df) - 1:
                df.iloc[loc:loc+1, df.columns.get_loc('signal')] = 0

        return df

    def calculate_position_size(
        self,
        balance: float,
        risk_percent: float,
        entry_price: float,
        stop_loss_price: float
    ) -> float:
        """
        Calculate position size for grid strategy.

        For grid strategies, risk is divided across grid lines since
        multiple positions might be opened.

        Args:
            balance: Account balance
            risk_percent: Risk per trade percentage
            entry_price: Entry price
            stop_loss_price: Stop loss price

        Returns:
            Position size in base currency
        """
        grid_lines = self.params['grid_lines']

        # Divide risk across grid lines
        risk_per_level = (balance * risk_percent / 100) / grid_lines

        # Calculate stop distance
        stop_distance = abs(entry_price - stop_loss_price)
        if stop_distance == 0:
            stop_distance = entry_price * 0.02  # Fallback: 2%

        # Calculate position size
        position_value = (risk_per_level / stop_distance) * entry_price
        position_size = position_value / entry_price

        # Apply safety limits
        max_position_value = balance * 0.5  # Max 50% of balance per position
        if position_size * entry_price > max_position_value:
            position_size = max_position_value / entry_price

        return position_size

    def get_stop_loss_price(self, entry_price: float, side: str) -> float:
        """
        Calculate stop loss price.

        For grid strategy, SL is at grid boundary (stop_trigger_percent).

        Args:
            entry_price: Entry price
            side: 'LONG' or 'SHORT'

        Returns:
            Stop loss price
        """
        stop_trigger_percent = self.params['stop_trigger_percent']

        if side.upper() == 'LONG':
            # Long SL below entry
            sl_price = entry_price * (1 - stop_trigger_percent / 100)
        else:
            # Short SL above entry
            sl_price = entry_price * (1 + stop_trigger_percent / 100)

        return sl_price

    def get_take_profit_price(self, entry_price: float, side: str) -> float:
        """
        Calculate take profit price.

        For grid strategy, TP is at next grid level (gap distance).

        Args:
            entry_price: Entry price
            side: 'LONG' or 'SHORT'

        Returns:
            Take profit price
        """
        take_profit_percent = self.params['take_profit_percent']

        if side.upper() == 'LONG':
            # Long TP above entry (next grid up)
            tp_price = entry_price * (1 + take_profit_percent / 100)
        else:
            # Short TP below entry (next grid down)
            tp_price = entry_price * (1 - take_profit_percent / 100)

        return tp_price
