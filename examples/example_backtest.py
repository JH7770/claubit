"""
Example: Running a backtest with Volatility Breakout Strategy

This script demonstrates how to:
1. Load historical data
2. Initialize a strategy
3. Run a backtest
4. Analyze results
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
import numpy as np
from modules import VectorizedBacktester
from strategies import VolatilityBreakoutStrategy

print("=" * 70)
print("BACKTEST EXAMPLE: Volatility Breakout Strategy")
print("=" * 70)

# 1. Create or load sample data
print("\n[Step 1] Loading historical data...")

# For this example, we'll create synthetic data
# In production, use DataCollector to load real data
def create_sample_data(n_periods=2000):
    dates = pd.date_range(start='2024-01-01', periods=n_periods, freq='1h')
    np.random.seed(42)
    returns = np.random.randn(n_periods) * 0.015  # 1.5% volatility
    price = 50000 * np.exp(np.cumsum(returns))

    df = pd.DataFrame({
        'open': price,
        'high': price * (1 + abs(np.random.randn(n_periods)) * 0.01),
        'low': price * (1 - abs(np.random.randn(n_periods)) * 0.01),
        'close': price * (1 + np.random.randn(n_periods) * 0.005),
        'volume': np.random.randint(100, 1000, n_periods) * 1000
    }, index=dates)

    return df

df = create_sample_data(n_periods=2000)
print(f"Loaded {len(df)} candles from {df.index[0]} to {df.index[-1]}")
print(f"Price range: ${df['close'].min():.0f} - ${df['close'].max():.0f}")

# 2. Initialize strategy
print("\n[Step 2] Initializing Volatility Breakout Strategy...")
strategy = VolatilityBreakoutStrategy(params={
    'k': 0.5,                    # Breakout noise ratio
    'lookback_period': 24,       # 24-hour range
    'ma_period': 20,
    'use_ma_filter': False,      # No MA filter
    'stop_loss_percent': 2.0,    # 2% stop loss
    'take_profit_percent': 4.0   # 4% take profit
})

print(f"Strategy initialized: {strategy}")

# 3. Run backtest
print("\n[Step 3] Running backtest...")
backtester = VectorizedBacktester(
    initial_balance=10000,
    leverage=10,
    commission=0.0004,   # 0.04% per trade
    slippage=0.0001      # 0.01% slippage
)

results = backtester.run_backtest(df, strategy, symbol='BTC/USDT')

# 4. Display results
print("\n" + "=" * 70)
print("BACKTEST RESULTS")
print("=" * 70)
print(f"Initial Balance:     ${backtester.initial_balance:,.2f}")
print(f"Final Equity:        ${results['final_equity']:,.2f}")
print(f"Total Return:        {results['total_return']:>10.2f}%")
print(f"Win Rate:            {results['win_rate']:>10.2f}%")
print(f"Profit Factor:       {results['profit_factor']:>10.2f}")
print(f"Max Drawdown:        {results['max_drawdown']:>10.2f}%")
print(f"Sharpe Ratio:        {results['sharpe_ratio']:>10.2f}")
print("-" * 70)
print(f"Total Trades:        {results['total_trades']:>10}")
print(f"Winning Trades:      {results['winning_trades']:>10}")
print(f"Losing Trades:       {results['losing_trades']:>10}")
print(f"Avg Win:             {results['avg_win']:>10.2f}%")
print(f"Avg Loss:            {results['avg_loss']:>10.2f}%")
print("-" * 70)
print(f"Composite Score:     {results['score']:>10.2f}")
print("=" * 70)

# 5. Show trade log sample
if len(results['trade_log']) > 0:
    print("\nTrade Log (First 10 trades):")
    print(results['trade_log'].head(10).to_string())
else:
    print("\nNo trades executed.")

# 6. Additional analysis
print("\n" + "=" * 70)
print("ADDITIONAL ANALYSIS")
print("=" * 70)

if results['total_trades'] > 0:
    avg_trade_return = results['total_return'] / results['total_trades']
    print(f"Average return per trade: {avg_trade_return:.2f}%")

    if 'avg_bars_held' in results:
        print(f"Average hold duration: {results['avg_bars_held']:.1f} bars")

    # Risk-adjusted metrics
    if results['sharpe_ratio'] > 1.5:
        print("✓ Excellent risk-adjusted returns (Sharpe > 1.5)")
    elif results['sharpe_ratio'] > 1.0:
        print("✓ Good risk-adjusted returns (Sharpe > 1.0)")
    else:
        print("⚠ Low risk-adjusted returns (Sharpe < 1.0)")

print("=" * 70)
print("\nBacktest complete! Adjust strategy parameters and re-run to optimize.")
