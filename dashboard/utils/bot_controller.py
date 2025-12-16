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

    def start_bot(self, mode: str = "scheduled") -> bool:
        """
        Start the trading bot in background.

        Args:
            mode: Execution mode ('scheduled', 'once', etc.)

        Returns:
            True if started successfully, False otherwise
        """
        if self.is_running():
            return False

        try:
            # Start bot as subprocess in background
            process = subprocess.Popen(
                [sys.executable, "main_bot.py", "--mode", mode],
                cwd=Path.cwd(),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                start_new_session=True  # Detach from dashboard process
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
