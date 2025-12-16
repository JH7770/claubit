"""
Metric Cards Module

Provides standardized metric display components for the dashboard.
"""

import streamlit as st
from typing import Dict, Optional, Tuple, List
from dashboard.utils.formatters import format_currency, format_percentage


class MetricCard:
    """Standardized metric display components."""

    @staticmethod
    def display_4_column_metrics(
        metrics: List[Tuple[str, str, Optional[str]]]
    ):
        """
        Display 4 metrics in columns.

        Args:
            metrics: List of tuples (label, value, delta)
                Example: [("Balance", "$10,000", "+$500"), ...]
        """
        cols = st.columns(4)

        for i, (label, value, delta) in enumerate(metrics[:4]):  # Limit to 4
            with cols[i]:
                if delta and delta != "":
                    # Determine delta color
                    delta_color = "normal"
                    if isinstance(delta, str):
                        if delta.startswith('-'):
                            delta_color = "inverse"
                        elif delta.startswith('+'):
                            delta_color = "normal"

                    st.metric(
                        label=label,
                        value=value,
                        delta=delta,
                        delta_color=delta_color
                    )
                else:
                    st.metric(label=label, value=value)

    @staticmethod
    def display_grid_metrics(
        metrics: Dict[str, Tuple[str, Optional[str]]],
        columns: int = 3
    ):
        """
        Display metrics in a grid layout.

        Args:
            metrics: Dictionary of {label: (value, delta)}
            columns: Number of columns in grid
        """
        metric_items = list(metrics.items())
        rows = (len(metric_items) + columns - 1) // columns  # Ceiling division

        for row in range(rows):
            cols = st.columns(columns)
            for col_idx in range(columns):
                item_idx = row * columns + col_idx
                if item_idx < len(metric_items):
                    label, (value, delta) = metric_items[item_idx]
                    with cols[col_idx]:
                        if delta:
                            st.metric(label=label, value=value, delta=delta)
                        else:
                            st.metric(label=label, value=value)

    @staticmethod
    def status_indicator(is_running: bool, label: str = "Bot Status") -> str:
        """
        Return colored status indicator.

        Args:
            is_running: Boolean status
            label: Status label

        Returns:
            Formatted status string with emoji
        """
        if is_running:
            return f"{label}: 🟢 Running"
        else:
            return f"{label}: 🔴 Stopped"

    @staticmethod
    def display_status_badge(
        is_running: bool,
        running_text: str = "Running",
        stopped_text: str = "Stopped"
    ):
        """
        Display status as a colored badge.

        Args:
            is_running: Boolean status
            running_text: Text to show when running
            stopped_text: Text to show when stopped
        """
        if is_running:
            st.success(f"🟢 {running_text}")
        else:
            st.error(f"🔴 {stopped_text}")

    @staticmethod
    def format_currency_metric(amount: float, decimals: int = 2) -> str:
        """
        Format currency for metric display.

        Args:
            amount: Amount to format
            decimals: Number of decimal places

        Returns:
            Formatted currency string
        """
        return format_currency(amount, decimals, include_sign=False)

    @staticmethod
    def format_percentage_metric(value: float, decimals: int = 2) -> str:
        """
        Format percentage for metric display.

        Args:
            value: Value to format
            decimals: Number of decimal places

        Returns:
            Formatted percentage string
        """
        return format_percentage(value, decimals, include_sign=False)

    @staticmethod
    def display_kpi_card(
        title: str,
        value: str,
        delta: Optional[str] = None,
        icon: Optional[str] = None,
        color: Optional[str] = None
    ):
        """
        Display a custom KPI card with styling.

        Args:
            title: Card title
            value: Main value to display
            delta: Change/delta value
            icon: Emoji icon
            color: Background color (green/red/blue/gray)
        """
        # Determine background color
        bg_colors = {
            'green': '#D4EDDA',
            'red': '#F8D7DA',
            'blue': '#D1ECF1',
            'gray': '#E2E3E5'
        }
        bg_color = bg_colors.get(color, '#FFFFFF')

        # Build HTML
        icon_html = f"<span style='font-size: 24px;'>{icon}</span> " if icon else ""
        delta_html = f"<div style='color: gray; font-size: 14px;'>{delta}</div>" if delta else ""

        card_html = f"""
        <div style="
            background-color: {bg_color};
            padding: 20px;
            border-radius: 10px;
            border-left: 5px solid {bg_colors.get(color, '#000000')};
            margin-bottom: 10px;
        ">
            <div style="color: #666; font-size: 14px; margin-bottom: 5px;">{icon_html}{title}</div>
            <div style="font-size: 28px; font-weight: bold; margin-bottom: 5px;">{value}</div>
            {delta_html}
        </div>
        """

        st.markdown(card_html, unsafe_allow_html=True)

    @staticmethod
    def display_info_box(
        message: str,
        box_type: str = "info",
        icon: Optional[str] = None
    ):
        """
        Display an informational box.

        Args:
            message: Message to display
            box_type: Type of box (info/warning/success/error)
            icon: Optional emoji icon
        """
        icon_map = {
            'info': 'ℹ️',
            'warning': '⚠️',
            'success': '✅',
            'error': '❌'
        }

        display_icon = icon or icon_map.get(box_type, 'ℹ️')

        if box_type == 'info':
            st.info(f"{display_icon} {message}")
        elif box_type == 'warning':
            st.warning(f"{display_icon} {message}")
        elif box_type == 'success':
            st.success(f"{display_icon} {message}")
        elif box_type == 'error':
            st.error(f"{display_icon} {message}")
        else:
            st.info(f"{display_icon} {message}")

    @staticmethod
    def display_progress_bar(
        current: float,
        total: float,
        label: str = "",
        show_percentage: bool = True
    ):
        """
        Display a progress bar.

        Args:
            current: Current value
            total: Total/max value
            label: Label text
            show_percentage: Show percentage text
        """
        percentage = (current / total) * 100 if total > 0 else 0
        percentage = min(100, max(0, percentage))  # Clamp to 0-100

        if show_percentage:
            st.write(f"{label} ({percentage:.1f}%)")
        else:
            st.write(label)

        st.progress(percentage / 100)

    @staticmethod
    def display_stat_row(stats: List[Tuple[str, str]]):
        """
        Display a row of statistics.

        Args:
            stats: List of (label, value) tuples
        """
        cols = st.columns(len(stats))

        for i, (label, value) in enumerate(stats):
            with cols[i]:
                st.markdown(f"**{label}**")
                st.markdown(f"<h3 style='margin:0;'>{value}</h3>", unsafe_allow_html=True)
