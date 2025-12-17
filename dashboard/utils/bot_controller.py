"""
Bot Controller Module

Manages the trading bot process lifecycle (start/stop/status).
Uses PID file approach for process tracking.
"""

import subprocess
import psutil
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict
import sys


class BotController:
    """Controls main_bot.py process lifecycle."""

    PID_FILE = Path("bot.pid")

    def __init__(self):
        """Initialize bot controller."""
        pass

    def start_bot(self, mode: str = "scheduled", skip_selection: bool = False) -> bool:
        """
        Start the trading bot in background.

        Args:
            mode: Execution mode ('scheduled', 'once', etc.)
            skip_selection: If True, skip strategy selection and use previous strategy

        Returns:
            True if started successfully, False otherwise
        """
        if self.is_running():
            return False

        try:
            # Ensure logs directory exists
            log_dir = Path("logs")
            log_dir.mkdir(exist_ok=True)
            log_file = log_dir / "bot.log"

            # Build command with optional --skip-selection flag
            cmd = [sys.executable, "main_bot.py", "--mode", mode]
            if skip_selection and mode == "once":
                cmd.append("--skip-selection")

            # Open log file for appending
            with open(log_file, "a") as f:
                # Start bot as subprocess in background
                # On Windows, creationflags=subprocess.CREATE_NO_WINDOW can hide the console window if desired
                # We redirect stdout/stderr to the log file to avoid buffer filling and broken pipes
                kwargs = {}
                if sys.platform == 'win32':
                    kwargs['creationflags'] = subprocess.CREATE_NEW_PROCESS_GROUP
                else:
                    kwargs['start_new_session'] = True

                process = subprocess.Popen(
                    cmd,
                    cwd=Path.cwd(),
                    stdout=f,
                    stderr=subprocess.STDOUT,  # Redirect stderr to stdout (log file)
                    **kwargs
                )

            # Save PID to file
            self.PID_FILE.write_text(str(process.pid))
            return True

        except Exception as e:
            print(f"Error starting bot: {e}")
            return False

    def stop_bot(self, timeout: int = 10) -> bool:
        """
        Stop the running bot gracefully.

        Args:
            timeout: Seconds to wait for graceful shutdown

        Returns:
            True if stopped successfully, False otherwise
        """
        if not self.is_running():
            return False

        try:
            pid = int(self.PID_FILE.read_text())
            process = psutil.Process(pid)

            # Send SIGTERM for graceful shutdown
            process.terminate()

            # Wait for process to exit
            try:
                process.wait(timeout=timeout)
            except psutil.TimeoutExpired:
                # Force kill if doesn't stop gracefully
                process.kill()
                process.wait(timeout=5)

            # Clean up PID file
            self.PID_FILE.unlink(missing_ok=True)
            return True

        except psutil.NoSuchProcess:
            # Process already dead, clean up PID file
            self.PID_FILE.unlink(missing_ok=True)
            return False
        except Exception as e:
            print(f"Error stopping bot: {e}")
            return False

    def is_running(self) -> bool:
        """
        Check if bot is currently running.

        Returns:
            True if bot process is running, False otherwise
        """
        if not self.PID_FILE.exists():
            return False

        try:
            pid = int(self.PID_FILE.read_text())
            process = psutil.Process(pid)

            # Check if process exists and is a Python process
            if process.is_running():
                # Verify it's actually our bot by checking command line
                cmdline = ' '.join(process.cmdline())
                if 'main_bot.py' in cmdline:
                    return True

            # PID file exists but process is not our bot
            self.PID_FILE.unlink(missing_ok=True)
            return False

        except (psutil.NoSuchProcess, ValueError, FileNotFoundError):
            # PID file exists but process is dead or invalid
            self.PID_FILE.unlink(missing_ok=True)
            return False

    def get_status(self) -> Dict:
        """
        Get detailed bot process status.

        Returns:
            Dict with process status information
        """
        if not self.is_running():
            return {
                'status': 'stopped',
                'pid': None,
                'cpu_percent': 0.0,
                'memory_mb': 0.0,
                'started_at': None,
                'uptime_seconds': 0
            }

        try:
            pid = int(self.PID_FILE.read_text())
            process = psutil.Process(pid)

            create_time = datetime.fromtimestamp(process.create_time())
            uptime = (datetime.now() - create_time).total_seconds()

            return {
                'status': 'running',
                'pid': pid,
                'cpu_percent': process.cpu_percent(interval=0.1),
                'memory_mb': process.memory_info().rss / 1024 / 1024,
                'started_at': create_time,
                'uptime_seconds': uptime
            }

        except Exception as e:
            return {
                'status': 'error',
                'error': str(e),
                'pid': None,
                'cpu_percent': 0.0,
                'memory_mb': 0.0,
                'started_at': None,
                'uptime_seconds': 0
            }

    def restart_bot(self, mode: str = "scheduled") -> bool:
        """
        Restart the bot (stop then start).

        Args:
            mode: Execution mode for restart

        Returns:
            True if restarted successfully, False otherwise
        """
        if self.is_running():
            if not self.stop_bot():
                return False

        return self.start_bot(mode)

    def get_bot_logs(self, lines: int = 50) -> str:
        """
        Get recent bot log output (if available).

        Args:
            lines: Number of lines to retrieve

        Returns:
            Log output as string
        """
        # This would require the bot to write logs to a file
        # For now, return a placeholder
        log_file = Path("logs/bot.log")

        if not log_file.exists():
            return "No log file found. Bot may not be configured to write logs."

        try:
            with open(log_file, 'r') as f:
                all_lines = f.readlines()
                return ''.join(all_lines[-lines:])
        except Exception as e:
            return f"Error reading logs: {e}"

    def force_close_all_positions(self, reason: str = "dashboard_manual") -> Dict[str, any]:
        """
        Force close all open positions (works in both paper and live modes).

        This is a direct execution method - it doesn't signal the bot process,
        it directly closes positions via the appropriate executor.

        Args:
            reason: Reason for force close (for logging)

        Returns:
            Dict containing:
                - success: bool
                - mode: str ('paper' or 'live')
                - positions_closed: int
                - total_pnl: float
                - message: str (human-readable summary)
                - details: Dict (detailed results)
        """
        try:
            from config.config import Config
            from modules.executor import OrderExecutor
            from modules.collector import DataCollector
            from modules.notifier import TelegramNotifier
            from database.init_db import DatabaseManager

            config = Config()
            db_manager = DatabaseManager(config.DB_PATH)
            collector = DataCollector(config.EXCHANGE_NAME)

            # Initialize notifier
            notifier = None
            if config.TELEGRAM_BOT_TOKEN and config.TELEGRAM_CHAT_ID:
                try:
                    notifier = TelegramNotifier(
                        bot_token=config.TELEGRAM_BOT_TOKEN,
                        chat_id=config.TELEGRAM_CHAT_ID
                    )
                except:
                    pass  # Continue without notifications if fails

            is_live = config.is_live_mode()
            mode = "live" if is_live else "paper"

            # Execute based on mode
            if is_live:
                result = self._force_close_live(config, db_manager, collector, notifier, reason)
            else:
                result = self._force_close_paper(config, db_manager, collector, notifier, reason)

            # Log activity to database
            try:
                db_manager.log_activity(
                    event_type='force_close_all',
                    message=f'Force closed all positions via dashboard ({result["positions_closed"]} positions)',
                    event_category='trading',
                    severity='WARNING',
                    details={
                        'reason': reason,
                        'mode': mode,
                        'positions_closed': result['positions_closed'],
                        'total_pnl': result['total_pnl']
                    }
                )
            except Exception as e:
                print(f"Error logging activity: {e}")

            # Send Telegram notification
            if notifier:
                try:
                    self._send_force_close_notification(
                        notifier,
                        mode,
                        result['positions_closed'],
                        result['total_pnl'],
                        reason
                    )
                except Exception as e:
                    print(f"Error sending notification: {e}")

            return {
                'success': result['success'],
                'mode': mode,
                'positions_closed': result['positions_closed'],
                'total_pnl': result['total_pnl'],
                'message': result['message'],
                'details': result
            }

        except Exception as e:
            return {
                'success': False,
                'mode': 'unknown',
                'positions_closed': 0,
                'total_pnl': 0.0,
                'message': f"Error: {str(e)}",
                'details': {'error': str(e)}
            }

    def _force_close_paper(self, config, db_manager, collector, notifier, reason):
        """Close all positions in paper trading mode."""
        # Get open positions from database
        conn = db_manager.connect()
        conn.row_factory = lambda cursor, row: dict(zip([col[0] for col in cursor.description], row))
        cursor = conn.execute("SELECT * FROM positions WHERE status = 'open'")
        positions = cursor.fetchall()

        if not positions:
            conn.close()
            return {
                'success': True,
                'positions_closed': 0,
                'total_pnl': 0.0,
                'message': 'No open positions to close'
            }

        closed_count = 0
        total_pnl = 0.0

        for pos in positions:
            try:
                # Fetch current price
                try:
                    ticker = collector.exchange.fetch_ticker(pos['symbol'])
                    current_price = ticker['last']
                except Exception as e:
                    print(f"Failed to fetch price for {pos['symbol']}, using entry price: {e}")
                    current_price = pos['entry_price']  # Fallback: 0% PNL

                # Calculate PNL
                if pos['side'] == 'LONG':
                    pnl = (current_price - pos['entry_price']) * pos['amount'] * pos['leverage']
                else:  # SHORT
                    pnl = (pos['entry_price'] - current_price) * pos['amount'] * pos['leverage']

                pnl_percent = (pnl / (pos['entry_price'] * pos['amount'])) * 100 if pos['entry_price'] * pos['amount'] != 0 else 0.0

                # Update position status
                conn.execute("""
                    UPDATE positions
                    SET status = 'closed'
                    WHERE id = ?
                """, (pos['id'],))

                # Log trade
                conn.execute("""
                    INSERT INTO trade_history
                    (timestamp, symbol, side, entry_price, exit_price, amount, leverage,
                     pnl, pnl_percent, strategy_name, exit_reason, paper_trading)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    datetime.now(),
                    pos['symbol'],
                    pos['side'],
                    pos['entry_price'],
                    current_price,
                    pos['amount'],
                    pos['leverage'],
                    pnl,
                    pnl_percent,
                    pos.get('strategy_name', 'Unknown'),
                    reason,
                    True  # paper_trading flag
                ))

                closed_count += 1
                total_pnl += pnl

            except Exception as e:
                print(f"Error closing position {pos['symbol']}: {e}")

        conn.commit()
        conn.close()

        return {
            'success': True,
            'positions_closed': closed_count,
            'total_pnl': total_pnl,
            'message': f'Successfully closed {closed_count} positions'
        }

    def _force_close_live(self, config, db_manager, collector, notifier, reason):
        """Close all positions in live trading mode."""
        from modules.executor import OrderExecutor

        executor = OrderExecutor(
            exchange_name=config.EXCHANGE_NAME,
            api_key=config.API_KEY,
            api_secret=config.API_SECRET,
            testnet=False
        )

        # Use new close_all_positions method
        result = executor.close_all_positions(reason=reason)

        if not result['success'] or result['positions_closed'] == 0:
            return {
                'success': result['success'],
                'positions_closed': result['positions_closed'],
                'total_pnl': result['total_pnl'],
                'message': 'No positions closed or errors occurred'
            }

        # Update database
        conn = db_manager.connect()

        for closed_pos in result['closed_positions']:
            try:
                # Update positions table
                conn.execute("""
                    UPDATE positions
                    SET status = 'closed'
                    WHERE symbol = ? AND status = 'open'
                """, (closed_pos['symbol'],))

                # Log trade (Note: we don't have entry_price from result, so we use 0.0)
                conn.execute("""
                    INSERT INTO trade_history
                    (timestamp, symbol, side, entry_price, exit_price, amount, leverage,
                     pnl, pnl_percent, strategy_name, exit_reason, paper_trading)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    datetime.now(),
                    closed_pos['symbol'],
                    closed_pos['side'],
                    0.0,  # Entry price not available from result
                    0.0,  # Exit price not available
                    closed_pos['contracts'],
                    config.LEVERAGE,
                    closed_pos['pnl'],
                    0.0,  # PNL percent calculation would need entry price
                    'Unknown',
                    reason,
                    False  # live trading
                ))
            except Exception as e:
                print(f"Error updating database for {closed_pos['symbol']}: {e}")

        conn.commit()
        conn.close()

        return {
            'success': True,
            'positions_closed': result['positions_closed'],
            'total_pnl': result['total_pnl'],
            'message': f'Successfully closed {result["positions_closed"]} live positions'
        }

    def _send_force_close_notification(self, notifier, mode, count, total_pnl, reason):
        """Send Telegram notification for force close event."""
        mode_emoji = "📝" if mode == "paper" else "💰"
        pnl_emoji = "✅" if total_pnl >= 0 else "❌"

        message = f"""
🛑 <b>FORCE CLOSE ALL POSITIONS</b>

<b>Mode:</b> {mode.upper()} {mode_emoji}
<b>Positions Closed:</b> {count}
{pnl_emoji} <b>Total PNL:</b> ${total_pnl:,.2f}
<b>Reason:</b> {reason}
<b>Triggered By:</b> Dashboard
<b>Time:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""

        notifier.send_risk_alert("FORCE CLOSE", message)
