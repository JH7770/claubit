"""
Main Trading Bot Orchestrator

Coordinates the full daily workflow:
- 20:30-21:30 KST: Data synchronization
- 21:30-22:20 KST: Daily strategy selection
- 22:30-01:00 KST: Trading session (paper or live)
- 01:00+ KST: Position cleanup and daily report

Can run as scheduled bot or one-time execution.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from datetime import datetime
import logging
from typing import Optional
import json

from apscheduler.schedulers.blocking import BlockingScheduler
from pytz import timezone

from config.config import Config
from modules.selector import DailyStrategySelector
from modules.paper_trader import PaperTradingSimulator
from modules.collector import DataCollector
from modules.executor import OrderExecutor
from modules.notifier import TelegramNotifier
from database.init_db import DatabaseManager

# Import strategies for loading
from strategies import (
    VolatilityBreakoutStrategy,
    RSIBollingerReversionStrategy,
    VolumeWeightedMACrossStrategy
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TradingBot:
    """
    Main trading bot orchestrator.

    Coordinates daily workflow:
    1. Data sync
    2. Strategy selection
    3. Trading session
    4. Cleanup and reporting
    """

    def __init__(self, config: Optional[Config] = None):
        """
        Initialize trading bot.

        Args:
            config: Configuration instance
        """
        self.config = config or Config()

        # Initialize core modules
        self.db_manager = DatabaseManager(self.config.DB_PATH)
        self.collector = DataCollector(self.config.EXCHANGE_NAME)
        self.notifier = TelegramNotifier(
            bot_token=self.config.TELEGRAM_BOT_TOKEN,
            chat_id=self.config.TELEGRAM_CHAT_ID
        ) if self.config.TELEGRAM_BOT_TOKEN and self.config.TELEGRAM_CHAT_ID else None

        # Initialize selector
        self.selector = DailyStrategySelector(
            db_manager=self.db_manager,
            collector=self.collector,
            notifier=self.notifier,
            config=self.config
        )

        # Initialize trading executor (paper or live)
        if self.config.is_live_mode():
            logger.warning("⚠ LIVE TRADING MODE ENABLED ⚠")
            self.executor = OrderExecutor(
                exchange_name=self.config.EXCHANGE_NAME,
                api_key=self.config.API_KEY,
                api_secret=self.config.API_SECRET,
                leverage=self.config.LEVERAGE
            )
        else:
            logger.info("Paper trading mode enabled")
            self.executor = PaperTradingSimulator(
                initial_balance=self.config.PAPER_TRADING_INITIAL_BALANCE,
                leverage=self.config.LEVERAGE,
                max_daily_loss_percent=self.config.MAX_DAILY_LOSS_PERCENT,
                db_manager=self.db_manager,
                collector=self.collector,
                notifier=self.notifier,
                config=self.config
            )

        # Strategy class mapping
        self.strategy_class_map = {
            'Volatility_Breakout': VolatilityBreakoutStrategy,
            'Volatility_Breakout_k0.4': VolatilityBreakoutStrategy,
            'Volatility_Breakout_k0.5': VolatilityBreakoutStrategy,
            'Volatility_Breakout_k0.6': VolatilityBreakoutStrategy,
            'RSI_Bollinger_Reversion': RSIBollingerReversionStrategy,
            'RSI_Bollinger_Standard': RSIBollingerReversionStrategy,
            'RSI_Bollinger_Aggressive': RSIBollingerReversionStrategy,
            'RSI_Bollinger_Conservative': RSIBollingerReversionStrategy,
            'Volume_MA_Cross': VolumeWeightedMACrossStrategy,
            'Volume_MA_Cross_Fast': VolumeWeightedMACrossStrategy,
            'Volume_MA_Cross_Standard': VolumeWeightedMACrossStrategy,
            'Volume_MA_Cross_Slow': VolumeWeightedMACrossStrategy,
        }

        # State
        self.today_strategy = None
        self.today_strategy_instance = None

        logger.info("TradingBot initialized")
        logger.info(f"  Mode: {'LIVE' if self.config.is_live_mode() else 'PAPER'}")
        logger.info(f"  Exchange: {self.config.EXCHANGE_NAME}")
        logger.info(f"  Primary Symbol: {self.config.PRIMARY_SYMBOL}")
        logger.info(f"  Leverage: {self.config.LEVERAGE}x")

    def run_data_sync(self):
        """
        20:30-21:30 KST: Synchronize historical data.

        Updates parquet files for primary and secondary symbols.
        """
        logger.info("="*70)
        logger.info("TASK 1: Data Synchronization")
        logger.info("="*70)

        try:
            symbols = [self.config.PRIMARY_SYMBOL]
            if self.config.SECONDARY_SYMBOL:
                symbols.append(self.config.SECONDARY_SYMBOL)

            for symbol in symbols:
                logger.info(f"Updating data for {symbol}...")

                # Download 7 days of 1-minute data
                df = self.collector.download_historical_data(
                    symbol=symbol,
                    timeframe='1m',
                    days=7
                )

                if df is not None:
                    logger.info(f"  ✓ Downloaded {len(df)} candles for {symbol}")
                else:
                    logger.error(f"  ✗ Failed to download data for {symbol}")

            logger.info("Data synchronization completed")

            if self.notifier:
                self.notifier.send_message("✓ Data synchronization completed successfully")

        except Exception as e:
            logger.error(f"Error in data sync: {e}", exc_info=True)
            if self.notifier:
                self.notifier.send_error(
                    error_type="DATA_SYNC_ERROR",
                    error_message=str(e)
                )

    def run_strategy_selection(self):
        """
        21:30-22:20 KST: Select best strategy for today.

        Backtests all strategies and selects the champion.
        """
        logger.info("="*70)
        logger.info("TASK 2: Daily Strategy Selection")
        logger.info("="*70)

        try:
            # Run selection
            result = self.selector.select_daily_strategy(
                symbols=[self.config.PRIMARY_SYMBOL],
                timeframe='1m',
                lookback_days=self.config.SELECTOR_LOOKBACK_DAYS,
                mode=self.config.SELECTOR_MODE
            )

            # Store selected strategy
            self.today_strategy = result

            # Load strategy instance
            strategy_name = result['selected_strategy']
            strategy_params = result['selected_params']

            # Get base strategy name (remove variant suffix)
            base_name = strategy_name.split('_Optimized')[0]

            if base_name in self.strategy_class_map:
                strategy_class = self.strategy_class_map[base_name]
                self.today_strategy_instance = strategy_class(params=strategy_params)
                logger.info(f"✓ Loaded strategy instance: {strategy_class.__name__}")
            else:
                logger.warning(f"Unknown strategy: {base_name}, using default")
                self.today_strategy_instance = VolatilityBreakoutStrategy(params=strategy_params)

            logger.info("="*70)
            logger.info(f"✓ TODAY'S CHAMPION: {result['selected_strategy']}")
            logger.info(f"  Score: {result['score']:.2f}")
            logger.info(f"  Backtest Return: {result['backtest_results']['total_return']:.2f}%")
            logger.info(f"  Win Rate: {result['backtest_results']['win_rate']:.2f}%")
            logger.info("="*70)

        except Exception as e:
            logger.error(f"Error in strategy selection: {e}", exc_info=True)
            if self.notifier:
                self.notifier.send_error(
                    error_type="STRATEGY_SELECTION_ERROR",
                    error_message=str(e)
                )

            # Load default strategy as fallback
            logger.warning("Loading default fallback strategy")
            self.today_strategy_instance = VolatilityBreakoutStrategy()

    def run_trading_session(self):
        """
        22:30-01:00 KST: Execute trading session.

        Uses selected strategy with paper trader or live executor.
        """
        logger.info("="*70)
        logger.info("TASK 3: Trading Session")
        logger.info("="*70)

        if self.today_strategy_instance is None:
            logger.error("No strategy selected! Aborting trading session.")
            return

        try:
            if isinstance(self.executor, PaperTradingSimulator):
                # Paper trading mode
                logger.info("Starting PAPER TRADING session...")

                self.executor.run_trading_loop(
                    symbol=self.config.PRIMARY_SYMBOL,
                    strategy=self.today_strategy_instance,
                    interval_seconds=self.config.PAPER_TRADING_POLL_INTERVAL,
                    duration_hours=self.config.PAPER_TRADING_SESSION_DURATION
                )

                logger.info("Paper trading session completed")

            else:
                # Live trading mode
                logger.warning("⚠ LIVE TRADING SESSION NOT YET IMPLEMENTED ⚠")
                logger.warning("This would execute real trades on the exchange")
                logger.warning("Implementation pending for safety reasons")

                # TODO: Implement live trading session
                # This should:
                # 1. Set leverage on exchange
                # 2. Monitor prices in real-time
                # 3. Execute strategy signals as real orders
                # 4. Manage positions with SL/TP
                # 5. Report results

        except Exception as e:
            logger.error(f"Error in trading session: {e}", exc_info=True)
            if self.notifier:
                self.notifier.send_error(
                    error_type="TRADING_SESSION_ERROR",
                    error_message=str(e)
                )

    def run_session_cleanup(self):
        """
        01:00+ KST: Close all positions and generate daily report.
        """
        logger.info("="*70)
        logger.info("TASK 4: Session Cleanup")
        logger.info("="*70)

        try:
            if isinstance(self.executor, PaperTradingSimulator):
                # Close any remaining positions
                self.executor.force_close_all_positions(reason="session_end")

                # Save daily summary
                today = datetime.now().strftime('%Y-%m-%d')
                self.executor.save_daily_summary(today)

                # Get and display stats
                stats = self.executor.get_daily_stats()

                logger.info("Daily Performance Summary:")
                logger.info(f"  Total Trades: {stats['total_trades']}")
                logger.info(f"  Win Rate: {stats['win_rate']:.1f}%")
                logger.info(f"  Total PNL: ${stats['total_pnl']:.2f} ({stats['pnl_percent']:+.2f}%)")
                logger.info(f"  Final Balance: ${stats['current_balance']:.2f}")

            logger.info("Session cleanup completed")

        except Exception as e:
            logger.error(f"Error in session cleanup: {e}", exc_info=True)

    def send_heartbeat(self):
        """Send hourly heartbeat to confirm bot is running."""
        if self.notifier:
            try:
                self.notifier.send_heartbeat()
                logger.debug("Heartbeat sent")
            except Exception as e:
                logger.error(f"Error sending heartbeat: {e}")

    def run_full_cycle_once(self):
        """
        Run full daily cycle once (for testing).

        Executes all 4 tasks sequentially.
        """
        logger.info("Starting full daily cycle (one-time execution)")

        self.run_data_sync()
        self.run_strategy_selection()
        self.run_trading_session()
        self.run_session_cleanup()

        logger.info("Full daily cycle completed")

    def start_scheduled_bot(self):
        """
        Start bot with APScheduler.

        Schedules all tasks according to daily workflow.
        """
        logger.info("="*70)
        logger.info("STARTING SCHEDULED TRADING BOT")
        logger.info("="*70)

        kst = timezone('Asia/Seoul')
        scheduler = BlockingScheduler(timezone=kst)

        # Data synchronization (20:30 KST)
        scheduler.add_job(
            self.run_data_sync,
            trigger='cron',
            hour=20,
            minute=30,
            id='data_sync',
            name='Data Synchronization'
        )
        logger.info("Scheduled: Data Sync at 20:30 KST")

        # Strategy selection (21:30 KST)
        scheduler.add_job(
            self.run_strategy_selection,
            trigger='cron',
            hour=21,
            minute=30,
            id='strategy_selection',
            name='Strategy Selection'
        )
        logger.info("Scheduled: Strategy Selection at 21:30 KST")

        # Trading session (22:30 KST)
        scheduler.add_job(
            self.run_trading_session,
            trigger='cron',
            hour=22,
            minute=30,
            id='trading_session',
            name='Trading Session'
        )
        logger.info("Scheduled: Trading Session at 22:30 KST")

        # Session cleanup (01:00 KST)
        scheduler.add_job(
            self.run_session_cleanup,
            trigger='cron',
            hour=1,
            minute=0,
            id='cleanup',
            name='Session Cleanup'
        )
        logger.info("Scheduled: Cleanup at 01:00 KST")

        # Hourly heartbeat
        scheduler.add_job(
            self.send_heartbeat,
            trigger='interval',
            hours=1,
            id='heartbeat',
            name='Heartbeat'
        )
        logger.info("Scheduled: Heartbeat every 1 hour")

        logger.info("="*70)
        logger.info("Bot is now running. Press Ctrl+C to stop.")
        logger.info("="*70)

        try:
            scheduler.start()
        except (KeyboardInterrupt, SystemExit):
            logger.info("Shutting down gracefully...")
            scheduler.shutdown()
            logger.info("Bot stopped")


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description='US Market Volatility Hunter Bot')
    parser.add_argument(
        '--mode',
        choices=['scheduled', 'once', 'sync', 'select', 'trade', 'cleanup'],
        default='once',
        help='Execution mode (default: once)'
    )

    args = parser.parse_args()

    # Initialize bot
    bot = TradingBot()

    # Execute based on mode
    if args.mode == 'scheduled':
        bot.start_scheduled_bot()
    elif args.mode == 'once':
        bot.run_full_cycle_once()
    elif args.mode == 'sync':
        bot.run_data_sync()
    elif args.mode == 'select':
        bot.run_strategy_selection()
    elif args.mode == 'trade':
        bot.run_trading_session()
    elif args.mode == 'cleanup':
        bot.run_session_cleanup()


if __name__ == "__main__":
    main()
