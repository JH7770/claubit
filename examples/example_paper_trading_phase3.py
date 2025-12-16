"""
Example: Phase 3 Paper Trading Simulator

Demonstrates the PaperTradingSimulator module usage.
Shows manual position management and automated trading loops.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import time
from datetime import datetime
from modules.paper_trader import PaperTradingSimulator
from strategies import VolatilityBreakoutStrategy
from config.config import Config

print("=" * 70)
print("PHASE 3: PAPER TRADING SIMULATOR DEMONSTRATION")
print("=" * 70)

# Initialize configuration
config = Config()

# Example 1: Basic Position Management
print("\n" + "=" * 70)
print("EXAMPLE 1: MANUAL POSITION MANAGEMENT")
print("=" * 70)

try:
    # Initialize simulator
    simulator = PaperTradingSimulator(
        initial_balance=10000,
        leverage=10,
        max_daily_loss_percent=5.0,
        config=config
    )

    print(f"\n✓ Simulator initialized")
    print(f"  Initial Balance: ${simulator.get_balance():.2f}")
    print(f"  Leverage: {simulator.leverage}x")
    print(f"  Max Daily Loss: {simulator.max_daily_loss_percent}%")

    # Test opening a LONG position
    print("\n[Test 1] Opening LONG position...")
    simulator.open_position(
        symbol='BTC/USDT',
        side='LONG',
        entry_price=50000,
        amount=0.02,  # 0.02 BTC
        stop_loss=49000,
        take_profit=51000,
        strategy_name='TestStrategy'
    )

    position = simulator.get_position('BTC/USDT')
    print(f"  ✓ Position opened")
    print(f"    Entry: ${position['entry_price']:.2f}")
    print(f"    Amount: {position['amount']:.6f} BTC")
    print(f"    SL: ${position['stop_loss']:.2f}")
    print(f"    TP: ${position['take_profit']:.2f}")
    print(f"  Balance after opening: ${simulator.get_balance():.2f}")

    # Test closing position with profit
    print("\n[Test 2] Closing position with profit...")
    trade = simulator.close_position('BTC/USDT', 50500, exit_reason='manual_test')

    print(f"  ✓ Position closed")
    print(f"    Exit: ${trade['exit_price']:.2f}")
    print(f"    PNL: ${trade['pnl']:.2f} ({trade['pnl_percent']:+.2f}%)")
    print(f"    Duration: {trade['duration_seconds']:.0f}s")
    print(f"  Balance after closing: ${simulator.get_balance():.2f}")

    # Test opening a SHORT position
    print("\n[Test 3] Opening SHORT position...")
    simulator.open_position(
        symbol='ETH/USDT',
        side='SHORT',
        entry_price=3000,
        amount=0.5,  # 0.5 ETH
        stop_loss=3100,
        take_profit=2900,
        strategy_name='TestStrategy'
    )

    print(f"  ✓ SHORT position opened")
    print(f"  Balance: ${simulator.get_balance():.2f}")

    # Test closing with loss
    print("\n[Test 4] Closing position with loss...")
    trade = simulator.close_position('ETH/USDT', 3050, exit_reason='stop_loss')

    print(f"  ✓ Position closed")
    print(f"    PNL: ${trade['pnl']:.2f} ({trade['pnl_percent']:+.2f}%)")
    print(f"  Final Balance: ${simulator.get_balance():.2f}")

    # Display statistics
    stats = simulator.get_daily_stats()
    print("\n" + "=" * 70)
    print("DAILY STATISTICS")
    print("=" * 70)
    print(f"Total Trades:     {stats['total_trades']}")
    print(f"Winning Trades:   {stats['winning_trades']}")
    print(f"Losing Trades:    {stats['losing_trades']}")
    print(f"Win Rate:         {stats['win_rate']:.1f}%")
    print(f"Total PNL:        ${stats['total_pnl']:.2f} ({stats['pnl_percent']:+.2f}%)")
    print(f"Gross Profit:     ${stats['gross_profit']:.2f}")
    print(f"Gross Loss:       ${stats['gross_loss']:.2f}")
    print(f"Current Equity:   ${stats['current_equity']:.2f}")

except Exception as e:
    print(f"\n✗ Error in manual position management: {e}")
    import traceback
    traceback.print_exc()

# Example 2: Stop Loss / Take Profit Triggers
print("\n" + "=" * 70)
print("EXAMPLE 2: SL/TP TRIGGER SIMULATION")
print("=" * 70)

try:
    simulator2 = PaperTradingSimulator(
        initial_balance=10000,
        leverage=10,
        max_daily_loss_percent=5.0
    )

    # Open position
    print("\n[Test] Opening position with tight SL/TP...")
    simulator2.open_position(
        symbol='BTC/USDT',
        side='LONG',
        entry_price=50000,
        amount=0.01,
        stop_loss=49500,
        take_profit=50500,
        strategy_name='TestStrategy'
    )

    # Simulate price movements
    print("\n[Simulation] Testing price movements...")

    # Price drops but not enough for SL
    print("  Price at $49600 (above SL)...")
    simulator2.check_stop_loss_take_profit('BTC/USDT', 49600)
    if 'BTC/USDT' in simulator2.positions:
        print("    ✓ Position still open")

    # Price hits stop loss
    print("  Price at $49400 (below SL)...")
    simulator2.check_stop_loss_take_profit('BTC/USDT', 49400)
    if 'BTC/USDT' not in simulator2.positions:
        print("    ✓ Stop loss triggered - position closed")

    # Open another position
    simulator2.open_position(
        symbol='BTC/USDT',
        side='LONG',
        entry_price=50000,
        amount=0.01,
        stop_loss=49500,
        take_profit=50500,
        strategy_name='TestStrategy'
    )

    # Price hits take profit
    print("  Price at $50600 (above TP)...")
    simulator2.check_stop_loss_take_profit('BTC/USDT', 50600)
    if 'BTC/USDT' not in simulator2.positions:
        print("    ✓ Take profit triggered - position closed")

    stats2 = simulator2.get_daily_stats()
    print(f"\n  Final PNL: ${stats2['total_pnl']:.2f}")

except Exception as e:
    print(f"\n✗ Error in SL/TP simulation: {e}")
    import traceback
    traceback.print_exc()

# Example 3: Circuit Breaker Test
print("\n" + "=" * 70)
print("EXAMPLE 3: CIRCUIT BREAKER TEST")
print("=" * 70)

try:
    simulator3 = PaperTradingSimulator(
        initial_balance=10000,
        leverage=10,
        max_daily_loss_percent=5.0  # 5% max loss
    )

    print(f"\n[Test] Simulating large loss to trigger circuit breaker...")
    print(f"  Max daily loss threshold: {simulator3.max_daily_loss_percent}%")

    # Open and close with big loss
    simulator3.open_position(
        symbol='BTC/USDT',
        side='LONG',
        entry_price=50000,
        amount=0.05,
        stop_loss=45000,
        take_profit=55000,
        strategy_name='TestStrategy'
    )

    # Close with 10% price drop (= 100% loss with 10x leverage)
    trade = simulator3.close_position('BTC/USDT', 45000, exit_reason='stop_loss')

    print(f"  Position closed with PNL: ${trade['pnl']:.2f}")

    # Check circuit breaker
    if simulator3.check_circuit_breaker():
        print(f"  🚨 CIRCUIT BREAKER TRIGGERED")
        print(f"    Daily loss: ${simulator3.daily_pnl:.2f}")
        print(f"    Remaining balance: ${simulator3.get_balance():.2f}")

        # Try to open new position (should fail)
        try:
            simulator3.open_position(
                symbol='ETH/USDT',
                side='LONG',
                entry_price=3000,
                amount=0.1,
                stop_loss=2900,
                take_profit=3100,
                strategy_name='TestStrategy'
            )
        except ValueError as e:
            print(f"  ✓ New position blocked: {e}")

except Exception as e:
    print(f"\n✗ Error in circuit breaker test: {e}")
    import traceback
    traceback.print_exc()

# Example 4: Strategy Integration (Short Demo)
print("\n" + "=" * 70)
print("EXAMPLE 4: STRATEGY INTEGRATION (DEMO)")
print("=" * 70)
print("Note: Full trading loop requires live exchange connection.")
print("See main_bot.py for production implementation.")

try:
    simulator4 = PaperTradingSimulator(
        initial_balance=10000,
        leverage=10,
        max_daily_loss_percent=5.0
    )

    # Initialize strategy
    strategy = VolatilityBreakoutStrategy(params={
        'k': 0.5,
        'lookback_period': 24,
        'stop_loss_percent': 2.0,
        'take_profit_percent': 4.0
    })

    print(f"\n✓ Strategy initialized: {strategy.__class__.__name__}")

    # Simulate signal execution
    print("\n[Simulation] Executing LONG signal...")
    simulator4.execute_strategy_signal(
        symbol='BTC/USDT',
        strategy=strategy,
        current_price=50000,
        signal=1  # LONG
    )

    if 'BTC/USDT' in simulator4.positions:
        pos = simulator4.get_position('BTC/USDT')
        print(f"  ✓ Position opened via strategy")
        print(f"    Amount: {pos['amount']:.6f}")
        print(f"    SL: ${pos['stop_loss']:.2f}")
        print(f"    TP: ${pos['take_profit']:.2f}")

    # Simulate signal reversal
    print("\n[Simulation] Executing SHORT signal (reversal)...")
    simulator4.execute_strategy_signal(
        symbol='BTC/USDT',
        strategy=strategy,
        current_price=51000,
        signal=-1  # SHORT
    )

    if 'BTC/USDT' in simulator4.positions:
        pos = simulator4.get_position('BTC/USDT')
        print(f"  ✓ Position reversed to {pos['side']}")

except Exception as e:
    print(f"\n✗ Error in strategy integration: {e}")
    import traceback
    traceback.print_exc()

# Summary
print("\n" + "=" * 70)
print("SUMMARY")
print("=" * 70)
print("""
The PaperTradingSimulator module provides:

1. **Portfolio Management**
   - Virtual balance and position tracking
   - Margin calculation with leverage
   - Real-time equity calculation

2. **Position Operations**
   - Open/close positions manually
   - Automatic SL/TP triggers
   - PNL calculation with leverage

3. **Risk Management**
   - Circuit breaker for max daily loss
   - Position size limits
   - Emergency position closure

4. **Strategy Integration**
   - Execute signals from any strategy
   - Automatic position sizing
   - SL/TP calculation from strategy

5. **Performance Tracking**
   - Daily statistics (PNL, win rate, etc.)
   - Trade logging to database
   - Telegram notifications

6. **Trading Loop**
   - Continuous real-time monitoring
   - Price feed integration
   - Signal generation and execution

Usage in Production:
  1. Use with DailyStrategySelector for strategy
  2. Run via main_bot.py with scheduler
  3. Monitor via Telegram notifications
  4. Validate performance before live trading

Next Steps:
  1. Test with selected strategies
  2. Run full 3-hour trading sessions
  3. Analyze performance vs backtests
  4. Fine-tune parameters if needed
  5. Consider live trading after validation
""")

print("=" * 70)
print("Demonstration complete!")
print("=" * 70)
