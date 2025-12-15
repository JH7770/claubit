"""
Example: Optimizing strategy parameters using Optuna

This script demonstrates how to:
1. Define parameter search space
2. Run Bayesian optimization
3. Analyze optimization results
4. Test best parameters
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
import numpy as np
from modules import VectorizedBacktester, StrategyOptimizer
from modules.optimizer import VOLATILITY_BREAKOUT_SPACE
from strategies import VolatilityBreakoutStrategy

print("=" * 70)
print("OPTIMIZATION EXAMPLE: Volatility Breakout Strategy")
print("=" * 70)

# 1. Load data
print("\n[Step 1] Loading historical data...")

def create_sample_data(n_periods=1500):
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
print(f"Loaded {len(df)} candles for optimization")

# 2. Define parameter search space
print("\n[Step 2] Defining parameter search space...")
param_space = {
    'k': {
        'type': 'float',
        'low': 0.3,
        'high': 0.8,
        'step': 0.1
    },
    'lookback_period': {
        'type': 'categorical',
        'choices': [12, 24, 48]
    },
    'stop_loss_percent': {
        'type': 'float',
        'low': 1.5,
        'high': 3.0,
        'step': 0.5
    },
    'take_profit_percent': {
        'type': 'float',
        'low': 3.0,
        'high': 6.0,
        'step': 1.0
    }
}

print("Parameter space:")
for param, config in param_space.items():
    print(f"  {param}: {config}")

# 3. Initialize optimizer
print("\n[Step 3] Initializing optimizer...")
backtester = VectorizedBacktester(initial_balance=10000, leverage=10)
optimizer = StrategyOptimizer(backtester)

# 4. Run optimization
print("\n[Step 4] Running Bayesian optimization...")
print("This may take a few minutes...")

best_params, trials_df = optimizer.optimize_strategy(
    strategy_class=VolatilityBreakoutStrategy,
    df=df,
    param_space=param_space,
    n_trials=30,  # Increase for better results (e.g., 100)
    objective_metric='score',
    timeout=300,  # 5 minutes timeout
    min_trades=10,
    max_drawdown=30.0,
    show_progress=True
)

# 5. Display results
print("\n" + "=" * 70)
print("OPTIMIZATION RESULTS")
print("=" * 70)
print("\nBest Parameters Found:")
for param, value in best_params.items():
    print(f"  {param}: {value}")

print("\nTop 5 Parameter Combinations:")
print(trials_df.head().to_string(index=False))

# 6. Test best parameters with backtest
print("\n[Step 5] Testing best parameters with full backtest...")
best_strategy = VolatilityBreakoutStrategy(params=best_params)
best_results = backtester.run_backtest(df, best_strategy)

print("\nBacktest Results with Optimized Parameters:")
print(f"  Total Return:    {best_results['total_return']:.2f}%")
print(f"  Win Rate:        {best_results['win_rate']:.2f}%")
print(f"  Profit Factor:   {best_results['profit_factor']:.2f}")
print(f"  Max Drawdown:    {best_results['max_drawdown']:.2f}%")
print(f"  Sharpe Ratio:    {best_results['sharpe_ratio']:.2f}")
print(f"  Total Trades:    {best_results['total_trades']}")
print(f"  Composite Score: {best_results['score']:.2f}")

# 7. Compare with default parameters
print("\n[Step 6] Comparing with default parameters...")
default_strategy = VolatilityBreakoutStrategy()  # Default params
default_results = backtester.run_backtest(df, default_strategy)

print("\nPerformance Comparison:")
print(f"{'Metric':<20} {'Default':<15} {'Optimized':<15} {'Improvement'}")
print("-" * 70)

metrics_to_compare = [
    ('Total Return %', 'total_return'),
    ('Win Rate %', 'win_rate'),
    ('Profit Factor', 'profit_factor'),
    ('Max Drawdown %', 'max_drawdown'),
    ('Total Trades', 'total_trades'),
    ('Composite Score', 'score')
]

for label, key in metrics_to_compare:
    default_val = default_results[key]
    optimized_val = best_results[key]

    # Calculate improvement (inverted for drawdown)
    if 'drawdown' in key.lower():
        improvement = ((default_val - optimized_val) / default_val * 100) if default_val != 0 else 0
    else:
        improvement = ((optimized_val - default_val) / default_val * 100) if default_val != 0 else 0

    print(f"{label:<20} {default_val:<15.2f} {optimized_val:<15.2f} {improvement:+.1f}%")

print("=" * 70)
print("\nOptimization complete!")
print("Use these optimized parameters in your live trading strategy.")
