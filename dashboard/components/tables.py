"""
Table Formatters Module

Provides functions to format DataFrames for display in the dashboard.
"""

import pandas as pd
import streamlit as st
from typing import Optional
from dashboard.utils.formatters import (
    format_currency,
    format_percentage,
    format_timestamp,
    format_side_emoji,
    format_exit_reason,
    color_pnl
)


class TableFormatter:
    """Format DataFrames for dashboard display."""

    @staticmethod
    def format_trade_table(df: pd.DataFrame) -> pd.DataFrame:
        """
        Format trade history table with colored PNL.

        Args:
            df: DataFrame with trade data

        Returns:
            Formatted DataFrame
        """
        if df.empty:
            return df

        df_display = df.copy()

        # Format timestamp
        if 'timestamp' in df_display.columns:
            df_display['Time'] = df_display['timestamp'].apply(
                lambda x: format_timestamp(x, "%Y-%m-%d %H:%M")
            )
            df_display = df_display.drop('timestamp', axis=1)

        # Format side with emoji
        if 'side' in df_display.columns:
            df_display['Side'] = df_display['side'].apply(format_side_emoji)
            df_display = df_display.drop('side', axis=1)

        # Format prices
        for col in ['entry_price', 'exit_price']:
            if col in df_display.columns:
                df_display[col.replace('_', ' ').title()] = df_display[col].apply(
                    lambda x: f"${x:,.2f}" if pd.notna(x) else ""
                )
                df_display = df_display.drop(col, axis=1)

        # Format PNL
        if 'pnl' in df_display.columns:
            df_display['PNL'] = df_display['pnl'].apply(
                lambda x: format_currency(x, decimals=2, include_sign=True) if pd.notna(x) else ""
            )
            df_display = df_display.drop('pnl', axis=1)

        # Format PNL percent
        if 'pnl_percent' in df_display.columns:
            df_display['PNL %'] = df_display['pnl_percent'].apply(
                lambda x: format_percentage(x, decimals=2, include_sign=True) if pd.notna(x) else ""
            )
            df_display = df_display.drop('pnl_percent', axis=1)

        # Format exit reason
        if 'exit_reason' in df_display.columns:
            df_display['Exit Reason'] = df_display['exit_reason'].apply(format_exit_reason)
            df_display = df_display.drop('exit_reason', axis=1)

        # Clean up column names
        df_display.columns = [col.replace('_', ' ').title() for col in df_display.columns]

        return df_display

    @staticmethod
    def format_strategy_ranking(df: pd.DataFrame) -> pd.DataFrame:
        """
        Format strategy performance ranking table.

        Args:
            df: DataFrame with strategy ranking data

        Returns:
            Formatted DataFrame
        """
        if df.empty:
            return df

        df_display = df.copy()

        # Add rank medals
        if 'rank' in df_display.columns:
            df_display['Rank'] = df_display['rank'].apply(
                lambda x: f"🥇 {x}" if x == 1 else f"🥈 {x}" if x == 2 else f"🥉 {x}" if x == 3 else str(x)
            )
            df_display = df_display.drop('rank', axis=1)

        # Format numeric columns
        for col in ['total_return', 'win_rate']:
            if col in df_display.columns:
                df_display[col.replace('_', ' ').title()] = df_display[col].apply(
                    lambda x: format_percentage(x, decimals=2, include_sign=False) if pd.notna(x) else ""
                )
                df_display = df_display.drop(col, axis=1)

        for col in ['score', 'profit_factor', 'sharpe_ratio']:
            if col in df_display.columns:
                df_display[col.replace('_', ' ').title()] = df_display[col].apply(
                    lambda x: f"{x:.2f}" if pd.notna(x) else ""
                )
                df_display = df_display.drop(col, axis=1)

        if 'max_drawdown' in df_display.columns:
            df_display['Max Drawdown'] = df_display['max_drawdown'].apply(
                lambda x: format_percentage(abs(x), decimals=2, include_sign=False) if pd.notna(x) else ""
            )
            df_display = df_display.drop('max_drawdown', axis=1)

        # Clean up column names
        df_display.columns = [col.replace('_', ' ').title() for col in df_display.columns]

        return df_display

    @staticmethod
    def format_position_table(df: pd.DataFrame) -> pd.DataFrame:
        """
        Format current positions table with unrealized PNL.

        Args:
            df: DataFrame with position data

        Returns:
            Formatted DataFrame
        """
        if df.empty:
            return df

        df_display = df.copy()

        # Format side with emoji
        if 'side' in df_display.columns:
            df_display['Side'] = df_display['side'].apply(format_side_emoji)
            df_display = df_display.drop('side', axis=1)

        # Format prices
        for col in ['entry_price', 'stop_loss', 'take_profit']:
            if col in df_display.columns:
                df_display[col.replace('_', ' ').title()] = df_display[col].apply(
                    lambda x: f"${x:,.2f}" if pd.notna(x) else ""
                )
                df_display = df_display.drop(col, axis=1)

        # Format opened_at timestamp
        if 'opened_at' in df_display.columns:
            df_display['Opened At'] = df_display['opened_at'].apply(
                lambda x: format_timestamp(x, "%Y-%m-%d %H:%M")
            )
            df_display = df_display.drop('opened_at', axis=1)

        # Clean up column names
        df_display.columns = [col.replace('_', ' ').title() for col in df_display.columns]

        return df_display

    @staticmethod
    def format_daily_summary_table(df: pd.DataFrame) -> pd.DataFrame:
        """
        Format daily summary table.

        Args:
            df: DataFrame with daily summary data

        Returns:
            Formatted DataFrame
        """
        if df.empty:
            return df

        df_display = df.copy()

        # Format date
        if 'date' in df_display.columns:
            df_display['Date'] = pd.to_datetime(df_display['date']).dt.strftime('%Y-%m-%d')
            df_display = df_display.drop('date', axis=1)

        # Format PNL
        if 'total_pnl' in df_display.columns:
            df_display['Total PNL'] = df_display['total_pnl'].apply(
                lambda x: format_currency(x, decimals=2, include_sign=True) if pd.notna(x) else ""
            )
            df_display = df_display.drop('total_pnl', axis=1)

        # Format win rate
        if 'win_rate' in df_display.columns:
            df_display['Win Rate'] = df_display['win_rate'].apply(
                lambda x: format_percentage(x, decimals=1, include_sign=False) if pd.notna(x) else ""
            )
            df_display = df_display.drop('win_rate', axis=1)

        # Format balances
        for col in ['starting_balance', 'ending_balance']:
            if col in df_display.columns:
                df_display[col.replace('_', ' ').title()] = df_display[col].apply(
                    lambda x: f"${x:,.2f}" if pd.notna(x) else ""
                )
                df_display = df_display.drop(col, axis=1)

        # Clean up column names
        df_display.columns = [col.replace('_', ' ').title() for col in df_display.columns]

        return df_display

    @staticmethod
    def display_dataframe(
        df: pd.DataFrame,
        title: Optional[str] = None,
        height: Optional[int] = None,
        use_container_width: bool = True
    ):
        """
        Display DataFrame with title and styling.

        Args:
            df: DataFrame to display
            title: Optional title
            height: Optional height in pixels
            use_container_width: Use full container width
        """
        if title:
            st.subheader(title)

        if df.empty:
            st.info("No data available")
        else:
            st.dataframe(
                df,
                height=height,
                use_container_width=use_container_width
            )

    @staticmethod
    def display_downloadable_table(
        df: pd.DataFrame,
        df_display: Optional[pd.DataFrame] = None,
        filename: str = "data.csv",
        title: Optional[str] = None
    ):
        """
        Display table with download button.

        Args:
            df: Raw DataFrame (for download)
            df_display: Formatted DataFrame for display (optional)
            filename: Download filename
            title: Optional title
        """
        if title:
            st.subheader(title)

        if df.empty:
            st.info("No data available")
            return

        # Display formatted or raw data
        display_df = df_display if df_display is not None else df

        col1, col2 = st.columns([4, 1])

        with col1:
            st.dataframe(display_df, use_container_width=True)

        with col2:
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Download CSV",
                data=csv,
                file_name=filename,
                mime="text/csv"
            )
