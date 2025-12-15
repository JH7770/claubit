"""Strategies package for trading bot."""

from .base_strategy import BaseStrategy, SimpleMovingAverageCrossStrategy
from .volatility_breakout import VolatilityBreakoutStrategy
from .rsi_bollinger import RSIBollingerReversionStrategy
from .volume_ma_cross import VolumeWeightedMACrossStrategy

__all__ = [
    'BaseStrategy',
    'SimpleMovingAverageCrossStrategy',
    'VolatilityBreakoutStrategy',
    'RSIBollingerReversionStrategy',
    'VolumeWeightedMACrossStrategy',
]
