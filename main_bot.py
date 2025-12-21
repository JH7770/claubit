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
import signal
import os
import threading

from apscheduler.schedulers.blocking import BlockingScheduler
from pytz import timezone

from config.config import Config
from config.logging_config import setup_logging, get_logger
from modules.selector import DailyStrategySelector
from modules.paper_trader import PaperTradingSimulator
from modules.live_trader import LiveTradingManager
from modules.collector import DataCollector
from modules.executor import OrderExecutor
from modules.notifier import TelegramNotifier
from database.init_db import DatabaseManager

# Import strategies for loading
from strategies import (
    VolatilityBreakoutStrategy,
    RSIBollingerReversionStrategy,
    VolumeWeightedMACrossStrategy,
    DynamicScalpingGridStrategy
)

# Initialize centralized logging
setup_logging()
logger = get_logger(__name__)


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

        # Shutdown flag
        self.should_stop = False

        # Scheduler reference (for scheduled mode)
        self.scheduler = None

        # Register signal handlers for graceful shutdown
        signal.signal(signal.SIGTERM, self._handle_shutdown)
        signal.signal(signal.SIGINT, self._handle_shutdown)

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
                testnet=False,
                notifier=self.notifier,
                leverage=self.config.LEVERAGE,
                current_strategy='Unknown'
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
            'Scalping_Grid': DynamicScalpingGridStrategy,
            'Scalping_Grid_Conservative': DynamicScalpingGridStrategy,
            'Scalping_Grid_Aggressive': DynamicScalpingGridStrategy,
        }

        # State
        self.today_strategy = None
        self.today_strategy_instance = None

        # Initialize start time for heartbeat
        self.start_time = datetime.now()

        # Task overlap prevention lock
        self._task_lock = threading.Lock()

        logger.info("TradingBot initialized")
        logger.info(f"  Mode: {'LIVE' if self.config.is_live_mode() else 'PAPER'}")
        logger.info(f"  Exchange: {self.config.EXCHANGE_NAME}")
        logger.info(f"  Primary Symbol: {self.config.PRIMARY_SYMBOL}")
        logger.info(f"  Leverage: {self.config.LEVERAGE}x")

    def _handle_shutdown(self, signum, frame):
        """
        Handle shutdown signal gracefully.

        Args:
            signum: Signal number
            frame: Current stack frame
        """
        logger.info(f"Shutdown signal received (signal {signum}), stopping bot gracefully...")
        self.should_stop = True

        # Close all open positions
        try:
            if hasattr(self.executor, 'force_close_all_positions'):
                logger.info("Closing all open positions...")
                self.executor.force_close_all_positions(reason="shutdown")
        except Exception as e:
            logger.error(f"Error closing positions during shutdown: {e}")

        # Shutdown database manager
        try:
            self.db_manager.shutdown()
        except Exception as e:
            logger.error(f"Error shutting down database manager: {e}")

    def _update_task_status(self, task: str, status: str):
        """
        Update bot_status with current task.

        Args:
            task: 'idle', 'data_sync', 'strategy_selection', 'trading', 'cleanup'
            status: 'started', 'completed', 'initialized'
        """
        try:
            next_job = self._get_next_scheduled_job()

            # Get current balance and positions from executor
            current_balance = 0.0
            daily_pnl = 0.0
            active_positions = 0

            if hasattr(self.executor, 'balance'):
                current_balance = self.executor.balance
            if hasattr(self.executor, 'daily_pnl'):
                daily_pnl = self.executor.daily_pnl
            if hasattr(self.executor, 'positions'):
                active_positions = len(self.executor.positions)

            self.db_manager.update_bot_status({
                'status': 'running' if status != 'stopped' else 'stopped',
                'mode': 'scheduled' if self.scheduler else 'once',
                'current_task': task,
                'task_start_time': datetime.now() if status == 'started' else None,
                'current_balance': current_balance,
                'daily_pnl': daily_pnl,
                'active_positions': active_positions,
                'next_task': next_job['name'] if next_job else None,
                'next_task_time': next_job['next_run_time'] if next_job else None
            })
        except Exception as e:
            logger.warning(f"Failed to update task status: {e}")

    def _log_activity(self, event_type: str, message: str, **kwargs):
        """
        Log activity event.

        Args:
            event_type: 'task_start', 'task_end', 'signal', 'position_open', etc.
            message: Human-readable message
            kwargs: Additional fields (task_name, details, severity, event_category)
        """
        try:
            self.db_manager.log_activity(
                event_type,
                message,
                event_category=kwargs.get('event_category', 'bot'),
                **kwargs
            )
        except Exception as e:
            logger.warning(f"Failed to log activity: {e}")

    def _get_next_scheduled_job(self):
        """
        Get next scheduled job from APScheduler.

        Returns:
            Dict with job info or None if no scheduler/jobs
        """
        if not self.scheduler:
            return None

        try:
            jobs = self.scheduler.get_jobs()
            if not jobs:
                return None

            # Sort by next_run_time
            jobs_sorted = sorted(
                [j for j in jobs if j.next_run_time],
                key=lambda j: j.next_run_time
            )

            if not jobs_sorted:
                return None

            next_job = jobs_sorted[0]
            return {
                'name': next_job.name,
                'id': next_job.id,
                'next_run_time': next_job.next_run_time
            }
        except Exception as e:
            logger.warning(f"Failed to get next scheduled job: {e}")
            return None

    def run_data_sync(self):
        """
        20:30-21:30 KST: Synchronize historical data.

        Updates parquet files for primary and secondary symbols.
        """
        # Acquire task lock to prevent overlapping tasks
        if not self._task_lock.acquire(blocking=False):
            logger.warning("Data sync already running, skipping...")
            return

        self._update_task_status('data_sync', 'started')
        self._log_activity('task_start', 'Starting data synchronization', task_name='data_sync')

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

            self._update_task_status('idle', 'completed')
            self._log_activity('task_end', 'Data synchronization completed',
                              task_name='data_sync', severity='SUCCESS')

        except Exception as e:
            logger.error(f"Error in data sync: {e}", exc_info=True)
            self._log_activity('task_end', f'Data sync failed: {str(e)}',
                              task_name='data_sync', severity='ERROR')
            if self.notifier:
                self.notifier.send_error_alert(
                    error_type="DATA_SYNC_ERROR",
                    error_message=str(e)
                )
            raise
        finally:
            # Release lock
            self._task_lock.release()

    def load_previous_strategy(self):
        """
        Load the most recent selected strategy from database.

        Returns:
            bool: True if strategy was loaded successfully, False otherwise
        """
        logger.info("="*70)
        logger.info("Loading Previous Strategy")
        logger.info("="*70)

        conn = None
        try:
            # Get today's date
            today = datetime.now().strftime('%Y-%m-%d')

            # Query database for today's strategy first, then fall back to most recent
            conn = self.db_manager.get_connection()
            cursor = conn.cursor()

            # Try to get today's strategy
            cursor.execute("""
                SELECT strategy_name, params, score, total_return, win_rate,
                       max_drawdown, sharpe_ratio, profit_factor, total_trades
                FROM backtest_results
                WHERE date = ? AND rank = 1
                ORDER BY created_at DESC
                LIMIT 1
            """, (today,))

            result = cursor.fetchone()

            # If no strategy for today, get the most recent one
            if not result:
                logger.info("No strategy found for today, loading most recent strategy...")
                cursor.execute("""
                    SELECT strategy_name, params, score, total_return, win_rate,
                           max_drawdown, sharpe_ratio, profit_factor, total_trades, date
                    FROM backtest_results
                    WHERE rank = 1
                    ORDER BY date DESC, created_at DESC
                    LIMIT 1
                """)
                result = cursor.fetchone()

            if not result:
                logger.error("No previous strategy found in database")
                return False

            # Parse result
            strategy_name = result[0]
            params_json = result[1]
            strategy_params = json.loads(params_json) if params_json else {}

            # Store selected strategy
            self.today_strategy = {
                'selected_strategy': strategy_name,
                'selected_params': strategy_params,
                'score': result[2],
                'backtest_results': {
                    'total_return': result[3],
                    'win_rate': result[4],
                    'max_drawdown': result[5],
                    'sharpe_ratio': result[6],
                    'profit_factor': result[7],
                    'total_trades': result[8]
                },
                'timeframe': '1m'  # Default timeframe
            }

            # Load strategy instance
            base_name = strategy_name.split('_Optimized')[0]

            if base_name in self.strategy_class_map:
                strategy_class = self.strategy_class_map[base_name]
                self.today_strategy_instance = strategy_class(params=strategy_params)
                logger.info(f"✓ Loaded previous strategy: {strategy_class.__name__}")
                # Update executor strategy name if in live mode
                if self.config.is_live_mode() and hasattr(self.executor, 'current_strategy'):
                    self.executor.current_strategy = strategy_name
            else:
                logger.warning(f"Unknown strategy: {base_name}, using default")
                self.today_strategy_instance = VolatilityBreakoutStrategy(params=strategy_params)
                # Update executor strategy name if in live mode
                if self.config.is_live_mode() and hasattr(self.executor, 'current_strategy'):
                    self.executor.current_strategy = 'Volatility_Breakout'

            logger.info("="*70)
            logger.info(f"✓ LOADED PREVIOUS STRATEGY: {strategy_name}")
            logger.info(f"  Score: {result[2]:.2f}")
            logger.info(f"  Backtest Return: {result[3]:.2f}%")
            logger.info(f"  Win Rate: {result[4]:.2f}%")
            if len(result) > 9:  # Has date field
                logger.info(f"  Date: {result[9]}")
            logger.info("="*70)

            self._log_activity('strategy_load', f'Loaded previous strategy: {strategy_name}',
                              task_name='strategy_selection', severity='INFO',
                              details={'strategy': strategy_name,
                                      'score': result[2],
                                      'return': result[3]})

            return True

        except Exception as e:
            logger.error(f"Error loading previous strategy: {e}", exc_info=True)
            self._log_activity('strategy_load', f'Failed to load previous strategy: {str(e)}',
                              task_name='strategy_selection', severity='ERROR')
            return False
        finally:
            if conn:
                conn.close()

    def run_strategy_selection(self):
        """
        21:30-22:20 KST: Select best strategy for today.

        Backtests all strategies and selects the champion.
        """
        # Acquire task lock to prevent overlapping tasks
        if not self._task_lock.acquire(blocking=False):
            logger.warning("Strategy selection already running, skipping...")
            return

        self._update_task_status('strategy_selection', 'started')
        self._log_activity('task_start', 'Starting strategy selection', task_name='strategy_selection')

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
                # Update executor strategy name if in live mode
                if self.config.is_live_mode() and hasattr(self.executor, 'current_strategy'):
                    self.executor.current_strategy = strategy_name
            else:
                logger.warning(f"Unknown strategy: {base_name}, using default")
                self.today_strategy_instance = VolatilityBreakoutStrategy(params=strategy_params)
                # Update executor strategy name if in live mode
                if self.config.is_live_mode() and hasattr(self.executor, 'current_strategy'):
                    self.executor.current_strategy = 'Volatility_Breakout'

            logger.info("="*70)
            logger.info(f"✓ TODAY'S CHAMPION: {result['selected_strategy']}")
            logger.info(f"  Score: {result['score']:.2f}")
            logger.info(f"  Backtest Return: {result['backtest_results']['total_return']:.2f}%")
            logger.info(f"  Win Rate: {result['backtest_results']['win_rate']:.2f}%")
            logger.info("="*70)

            self._update_task_status('idle', 'completed')
            self._log_activity('task_end', f'Selected strategy: {result["selected_strategy"]}',
                              task_name='strategy_selection', severity='SUCCESS',
                              details={'strategy': result['selected_strategy'],
                                      'score': result['score'],
                                      'return': result['backtest_results']['total_return']})

        except Exception as e:
            logger.error(f"Error in strategy selection: {e}", exc_info=True)
            self._log_activity('task_end', f'Strategy selection failed: {str(e)}',
                              task_name='strategy_selection', severity='ERROR')
            if self.notifier:
                self.notifier.send_error_alert(
                    error_type="STRATEGY_SELECTION_ERROR",
                    error_message=str(e)
                )

            # Load default strategy as fallback
            logger.warning("Loading default fallback strategy")
            self.today_strategy_instance = VolatilityBreakoutStrategy()
            # Update executor strategy name if in live mode
            if self.config.is_live_mode() and hasattr(self.executor, 'current_strategy'):
                self.executor.current_strategy = 'Volatility_Breakout'
            raise
        finally:
            # Release lock
            self._task_lock.release()

    def run_trading_session(self):
        """
        22:30-01:00 KST: Execute trading session.

        Uses selected strategy with paper trader or live executor.
        """
        # Acquire task lock to prevent overlapping tasks
        if not self._task_lock.acquire(blocking=False):
            logger.warning("Trading session already running, skipping...")
            return

        self._update_task_status('trading', 'started')
        self._log_activity('task_start', 'Starting trading session', task_name='trading')

        logger.info("="*70)
        logger.info("TASK 3: Trading Session")
        logger.info("="*70)

        # Load previous strategy if none selected
        if self.today_strategy_instance is None:
            logger.warning("No strategy selected, attempting to load previous strategy...")
            if not self.load_previous_strategy():
                logger.error("Failed to load previous strategy! Aborting trading session.")
                self._log_activity('task_end', 'Trading session aborted: No strategy available',
                                  task_name='trading', severity='ERROR')
                self._task_lock.release()
                return

        try:
            if isinstance(self.executor, PaperTradingSimulator):
                # Paper trading mode
                logger.info("Starting PAPER TRADING session...")

                # Send session start notification
                if self.notifier:
                    try:
                        self.notifier.send_trading_session_start(
                            trading_mode=self.config.TRADING_MODE,
                            strategy_name=self.today_strategy['selected_strategy'],
                            strategy_params=self.today_strategy['selected_params'],
                            symbol=self.config.PRIMARY_SYMBOL,
                            session_duration_hours=self.config.PAPER_TRADING_SESSION_DURATION,
                            initial_balance=self.executor.balance,
                            leverage=self.executor.leverage,
                            max_loss_percent=self.executor.max_daily_loss_percent,
                            backtest_results=self.today_strategy.get('backtest_results'),
                            timeframe=self.today_strategy.get('timeframe', '1m')
                        )
                    except Exception as e:
                        logger.warning(f"Failed to send session start notification: {e}")

                self.executor.run_trading_loop(
                    symbol=self.config.PRIMARY_SYMBOL,
                    strategy=self.today_strategy_instance,
                    timeframe=self.today_strategy.get('timeframe', '1m'),
                    interval_seconds=self.config.PAPER_TRADING_POLL_INTERVAL,
                    duration_hours=self.config.PAPER_TRADING_SESSION_DURATION
                )

                logger.info("Paper trading session completed")

            else:
                # Live trading mode
                logger.warning("=" * 70)
                logger.warning("⚠ LIVE TRADING MODE - REAL MONEY AT RISK ⚠")
                logger.warning("=" * 70)

                # Initialize live trading manager
                live_manager = LiveTradingManager(
                    executor=self.executor,
                    db_manager=self.db_manager,
                    collector=self.collector,
                    notifier=self.notifier,
                    config=self.config
                )

                # Send session start notification
                if self.notifier and self.today_strategy:
                    try:
                        self.notifier.send_trading_session_start(
                            trading_mode=self.config.TRADING_MODE,
                            strategy_name=self.today_strategy['selected_strategy'],
                            strategy_params=self.today_strategy['selected_params'],
                            symbol=self.config.PRIMARY_SYMBOL,
                            session_duration_hours=self.config.PAPER_TRADING_SESSION_DURATION,
                            initial_balance=self.executor.get_balance('USDT') or 0,
                            leverage=self.config.LEVERAGE,
                            max_loss_percent=self.config.MAX_DAILY_LOSS_PERCENT,
                            backtest_results=self.today_strategy.get('backtest_results'),
                            timeframe=self.today_strategy.get('timeframe', '1m')
                        )
                    except Exception as e:
                        logger.warning(f"Failed to send session start notification: {e}")

                # Initialize session (set leverage, check balance, clean up)
                init_success = live_manager.initialize_session(
                    symbol=self.config.PRIMARY_SYMBOL,
                    leverage=self.config.LEVERAGE
                )

                if not init_success:
                    logger.error("Failed to initialize live trading session")
                    return

                # Run live trading loop
                live_manager.run_trading_loop(
                    symbol=self.config.PRIMARY_SYMBOL,
                    strategy=self.today_strategy_instance,
                    timeframe=self.today_strategy.get('timeframe', '1m'),
                    interval_seconds=self.config.PAPER_TRADING_POLL_INTERVAL,
                    duration_hours=self.config.PAPER_TRADING_SESSION_DURATION
                )

                logger.info("Live trading session completed")

            self._update_task_status('idle', 'completed')
            self._log_activity('task_end', 'Trading session completed',
                              task_name='trading', severity='SUCCESS')

        except Exception as e:
            logger.error(f"Error in trading session: {e}", exc_info=True)
            self._log_activity('task_end', f'Trading session failed: {str(e)}',
                              task_name='trading', severity='ERROR')
            if self.notifier:
                self.notifier.send_error_alert(
                    error_type="TRADING_SESSION_ERROR",
                    error_message=str(e)
                )
            raise
        finally:
            # Release lock
            self._task_lock.release()

    def run_session_cleanup(self):
        """
        01:00+ KST: Close all positions and generate daily report.
        """
        # Acquire task lock to prevent overlapping tasks
        if not self._task_lock.acquire(blocking=False):
            logger.warning("Cleanup already running, skipping...")
            return

        self._update_task_status('cleanup', 'started')
        self._log_activity('task_start', 'Starting session cleanup', task_name='cleanup')

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

            self._update_task_status('idle', 'completed')
            self._log_activity('task_end', 'Cleanup completed',
                              task_name='cleanup', severity='SUCCESS')

        except Exception as e:
            logger.error(f"Error in session cleanup: {e}", exc_info=True)
            self._log_activity('task_end', f'Cleanup failed: {str(e)}',
                              task_name='cleanup', severity='ERROR')
            raise
        finally:
            # Release lock
            self._task_lock.release()

    def send_heartbeat(self):
        """Send hourly heartbeat to confirm bot is running."""
        if self.notifier:
            try:
                # Calculate heartbeat parameters
                uptime_hours = (datetime.now() - self.start_time).total_seconds() / 3600
                active_positions = len(self.db_manager.get_open_positions())
                daily_summary = self.db_manager.get_daily_summary(datetime.now().strftime('%Y-%m-%d'))
                pnl_today = daily_summary.get('total_pnl', 0.0) if daily_summary else 0.0

                self.notifier.send_heartbeat(uptime_hours, active_positions, pnl_today)
                logger.debug("Heartbeat sent")
            except Exception as e:
                logger.error(f"Error sending heartbeat: {e}")

    def run_full_cycle_once(self, skip_selection: bool = False):
        """
        Run full daily cycle once (for testing).

        Executes all 4 tasks sequentially.

        Args:
            skip_selection: If True, load previous strategy instead of selecting new one
        """
        logger.info("Starting full daily cycle (one-time execution)")

        self.run_data_sync()

        # Strategy selection or loading
        if skip_selection:
            logger.info("Skipping strategy selection - loading previous strategy")
            if not self.load_previous_strategy():
                logger.warning("Failed to load previous strategy, running selection instead")
                self.run_strategy_selection()
        else:
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

        # Send bot start notification
        if self.notifier:
            try:
                schedule_info = """
📅 <b>Daily Schedule (KST):</b>
• 20:30 - Data Synchronization
• 21:30 - Strategy Selection
• 22:30 - Trading Session Start
• 01:00 - Session Cleanup

The bot will automatically execute trades at 22:30 KST.
"""
                self.notifier.send_bot_status(
                    status='Started',
                    details=schedule_info
                )
                logger.info("✓ Bot start notification sent")
            except Exception as e:
                logger.warning(f"Failed to send bot start notification: {e}")

        kst = timezone('Asia/Seoul')
        self.scheduler = BlockingScheduler(timezone=kst)

        # Data synchronization (20:30 KST)
        self.scheduler.add_job(
            self.run_data_sync,
            trigger='cron',
            hour=20,
            minute=30,
            id='data_sync',
            name='Data Synchronization'
        )
        logger.info("Scheduled: Data Sync at 20:30 KST")

        # Strategy selection (21:30 KST)
        self.scheduler.add_job(
            self.run_strategy_selection,
            trigger='cron',
            hour=21,
            minute=30,
            id='strategy_selection',
            name='Strategy Selection'
        )
        logger.info("Scheduled: Strategy Selection at 21:30 KST")

        # Trading session (22:30 KST)
        self.scheduler.add_job(
            self.run_trading_session,
            trigger='cron',
            hour=22,
            minute=30,
            id='trading_session',
            name='Trading Session'
        )
        logger.info("Scheduled: Trading Session at 22:30 KST")

        # Session cleanup (01:00 KST)
        self.scheduler.add_job(
            self.run_session_cleanup,
            trigger='cron',
            hour=1,
            minute=0,
            id='cleanup',
            name='Session Cleanup'
        )
        logger.info("Scheduled: Cleanup at 01:00 KST")

        # Hourly heartbeat
        self.scheduler.add_job(
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

        # Initial status update
        self._update_task_status('idle', 'initialized')

        try:
            # Run scheduler in non-blocking mode
            self.scheduler.start()
            # Reset start time when scheduled mode starts
            self.start_time = datetime.now()
        except (KeyboardInterrupt, SystemExit):
            logger.info("Keyboard interrupt received, shutting down gracefully...")
            self.should_stop = True
        finally:
            # Update status on shutdown
            self.db_manager.update_bot_status({
                'status': 'stopped',
                'current_task': 'idle'
            })
            self.scheduler.shutdown()
            self.db_manager.shutdown()
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
    parser.add_argument(
        '--skip-selection',
        action='store_true',
        help='Skip strategy selection and use previous strategy (only for "once" mode)'
    )

    args = parser.parse_args()

    # Initialize bot
    bot = TradingBot()

    # PID file management for scheduled mode
    pid_file = Path("bot.pid")

    try:
        # Save PID when starting in scheduled mode
        if args.mode == 'scheduled':
            pid_file.write_text(str(os.getpid()))
            logger.info(f"PID {os.getpid()} written to {pid_file}")

        # Execute based on mode
        if args.mode == 'scheduled':
            bot.start_scheduled_bot()
        elif args.mode == 'once':
            bot.run_full_cycle_once(skip_selection=args.skip_selection)
        elif args.mode == 'sync':
            bot.run_data_sync()
        elif args.mode == 'select':
            bot.run_strategy_selection()
        elif args.mode == 'trade':
            bot.run_trading_session()
        elif args.mode == 'cleanup':
            bot.run_session_cleanup()

    finally:
        # Clean up PID file
        if args.mode == 'scheduled' and pid_file.exists():
            pid_file.unlink(missing_ok=True)
            logger.info("PID file removed")


if __name__ == "__main__":
    main()
