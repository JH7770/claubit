"""
Data Loader Module for Dashboard

Provides centralized database query layer with caching and read-only access
to avoid database locks while the bot is running.
"""

import sqlite3
import pandas as pd
from datetime import datetime, timedelta
from typing import Optional, Dict, List
from pathlib import Path
import streamlit as st


class DashboardDataLoader:
    """Handles all database queries for dashboard with caching."""

    def __init__(self, db_path: str):
        """
        Initialize data loader.

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = Path(db_path)

    def _get_connection(self):
        """
        Get read-only database connection.

        Returns:
            SQLite connection in read-only mode
        """
        try:
            conn = sqlite3.connect(
                f"file:{self.db_path}?mode=ro",
                uri=True,
                timeout=10.0
            )
            conn.row_factory = sqlite3.Row
            return conn
        except sqlite3.OperationalError:
            # Fallback to regular connection if read-only fails
            conn = sqlite3.connect(str(self.db_path), timeout=10.0)
            conn.row_factory = sqlite3.Row
            return conn

    @st.cache_data(ttl=30, show_spinner=False)
    def get_bot_status(_self) -> Optional[Dict]:
        """
        Get current bot status from bot_status table.

        Returns:
            Dict with bot status info or None if not found
        """
        try:
            conn = _self._get_connection()
            cursor = conn.execute("""
                SELECT * FROM bot_status
                ORDER BY updated_at DESC
                LIMIT 1
            """)
            result = cursor.fetchone()
            conn.close()

            if result:
                return dict(result)
            return None
        except Exception as e:
            st.warning(f"Error loading bot status: {e}")
            return None

    @st.cache_data(ttl=10, show_spinner=False)
    def get_open_positions(_self) -> pd.DataFrame:
        """
        Get all open positions.

        Returns:
            DataFrame with open positions
        """
        try:
            conn = _self._get_connection()
            df = pd.read_sql_query("""
                SELECT * FROM positions
                WHERE status = 'open'
                ORDER BY opened_at DESC
            """, conn)
            conn.close()
            return df
        except Exception as e:
            st.warning(f"Error loading positions: {e}")
            return pd.DataFrame()

    @st.cache_data(ttl=60, show_spinner=False)
    def get_today_strategy(_self, date: Optional[str] = None) -> Optional[Dict]:
        """
        Get today's selected strategy.

        Args:
            date: Date string (YYYY-MM-DD), defaults to today

        Returns:
            Dict with strategy info or None if not found
        """
        if date is None:
            date = datetime.now().strftime('%Y-%m-%d')

        try:
            conn = _self._get_connection()
            cursor = conn.execute("""
                SELECT * FROM backtest_results
                WHERE date = ?
                ORDER BY score DESC
                LIMIT 1
            """, (date,))
            result = cursor.fetchone()
            conn.close()

            if result:
                return dict(result)
            return None
        except Exception as e:
            st.warning(f"Error loading today's strategy: {e}")
            return None

    @st.cache_data(ttl=300, show_spinner=False)
    def get_strategy_rankings(_self, date: str) -> pd.DataFrame:
        """
        Get all strategy rankings for a specific date.

        Args:
            date: Date string (YYYY-MM-DD)

        Returns:
            DataFrame with all strategies ranked
        """
        try:
            conn = _self._get_connection()
            df = pd.read_sql_query("""
                SELECT * FROM backtest_results
                WHERE date = ?
                ORDER BY score DESC
            """, conn, params=(date,))
            conn.close()
            return df
        except Exception as e:
            st.warning(f"Error loading strategy rankings: {e}")
            return pd.DataFrame()

    @st.cache_data(ttl=60, show_spinner=False)
    def get_daily_summary(_self, date: Optional[str] = None) -> Optional[Dict]:
        """
        Get daily summary for specific date.

        Args:
            date: Date string (YYYY-MM-DD), defaults to today

        Returns:
            Dict with daily summary or None if not found
        """
        if date is None:
            date = datetime.now().strftime('%Y-%m-%d')

        try:
            conn = _self._get_connection()
            cursor = conn.execute("""
                SELECT * FROM daily_summary
                WHERE date = ?
            """, (date,))
            result = cursor.fetchone()
            conn.close()

            if result:
                return dict(result)
            return None
        except Exception as e:
            st.warning(f"Error loading daily summary: {e}")
            return None

    @st.cache_data(ttl=300, show_spinner=False)
    def get_trade_history(_self,
                          start_date: Optional[str] = None,
                          end_date: Optional[str] = None,
                          symbol: Optional[str] = None,
                          strategy: Optional[str] = None) -> pd.DataFrame:
        """
        Get trade history with optional filters.

        Args:
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            symbol: Filter by symbol
            strategy: Filter by strategy name

        Returns:
            DataFrame with trade history
        """
        if start_date is None:
            start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        if end_date is None:
            end_date = datetime.now().strftime('%Y-%m-%d')

        query = """
            SELECT * FROM trade_history
            WHERE DATE(timestamp) BETWEEN ? AND ?
        """
        params = [start_date, end_date]

        if symbol:
            query += " AND symbol = ?"
            params.append(symbol)

        if strategy:
            query += " AND strategy_name = ?"
            params.append(strategy)

        query += " ORDER BY timestamp DESC"

        try:
            conn = _self._get_connection()
            df = pd.read_sql_query(query, conn, params=params)
            conn.close()

            # Convert timestamp to datetime
            if not df.empty and 'timestamp' in df.columns:
                df['timestamp'] = pd.to_datetime(df['timestamp'])

            return df
        except Exception as e:
            st.warning(f"Error loading trade history: {e}")
            return pd.DataFrame()

    @st.cache_data(ttl=300, show_spinner=False)
    def get_daily_summaries(_self,
                           start_date: Optional[str] = None,
                           end_date: Optional[str] = None) -> pd.DataFrame:
        """
        Get daily summaries for a date range.

        Args:
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)

        Returns:
            DataFrame with daily summaries
        """
        if start_date is None:
            start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        if end_date is None:
            end_date = datetime.now().strftime('%Y-%m-%d')

        try:
            conn = _self._get_connection()
            df = pd.read_sql_query("""
                SELECT * FROM daily_summary
                WHERE date BETWEEN ? AND ?
                ORDER BY date ASC
            """, conn, params=(start_date, end_date))
            conn.close()

            # Convert date to datetime
            if not df.empty and 'date' in df.columns:
                df['date'] = pd.to_datetime(df['date'])

            return df
        except Exception as e:
            st.warning(f"Error loading daily summaries: {e}")
            return pd.DataFrame()

    @st.cache_data(ttl=300, show_spinner=False)
    def get_optimization_runs(_self, limit: int = 20) -> pd.DataFrame:
        """
        Get optimization run history.

        Args:
            limit: Maximum number of runs to retrieve

        Returns:
            DataFrame with optimization runs
        """
        try:
            conn = _self._get_connection()
            df = pd.read_sql_query("""
                SELECT * FROM optimization_runs
                ORDER BY date DESC, created_at DESC
                LIMIT ?
            """, conn, params=(limit,))
            conn.close()

            # Convert date to datetime
            if not df.empty and 'date' in df.columns:
                df['date'] = pd.to_datetime(df['date'])

            return df
        except Exception as e:
            st.warning(f"Error loading optimization runs: {e}")
            return pd.DataFrame()

    def get_cumulative_pnl(_self,
                           start_date: Optional[str] = None,
                           end_date: Optional[str] = None) -> pd.DataFrame:
        """
        Calculate cumulative PNL from trade history.

        Args:
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)

        Returns:
            DataFrame with cumulative PNL
        """
        trades = _self.get_trade_history(start_date, end_date)

        if trades.empty:
            return pd.DataFrame()

        # Calculate cumulative sum
        trades = trades.sort_values('timestamp')
        trades['cumulative_pnl'] = trades['pnl'].cumsum()

        return trades[['timestamp', 'pnl', 'cumulative_pnl', 'symbol', 'strategy_name']]

    def get_unique_symbols(_self) -> List[str]:
        """
        Get list of unique symbols traded.

        Returns:
            List of symbol strings
        """
        try:
            conn = _self._get_connection()
            cursor = conn.execute("""
                SELECT DISTINCT symbol FROM trade_history
                ORDER BY symbol
            """)
            symbols = [row[0] for row in cursor.fetchall()]
            conn.close()
            return symbols
        except Exception as e:
            st.warning(f"Error loading symbols: {e}")
            return []

    def get_unique_strategies(_self) -> List[str]:
        """
        Get list of unique strategies used.

        Returns:
            List of strategy name strings
        """
        try:
            conn = _self._get_connection()
            cursor = conn.execute("""
                SELECT DISTINCT strategy_name FROM trade_history
                WHERE strategy_name IS NOT NULL
                ORDER BY strategy_name
            """)
            strategies = [row[0] for row in cursor.fetchall()]
            conn.close()
            return strategies
        except Exception as e:
            st.warning(f"Error loading strategies: {e}")
            return []

    def get_trade_statistics(_self,
                            start_date: Optional[str] = None,
                            end_date: Optional[str] = None) -> Dict:
        """
        Get aggregated trade statistics for a date range.

        Args:
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)

        Returns:
            Dict with aggregated statistics
        """
        trades = _self.get_trade_history(start_date, end_date)

        if trades.empty:
            return {
                'total_trades': 0,
                'winning_trades': 0,
                'losing_trades': 0,
                'win_rate': 0.0,
                'total_pnl': 0.0,
                'avg_pnl': 0.0,
                'best_trade': 0.0,
                'worst_trade': 0.0
            }

        winning_trades = len(trades[trades['pnl'] > 0])
        losing_trades = len(trades[trades['pnl'] <= 0])
        total_trades = len(trades)

        return {
            'total_trades': total_trades,
            'winning_trades': winning_trades,
            'losing_trades': losing_trades,
            'win_rate': (winning_trades / total_trades * 100) if total_trades > 0 else 0.0,
            'total_pnl': trades['pnl'].sum(),
            'avg_pnl': trades['pnl'].mean(),
            'best_trade': trades['pnl'].max(),
            'worst_trade': trades['pnl'].min()
        }

    def clear_cache(_self):
        """Clear all cached data."""
        st.cache_data.clear()
