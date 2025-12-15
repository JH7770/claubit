"""
Telegram Notifier Module
Handles sending notifications and alerts via Telegram.
"""

from telegram import Bot
from telegram.error import TelegramError
from datetime import datetime
from typing import Optional, Dict, List
import asyncio


class TelegramNotifier:
    """Sends trading notifications and alerts via Telegram bot."""

    def __init__(self, bot_token: str, chat_id: str):
        """
        Initialize the Telegram notifier.

        Args:
            bot_token: Telegram bot token
            chat_id: Telegram chat ID to send messages to
        """
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.bot = Bot(token=bot_token)

    async def send_message(self, message: str, parse_mode: str = 'HTML') -> bool:
        """
        Send a message to Telegram.

        Args:
            message: Message text
            parse_mode: Parse mode ('HTML' or 'Markdown')

        Returns:
            True if successful, False otherwise
        """
        try:
            await self.bot.send_message(
                chat_id=self.chat_id,
                text=message,
                parse_mode=parse_mode
            )
            return True

        except TelegramError as e:
            print(f"Error sending Telegram message: {e}")
            return False

    def send_sync(self, message: str, parse_mode: str = 'HTML') -> bool:
        """
        Synchronous wrapper for send_message.

        Args:
            message: Message text
            parse_mode: Parse mode ('HTML' or 'Markdown')

        Returns:
            True if successful, False otherwise
        """
        try:
            return asyncio.run(self.send_message(message, parse_mode))
        except Exception as e:
            print(f"Error in sync send: {e}")
            return False

    def send_trade_entry(
        self,
        symbol: str,
        side: str,
        entry_price: float,
        amount: float,
        leverage: int,
        strategy: str,
        stop_loss: Optional[float] = None,
        take_profit: Optional[float] = None
    ) -> bool:
        """
        Send trade entry notification.

        Args:
            symbol: Trading pair symbol
            side: 'long' or 'short'
            entry_price: Entry price
            amount: Position size
            leverage: Leverage used
            strategy: Strategy name
            stop_loss: Stop loss price
            take_profit: Take profit price

        Returns:
            True if successful, False otherwise
        """
        emoji = "🟢" if side.lower() == 'long' else "🔴"
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        message = f"""
{emoji} <b>TRADE ENTRY - {side.upper()}</b>

<b>Symbol:</b> {symbol}
<b>Entry Price:</b> ${entry_price:,.2f}
<b>Amount:</b> {amount:.4f}
<b>Leverage:</b> {leverage}x
<b>Strategy:</b> {strategy}
"""

        if stop_loss:
            message += f"<b>Stop Loss:</b> ${stop_loss:,.2f}\n"

        if take_profit:
            message += f"<b>Take Profit:</b> ${take_profit:,.2f}\n"

        message += f"\n<b>Time:</b> {timestamp}"

        return self.send_sync(message)

    def send_trade_exit(
        self,
        symbol: str,
        side: str,
        exit_price: float,
        entry_price: float,
        amount: float,
        pnl: float,
        pnl_percent: float,
        exit_reason: str = "Manual"
    ) -> bool:
        """
        Send trade exit notification.

        Args:
            symbol: Trading pair symbol
            side: 'long' or 'short'
            exit_price: Exit price
            entry_price: Entry price
            amount: Position size
            pnl: Profit/Loss in USDT
            pnl_percent: Profit/Loss percentage
            exit_reason: Reason for exit (TP/SL/Manual)

        Returns:
            True if successful, False otherwise
        """
        emoji = "✅" if pnl >= 0 else "❌"
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        message = f"""
{emoji} <b>TRADE EXIT - {side.upper()}</b>

<b>Symbol:</b> {symbol}
<b>Entry Price:</b> ${entry_price:,.2f}
<b>Exit Price:</b> ${exit_price:,.2f}
<b>Amount:</b> {amount:.4f}

<b>PNL:</b> ${pnl:,.2f} ({pnl_percent:+.2f}%)
<b>Reason:</b> {exit_reason}

<b>Time:</b> {timestamp}
"""

        return self.send_sync(message)

    def send_daily_report(
        self,
        date: str,
        total_trades: int,
        winning_trades: int,
        losing_trades: int,
        total_pnl: float,
        win_rate: float,
        strategy_used: str,
        balance: float
    ) -> bool:
        """
        Send daily trading report.

        Args:
            date: Trading date
            total_trades: Total number of trades
            winning_trades: Number of winning trades
            losing_trades: Number of losing trades
            total_pnl: Total profit/loss
            win_rate: Win rate percentage
            strategy_used: Strategy that was used
            balance: Current account balance

        Returns:
            True if successful, False otherwise
        """
        emoji = "📊"
        pnl_emoji = "💰" if total_pnl >= 0 else "📉"

        message = f"""
{emoji} <b>DAILY TRADING REPORT</b>
<b>Date:</b> {date}

<b>Performance:</b>
• Total Trades: {total_trades}
• Wins: {winning_trades} | Losses: {losing_trades}
• Win Rate: {win_rate:.1f}%

{pnl_emoji} <b>PNL:</b> ${total_pnl:,.2f}

<b>Strategy Used:</b> {strategy_used}
<b>Account Balance:</b> ${balance:,.2f}

━━━━━━━━━━━━━━━━━━━━
"""

        return self.send_sync(message)

    def send_error_alert(self, error_type: str, error_message: str, context: str = "") -> bool:
        """
        Send error/exception alert.

        Args:
            error_type: Type of error
            error_message: Error message
            context: Additional context

        Returns:
            True if successful, False otherwise
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        message = f"""
🚨 <b>ERROR ALERT</b>

<b>Type:</b> {error_type}
<b>Message:</b> {error_message}
"""

        if context:
            message += f"<b>Context:</b> {context}\n"

        message += f"\n<b>Time:</b> {timestamp}"

        return self.send_sync(message)

    def send_bot_status(self, status: str, details: str = "") -> bool:
        """
        Send bot status update.

        Args:
            status: Status message (e.g., 'Started', 'Stopped', 'Paused')
            details: Additional details

        Returns:
            True if successful, False otherwise
        """
        emoji_map = {
            'started': '🟢',
            'stopped': '🔴',
            'paused': '⏸️',
            'resumed': '▶️'
        }

        emoji = emoji_map.get(status.lower(), '🔵')
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        message = f"""
{emoji} <b>BOT STATUS: {status.upper()}</b>
"""

        if details:
            message += f"\n{details}\n"

        message += f"\n<b>Time:</b> {timestamp}"

        return self.send_sync(message)

    def send_heartbeat(self, uptime_hours: float, active_positions: int, pnl_today: float) -> bool:
        """
        Send periodic heartbeat message to confirm bot is running.

        Args:
            uptime_hours: Hours the bot has been running
            active_positions: Number of active positions
            pnl_today: Today's PNL

        Returns:
            True if successful, False otherwise
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        message = f"""
💓 <b>HEARTBEAT</b>

<b>Uptime:</b> {uptime_hours:.1f} hours
<b>Active Positions:</b> {active_positions}
<b>Today's PNL:</b> ${pnl_today:,.2f}

<b>Time:</b> {timestamp}
"""

        return self.send_sync(message)

    def send_strategy_selection(
        self,
        strategy_name: str,
        params: Dict,
        backtest_results: Dict
    ) -> bool:
        """
        Send daily strategy selection notification.

        Args:
            strategy_name: Name of selected strategy
            params: Strategy parameters
            backtest_results: Backtest performance metrics

        Returns:
            True if successful, False otherwise
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        message = f"""
🎯 <b>TODAY'S STRATEGY SELECTED</b>

<b>Strategy:</b> {strategy_name}

<b>Parameters:</b>
"""

        for key, value in params.items():
            message += f"• {key}: {value}\n"

        message += f"""
<b>Backtest Performance:</b>
• Win Rate: {backtest_results.get('win_rate', 0):.1f}%
• Profit Factor: {backtest_results.get('profit_factor', 0):.2f}
• Total Return: {backtest_results.get('total_return', 0):.2f}%
• Max Drawdown: {backtest_results.get('max_drawdown', 0):.2f}%

<b>Time:</b> {timestamp}
"""

        return self.send_sync(message)

    def send_risk_alert(self, alert_type: str, message_text: str) -> bool:
        """
        Send risk management alert.

        Args:
            alert_type: Type of risk alert
            message_text: Alert message

        Returns:
            True if successful, False otherwise
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        message = f"""
⚠️ <b>RISK ALERT: {alert_type.upper()}</b>

{message_text}

<b>Time:</b> {timestamp}
"""

        return self.send_sync(message)


if __name__ == "__main__":
    # Test the notifier
    # Note: Replace with your actual bot token and chat ID
    print("Testing Telegram Notifier...")

    # Uncomment to test with real credentials
    # notifier = TelegramNotifier(
    #     bot_token="YOUR_BOT_TOKEN",
    #     chat_id="YOUR_CHAT_ID"
    # )
    #
    # # Test trade entry notification
    # notifier.send_trade_entry(
    #     symbol="BTC/USDT",
    #     side="long",
    #     entry_price=50000.0,
    #     amount=0.01,
    #     leverage=10,
    #     strategy="Volatility Breakout",
    #     stop_loss=49000.0,
    #     take_profit=51000.0
    # )
    #
    # # Test heartbeat
    # notifier.send_heartbeat(
    #     uptime_hours=2.5,
    #     active_positions=1,
    #     pnl_today=150.0
    # )

    print("Notifier module ready. Add credentials to test.")
