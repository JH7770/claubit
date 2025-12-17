"""
Test Force Close All Positions Feature

Tests the force close functionality for paper trading mode.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from datetime import datetime
from config.config import Config
from database.init_db import DatabaseManager
from dashboard.utils.bot_controller import BotController


def create_test_positions(db_manager):
    """Create some test positions in the database."""
    print("\n=== Creating Test Positions ===")

    conn = db_manager.connect()

    # Insert test positions
    test_positions = [
        {
            'symbol': 'BTC/USDT',
            'side': 'LONG',
            'entry_price': 50000.0,
            'amount': 0.1,
            'leverage': 10,
            'stop_loss': 49000.0,
            'take_profit': 52000.0,
            'strategy_name': 'TestStrategy',
            'opened_at': datetime.now()
        },
        {
            'symbol': 'ETH/USDT',
            'side': 'SHORT',
            'entry_price': 3000.0,
            'amount': 1.0,
            'leverage': 10,
            'stop_loss': 3100.0,
            'take_profit': 2900.0,
            'strategy_name': 'TestStrategy',
            'opened_at': datetime.now()
        }
    ]

    for pos in test_positions:
        conn.execute("""
            INSERT INTO positions
            (symbol, side, entry_price, amount, leverage, stop_loss, take_profit,
             strategy_id, strategy_name, opened_at, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'open')
        """, (
            pos['symbol'], pos['side'], pos['entry_price'], pos['amount'],
            pos['leverage'], pos['stop_loss'], pos['take_profit'],
            1, pos['strategy_name'], pos['opened_at']
        ))
        print(f"[OK] Created test position: {pos['symbol']} {pos['side']}")

    conn.commit()
    conn.close()
    print("[OK] Test positions created successfully")


def verify_positions_closed(db_manager):
    """Verify that all positions were closed."""
    print("\n=== Verifying Positions Closed ===")

    conn = db_manager.connect()

    # Check open positions
    cursor = conn.execute("SELECT COUNT(*) FROM positions WHERE status = 'open'")
    open_count = cursor.fetchone()[0]
    print(f"Open positions: {open_count}")

    # Check closed positions
    cursor = conn.execute("SELECT COUNT(*) FROM positions WHERE status = 'closed'")
    closed_count = cursor.fetchone()[0]
    print(f"Closed positions: {closed_count}")

    # Check trade history
    cursor = conn.execute("""
        SELECT COUNT(*) FROM trade_history
        WHERE strategy_name = 'TestStrategy'
    """)
    trade_history_count = cursor.fetchone()[0]
    print(f"Trade history records: {trade_history_count}")

    # Check activity log
    cursor = conn.execute("""
        SELECT COUNT(*) FROM activity_log
        WHERE event_type = 'force_close_all'
    """)
    activity_log_count = cursor.fetchone()[0]
    print(f"Activity log records: {activity_log_count}")

    conn.close()

    # Verify results
    success = (open_count == 0 and closed_count >= 2 and
               trade_history_count >= 2 and activity_log_count >= 1)

    if success:
        print("[PASS] All verifications passed!")
    else:
        print("[FAIL] Some verifications failed")

    return success


def cleanup_test_data(db_manager):
    """Clean up test data from database."""
    print("\n=== Cleaning Up Test Data ===")

    conn = db_manager.connect()

    # Delete test positions
    conn.execute("DELETE FROM positions WHERE strategy_name = 'TestStrategy'")

    # Delete test trades
    conn.execute("DELETE FROM trade_history WHERE strategy_name = 'TestStrategy'")

    # Delete test activity logs
    conn.execute("DELETE FROM activity_log WHERE event_type = 'force_close_all'")

    conn.commit()
    conn.close()

    print("[OK] Test data cleaned up")


def main():
    """Main test function."""
    print("=" * 60)
    print("FORCE CLOSE ALL POSITIONS - TEST")
    print("=" * 60)

    # Initialize
    config = Config()
    db_manager = DatabaseManager(config.DB_PATH)
    bot_controller = BotController()

    # Ensure we're in paper trading mode
    if config.is_live_mode():
        print("[ERROR] This test must be run in Paper Trading mode!")
        print("Please set TRADING_MODE=Paper in your .env file")
        return

    print(f"[OK] Running in {config.TRADING_MODE} mode")
    print(f"[OK] Database: {config.DB_PATH}")

    try:
        # Step 1: Create test positions
        create_test_positions(db_manager)

        # Step 2: Verify positions exist
        conn = db_manager.connect()
        cursor = conn.execute("SELECT COUNT(*) FROM positions WHERE status = 'open'")
        initial_open_count = cursor.fetchone()[0]
        conn.close()
        print(f"\n[OK] Initial open positions: {initial_open_count}")

        # Step 3: Execute force close
        print("\n=== Executing Force Close ===")
        result = bot_controller.force_close_all_positions(
            reason="test_force_close"
        )

        print(f"\nForce Close Result:")
        print(f"  Success: {result['success']}")
        print(f"  Mode: {result['mode']}")
        print(f"  Positions Closed: {result['positions_closed']}")
        print(f"  Total PNL: ${result['total_pnl']:,.2f}")
        print(f"  Message: {result['message']}")

        if not result['success']:
            print(f"\n[FAIL] Force close failed!")
            print(f"Details: {result['details']}")
            return

        # Step 4: Verify results
        success = verify_positions_closed(db_manager)

        if success:
            print("\n" + "=" * 60)
            print("[PASS] ALL TESTS PASSED!")
            print("=" * 60)
        else:
            print("\n" + "=" * 60)
            print("[FAIL] SOME TESTS FAILED")
            print("=" * 60)

    except Exception as e:
        print(f"\n[ERROR] Error during testing: {e}")
        import traceback
        traceback.print_exc()

    finally:
        # Clean up
        cleanup_test_data(db_manager)
        print("\n[OK] Test completed")


if __name__ == "__main__":
    main()
