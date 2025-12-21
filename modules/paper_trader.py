"""
Paper Trading Simulator Module

Simulates live trading in real-time without executing actual orders.
Used for strategy validation and testing before live deployment.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import time
import logging
import json

from modules.collector import DataCollector
from modules.notifier import TelegramNotifier
from database.init_db import DatabaseManager
from config.config import Config
from strategies.base_strategy import BaseStrategy

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class PaperTradingSimulator:
    """
    Paper trading simulator for real-time strategy testing.

    Features:
    - Virtual portfolio management
    - Real-time position tracking
    - SL/TP trigger simulation
    - Circuit breaker risk management
    - Performance tracking and reporting
    """

    def __init__(
        self,
        initial_balance: Optional[float] = None,
        leverage: Optional[int] = None,
        max_daily_loss_percent: Optional[float] = None,
        db_manager: Optional[DatabaseManager] = None,
        collector: Optional[DataCollector] = None,
        notifier: Optional[TelegramNotifier] = None,
        config: Optional[Config] = None
    ):
        """
        Initialize paper trading simulator.

        Args:
            initial_balance: Starting virtual balance (default: from config)
            leverage: Leverage multiplier (default: from config)
            max_daily_loss_percent: Circuit breaker threshold (default: from config)
            db_manager: DatabaseManager for logging
            collector: DataCollector for live prices
            notifier: Optional TelegramNotifier
            config: Configuration instance
        """
        self.config = config or Config()
        self.initial_balance = initial_balance or self.config.PAPER_TRADING_INITIAL_BALANCE
        self.leverage = leverage or self.config.LEVERAGE
        self.max_daily_loss_percent = max_daily_loss_percent or self.config.MAX_DAILY_LOSS_PERCENT

        self.db_manager = db_manager or DatabaseManager(self.config.DB_PATH)
        self.collector = collector or DataCollector(self.config.EXCHANGE_NAME)
        self.notifier = notifier

        # Portfolio state
        self.balance = self.initial_balance
        self.positions: Dict[str, Dict] = {}  # symbol -> position details
        self.trades_today: List[Dict] = []
        self.daily_pnl = 0.0
        self.peak_equity = self.initial_balance
        self.circuit_breaker_triggered = False
        self.session_start_time = datetime.now()

        # Statistics
        self.total_trades = 0
        self.winning_trades = 0
        self.losing_trades = 0
        self.gross_profit = 0.0
        self.gross_loss = 0.0

        logger.info(f"PaperTradingSimulator initialized - Balance: ${self.balance:.2f}, Leverage: {self.leverage}x")

    # Portfolio Management
    def get_balance(self) -> float:
        """Get current available balance."""
        return self.balance

    def get_equity(self) -> float:
        """
        Get total equity (balance + unrealized PNL).

        Returns:
            Total equity in USDT
        """
        unrealized_pnl = sum(
            self._calculate_unrealized_pnl(symbol, pos)
            for symbol, pos in self.positions.items()
        )
        return self.balance + unrealized_pnl

    def get_position(self, symbol: str) -> Optional[Dict]:
        """
        Get current position for symbol.

        Args:
            symbol: Trading symbol

        Returns:
            Dict with position info or None if no position
        """
        if symbol not in self.positions:
            return None

        pos = self.positions[symbol]
        unrealized_pnl = self._calculate_unrealized_pnl(symbol, pos)
        unrealized_pnl_percent = (unrealized_pnl / (pos['entry_price'] * pos['amount'])) * 100

        return {
            'symbol': symbol,
            'side': pos['side'],
            'entry_price': pos['entry_price'],
            'amount': pos['amount'],
            'stop_loss': pos['stop_loss'],
            'take_profit': pos['take_profit'],
            'unrealized_pnl': unrealized_pnl,
            'unrealized_pnl_percent': unrealized_pnl_percent,
            'entry_time': pos['entry_time'],
            'strategy_name': pos['strategy_name']
        }

    def get_all_positions(self) -> List[Dict]:
        """Get all open positions."""
        return [self.get_position(symbol) for symbol in self.positions.keys()]

    # Trading Operations
    def open_position(
        self,
        symbol: str,
        side: str,
        entry_price: float,
        amount: float,
        stop_loss: float,
        take_profit: float,
        strategy_name: str
    ) -> Dict:
        """
        Open a new virtual position.

        Args:
            symbol: Trading symbol
            side: 'LONG' or 'SHORT'
            entry_price: Entry price
            amount: Position size
            stop_loss: Stop loss price
            take_profit: Take profit price
            strategy_name: Name of strategy

        Returns:
            Dict with position details

        Raises:
            ValueError: If position already exists or insufficient balance
        """
        # Validate
        if symbol in self.positions:
            raise ValueError(f"Position already exists for {symbol}")

        if self.circuit_breaker_triggered:
            raise ValueError("Circuit breaker triggered - trading disabled")

        # Calculate margin required
        margin_required = self._calculate_margin_required(entry_price, amount)

        if margin_required > self.balance:
            raise ValueError(f"Insufficient balance: ${self.balance:.2f} < ${margin_required:.2f}")

        # Create position
        position = {
            'symbol': symbol,
            'side': side.upper(),
            'entry_price': entry_price,
            'amount': amount,
            'stop_loss': stop_loss,
            'take_profit': take_profit,
            'entry_time': datetime.now(),
            'strategy_name': strategy_name,
            'margin_used': margin_required
        }

        # Update state
        self.positions[symbol] = position
        self.balance -= margin_required

        # Save to database
        try:
            position_id = self.db_manager.save_position(position)
            position['id'] = position_id
        except Exception as e:
            logger.error(f"Error saving position to database: {e}")

        logger.info(f"✓ Opened {side} position for {symbol} @ ${entry_price:.2f} | Amount: {amount:.6f} | SL: ${stop_loss:.2f} | TP: ${take_profit:.2f}")

        # Send buy order notification
        if self.notifier:
            self.notifier.send_buy_order(
                symbol=symbol,
                side=side,
                entry_price=entry_price,
                amount=amount,
                leverage=self.leverage,
                strategy=strategy_name,
                stop_loss=stop_loss,
                take_profit=take_profit,
                order_type="MARKET",
                is_paper=True
            )

        # Log activity
        try:
            self.db_manager.log_activity(
                'position_open',
                f'Opened {side} position for {symbol}',
                event_category='trading',
                details={
                    'symbol': symbol,
                    'side': side,
                    'entry_price': entry_price,
                    'amount': amount,
                    'stop_loss': stop_loss,
                    'take_profit': take_profit,
                    'strategy_name': strategy_name
                }
            )
        except Exception as log_err:
            logger.warning(f"Failed to log position open: {log_err}")

        return position

    def close_position(
        self,
        symbol: str,
        exit_price: float,
        exit_reason: str = 'manual'
    ) -> Optional[Dict]:
        """
        Close existing virtual position.

        Args:
            symbol: Trading symbol
            exit_price: Exit price
            exit_reason: 'stop_loss', 'take_profit', 'signal', 'manual', etc.

        Returns:
            Dict with trade summary or None if no position
        """
        if symbol not in self.positions:
            logger.warning(f"No position to close for {symbol}")
            return None

        pos = self.positions[symbol]

        # Calculate PNL
        pnl, pnl_percent = self._calculate_pnl(pos, exit_price)

        # Calculate trade duration
        duration = datetime.now() - pos['entry_time']

        # Create trade record
        trade = {
            'timestamp': datetime.now(),
            'symbol': symbol,
            'side': pos['side'],
            'entry_price': pos['entry_price'],
            'exit_price': exit_price,
            'amount': pos['amount'],
            'leverage': self.leverage,
            'pnl': pnl,
            'pnl_percent': pnl_percent,
            'strategy_name': pos['strategy_name'],
            'exit_reason': exit_reason,
            'duration_seconds': duration.total_seconds(),
            'paper_trading': True
        }

        # Update portfolio
        self.balance += pos['margin_used']  # Return margin
        self.balance += pnl  # Add/subtract PNL
        self.daily_pnl += pnl

        # Update statistics
        self.total_trades += 1
        if pnl > 0:
            self.winning_trades += 1
            self.gross_profit += pnl
        else:
            self.losing_trades += 1
            self.gross_loss += abs(pnl)

        self.trades_today.append(trade)

        # Remove position
        del self.positions[symbol]

        # Update peak equity for drawdown calculation
        current_equity = self.get_equity()
        if current_equity > self.peak_equity:
            self.peak_equity = current_equity

        # Log to database
        try:
            self.db_manager.log_trade(trade)
            self.db_manager.close_position_db(symbol, pos.get('strategy_name'))
        except Exception as e:
            logger.error(f"Error logging trade to database: {e}")

        logger.info(f"✓ Closed {pos['side']} position for {symbol} @ ${exit_price:.2f} | PNL: ${pnl:.2f} ({pnl_percent:+.2f}%) | Reason: {exit_reason}")

        # Send notification
        if self.notifier:
            self.notifier.send_trade_exit(
                symbol=symbol,
                side=pos['side'],
                entry_price=pos['entry_price'],
                exit_price=exit_price,
                amount=pos['amount'],
                pnl=pnl,
                pnl_percent=pnl_percent,
                exit_reason=exit_reason
            )

        # Log activity
        try:
            severity = 'SUCCESS' if pnl > 0 else 'WARNING'
            self.db_manager.log_activity(
                'position_close',
                f'Closed {pos["side"]} position for {symbol}',
                event_category='trading',
                severity=severity,
                details={
                    'symbol': symbol,
                    'side': pos['side'],
                    'pnl': pnl,
                    'pnl_percent': pnl_percent,
                    'exit_reason': exit_reason,
                    'entry_price': pos['entry_price'],
                    'exit_price': exit_price
                }
            )
        except Exception as log_err:
            logger.warning(f"Failed to log position close: {log_err}")

        # Check circuit breaker
        if self.check_circuit_breaker():
            self.force_close_all_positions(reason="circuit_breaker")

        return trade

    def check_stop_loss_take_profit(self, symbol: str, current_price: float):
        """
        Check if SL/TP should trigger for a position.

        Args:
            symbol: Trading symbol
            current_price: Current market price
        """
        if symbol not in self.positions:
            return

        pos = self.positions[symbol]

        # Get candle data for trigger simulation (use high/low if available)
        # For simplicity, we'll use current price as both high and low
        high = current_price * 1.001  # Small buffer for realism
        low = current_price * 0.999

        if pos['side'] == 'LONG':
            # Check stop loss (price went below SL)
            if low <= pos['stop_loss']:
                logger.info(f"⚠ Stop Loss triggered for {symbol} @ ${pos['stop_loss']:.2f}")
                self.close_position(symbol, pos['stop_loss'], exit_reason='stop_loss')
                return

            # Check take profit (price went above TP)
            if high >= pos['take_profit']:
                logger.info(f"🎯 Take Profit triggered for {symbol} @ ${pos['take_profit']:.2f}")
                self.close_position(symbol, pos['take_profit'], exit_reason='take_profit')
                return

        elif pos['side'] == 'SHORT':
            # Check stop loss (price went above SL)
            if high >= pos['stop_loss']:
                logger.info(f"⚠ Stop Loss triggered for {symbol} @ ${pos['stop_loss']:.2f}")
                self.close_position(symbol, pos['stop_loss'], exit_reason='stop_loss')
                return

            # Check take profit (price went below TP)
            if low <= pos['take_profit']:
                logger.info(f"🎯 Take Profit triggered for {symbol} @ ${pos['take_profit']:.2f}")
                self.close_position(symbol, pos['take_profit'], exit_reason='take_profit')
                return

    # Strategy Integration
    def execute_strategy_signal(
        self,
        symbol: str,
        strategy: BaseStrategy,
        current_price: float,
        signal: int
    ):
        """
        Execute trading action based on strategy signal.

        Args:
            symbol: Trading symbol
            strategy: Strategy instance
            current_price: Current market price
            signal: 1=long, -1=short, 0=hold
        """
        if signal == 0:
            return  # No action

        # Check if we already have a position
        has_position = symbol in self.positions

        # If signal is opposite to current position, close first
        if has_position:
            current_side = self.positions[symbol]['side']
            if (signal == 1 and current_side == 'SHORT') or (signal == -1 and current_side == 'LONG'):
                logger.info(f"Closing opposite position before opening new one")
                self.close_position(symbol, current_price, exit_reason='signal_reversal')

        # Open new position if we don't have one
        if symbol not in self.positions:
            side = 'LONG' if signal == 1 else 'SHORT'

            # Calculate position size
            amount = strategy.calculate_position_size(
                signal=signal,
                price=current_price,
                balance=self.balance
            )

            if amount <= 0:
                logger.warning(f"Invalid position size: {amount}")
                return

            # Calculate SL/TP
            stop_loss = strategy.get_stop_loss_price(current_price, side)
            take_profit = strategy.get_take_profit_price(current_price, side)

            # Open position
            try:
                self.open_position(
                    symbol=symbol,
                    side=side,
                    entry_price=current_price,
                    amount=amount,
                    stop_loss=stop_loss,
                    take_profit=take_profit,
                    strategy_name=strategy.__class__.__name__
                )
            except ValueError as e:
                logger.error(f"Failed to open position: {e}")

    def run_trading_loop(
        self,
        symbol: str,
        strategy: BaseStrategy,
        timeframe: str = '1m',
        interval_seconds: Optional[int] = None,
        duration_hours: Optional[float] = None
    ):
        """
        Run continuous paper trading loop.

        Args:
            symbol: Trading symbol
            strategy: Strategy to trade
            timeframe: Candle timeframe for data fetching (default: 1m)
            interval_seconds: Polling interval (default: from config)
            duration_hours: Trading session duration (default: from config)
        """
        interval_seconds = interval_seconds or self.config.PAPER_TRADING_POLL_INTERVAL
        duration_hours = duration_hours or self.config.PAPER_TRADING_SESSION_DURATION

        logger.info(f"Starting paper trading loop for {symbol}")
        logger.info(f"  Strategy: {strategy.__class__.__name__}")
        logger.info(f"  Timeframe: {timeframe}")
        logger.info(f"  Interval: {interval_seconds}s")
        logger.info(f"  Duration: {duration_hours}h")

        self.reset_daily_stats()
        end_time = datetime.now() + timedelta(hours=duration_hours)

        try:
            while datetime.now() < end_time and not self.circuit_breaker_triggered:
                # 1. Fetch latest price
                try:
                    ticker = self.collector.exchange.fetch_ticker(symbol)
                    current_price = ticker['last']
                except Exception as e:
                    logger.error(f"Error fetching price: {e}")
                    time.sleep(interval_seconds)
                    continue

                # 2. Check SL/TP triggers for existing positions
                if symbol in self.positions:
                    self.check_stop_loss_take_profit(symbol, current_price)

                # 3. Generate strategy signal (need recent data)
                try:
                    # Fetch recent candles for signal generation
                    ohlcv = self.collector.exchange.fetch_ohlcv(symbol, timeframe, limit=100)
                    df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
                    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
                    df.set_index('timestamp', inplace=True)

                    # Generate signals
                    df_signals = strategy.generate_signals(df)
                    if len(df_signals) > 0:
                        signal = df_signals['signal'].iloc[-1]

                        # Extract indicator values for logging
                        indicators = self._extract_indicators(df_signals.iloc[-1])

                        # Log signal to database
                        try:
                            self.db_manager.log_trading_signal({
                                'symbol': symbol,
                                'strategy_name': strategy.__class__.__name__,
                                'signal': int(signal),
                                'current_price': current_price,
                                'indicators': indicators,
                                'position_opened': False  # Will update if position is opened
                            })
                        except Exception as log_err:
                            logger.warning(f"Failed to log signal: {log_err}")
                    else:
                        signal = 0

                except Exception as e:
                    logger.error(f"Error generating signal: {e}")
                    signal = 0

                # 4. Execute signal
                if signal != 0:
                    self.execute_strategy_signal(symbol, strategy, current_price, signal)

                # 5. Print status
                self.print_status()

                # 6. Sleep until next interval
                time.sleep(interval_seconds)

        except KeyboardInterrupt:
            logger.info("Trading loop interrupted by user")

        finally:
            # Cleanup: close all positions
            self.force_close_all_positions(reason="session_end")

            # Save daily summary
            today = datetime.now().strftime('%Y-%m-%d')
            self.save_daily_summary(today)

            logger.info("Paper trading session ended")

    # Risk Management
    def check_circuit_breaker(self) -> bool:
        """
        Check if circuit breaker should trigger.

        Returns:
            True if circuit breaker triggered, False otherwise
        """
        if self.circuit_breaker_triggered:
            return True

        # Calculate loss percentage
        loss_percent = (self.daily_pnl / self.initial_balance) * 100

        if loss_percent <= -self.max_daily_loss_percent:
            logger.error(f"🚨 CIRCUIT BREAKER TRIGGERED: Daily loss {loss_percent:.2f}% exceeds limit {self.max_daily_loss_percent}%")
            self.circuit_breaker_triggered = True

            if self.notifier:
                self.notifier.send_risk_alert(
                    alert_type="CIRCUIT_BREAKER",
                    message_text=f"Daily loss limit exceeded: {loss_percent:.2f}% / {self.max_daily_loss_percent}%"
                )

            return True

        return False

    def force_close_all_positions(self, reason: str = "circuit_breaker"):
        """
        Emergency close all positions.

        Args:
            reason: Reason for force close
        """
        if len(self.positions) == 0:
            return

        logger.warning(f"Force closing all positions - Reason: {reason}")

        # Get current prices and close all
        for symbol in list(self.positions.keys()):
            try:
                ticker = self.collector.exchange.fetch_ticker(symbol)
                current_price = ticker['last']
                self.close_position(symbol, current_price, exit_reason=reason)
            except Exception as e:
                logger.error(f"Error force closing {symbol}: {e}")

    # Performance Tracking
    def get_daily_stats(self) -> Dict:
        """
        Get current day's performance statistics.

        Returns:
            Dict with metrics
        """
        win_rate = (self.winning_trades / self.total_trades * 100) if self.total_trades > 0 else 0
        current_equity = self.get_equity()
        pnl_percent = ((current_equity - self.initial_balance) / self.initial_balance) * 100
        max_drawdown = ((self.peak_equity - current_equity) / self.peak_equity * 100) if self.peak_equity > 0 else 0

        return {
            'date': datetime.now().strftime('%Y-%m-%d'),
            'total_trades': self.total_trades,
            'winning_trades': self.winning_trades,
            'losing_trades': self.losing_trades,
            'win_rate': win_rate,
            'total_pnl': self.daily_pnl,
            'gross_profit': self.gross_profit,
            'gross_loss': self.gross_loss,
            'max_drawdown': max_drawdown,
            'current_equity': current_equity,
            'pnl_percent': pnl_percent,
            'current_balance': self.balance,
            'open_positions': len(self.positions)
        }

    def reset_daily_stats(self):
        """Reset daily statistics (called at session start)."""
        self.trades_today = []
        self.daily_pnl = 0.0
        self.peak_equity = self.get_equity()
        self.circuit_breaker_triggered = False
        self.session_start_time = datetime.now()
        self.total_trades = 0
        self.winning_trades = 0
        self.losing_trades = 0
        self.gross_profit = 0.0
        self.gross_loss = 0.0

        logger.info("Daily statistics reset")

    def save_daily_summary(self, date: str):
        """
        Save daily summary to database.

        Args:
            date: Trading date (YYYY-MM-DD)
        """
        stats = self.get_daily_stats()

        summary_data = {
            'date': date,
            'total_pnl': stats['total_pnl'],
            'total_trades': stats['total_trades'],
            'winning_trades': stats['winning_trades'],
            'losing_trades': stats['losing_trades'],
            'win_rate': stats['win_rate'],
            'strategy_used': 'Paper Trading',
            'starting_balance': self.initial_balance,
            'ending_balance': self.balance
        }

        try:
            self.db_manager.update_daily_summary(summary_data)
            logger.info(f"Daily summary saved for {date}")
        except Exception as e:
            logger.error(f"Error saving daily summary: {e}")

        # Send daily report
        if self.notifier:
            self.notifier.send_daily_report(
                date=date,
                total_trades=stats['total_trades'],
                winning_trades=stats['winning_trades'],
                losing_trades=stats['losing_trades'],
                total_pnl=stats['total_pnl'],
                win_rate=stats['win_rate'],
                strategy_used=summary_data['strategy_used'],
                balance=self.balance
            )

    # Helper methods
    def _extract_indicators(self, signal_row: pd.Series) -> dict:
        """
        Extract indicator values from signal row for logging.

        Args:
            signal_row: DataFrame row with signal and indicators

        Returns:
            Dictionary with indicator values
        """
        indicators = {}
        # Get all columns except 'signal'
        indicator_columns = [col for col in signal_row.index if col not in ['signal']]
        for col in indicator_columns:
            value = signal_row[col]
            # Convert to native Python types for JSON serialization
            if pd.notna(value):
                indicators[col] = float(value) if isinstance(value, (np.integer, np.floating)) else value
            else:
                indicators[col] = None
        return indicators

    # Reporting
    def print_status(self):
        """Print current trading status to console."""
        stats = self.get_daily_stats()

        print(f"\n{'='*70}")
        print(f"Paper Trading Status - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*70}")
        print(f"Balance: ${self.balance:.2f} | Equity: ${stats['current_equity']:.2f}")
        print(f"Daily PNL: ${stats['total_pnl']:.2f} ({stats['pnl_percent']:+.2f}%)")
        print(f"Trades: {stats['total_trades']} (W: {stats['winning_trades']}, L: {stats['losing_trades']}) | Win Rate: {stats['win_rate']:.1f}%")
        print(f"Open Positions: {stats['open_positions']}")
        if stats['open_positions'] > 0:
            for symbol, pos_data in self.positions.items():
                pos = self.get_position(symbol)
                print(f"  - {symbol}: {pos['side']} @ ${pos['entry_price']:.2f} | Unrealized: ${pos['unrealized_pnl']:.2f} ({pos['unrealized_pnl_percent']:+.2f}%)")
        print(f"{'='*70}\n")

    def send_status_update(self):
        """Send status update via Telegram."""
        if not self.notifier:
            return

        stats = self.get_daily_stats()
        message = f"""
📊 **Paper Trading Status**

**Portfolio:**
  • Balance: ${self.balance:.2f}
  • Equity: ${stats['current_equity']:.2f}
  • Daily PNL: ${stats['total_pnl']:.2f} ({stats['pnl_percent']:+.2f}%)

**Performance:**
  • Trades: {stats['total_trades']} (W: {stats['winning_trades']}, L: {stats['losing_trades']})
  • Win Rate: {stats['win_rate']:.1f}%
  • Max Drawdown: {stats['max_drawdown']:.2f}%

**Positions:** {stats['open_positions']} open
"""
        try:
            self.notifier.send_message(message)
        except Exception as e:
            logger.error(f"Error sending status update: {e}")

    # Utility Methods
    def _calculate_margin_required(self, price: float, amount: float) -> float:
        """Calculate margin required for position."""
        return (price * amount) / self.leverage

    def _calculate_unrealized_pnl(self, symbol: str, position: Dict) -> float:
        """Calculate unrealized PNL for a position."""
        try:
            ticker = self.collector.exchange.fetch_ticker(symbol)
            current_price = ticker['last']

            if position['side'] == 'LONG':
                price_change = current_price - position['entry_price']
            else:  # SHORT
                price_change = position['entry_price'] - current_price

            pnl = price_change * position['amount'] * self.leverage
            return pnl

        except Exception as e:
            logger.error(f"Error calculating unrealized PNL for {symbol}: {e}")
            return 0.0

    def _calculate_pnl(self, position: Dict, exit_price: float) -> Tuple[float, float]:
        """
        Calculate PNL for a closed position.

        Returns:
            Tuple of (pnl_absolute, pnl_percent)
        """
        if position['side'] == 'LONG':
            price_change = exit_price - position['entry_price']
        else:  # SHORT
            price_change = position['entry_price'] - exit_price

        # Calculate absolute PNL with leverage
        pnl = price_change * position['amount'] * self.leverage

        # Calculate percentage return
        pnl_percent = (price_change / position['entry_price']) * 100 * self.leverage

        return pnl, pnl_percent


if __name__ == "__main__":
    # Test the simulator
    print("=" * 70)
    print("Paper Trading Simulator Test")
    print("=" * 70)

    try:
        simulator = PaperTradingSimulator(
            initial_balance=10000,
            leverage=10,
            max_daily_loss_percent=5.0
        )

        print(f"\n✓ Initialized with balance: ${simulator.get_balance():.2f}")
        print(f"  Leverage: {simulator.leverage}x")
        print(f"  Max Daily Loss: {simulator.max_daily_loss_percent}%")

        # Test opening a position
        print("\n[Test] Opening LONG position...")
        simulator.open_position(
            symbol='BTC/USDT',
            side='LONG',
            entry_price=50000,
            amount=0.01,
            stop_loss=49000,
            take_profit=51000,
            strategy_name='TestStrategy'
        )

        print(f"  Balance after opening: ${simulator.get_balance():.2f}")
        print(f"  Open positions: {len(simulator.get_all_positions())}")

        # Test closing a position
        print("\n[Test] Closing position with profit...")
        trade = simulator.close_position('BTC/USDT', 50500, exit_reason='test')

        print(f"  PNL: ${trade['pnl']:.2f} ({trade['pnl_percent']:+.2f}%)")
        print(f"  Final balance: ${simulator.get_balance():.2f}")

        # Display stats
        stats = simulator.get_daily_stats()
        print(f"\n[Stats]")
        print(f"  Total trades: {stats['total_trades']}")
        print(f"  Win rate: {stats['win_rate']:.1f}%")
        print(f"  Total PNL: ${stats['total_pnl']:.2f}")

    except Exception as e:
        print(f"\n✗ Error: {e}")
