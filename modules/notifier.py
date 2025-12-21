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

    def send_buy_order(
        self,
        symbol: str,
        side: str,
        entry_price: float,
        amount: float,
        leverage: int,
        strategy: str,
        stop_loss: Optional[float] = None,
        take_profit: Optional[float] = None,
        order_type: str = "MARKET",
        is_paper: bool = False
    ) -> bool:
        """
        Send buy order notification with clear BUY emphasis.

        Args:
            symbol: Trading pair symbol
            side: 'long' or 'short'
            entry_price: Entry price
            amount: Position size
            leverage: Leverage used
            strategy: Strategy name
            stop_loss: Stop loss price
            take_profit: Take profit price
            order_type: Order type (MARKET/LIMIT)
            is_paper: Whether this is paper trading

        Returns:
            True if successful, False otherwise
        """
        emoji = "🟢" if side.lower() == 'long' else "🔴"
        mode_badge = "[PAPER MODE]\n" if is_paper else ""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Calculate position metrics
        position_value = entry_price * amount * leverage

        message = f"""
{emoji} <b>BUY ORDER EXECUTED - {side.upper()}</b>
{mode_badge}
<b>Symbol:</b> {symbol}
<b>Order Type:</b> {order_type}
<b>Entry Price:</b> ${entry_price:,.2f}
<b>Amount:</b> {amount:.6f}
<b>Leverage:</b> {leverage}x
<b>Strategy:</b> {strategy}
"""

        if stop_loss and take_profit:
            # Calculate percentages
            if side.lower() == 'long':
                sl_percent = ((stop_loss - entry_price) / entry_price) * 100
                tp_percent = ((take_profit - entry_price) / entry_price) * 100
            else:
                sl_percent = ((entry_price - stop_loss) / entry_price) * 100
                tp_percent = ((entry_price - take_profit) / entry_price) * 100

            # Calculate risk/reward
            risk_reward = abs(tp_percent) / abs(sl_percent) if sl_percent != 0 else 0

            # Calculate actual amounts
            max_risk = abs(entry_price - stop_loss) * amount * leverage
            potential_profit = abs(take_profit - entry_price) * amount * leverage

            message += f"""
<b>Stop Loss:</b> ${stop_loss:,.2f} ({sl_percent:+.2f}%)
<b>Take Profit:</b> ${take_profit:,.2f} ({tp_percent:+.2f}%)
<b>Risk/Reward:</b> 1:{risk_reward:.2f}

💰 <b>Position Value:</b> ${position_value:,.2f}
🎯 <b>Max Risk:</b> ${max_risk:,.2f}
✨ <b>Potential Profit:</b> ${potential_profit:,.2f}
"""
        else:
            message += f"\n💰 <b>Position Value:</b> ${position_value:,.2f}\n"

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

    def send_trading_session_start(
        self,
        trading_mode: str,
        strategy_name: str,
        strategy_params: Dict,
        symbol: str,
        session_duration_hours: float,
        initial_balance: float,
        leverage: int,
        max_loss_percent: float,
        backtest_results: Optional[Dict] = None,
        timeframe: str = '1m'
    ) -> bool:
        """
        Send trading session start notification.

        Args:
            trading_mode: 'Paper' or 'Live'
            strategy_name: Name of strategy being used
            strategy_params: Strategy parameters dict
            symbol: Trading symbol (e.g., 'BTC/USDT')
            session_duration_hours: Duration of trading session
            initial_balance: Starting balance
            leverage: Leverage multiplier
            max_loss_percent: Maximum daily loss percentage
            backtest_results: Optional backtest metrics
            timeframe: Candle timeframe (default: 1m)

        Returns:
            True if successful, False otherwise
        """
        from datetime import timedelta

        # Emoji based on mode
        mode_emoji = "📝" if trading_mode.lower() == 'paper' else "💰"
        mode_text = f"{trading_mode.upper()} TRADING {mode_emoji}"

        # Calculate session end time
        start_time = datetime.now()
        end_time = start_time + timedelta(hours=session_duration_hours)
        session_period = f"{start_time.strftime('%H:%M')}-{end_time.strftime('%H:%M')} KST"

        # Format strategy parameters
        params_text = ""
        for key, value in strategy_params.items():
            params_text += f"• {key}: {value}\n"

        # Build message
        message = f"""
🚀 <b>TRADING SESSION STARTED</b>

<b>Mode:</b> {mode_text}
<b>Symbol:</b> {symbol}
<b>Timeframe:</b> {timeframe}
<b>Duration:</b> {session_duration_hours} hours
<b>Session Period:</b> {session_period}

<b>Strategy Configuration:</b>
• Strategy: {strategy_name}
{params_text}"""

        # Add backtest results if available
        if backtest_results:
            message += f"""• Backtest Win Rate: {backtest_results.get('win_rate', 0):.1f}%
• Backtest Return: {backtest_results.get('total_return', 0):+.1f}%

"""
        else:
            message += "\n"

        # Calculate circuit breaker threshold
        circuit_breaker_amount = initial_balance * (max_loss_percent / 100)

        message += f"""<b>Risk Parameters:</b>
• Initial Balance: ${initial_balance:,.2f}
• Leverage: {leverage}x
• Max Daily Loss: {max_loss_percent}%
• Circuit Breaker: ${circuit_breaker_amount:,.2f}

<b>Time:</b> {start_time.strftime('%Y-%m-%d %H:%M:%S')}
━━━━━━━━━━━━━━━━━━━━
Good luck trading! 🎯
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
