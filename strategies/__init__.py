"""Strategies package for trading bot."""

from .base_strategy import BaseStrategy, SimpleMovingAverageCrossStrategy
from .volatility_breakout import VolatilityBreakoutStrategy
from .rsi_bollinger import RSIBollingerReversionStrategy
from .volume_ma_cross import VolumeWeightedMACrossStrategy
from .scalping_grid import DynamicScalpingGridStrategy
from .macd_momentum import MACDMomentumStrategy
from .supertrend import SupertrendStrategy
from .keltner_channel import KeltnerChannelReversionStrategy
from .stochastic_momentum import StochasticMomentumStrategy

__all__ = [
    'BaseStrategy',
    'SimpleMovingAverageCrossStrategy',
    'VolatilityBreakoutStrategy',
    'RSIBollingerReversionStrategy',
    'VolumeWeightedMACrossStrategy',
    'DynamicScalpingGridStrategy',
    'MACDMomentumStrategy',
    'SupertrendStrategy',
    'KeltnerChannelReversionStrategy',
    'StochasticMomentumStrategy',
]
