"""
Live Trading Manager Module

Executes real trades on the exchange using OrderExecutor.
Architecture mirrors PaperTradingSimulator but with actual order execution.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import time
from config.logging_config import get_logger

from modules.executor import OrderExecutor
from modules.collector import DataCollector
from modules.notifier import TelegramNotifier
from database.init_db import DatabaseManager
from config.config import Config
from strategies.base_strategy import BaseStrategy

logger = get_logger(__name__)


class LiveTradingManager:
    """
    Live trading session manager with real order execution.

    Key differences from PaperTradingSimulator:
    - Uses OrderExecutor for real trades (not simulated)
    - Fetches real account balance from exchange
    - Sets leverage on exchange via CCXT
    - Creates exchange SL/TP orders (not simulated triggers)
    - More conservative risk checks
    - Position sync with exchange every iteration
    """

    def __init__(
        self,
        executor: OrderExecutor,
        db_manager: DatabaseManager,
        collector: DataCollector,
        notifier: Optional[TelegramNotifier],
        config: Config
    ):
        """
        Initialize live trading manager.

        Args:
            executor: OrderExecutor for real trade execution
            db_manager: DatabaseManager for logging
            collector: DataCollector for live prices
            notifier: Optional TelegramNotifier
            config: Configuration instance
        """
        self.executor = executor
        self.db_manager = db_manager
        self.collector = collector
        self.notifier = notifier
        self.config = config

        self.leverage = config.LEVERAGE
        self.max_daily_loss_percent = config.MAX_DAILY_LOSS_PERCENT

        # Session state
        self.session_start_balance = 0.0
        self.session_start_time = datetime.now()
        self.circuit_breaker_triggered = False
        self.current_symbol = None
        self.current_position = None

        # Statistics
        self.trades_today = []
        self.total_trades = 0
        self.winning_trades = 0
        self.losing_trades = 0
        self.gross_profit = 0.0
        self.gross_loss = 0.0

        logger.info(f"LiveTradingManager initialized - Leverage: {self.leverage}x, Max Loss: {self.max_daily_loss_percent}%")

    def initialize_session(self, symbol: str, leverage: int) -> bool:
        """
        Initialize trading session.

        1. Set leverage on exchange
        2. Get current account balance
        3. Cancel existing orders
        4. Close existing positions (safety check)
        5. Reset session statistics
        6. Send Telegram notification

        Args:
            symbol: Trading pair symbol
            leverage: Leverage multiplier

        Returns:
            True if successful, False otherwise
        """
        try:
            logger.warning("=" * 70)
            logger.warning("⚠ LIVE TRADING SESSION STARTING - REAL MONEY AT RISK ⚠")
            logger.warning("=" * 70)

            # Set leverage on exchange
            logger.info(f"Setting leverage to {leverage}x for {symbol}...")
            if not self.executor.set_leverage(leverage, symbol):
                logger.error("Failed to set leverage")
                return False

            # Get account balance
            balance = self.executor.get_balance('USDT')
            if balance is None or balance <= 0:
                logger.error(f"Invalid account balance: {balance}")
                return False

            self.session_start_balance = balance
            logger.info(f"Account balance: ${balance:,.2f} USDT")

            # Cancel all existing orders for safety
            logger.info("Cancelling all existing orders...")
            self.executor.cancel_all_orders(symbol)

            # Check for existing positions
            existing_position = self.executor.get_position(symbol)
            if existing_position and existing_position.get('contracts', 0) != 0:
                logger.warning(f"Existing position found for {symbol}: {existing_position}")
                logger.warning("Please close existing positions before starting live trading")
                return False

            # Reset session state
            self.current_symbol = symbol
            self.current_position = None
            self.circuit_breaker_triggered = False
            self.session_start_time = datetime.now()
            self.trades_today = []
            self.total_trades = 0
            self.winning_trades = 0
            self.losing_trades = 0
            self.gross_profit = 0.0
            self.gross_loss = 0.0

            # Send notification
            if self.notifier:
                self.notifier.send_message(
                    f"🚀 <b>LIVE TRADING SESSION STARTED</b>\n\n"
                    f"Symbol: {symbol}\n"
                    f"Balance: ${balance:,.2f} USDT\n"
                    f"Leverage: {leverage}x\n"
                    f"Max Loss: {self.max_daily_loss_percent}%\n"
                    f"⚠ <b>Real money is at risk!</b>",
                    parse_mode='HTML'
                )

            logger.info("✓ Live trading session initialized successfully")
            logger.warning("=" * 70)
            return True

        except Exception as e:
            logger.error(f"Error initializing session: {e}")
            return False

    def open_live_position(
        self,
        symbol: str,
        side: str,
        entry_price: float,
        amount: float,
        stop_loss_price: float,
        take_profit_price: float,
        strategy_name: str
    ) -> bool:
        """
        Open a live position on the exchange.

        1. Validate balance and risk limits
        2. Execute market order via executor
        3. Set SL/TP orders via executor
        4. Log to database (paper_trading=False)
        5. Send Telegram notification
        6. Update internal tracking

        Args:
            symbol: Trading symbol
            side: 'LONG' or 'SHORT'
            entry_price: Expected entry price
            amount: Position size in base currency
            stop_loss_price: Stop loss price
            take_profit_price: Take profit price
            strategy_name: Name of strategy

        Returns:
            True if successful, False otherwise
        """
        try:
            # Circuit breaker check
            if self.circuit_breaker_triggered:
                logger.error("Circuit breaker triggered - trading disabled")
                return False

            # Check if position already exists
            if self.current_position is not None:
                logger.warning(f"Position already exists for {symbol}")
                return False

            # Validate balance
            current_balance = self.executor.get_balance('USDT')
            if current_balance is None or current_balance <= 0:
                logger.error("Insufficient balance")
                return False

            # Calculate margin required (simplified: position_value / leverage)
            position_value = entry_price * amount
            margin_required = position_value / self.leverage

            if margin_required > current_balance * 0.9:  # Leave 10% buffer
                logger.warning(f"Insufficient balance for position: ${margin_required:.2f} required, ${current_balance:.2f} available")
                return False

            # Execute market order
            logger.info(f"Opening {side} position for {symbol} @ ~${entry_price:.2f} | Amount: {amount:.6f}")
            order_side = 'buy' if side.upper() == 'LONG' else 'sell'
            order = self.executor.create_market_order(symbol, order_side, amount)

            if not order:
                logger.error("Failed to create market order")
                return False

            actual_entry_price = order.get('average', order.get('price', entry_price))
            logger.info(f"✓ Market order filled @ ${actual_entry_price:.2f}")

            # Set Stop Loss and Take Profit orders
            sl_tp_success = self.executor.set_stop_loss_take_profit(
                symbol=symbol,
                side=side,
                amount=amount,
                stop_loss_price=stop_loss_price,
                take_profit_price=take_profit_price
            )

            if not sl_tp_success:
                logger.warning("Failed to set SL/TP orders - position is open but unprotected!")
                # TODO: Consider closing position if SL/TP fails

            # Update internal state
            self.current_position = {
                'symbol': symbol,
                'side': side.upper(),
                'entry_price': actual_entry_price,
                'amount': amount,
                'stop_loss': stop_loss_price,
                'take_profit': take_profit_price,
                'entry_time': datetime.now(),
                'strategy_name': strategy_name,
                'order_id': order.get('id')
            }

            # Log to database (paper_trading=False)
            try:
                trade_id = self.db_manager.log_trade(
                    symbol=symbol,
                    side=side,
                    entry_price=actual_entry_price,
                    exit_price=None,
                    amount=amount,
                    pnl=None,
                    pnl_percent=None,
                    entry_time=self.current_position['entry_time'],
                    exit_time=None,
                    strategy_name=strategy_name,
                    exit_reason=None,
                    paper_trading=False  # Live trading
                )
                self.current_position['trade_id'] = trade_id
            except Exception as e:
                logger.error(f"Failed to log trade to database: {e}")

            # Send notification
            if self.notifier:
                self.notifier.send_buy_order(
                    symbol=symbol,
                    side=side,
                    entry_price=actual_entry_price,
                    amount=amount,
                    leverage=self.leverage,
                    strategy=strategy_name,
                    stop_loss=stop_loss_price,
                    take_profit=take_profit_price,
                    order_type="MARKET",
                    is_paper=False  # Live trading
                )

            logger.info(f"✓ Live position opened successfully | SL: ${stop_loss_price:.2f} | TP: ${take_profit_price:.2f}")
            return True

        except Exception as e:
            logger.error(f"Error opening live position: {e}")
            return False

    def close_live_position(self, exit_reason: str) -> Optional[Dict]:
        """
        Close the current live position.

        1. Get position from exchange
        2. Cancel SL/TP orders
        3. Close via executor.close_position()
        4. Calculate realized PNL
        5. Update database
        6. Send notification
        7. Update statistics

        Args:
            exit_reason: Reason for exit (e.g., 'SIGNAL', 'SL', 'TP', 'MANUAL')

        Returns:
            Dict with exit details or None if failed
        """
        try:
            if self.current_position is None:
                logger.warning("No open position to close")
                return None

            symbol = self.current_position['symbol']
            side = self.current_position['side']
            entry_price = self.current_position['entry_price']
            amount = self.current_position['amount']

            # Get current position from exchange
            exchange_position = self.executor.get_position(symbol)

            # Cancel SL/TP orders
            logger.info(f"Cancelling SL/TP orders for {symbol}...")
            self.executor.cancel_all_orders(symbol)

            # Close position
            logger.info(f"Closing {side} position for {symbol}...")
            close_result = self.executor.close_position(symbol)

            if not close_result:
                logger.error("Failed to close position on exchange")
                return None

            # Get exit price
            exit_price = close_result.get('average', close_result.get('price', 0))
            if exit_price == 0:
                # Fallback: get current market price
                try:
                    exit_price = self.collector.get_latest_price(symbol)
                except:
                    exit_price = entry_price  # Last resort

            # Calculate PNL
            if side.upper() == 'LONG':
                pnl_percent = ((exit_price - entry_price) / entry_price) * 100 * self.leverage
            else:  # SHORT
                pnl_percent = ((entry_price - exit_price) / entry_price) * 100 * self.leverage

            pnl_usdt = (pnl_percent / 100) * (entry_price * amount)

            # Update statistics
            self.total_trades += 1
            if pnl_usdt > 0:
                self.winning_trades += 1
                self.gross_profit += pnl_usdt
            else:
                self.losing_trades += 1
                self.gross_loss += abs(pnl_usdt)

            # Update database
            exit_time = datetime.now()
            if 'trade_id' in self.current_position:
                try:
                    self.db_manager.update_trade(
                        trade_id=self.current_position['trade_id'],
                        exit_price=exit_price,
                        exit_time=exit_time,
                        pnl=pnl_usdt,
                        pnl_percent=pnl_percent,
                        exit_reason=exit_reason
                    )
                except Exception as e:
                    logger.error(f"Failed to update trade in database: {e}")

            # Send notification
            if self.notifier:
                self.notifier.send_sell_order(
                    symbol=symbol,
                    side=side,
                    exit_price=exit_price,
                    amount=amount,
                    pnl=pnl_usdt,
                    pnl_percent=pnl_percent,
                    exit_reason=exit_reason,
                    is_paper=False  # Live trading
                )

            # Log trade
            trade_record = {
                'symbol': symbol,
                'side': side,
                'entry_price': entry_price,
                'exit_price': exit_price,
                'amount': amount,
                'pnl': pnl_usdt,
                'pnl_percent': pnl_percent,
                'exit_reason': exit_reason,
                'entry_time': self.current_position['entry_time'],
                'exit_time': exit_time
            }
            self.trades_today.append(trade_record)

            logger.info(f"✓ Position closed | Exit: ${exit_price:.2f} | PNL: ${pnl_usdt:.2f} ({pnl_percent:+.2f}%) | Reason: {exit_reason}")

            # Clear current position
            self.current_position = None

            return trade_record

        except Exception as e:
            logger.error(f"Error closing live position: {e}")
            return None

    def monitor_positions(self, current_price: float) -> Optional[str]:
        """
        Monitor current position and check for SL/TP triggers.

        Since SL/TP are exchange orders, they trigger automatically.
        This method checks if the position has disappeared (triggered).

        Args:
            current_price: Current market price

        Returns:
            Exit reason if position was closed, None otherwise
        """
        if self.current_position is None:
            return None

        try:
            symbol = self.current_position['symbol']

            # Get position from exchange
            exchange_position = self.executor.get_position(symbol)

            # Check if position disappeared (SL/TP triggered)
            if exchange_position is None or exchange_position.get('contracts', 0) == 0:
                logger.info("Position no longer exists on exchange - likely SL/TP triggered")

                # Determine exit reason based on price
                sl_price = self.current_position['stop_loss']
                tp_price = self.current_position['take_profit']
                side = self.current_position['side']

                if side.upper() == 'LONG':
                    if current_price <= sl_price * 1.01:  # 1% tolerance
                        exit_reason = 'SL'
                    elif current_price >= tp_price * 0.99:
                        exit_reason = 'TP'
                    else:
                        exit_reason = 'UNKNOWN'
                else:  # SHORT
                    if current_price >= sl_price * 0.99:
                        exit_reason = 'SL'
                    elif current_price <= tp_price * 1.01:
                        exit_reason = 'TP'
                    else:
                        exit_reason = 'UNKNOWN'

                # Close position in our tracking
                self.close_live_position(exit_reason)
                return exit_reason

            # Check circuit breaker
            self.check_circuit_breaker()

            return None

        except Exception as e:
            logger.error(f"Error monitoring positions: {e}")
            return None

    def execute_strategy_signal(
        self,
        symbol: str,
        signal: int,
        strategy: BaseStrategy,
        current_price: float,
        df: pd.DataFrame
    ) -> bool:
        """
        Execute trading signal from strategy.

        Logic:
        - signal = 0: Do nothing
        - signal = 1 (BUY): Open LONG position (close SHORT if exists)
        - signal = -1 (SELL): Open SHORT position (close LONG if exists)

        Args:
            symbol: Trading symbol
            signal: Trading signal (-1, 0, 1)
            strategy: Strategy instance
            current_price: Current market price
            df: Recent OHLCV data

        Returns:
            True if action taken, False otherwise
        """
        try:
            # No signal = no action
            if signal == 0:
                return False

            # Get account balance
            balance = self.executor.get_balance('USDT')
            if balance is None or balance <= 0:
                logger.error("Unable to get account balance")
                return False

            # Close opposite position if exists
            if self.current_position is not None:
                current_side = self.current_position['side']
                signal_side = 'LONG' if signal == 1 else 'SHORT'

                if current_side != signal_side:
                    logger.info(f"Closing {current_side} position to open {signal_side}")
                    self.close_live_position('SIGNAL')

            # If position exists and same direction, hold
            if self.current_position is not None:
                logger.debug(f"Holding existing {self.current_position['side']} position")
                return False

            # Open new position
            side = 'LONG' if signal == 1 else 'SHORT'

            # Calculate position size using strategy's method
            risk_percent = self.config.RISK_PERCENT_PER_TRADE
            sl_price = strategy.get_stop_loss_price(current_price, side)
            position_size = strategy.calculate_position_size(
                balance=balance,
                risk_percent=risk_percent,
                entry_price=current_price,
                stop_loss_price=sl_price
            )

            # Get TP price
            tp_price = strategy.get_take_profit_price(current_price, side)

            # Safety check: minimum position size
            min_notional = 5.0  # Binance minimum
            if position_size * current_price < min_notional:
                logger.warning(f"Position size too small: ${position_size * current_price:.2f} < ${min_notional}")
                return False

            # Open position
            return self.open_live_position(
                symbol=symbol,
                side=side,
                entry_price=current_price,
                amount=position_size,
                stop_loss_price=sl_price,
                take_profit_price=tp_price,
                strategy_name=strategy.name
            )

        except Exception as e:
            logger.error(f"Error executing strategy signal: {e}")
            return False

    def run_trading_loop(
        self,
        symbol: str,
        strategy: BaseStrategy,
        timeframe: str,
        interval_seconds: int,
        duration_hours: float
    ):
        """
        Main live trading loop.

        1. Fetch current price
        2. Monitor positions (check SL/TP triggers)
        3. Fetch recent OHLCV data
        4. Generate signals via strategy
        5. Execute signals
        6. Log statistics
        7. Check circuit breaker
        8. Sleep interval
        9. Repeat until duration or circuit breaker

        Args:
            symbol: Trading symbol
            strategy: Strategy instance
            timeframe: Candle timeframe (e.g., '1m')
            interval_seconds: Sleep interval between iterations
            duration_hours: Session duration in hours
        """
        try:
            end_time = datetime.now() + timedelta(hours=duration_hours)
            iteration = 0

            logger.info("=" * 70)
            logger.info(f"🚀 LIVE TRADING LOOP STARTED")
            logger.info(f"Strategy: {strategy.name}")
            logger.info(f"Timeframe: {timeframe}")
            logger.info(f"Duration: {duration_hours} hours")
            logger.info(f"Interval: {interval_seconds} seconds")
            logger.info("=" * 70)

            while datetime.now() < end_time and not self.circuit_breaker_triggered:
                iteration += 1
                logger.debug(f"--- Iteration {iteration} ---")

                try:
                    # 1. Fetch current price
                    current_price = self.collector.get_latest_price(symbol)
                    logger.debug(f"Current price: ${current_price:.2f}")

                    # 2. Monitor positions
                    exit_reason = self.monitor_positions(current_price)
                    if exit_reason:
                        logger.info(f"Position closed by exchange: {exit_reason}")

                    # 3. Fetch recent OHLCV data
                    df = self.collector.exchange.fetch_ohlcv(symbol, timeframe, limit=200)
                    df = pd.DataFrame(
                        df,
                        columns=['timestamp', 'open', 'high', 'low', 'close', 'volume']
                    )
                    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms', utc=True)
                    df.set_index('timestamp', inplace=True)

                    # 4. Generate signals
                    df_with_signals = strategy.generate_signals(df)
                    if df_with_signals.empty or 'signal' not in df_with_signals.columns:
                        logger.warning("Strategy did not generate signals")
                    else:
                        latest_signal = int(df_with_signals['signal'].iloc[-1])
                        logger.debug(f"Latest signal: {latest_signal}")

                        # 5. Execute signal
                        if latest_signal != 0:
                            self.execute_strategy_signal(
                                symbol=symbol,
                                signal=latest_signal,
                                strategy=strategy,
                                current_price=current_price,
                                df=df_with_signals
                            )

                    # 6. Log statistics (every 10 iterations)
                    if iteration % 10 == 0:
                        balance = self.executor.get_balance('USDT')
                        pnl_percent = ((balance - self.session_start_balance) / self.session_start_balance) * 100
                        logger.info(f"📊 Balance: ${balance:.2f} | PNL: {pnl_percent:+.2f}% | Trades: {self.total_trades} | Win Rate: {self.winning_trades}/{self.total_trades if self.total_trades > 0 else 1}")

                    # 7. Check circuit breaker
                    if self.check_circuit_breaker():
                        logger.error("Circuit breaker triggered - stopping trading loop")
                        break

                except Exception as e:
                    logger.error(f"Error in trading loop iteration: {e}")

                # 8. Sleep
                time.sleep(interval_seconds)

            # Cleanup: Close all positions
            logger.info("Trading loop ended - cleaning up...")
            if self.current_position is not None:
                self.close_live_position('SESSION_END')

            # Send final report
            self._send_final_report()

        except Exception as e:
            logger.error(f"Fatal error in trading loop: {e}")
        finally:
            logger.info("=" * 70)
            logger.info("🏁 LIVE TRADING SESSION ENDED")
            logger.info("=" * 70)

    def check_circuit_breaker(self) -> bool:
        """
        Check if circuit breaker should be triggered.

        Compares current balance to session start balance.
        If loss >= MAX_DAILY_LOSS_PERCENT, trigger emergency shutdown.

        Returns:
            True if triggered, False otherwise
        """
        if self.circuit_breaker_triggered:
            return True

        try:
            current_balance = self.executor.get_balance('USDT')
            if current_balance is None:
                return False

            loss_percent = ((self.session_start_balance - current_balance) / self.session_start_balance) * 100

            if loss_percent >= self.max_daily_loss_percent:
                self.circuit_breaker_triggered = True
                logger.error("=" * 70)
                logger.error(f"🚨 CIRCUIT BREAKER TRIGGERED 🚨")
                logger.error(f"Loss: {loss_percent:.2f}% >= {self.max_daily_loss_percent}%")
                logger.error(f"Start Balance: ${self.session_start_balance:.2f}")
                logger.error(f"Current Balance: ${current_balance:.2f}")
                logger.error("=" * 70)

                # Force close all positions
                self.force_close_all_positions()

                # Send emergency notification
                if self.notifier:
                    self.notifier.send_message(
                        f"🚨 <b>CIRCUIT BREAKER TRIGGERED</b> 🚨\n\n"
                        f"Loss: {loss_percent:.2f}% (Max: {self.max_daily_loss_percent}%)\n"
                        f"All positions closed\n"
                        f"Trading disabled",
                        parse_mode='HTML'
                    )

                return True

            return False

        except Exception as e:
            logger.error(f"Error checking circuit breaker: {e}")
            return False

    def force_close_all_positions(self):
        """Emergency shutdown - close all positions immediately."""
        try:
            logger.warning("Force closing all positions...")

            if self.current_position is not None:
                symbol = self.current_position['symbol']
                self.executor.cancel_all_orders(symbol)
                self.executor.close_position(symbol)
                self.close_live_position('CIRCUIT_BREAKER')

            logger.info("✓ All positions force closed")

        except Exception as e:
            logger.error(f"Error force closing positions: {e}")

    def _send_final_report(self):
        """Send final trading session report via Telegram."""
        try:
            final_balance = self.executor.get_balance('USDT')
            pnl = final_balance - self.session_start_balance if final_balance else 0
            pnl_percent = (pnl / self.session_start_balance) * 100 if self.session_start_balance > 0 else 0

            win_rate = (self.winning_trades / self.total_trades * 100) if self.total_trades > 0 else 0

            report = (
                f"📊 <b>LIVE TRADING SESSION REPORT</b>\n\n"
                f"Duration: {(datetime.now() - self.session_start_time).seconds / 3600:.1f} hours\n"
                f"Start Balance: ${self.session_start_balance:,.2f}\n"
                f"End Balance: ${final_balance:,.2f}\n"
                f"PNL: ${pnl:+,.2f} ({pnl_percent:+.2f}%)\n\n"
                f"Trades: {self.total_trades}\n"
                f"Wins: {self.winning_trades} | Losses: {self.losing_trades}\n"
                f"Win Rate: {win_rate:.1f}%\n"
                f"Gross Profit: ${self.gross_profit:.2f}\n"
                f"Gross Loss: ${self.gross_loss:.2f}\n"
            )

            if self.notifier:
                self.notifier.send_message(report, parse_mode='HTML')

            logger.info("✓ Final report sent")

        except Exception as e:
            logger.error(f"Error sending final report: {e}")
