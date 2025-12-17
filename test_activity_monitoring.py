"""
Test Activity Monitoring Feature

Tests the new activity monitoring functionality including:
- Database schema changes
- Bot status updates
- Activity logging
- Signal logging
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

# Fix encoding for Windows console
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

from datetime import datetime
from database.init_db import DatabaseManager


def test_database_schema():
    """Test that all new tables and columns exist."""
    print("=" * 70)
    print("TEST 1: Database Schema")
    print("=" * 70)

    db_manager = DatabaseManager()
    db_manager.connect()

    # Check bot_status columns
    cursor = db_manager.conn.execute("PRAGMA table_info(bot_status)")
    columns = {row[1] for row in cursor.fetchall()}

    required_columns = {
        'id', 'status', 'mode', 'current_balance', 'daily_pnl',
        'active_positions', 'last_heartbeat', 'updated_at',
        'current_task', 'task_start_time', 'next_task', 'next_task_time'
    }

    missing_columns = required_columns - columns
    if missing_columns:
        print(f"❌ Missing columns in bot_status: {missing_columns}")
        return False
    print("✅ bot_status table has all required columns")

    # Check activity_log table exists
    cursor = db_manager.conn.execute("""
        SELECT name FROM sqlite_master
        WHERE type='table' AND name='activity_log'
    """)
    if not cursor.fetchone():
        print("❌ activity_log table does not exist")
        return False
    print("✅ activity_log table exists")

    # Check trading_signals table exists
    cursor = db_manager.conn.execute("""
        SELECT name FROM sqlite_master
        WHERE type='table' AND name='trading_signals'
    """)
    if not cursor.fetchone():
        print("❌ trading_signals table does not exist")
        return False
    print("✅ trading_signals table exists")

    db_manager.close()
    print("\n✅ Schema test passed!\n")
    return True


def test_bot_status_updates():
    """Test bot status updates."""
    print("=" * 70)
    print("TEST 2: Bot Status Updates")
    print("=" * 70)

    db_manager = DatabaseManager()

    # Test update
    db_manager.update_bot_status({
        'status': 'running',
        'mode': 'scheduled',
        'current_task': 'data_sync',
        'task_start_time': datetime.now(),
        'current_balance': 10000.0,
        'daily_pnl': 50.0,
        'active_positions': 1,
        'next_task': 'Strategy Selection',
        'next_task_time': datetime.now()
    })

    # Wait for async write to complete
    import time
    time.sleep(1)

    # Verify
    db_manager.connect()
    cursor = db_manager.conn.execute("SELECT * FROM bot_status ORDER BY updated_at DESC LIMIT 1")
    result = cursor.fetchone()
    db_manager.close()

    if result:
        result_dict = dict(result)
        print(f"✅ Bot status updated successfully")
        print(f"   Status: {result_dict.get('status')}")
        print(f"   Current Task: {result_dict.get('current_task')}")
        print(f"   Next Task: {result_dict.get('next_task')}")
        print("\n✅ Bot status test passed!\n")
        return True
    else:
        print("❌ Bot status update failed")
        return False


def test_activity_logging():
    """Test activity logging."""
    print("=" * 70)
    print("TEST 3: Activity Logging")
    print("=" * 70)

    db_manager = DatabaseManager()

    # Log some test activities
    db_manager.log_activity(
        'task_start',
        'Test data synchronization started',
        task_name='data_sync',
        event_category='bot'
    )

    db_manager.log_activity(
        'task_end',
        'Test data synchronization completed',
        task_name='data_sync',
        severity='SUCCESS',
        event_category='bot',
        details={'symbols': ['BTC/USDT', 'ETH/USDT']}
    )

    db_manager.log_activity(
        'position_open',
        'Test position opened',
        event_category='trading',
        details={'symbol': 'BTC/USDT', 'side': 'LONG', 'entry_price': 50000}
    )

    # Wait for async writes
    import time
    time.sleep(1)

    # Verify
    activities = db_manager.get_recent_activity(limit=10)

    if activities and len(activities) >= 3:
        print(f"✅ Activity logging successful - {len(activities)} entries found")
        for activity in activities[:3]:
            print(f"   [{activity['severity']}] {activity['event_type']}: {activity['message']}")
        print("\n✅ Activity logging test passed!\n")
        return True
    else:
        print(f"❌ Activity logging failed - only {len(activities) if activities else 0} entries found")
        return False


def test_signal_logging():
    """Test trading signal logging."""
    print("=" * 70)
    print("TEST 4: Trading Signal Logging")
    print("=" * 70)

    db_manager = DatabaseManager()

    # Log some test signals
    db_manager.log_trading_signal({
        'symbol': 'BTC/USDT',
        'strategy_name': 'VolatilityBreakoutStrategy',
        'signal': 1,  # LONG
        'current_price': 50000.0,
        'indicators': {'rsi': 35, 'bb_upper': 51000, 'bb_lower': 49000},
        'position_opened': True
    })

    db_manager.log_trading_signal({
        'symbol': 'ETH/USDT',
        'strategy_name': 'RSIBollingerReversionStrategy',
        'signal': -1,  # SHORT
        'current_price': 3000.0,
        'indicators': {'rsi': 75, 'bb_upper': 3100, 'bb_lower': 2900},
        'position_opened': False
    })

    # Wait for async writes
    import time
    time.sleep(1)

    # Verify
    signals = db_manager.get_latest_signals(limit=10)

    if signals and len(signals) >= 2:
        print(f"✅ Signal logging successful - {len(signals)} signals found")
        for signal in signals[:2]:
            signal_type = '🟢 LONG' if signal['signal'] == 1 else '🔴 SHORT' if signal['signal'] == -1 else '⚪ HOLD'
            print(f"   {signal_type} {signal['symbol']} @ ${signal['current_price']:.2f}")
            print(f"      Strategy: {signal['strategy_name']}")
        print("\n✅ Signal logging test passed!\n")
        return True
    else:
        print(f"❌ Signal logging failed - only {len(signals) if signals else 0} signals found")
        return False


def main():
    """Run all tests."""
    print("\n" + "=" * 70)
    print("ACTIVITY MONITORING TESTS")
    print("=" * 70 + "\n")

    results = []

    results.append(("Schema", test_database_schema()))
    results.append(("Bot Status", test_bot_status_updates()))
    results.append(("Activity Logging", test_activity_logging()))
    results.append(("Signal Logging", test_signal_logging()))

    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)

    for test_name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{test_name}: {status}")

    all_passed = all(result[1] for result in results)
    print("\n" + "=" * 70)
    if all_passed:
        print("✅ ALL TESTS PASSED!")
    else:
        print("❌ SOME TESTS FAILED")
    print("=" * 70 + "\n")

    return all_passed


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
