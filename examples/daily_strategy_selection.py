"""
Example: Daily Strategy Selection Logic

This script demonstrates the meta-strategy approach where the best
performing strategy is selected daily based on recent backtesting results.

This is a preview of Phase 3 functionality.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
import numpy as np
from datetime import datetime
from modules import VectorizedBacktester
from strategies import (
    VolatilityBreakoutStrategy,
    RSIBollingerReversionStrategy,
    VolumeWeightedMACrossStrategy
)

print("=" * 70)
print("DAILY STRATEGY SELECTION SIMULATION")
print("Meta-Strategy Approach: Select Today's Champion")
print("=" * 70)

# 1. Load recent data
print("\n[Step 1] Loading recent market data...")

def create_sample_data(n_periods=2000):
    dates = pd.date_range(start='2024-01-01', periods=n_periods, freq='1h')
    np.random.seed(42)
    returns = np.random.randn(n_periods) * 0.015
    price = 50000 * np.exp(np.cumsum(returns))

    df = pd.DataFrame({
        'open': price,
        'high': price * (1 + abs(np.random.randn(n_periods)) * 0.01),
        'low': price * (1 - abs(np.random.randn(n_periods)) * 0.01),
        'close': price * (1 + np.random.randn(n_periods) * 0.005),
        'volume': np.random.randint(100, 1000, n_periods) * 1000
    }, index=dates)

    return df

df = create_sample_data()

# Use last 7 days for strategy selection
recent_df = df.iloc[-168:]  # 7 days × 24 hours
print(f"Using {len(recent_df)} candles (last 7 days)")
print(f"Period: {recent_df.index[0]} to {recent_df.index[-1]}")

# 2. Define strategy pool
print("\n[Step 2] Defining strategy pool...")
strategy_pool = [
    # ST-01 variants
    {
        'name': 'ST-01: Volatility Breakout (k=0.4)',
        'class': VolatilityBreakoutStrategy,
        'params': {'k': 0.4, 'lookback_period': 24}
    },
    {
        'name': 'ST-01: Volatility Breakout (k=0.5)',
        'class': VolatilityBreakoutStrategy,
        'params': {'k': 0.5, 'lookback_period': 24}
    },
    {
        'name': 'ST-01: Volatility Breakout (k=0.6)',
        'class': VolatilityBreakoutStrategy,
        'params': {'k': 0.6, 'lookback_period': 12}
    },

    # ST-02 variants
    {
        'name': 'ST-02: RSI Reversion (Standard)',
        'class': RSIBollingerReversionStrategy,
        'params': {
            'rsi_period': 14,
            'rsi_buy_threshold': 30,
            'rsi_sell_threshold': 70,
            'bb_stddev': 2.0
        }
    },
    {
        'name': 'ST-02: RSI Reversion (Aggressive)',
        'class': RSIBollingerReversionStrategy,
        'params': {
            'rsi_period': 14,
            'rsi_buy_threshold': 25,
            'rsi_sell_threshold': 75,
            'bb_stddev': 2.2
        }
    },

    # ST-03 variants
    {
        'name': 'ST-03: Volume MA Cross (Fast)',
        'class': VolumeWeightedMACrossStrategy,
        'params': {
            'short_window': 5,
            'long_window': 20,
            'vol_multiplier': 2.0
        }
    },
    {
        'name': 'ST-03: Volume MA Cross (Standard)',
        'class': VolumeWeightedMACrossStrategy,
        'params': {
            'short_window': 10,
            'long_window': 30,
            'vol_multiplier': 2.0
        }
    },
    {
        'name': 'ST-03: Volume MA Cross (Slow)',
        'class': VolumeWeightedMACrossStrategy,
        'params': {
            'short_window': 15,
            'long_window': 40,
            'vol_multiplier': 1.5
        }
    },
]

print(f"Total strategies in pool: {len(strategy_pool)}")

# 3. Backtest each strategy
print("\n[Step 3] Backtesting all strategies on recent data...")
backtester = VectorizedBacktester(initial_balance=10000, leverage=10)
results = []

for i, strat_config in enumerate(strategy_pool, 1):
    print(f"  [{i}/{len(strategy_pool)}] Testing {strat_config['name']}...")

    strategy = strat_config['class'](params=strat_config['params'])
    result = backtester.run_backtest(recent_df, strategy, symbol='BTC/USDT')

    results.append({
        'strategy_name': strat_config['name'],
        'total_return': result['total_return'],
        'win_rate': result['win_rate'],
        'profit_factor': result['profit_factor'],
        'max_drawdown': result['max_drawdown'],
        'total_trades': result['total_trades'],
        'score': result['score']
    })

# 4. Rank strategies by composite score
print("\n[Step 4] Ranking strategies by composite score...")
results_df = pd.DataFrame(results)
results_df = results_df.sort_values('score', ascending=False).reset_index(drop=True)
results_df['rank'] = range(1, len(results_df) + 1)

# 5. Display results
print("\n" + "=" * 70)
print("STRATEGY RANKING")
print("=" * 70)
print(f"\n{'Rank':<6} {'Strategy':<45} {'Score':<10} {'Return%':<10} {'Trades':<8}")
print("-" * 70)

for _, row in results_df.iterrows():
    print(f"{row['rank']:<6} {row['strategy_name']:<45} "
          f"{row['score']:<10.2f} {row['total_return']:<10.2f} {row['total_trades']:<8.0f}")

# 6. Select best strategy
best_strategy = results_df.iloc[0]

print("\n" + "=" * 70)
print("✓ SELECTED STRATEGY FOR TODAY")
print("=" * 70)
print(f"Strategy:        {best_strategy['strategy_name']}")
print(f"Composite Score: {best_strategy['score']:.2f}")
print(f"\nBacktest Performance (Last 7 Days):")
print(f"  Total Return:    {best_strategy['total_return']:.2f}%")
print(f"  Win Rate:        {best_strategy['win_rate']:.2f}%")
print(f"  Profit Factor:   {best_strategy['profit_factor']:.2f}")
print(f"  Max Drawdown:    {best_strategy['max_drawdown']:.2f}%")
print(f"  Total Trades:    {int(best_strategy['total_trades'])}")
print("=" * 70)

print("\n✓ This strategy would be loaded into the live trading system.")
print("  The bot would use these parameters for today's trading session.")

# 7. Show performance distribution
print("\n" + "=" * 70)
print("PERFORMANCE DISTRIBUTION")
print("=" * 70)

print("\nScore Distribution:")
for i, row in results_df.iterrows():
    bar_length = int(row['score'] / 2)  # Scale for display
    bar = '█' * max(0, bar_length)
    print(f"  {row['strategy_name'][:40]:<40} {bar} {row['score']:.1f}")

print("\n" + "=" * 70)
print("Strategy selection complete!")
print("\nNext steps:")
print("  1. Save selected strategy configuration to database")
print("  2. Load strategy into trading bot")
print("  3. Monitor performance during trading session")
print("  4. Repeat selection process tomorrow")
print("=" * 70)
