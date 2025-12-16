"""
Example: Phase 3 Daily Strategy Selection

Demonstrates the automated DailyStrategySelector module usage.
Shows both quick and comprehensive selection modes.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from modules.selector import DailyStrategySelector
from config.config import Config

print("=" * 70)
print("PHASE 3: DAILY STRATEGY SELECTOR DEMONSTRATION")
print("=" * 70)

# Initialize configuration
config = Config()

# Initialize selector
print("\n[1] Initializing DailyStrategySelector...")
selector = DailyStrategySelector(config=config)
print("  ✓ Selector initialized")

# Example 1: Quick Selection Mode
print("\n" + "=" * 70)
print("EXAMPLE 1: QUICK SELECTION MODE")
print("=" * 70)
print("Testing predefined parameter sets (fast, ~5-10 min)")

try:
    result = selector.select_daily_strategy(
        symbols=['BTC/USDT'],
        timeframe='1h',  # Using hourly for faster demo
        lookback_days=7,
        mode='quick'
    )

    print("\n✓ SELECTION COMPLETED")
    print("=" * 70)
    print(f"Selected Strategy: {result['selected_strategy']}")
    print(f"Composite Score:   {result['score']:.2f}")
    print(f"\nBacktest Performance (Last 7 Days):")
    print(f"  Total Return:    {result['backtest_results']['total_return']:.2f}%")
    print(f"  Win Rate:        {result['backtest_results']['win_rate']:.2f}%")
    print(f"  Profit Factor:   {result['backtest_results']['profit_factor']:.2f}")
    print(f"  Max Drawdown:    {result['backtest_results']['max_drawdown']:.2f}%")
    print(f"  Sharpe Ratio:    {result['backtest_results']['sharpe_ratio']:.2f}")
    print(f"  Total Trades:    {result['backtest_results']['total_trades']}")

    print(f"\nSelected Parameters:")
    for param, value in result['selected_params'].items():
        print(f"  {param}: {value}")

    print("\n" + "=" * 70)
    print("TOP 5 STRATEGIES")
    print("=" * 70)
    rank_table = result['rank_table']
    for i in range(min(5, len(rank_table))):
        row = rank_table.iloc[i]
        print(f"{i+1}. {row['strategy_name']}")
        print(f"   Score: {row['score']:.2f} | Return: {row['total_return']:.2f}% | Win Rate: {row['win_rate']:.2f}%")

except Exception as e:
    print(f"\n✗ Error in quick selection: {e}")
    import traceback
    traceback.print_exc()

# Example 2: Retrieving Today's Strategy
print("\n" + "=" * 70)
print("EXAMPLE 2: RETRIEVE TODAY'S SELECTED STRATEGY")
print("=" * 70)

try:
    from datetime import datetime
    today = datetime.now().strftime('%Y-%m-%d')

    strategy = selector.get_today_strategy(date=today)

    if strategy:
        print(f"\n✓ Strategy for {today}:")
        print(f"  Name: {strategy['strategy_name']}")
        print(f"  Score: {strategy['score']:.2f}")
        print(f"  Parameters: {strategy['params']}")
        print(f"\n  This strategy would be loaded into the trading bot.")
    else:
        print(f"\n  No strategy selected for {today}")

except Exception as e:
    print(f"\n✗ Error retrieving strategy: {e}")

# Example 3: Comprehensive Mode (commented out - takes longer)
print("\n" + "=" * 70)
print("EXAMPLE 3: COMPREHENSIVE SELECTION MODE (DISABLED)")
print("=" * 70)
print("This mode uses Optuna optimization and takes 20-30 minutes.")
print("To enable, uncomment the code below and run separately.")

"""
# Uncomment to test comprehensive mode:
print("\nRunning comprehensive selection with Optuna optimization...")
try:
    result_comprehensive = selector.select_daily_strategy(
        symbols=['BTC/USDT'],
        timeframe='1h',
        lookback_days=7,
        mode='comprehensive'  # Uses Optuna with 50 trials per strategy
    )

    print(f"\n✓ Optimized Strategy: {result_comprehensive['selected_strategy']}")
    print(f"  Score: {result_comprehensive['score']:.2f}")
    print(f"  Optimized Parameters: {result_comprehensive['selected_params']}")

except Exception as e:
    print(f"\n✗ Error in comprehensive selection: {e}")
"""

# Summary
print("\n" + "=" * 70)
print("SUMMARY")
print("=" * 70)
print("""
The DailyStrategySelector module provides:

1. **Quick Mode** (5-10 min)
   - Tests predefined parameter sets for all strategies
   - Fast execution for daily pre-market selection
   - Suitable for automated daily workflow

2. **Comprehensive Mode** (20-30 min)
   - Uses Optuna Bayesian optimization
   - Finds optimal parameters for each strategy
   - More thorough but slower
   - Recommended for weekly parameter tuning

3. **Database Integration**
   - All results saved to backtest_results table
   - Ranked by composite score
   - Retrievable for later use

4. **Telegram Notifications**
   - Sends selection announcement
   - Includes performance metrics
   - Shows top alternatives

Next Steps:
  1. Integrate with main_bot.py for scheduled execution
  2. Test with live market data
  3. Validate selected strategies in paper trading
  4. Fine-tune selection criteria if needed
""")

print("=" * 70)
print("Demonstration complete!")
print("=" * 70)
