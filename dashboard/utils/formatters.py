"""
Formatters Module

Helper functions for formatting data for display in the dashboard.
"""

from datetime import datetime, timedelta
from typing import Union


def format_currency(amount: float, decimals: int = 2, include_sign: bool = False) -> str:
    """
    Format amount as currency with optional color coding.

    Args:
        amount: Amount to format
        decimals: Number of decimal places
        include_sign: Include + for positive numbers

    Returns:
        Formatted currency string
    """
    sign = ""
    if include_sign and amount > 0:
        sign = "+"
    elif amount < 0:
        sign = "-"
        amount = abs(amount)

    return f"{sign}${amount:,.{decimals}f}"


def format_percentage(value: float, decimals: int = 2, include_sign: bool = True) -> str:
    """
    Format value as percentage.

    Args:
        value: Value to format (e.g., 2.5 for 2.5%)
        decimals: Number of decimal places
        include_sign: Include + for positive numbers

    Returns:
        Formatted percentage string
    """
    sign = ""
    if include_sign:
        if value > 0:
            sign = "+"
        elif value < 0:
            sign = "-"
            value = abs(value)

    return f"{sign}{value:.{decimals}f}%"


def format_timestamp(dt: Union[datetime, str], format_string: str = "%Y-%m-%d %H:%M:%S") -> str:
    """
    Format timestamp as human-readable string.

    Args:
        dt: Datetime object or string
        format_string: strftime format string

    Returns:
        Formatted timestamp string
    """
    if isinstance(dt, str):
        try:
            dt = datetime.fromisoformat(dt)
        except ValueError:
            return dt  # Return as-is if can't parse

    if isinstance(dt, datetime):
        return dt.strftime(format_string)

    return str(dt)


def format_duration(seconds: float) -> str:
    """
    Format duration in seconds as human-readable string.

    Args:
        seconds: Duration in seconds

    Returns:
        Formatted duration string (e.g., "2h 15m", "45s")
    """
    if seconds < 60:
        return f"{int(seconds)}초"

    elif seconds < 3600:
        minutes = int(seconds / 60)
        secs = int(seconds % 60)
        return f"{minutes}분 {secs}초" if secs > 0 else f"{minutes}분"

    else:
        hours = int(seconds / 3600)
        minutes = int((seconds % 3600) / 60)
        return f"{hours}시간 {minutes}분" if minutes > 0 else f"{hours}시간"


def format_number(value: float, decimals: int = 2, compact: bool = False) -> str:
    """
    Format number with optional compact notation.

    Args:
        value: Number to format
        decimals: Number of decimal places
        compact: Use K/M/B notation

    Returns:
        Formatted number string
    """
    if compact:
        if abs(value) >= 1e9:
            return f"{value/1e9:.{decimals}f}B"
        elif abs(value) >= 1e6:
            return f"{value/1e6:.{decimals}f}M"
        elif abs(value) >= 1e3:
            return f"{value/1e3:.{decimals}f}K"

    return f"{value:,.{decimals}f}"


def format_side_emoji(side: str) -> str:
    """
    Format trade side with emoji.

    Args:
        side: Trade side ('LONG' or 'SHORT')

    Returns:
        Side with emoji
    """
    if side.upper() == 'LONG':
        return "🟢 LONG"
    elif side.upper() == 'SHORT':
        return "🔴 SHORT"
    else:
        return side


def format_exit_reason(reason: str) -> str:
    """
    Format exit reason with emoji.

    Args:
        reason: Exit reason string

    Returns:
        Formatted exit reason with emoji
    """
    reason_map = {
        'take_profit': '🎯 이익 실현',
        'stop_loss': '⚠️ 손절매',
        'signal': '📊 신호',
        'signal_reversal': '🔄 신호 반전',
        'manual': '✋ 수동',
        'circuit_breaker': '🚨 서킷 브레이커',
        'session_end': '🏁 세션 종료',
        'shutdown': '🛑 셧다운'
    }

    return reason_map.get(reason.lower(), reason)


def color_pnl(pnl: float) -> str:
    """
    Return color based on PNL value.

    Args:
        pnl: Profit/Loss value

    Returns:
        Color string (green/red/gray)
    """
    if pnl > 0:
        return "green"
    elif pnl < 0:
        return "red"
    else:
        return "gray"


def format_relative_time(dt: Union[datetime, str]) -> str:
    """
    Format datetime as relative time (e.g., "2 hours ago").

    Args:
        dt: Datetime object or string

    Returns:
        Relative time string
    """
    if isinstance(dt, str):
        try:
            dt = datetime.fromisoformat(dt)
        except ValueError:
            return dt

    if not isinstance(dt, datetime):
        return str(dt)

    now = datetime.now()
    diff = now - dt

    if diff.total_seconds() < 60:
        return "방금 전"
    elif diff.total_seconds() < 3600:
        minutes = int(diff.total_seconds() / 60)
        return f"{minutes}분 전"
    elif diff.total_seconds() < 86400:
        hours = int(diff.total_seconds() / 3600)
        return f"{hours}시간 전"
    else:
        days = int(diff.total_seconds() / 86400)
        return f"{days}일 전"


def truncate_string(text: str, max_length: int = 50, suffix: str = "...") -> str:
    """
    Truncate string to maximum length.

    Args:
        text: String to truncate
        max_length: Maximum length
        suffix: Suffix to add if truncated

    Returns:
        Truncated string
    """
    if len(text) <= max_length:
        return text

    return text[:max_length - len(suffix)] + suffix
