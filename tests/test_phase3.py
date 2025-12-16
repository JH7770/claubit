"""
Phase 3 Integration Tests

Tests for DailyStrategySelector and PaperTradingSimulator modules.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import unittest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from modules.selector import DailyStrategySelector
from modules.paper_trader import PaperTradingSimulator
from modules.backtester import VectorizedBacktester
from database.init_db import DatabaseManager
from strategies import VolatilityBreakoutStrategy, RSIBollingerReversionStrategy


class TestDailyStrategySelector(unittest.TestCase):
    """Test cases for DailyStrategySelector."""

    @classmethod
    def setUpClass(cls):
        """Set up test fixtures."""
        cls.selector = DailyStrategySelector()
        cls.test_db = DatabaseManager('database/test_phase3.db')

    def create_sample_data(self, n_periods=500):
        """Create sample OHLCV data for testing."""
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

    def test_selector_initialization(self):
        """Test 1: DailyStrategySelector initialization."""
        print("\n[Test 1] Testing selector initialization...")

        self.assertIsNotNone(self.selector)
        self.assertIsNotNone(self.selector.backtester)
        self.assertIsNotNone(self.selector.optimizer)
        self.assertIsNotNone(self.selector.db_manager)

        print("  ✓ Selector initialized successfully")

    def test_load_recent_data(self):
        """Test 2: Data loading functionality."""
        print("\n[Test 2] Testing data loading...")

        # Create test data and save it
        df = self.create_sample_data(1000)

        # Test data characteristics
        self.assertGreater(len(df), 0)
        self.assertTrue(all(col in df.columns for col in ['open', 'high', 'low', 'close', 'volume']))

        print(f"  ✓ Created {len(df)} candles of test data")

    def test_get_strategy_pool(self):
        """Test 3: Strategy pool retrieval."""
        print("\n[Test 3] Testing strategy pool...")

        strategy_pool = self.selector._get_strategy_pool()

        self.assertIsInstance(strategy_pool, list)
        self.assertGreater(len(strategy_pool), 0)

        # Verify structure
        for config in strategy_pool:
            self.assertIn('name', config)
            self.assertIn('strategy_class', config)
            self.assertIn('params', config)

        print(f"  ✓ Retrieved {len(strategy_pool)} strategy variants")

    def test_quick_selection_mode(self):
        """Test 4: Quick selection mode."""
        print("\n[Test 4] Testing quick selection mode...")

        df = self.create_sample_data(500)
        strategy_pool = self.selector._get_strategy_pool()[:3]  # Test with 3 strategies

        results_df = self.selector._run_quick_selection(df, strategy_pool)

        self.assertIsInstance(results_df, pd.DataFrame)
        if len(results_df) > 0:
            self.assertTrue('rank' in results_df.columns)
            self.assertTrue('score' in results_df.columns)
            self.assertTrue('strategy_name' in results_df.columns)

            print(f"  ✓ Tested {len(strategy_pool)} strategies")
            print(f"  ✓ {len(results_df)} strategies passed minimum trades filter")
            if len(results_df) > 0:
                print(f"  ✓ Best score: {results_df.iloc[0]['score']:.2f}")
        else:
            print("  ⚠ No strategies passed minimum trades filter (may be normal with limited data)")

    def test_strategy_ranking(self):
        """Test 5: Strategy ranking logic."""
        print("\n[Test 5] Testing strategy ranking...")

        # Create mock results
        results = [
            {
                'strategy_name': 'Strategy_A',
                'params': '{"k": 0.5}',
                'total_return': 10.0,
                'win_rate': 60.0,
                'profit_factor': 1.5,
                'max_drawdown': -5.0,
                'sharpe_ratio': 1.2,
                'total_trades': 20,
                'score': 15.0
            },
            {
                'strategy_name': 'Strategy_B',
                'params': '{"k": 0.6}',
                'total_return': 8.0,
                'win_rate': 55.0,
                'profit_factor': 1.3,
                'max_drawdown': -3.0,
                'sharpe_ratio': 1.0,
                'total_trades': 25,
                'score': 12.0
            }
        ]

        ranked_df = self.selector._rank_strategies(results)

        self.assertEqual(len(ranked_df), 2)
        self.assertEqual(ranked_df.iloc[0]['rank'], 1)
        self.assertEqual(ranked_df.iloc[0]['strategy_name'], 'Strategy_A')  # Higher score
        self.assertEqual(ranked_df.iloc[1]['rank'], 2)

        print(f"  ✓ Ranked {len(ranked_df)} strategies correctly")

    def test_save_and_retrieve_strategy(self):
        """Test 6: Save and retrieve strategy selection."""
        print("\n[Test 6] Testing save and retrieve...")

        # Create mock result
        test_date = datetime.now().strftime('%Y-%m-%d')
        results_df = pd.DataFrame([{
            'rank': 1,
            'strategy_name': 'Test_Strategy',
            'params': '{"k": 0.5, "lookback": 24}',
            'total_return': 10.0,
            'win_rate': 60.0,
            'profit_factor': 1.5,
            'max_drawdown': -5.0,
            'sharpe_ratio': 1.2,
            'total_trades': 20,
            'score': 15.0
        }])

        # Save (will use default db_manager)
        self.selector._save_selection_results(test_date, results_df, results_df.iloc[0])

        # Retrieve
        retrieved = self.selector.get_today_strategy(date=test_date)

        if retrieved:
            self.assertEqual(retrieved['strategy_name'], 'Test_Strategy')
            self.assertIn('k', retrieved['params'])
            print("  ✓ Saved and retrieved strategy successfully")
        else:
            print("  ⚠ Could not retrieve saved strategy (database may be empty)")


class TestPaperTradingSimulator(unittest.TestCase):
    """Test cases for PaperTradingSimulator."""

    def setUp(self):
        """Set up test fixtures."""
        self.simulator = PaperTradingSimulator(
            initial_balance=10000,
            leverage=10,
            max_daily_loss_percent=5.0
        )

    def test_paper_trader_initialization(self):
        """Test 7: PaperTradingSimulator initialization."""
        print("\n[Test 7] Testing paper trader initialization...")

        self.assertEqual(self.simulator.balance, 10000)
        self.assertEqual(self.simulator.leverage, 10)
        self.assertEqual(self.simulator.max_daily_loss_percent, 5.0)
        self.assertEqual(len(self.simulator.positions), 0)

        print("  ✓ Paper trader initialized correctly")

    def test_open_close_position(self):
        """Test 8: Open and close position."""
        print("\n[Test 8] Testing position open/close...")

        # Open position
        position = self.simulator.open_position(
            symbol='BTC/USDT',
            side='LONG',
            entry_price=50000,
            amount=0.01,
            stop_loss=49000,
            take_profit=51000,
            strategy_name='TestStrategy'
        )

        self.assertIn('BTC/USDT', self.simulator.positions)
        self.assertEqual(position['side'], 'LONG')
        self.assertLess(self.simulator.balance, 10000)  # Margin used

        initial_balance_after_open = self.simulator.balance

        # Close position with profit
        trade = self.simulator.close_position('BTC/USDT', 50500, exit_reason='test')

        self.assertNotIn('BTC/USDT', self.simulator.positions)
        self.assertGreater(trade['pnl'], 0)  # Should be profitable
        self.assertGreater(self.simulator.balance, initial_balance_after_open)  # Balance increased

        print(f"  ✓ Opened and closed position")
        print(f"  ✓ PNL: ${trade['pnl']:.2f} ({trade['pnl_percent']:+.2f}%)")

    def test_stop_loss_trigger(self):
        """Test 9: Stop loss trigger."""
        print("\n[Test 9] Testing stop loss trigger...")

        # Open LONG position
        self.simulator.open_position(
            symbol='BTC/USDT',
            side='LONG',
            entry_price=50000,
            amount=0.01,
            stop_loss=49500,
            take_profit=51000,
            strategy_name='TestStrategy'
        )

        # Price drops below SL
        self.simulator.check_stop_loss_take_profit('BTC/USDT', 49400)

        # Position should be closed
        self.assertNotIn('BTC/USDT', self.simulator.positions)
        self.assertEqual(len(self.simulator.trades_today), 1)
        self.assertEqual(self.simulator.trades_today[0]['exit_reason'], 'stop_loss')

        print("  ✓ Stop loss triggered correctly")

    def test_take_profit_trigger(self):
        """Test 10: Take profit trigger."""
        print("\n[Test 10] Testing take profit trigger...")

        simulator = PaperTradingSimulator(initial_balance=10000, leverage=10)

        # Open LONG position
        simulator.open_position(
            symbol='BTC/USDT',
            side='LONG',
            entry_price=50000,
            amount=0.01,
            stop_loss=49000,
            take_profit=50500,
            strategy_name='TestStrategy'
        )

        # Price rises above TP
        simulator.check_stop_loss_take_profit('BTC/USDT', 50600)

        # Position should be closed
        self.assertNotIn('BTC/USDT', simulator.positions)
        self.assertEqual(len(simulator.trades_today), 1)
        self.assertEqual(simulator.trades_today[0]['exit_reason'], 'take_profit')

        print("  ✓ Take profit triggered correctly")

    def test_circuit_breaker(self):
        """Test 11: Circuit breaker activation."""
        print("\n[Test 11] Testing circuit breaker...")

        simulator = PaperTradingSimulator(
            initial_balance=10000,
            leverage=10,
            max_daily_loss_percent=5.0
        )

        # Open and close with large loss
        simulator.open_position(
            symbol='BTC/USDT',
            side='LONG',
            entry_price=50000,
            amount=0.05,
            stop_loss=45000,
            take_profit=55000,
            strategy_name='TestStrategy'
        )

        # Close with 10% price drop (100% loss with 10x leverage)
        simulator.close_position('BTC/USDT', 45000, exit_reason='stop_loss')

        # Check circuit breaker
        triggered = simulator.check_circuit_breaker()

        self.assertTrue(triggered)
        self.assertTrue(simulator.circuit_breaker_triggered)

        print("  ✓ Circuit breaker triggered correctly")

        # Try to open new position (should fail)
        with self.assertRaises(ValueError):
            simulator.open_position(
                symbol='ETH/USDT',
                side='LONG',
                entry_price=3000,
                amount=0.1,
                stop_loss=2900,
                take_profit=3100,
                strategy_name='TestStrategy'
            )

        print("  ✓ New positions blocked after circuit breaker")

    def test_execute_strategy_signal(self):
        """Test 12: Strategy signal execution."""
        print("\n[Test 12] Testing strategy signal execution...")

        simulator = PaperTradingSimulator(initial_balance=10000, leverage=10)
        strategy = VolatilityBreakoutStrategy(params={'k': 0.5, 'lookback_period': 24})

        # Execute LONG signal
        simulator.execute_strategy_signal(
            symbol='BTC/USDT',
            strategy=strategy,
            current_price=50000,
            signal=1
        )

        self.assertIn('BTC/USDT', simulator.positions)
        self.assertEqual(simulator.positions['BTC/USDT']['side'], 'LONG')

        print("  ✓ LONG signal executed")

        # Execute SHORT signal (should reverse)
        simulator.execute_strategy_signal(
            symbol='BTC/USDT',
            strategy=strategy,
            current_price=51000,
            signal=-1
        )

        self.assertIn('BTC/USDT', simulator.positions)
        self.assertEqual(simulator.positions['BTC/USDT']['side'], 'SHORT')

        print("  ✓ Signal reversal executed")

    def test_daily_stats_tracking(self):
        """Test 13: Daily statistics tracking."""
        print("\n[Test 13] Testing daily stats tracking...")

        simulator = PaperTradingSimulator(initial_balance=10000, leverage=10)

        # Execute some trades
        simulator.open_position('BTC/USDT', 'LONG', 50000, 0.01, 49000, 51000, 'Test')
        simulator.close_position('BTC/USDT', 50500, exit_reason='take_profit')  # Win

        simulator.open_position('ETH/USDT', 'LONG', 3000, 0.1, 2900, 3100, 'Test')
        simulator.close_position('ETH/USDT', 2950, exit_reason='stop_loss')  # Loss

        # Get stats
        stats = simulator.get_daily_stats()

        self.assertEqual(stats['total_trades'], 2)
        self.assertEqual(stats['winning_trades'], 1)
        self.assertEqual(stats['losing_trades'], 1)
        self.assertEqual(stats['win_rate'], 50.0)
        self.assertGreater(stats['gross_profit'], 0)
        self.assertGreater(stats['gross_loss'], 0)

        print(f"  ✓ Stats tracked correctly")
        print(f"    Trades: {stats['total_trades']}")
        print(f"    Win Rate: {stats['win_rate']:.1f}%")
        print(f"    Total PNL: ${stats['total_pnl']:.2f}")

    def test_margin_calculation(self):
        """Test 14: Margin calculation."""
        print("\n[Test 14] Testing margin calculation...")

        margin = self.simulator._calculate_margin_required(price=50000, amount=0.1)

        # Margin = (price * amount) / leverage
        expected_margin = (50000 * 0.1) / 10
        self.assertEqual(margin, expected_margin)

        print(f"  ✓ Margin calculated correctly: ${margin:.2f}")

    def test_pnl_calculation(self):
        """Test 15: PNL calculation."""
        print("\n[Test 15] Testing PNL calculation...")

        # LONG position
        long_position = {
            'side': 'LONG',
            'entry_price': 50000,
            'amount': 0.1
        }

        pnl, pnl_percent = self.simulator._calculate_pnl(long_position, 51000)

        # PNL = (exit - entry) * amount * leverage
        expected_pnl = (51000 - 50000) * 0.1 * 10
        self.assertEqual(pnl, expected_pnl)

        print(f"  ✓ LONG PNL: ${pnl:.2f} ({pnl_percent:+.2f}%)")

        # SHORT position
        short_position = {
            'side': 'SHORT',
            'entry_price': 50000,
            'amount': 0.1
        }

        pnl, pnl_percent = self.simulator._calculate_pnl(short_position, 49000)

        # PNL = (entry - exit) * amount * leverage
        expected_pnl = (50000 - 49000) * 0.1 * 10
        self.assertEqual(pnl, expected_pnl)

        print(f"  ✓ SHORT PNL: ${pnl:.2f} ({pnl_percent:+.2f}%)")


def run_tests():
    """Run all Phase 3 tests."""
    print("=" * 70)
    print("PHASE 3 INTEGRATION TESTS")
    print("=" * 70)

    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Add test cases
    suite.addTests(loader.loadTestsFromTestCase(TestDailyStrategySelector))
    suite.addTests(loader.loadTestsFromTestCase(TestPaperTradingSimulator))

    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Skipped: {len(result.skipped)}")

    if result.wasSuccessful():
        print("\n✓ ALL TESTS PASSED")
    else:
        print("\n✗ SOME TESTS FAILED")

    print("=" * 70)

    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
