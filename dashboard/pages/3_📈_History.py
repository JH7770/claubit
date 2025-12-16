"""
History & Analysis Page

Historical trade analysis with filtering and comprehensive visualizations.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

from dashboard.utils.data_loader import DashboardDataLoader
from dashboard.components.charts import ChartBuilder
from dashboard.components.metrics import MetricCard
from dashboard.components.tables import TableFormatter
from dashboard.utils.formatters import format_currency, format_percentage
from config.config import Config


st.set_page_config(page_title="History & Analysis", page_icon="📈", layout="wide")

# Title
st.title("📈 History & Analysis")
st.markdown("Analyze historical trading performance and detailed trade records")
st.markdown("---")

# Initialize data loader
if 'data_loader' not in st.session_state:
    config = Config()
    st.session_state.data_loader = DashboardDataLoader(config.DB_PATH)

data_loader = st.session_state.data_loader

# Filters Section
st.markdown("### 🔍 Filters")

col1, col2, col3, col4 = st.columns(4)

with col1:
    start_date = st.date_input(
        "Start Date",
        value=datetime.now() - timedelta(days=30),
        max_value=datetime.now()
    )

with col2:
    end_date = st.date_input(
        "End Date",
        value=datetime.now(),
        max_value=datetime.now()
    )

with col3:
    # Get unique symbols
    symbols = data_loader.get_unique_symbols()
    symbol_filter = st.selectbox(
        "Symbol",
        options=["All"] + symbols,
        index=0
    )

with col4:
    # Get unique strategies
    strategies = data_loader.get_unique_strategies()
    strategy_filter = st.selectbox(
        "Strategy",
        options=["All"] + strategies,
        index=0
    )

# Convert dates to strings
start_date_str = start_date.strftime('%Y-%m-%d')
end_date_str = end_date.strftime('%Y-%m-%d')

# Apply filters
symbol_param = None if symbol_filter == "All" else symbol_filter
strategy_param = None if strategy_filter == "All" else strategy_filter

st.markdown("---")

# Load data
trades = data_loader.get_trade_history(
    start_date=start_date_str,
    end_date=end_date_str,
    symbol=symbol_param,
    strategy=strategy_param
)

daily_summaries = data_loader.get_daily_summaries(
    start_date=start_date_str,
    end_date=end_date_str
)

# Performance Summary Metrics
st.markdown("### 📊 Performance Summary")

if not trades.empty:
    stats = data_loader.get_trade_statistics(start_date_str, end_date_str)

    metrics_data = [
        ("Total Trades", str(stats['total_trades']), None),
        ("Total PNL", format_currency(stats['total_pnl'], include_sign=True), None),
        ("Win Rate", format_percentage(stats['win_rate']), None),
        ("Avg PNL", format_currency(stats['avg_pnl'], include_sign=True), None)
    ]

    MetricCard.display_4_column_metrics(metrics_data)

    col1, col2 = st.columns(2)
    with col1:
        st.metric("Best Trade", format_currency(stats['best_trade'], include_sign=True))
    with col2:
        st.metric("Worst Trade", format_currency(stats['worst_trade'], include_sign=True))

else:
    st.info("No trades found for the selected filters")

st.markdown("---")

# Cumulative Return Chart
st.markdown("### 📈 Cumulative Return")

if not trades.empty:
    cum_pnl = data_loader.get_cumulative_pnl(start_date_str, end_date_str)

    if not cum_pnl.empty:
        st.plotly_chart(
            ChartBuilder.equity_curve(
                cum_pnl,
                x_col='timestamp',
                y_col='cumulative_pnl',
                title="Cumulative PNL Over Time",
                height=400
            ),
            use_container_width=True
        )
    else:
        st.info("No cumulative PNL data available")
else:
    st.info("No trade data to display")

st.markdown("---")

# Daily PNL Chart
st.markdown("### 📊 Daily PNL")

if not daily_summaries.empty:
    st.plotly_chart(
        ChartBuilder.daily_pnl_bar(
            daily_summaries,
            date_col='date',
            pnl_col='total_pnl',
            title="Daily Profit/Loss",
            height=400
        ),
        use_container_width=True
    )
else:
    st.info("No daily summary data available")

st.markdown("---")

# Exit Reason Distribution
st.markdown("### 🎯 Exit Reason Distribution")

if not trades.empty and 'exit_reason' in trades.columns:
    col1, col2 = st.columns([2, 1])

    with col1:
        st.plotly_chart(
            ChartBuilder.exit_reason_pie(
                trades,
                reason_col='exit_reason',
                title="Trade Exit Reasons",
                height=400
            ),
            use_container_width=True
        )

    with col2:
        st.markdown("#### Exit Reasons")
        reason_counts = trades['exit_reason'].value_counts()
        for reason, count in reason_counts.items():
            st.write(f"**{reason}**: {count} ({count/len(trades)*100:.1f}%)")

else:
    st.info("No exit reason data available")

st.markdown("---")

# Trade Log Table
st.markdown("### 📋 Trade Log")

if not trades.empty:
    # Format trade table
    trades_display = TableFormatter.format_trade_table(trades)

    # Pagination
    page_size = 50
    total_trades = len(trades_display)
    total_pages = (total_trades + page_size - 1) // page_size

    col1, col2, col3 = st.columns([2, 1, 1])

    with col1:
        st.caption(f"Total trades: {total_trades}")

    with col2:
        page = st.number_input(
            "Page",
            min_value=1,
            max_value=max(1, total_pages),
            value=1,
            step=1
        )

    with col3:
        csv = trades.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Download CSV",
            data=csv,
            file_name=f"trades_{start_date_str}_to_{end_date_str}.csv",
            mime="text/csv"
        )

    # Display paginated table
    start_idx = (page - 1) * page_size
    end_idx = min(start_idx + page_size, total_trades)

    st.dataframe(
        trades_display.iloc[start_idx:end_idx],
        use_container_width=True,
        hide_index=True
    )

    st.caption(f"Showing {start_idx + 1}-{end_idx} of {total_trades} trades")

else:
    st.info("No trades to display")

st.markdown("---")

# Additional Analytics
with st.expander("📊 Additional Analytics"):
    if not trades.empty:
        st.markdown("#### Trade Duration Analysis")

        if 'duration_seconds' in trades.columns:
            trades['duration_minutes'] = trades['duration_seconds'] / 60
            avg_duration = trades['duration_minutes'].mean()
            max_duration = trades['duration_minutes'].max()
            min_duration = trades['duration_minutes'].min()

            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Avg Duration", f"{avg_duration:.1f} min")
            with col2:
                st.metric("Max Duration", f"{max_duration:.1f} min")
            with col3:
                st.metric("Min Duration", f"{min_duration:.1f} min")

        st.markdown("#### PNL Distribution")

        if 'pnl' in trades.columns:
            positive_trades = trades[trades['pnl'] > 0]
            negative_trades = trades[trades['pnl'] <= 0]

            col1, col2 = st.columns(2)
            with col1:
                st.metric(
                    "Avg Winning Trade",
                    format_currency(positive_trades['pnl'].mean() if not positive_trades.empty else 0)
                )
            with col2:
                st.metric(
                    "Avg Losing Trade",
                    format_currency(negative_trades['pnl'].mean() if not negative_trades.empty else 0)
                )

        st.markdown("#### Strategy Performance Breakdown")

        if 'strategy_name' in trades.columns and 'pnl' in trades.columns:
            strategy_pnl = trades.groupby('strategy_name')['pnl'].agg(['sum', 'mean', 'count'])
            strategy_pnl.columns = ['Total PNL', 'Avg PNL', 'Trade Count']
            strategy_pnl = strategy_pnl.sort_values('Total PNL', ascending=False)

            st.dataframe(strategy_pnl, use_container_width=True)

# Footer
st.markdown("---")
st.caption(f"Date range: {start_date_str} to {end_date_str} | Last updated: {datetime.now().strftime('%H:%M:%S')}")
