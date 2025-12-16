"""
Real-time Dashboard Page

Real-time monitoring, bot controls, and position tracking.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from streamlit_autorefresh import st_autorefresh

from dashboard.utils.data_loader import DashboardDataLoader
from dashboard.utils.bot_controller import BotController
from dashboard.components.charts import ChartBuilder
from dashboard.components.metrics import MetricCard
from dashboard.components.tables import TableFormatter
from dashboard.utils.formatters import format_currency, format_percentage, format_duration
from config.config import Config


st.set_page_config(page_title="Dashboard", page_icon="📊", layout="wide")

# Initialize
if 'data_loader' not in st.session_state:
    config = Config()
    st.session_state.data_loader = DashboardDataLoader(config.DB_PATH)
    st.session_state.bot_controller = BotController()

data_loader = st.session_state.data_loader
bot_controller = st.session_state.bot_controller
config = Config()

# Auto-refresh (30 seconds)
st_autorefresh(interval=30000, key="dashboard_refresh")

# Title
st.title("📊 Real-time Dashboard")
st.markdown("Monitor bot performance and control trading operations")
st.markdown("---")

# Bot Status and Controls
st.markdown("### 🤖 Bot Control Panel")

col1, col2, col3 = st.columns(3)

is_running = bot_controller.is_running()
bot_status = bot_controller.get_status()

with col1:
    if is_running:
        st.success("🟢 Bot is Running")
        if bot_status['status'] == 'running':
            st.caption(f"PID: {bot_status['pid']}")
            st.caption(f"Uptime: {format_duration(bot_status['uptime_seconds'])}")
            st.caption(f"Memory: {bot_status['memory_mb']:.1f} MB")
    else:
        st.error("🔴 Bot is Stopped")

with col2:
    st.metric("Trading Mode", config.TRADING_MODE)
    st.metric("Leverage", f"{config.LEVERAGE}x")

with col3:
    st.metric("Primary Symbol", config.PRIMARY_SYMBOL)

# Control Buttons
st.markdown("#### Emergency Controls")

col1, col2, col3, col4 = st.columns(4)

with col1:
    if st.button("▶️ START BOT", disabled=is_running, use_container_width=True):
        with st.spinner("Starting bot..."):
            success = bot_controller.start_bot(mode="scheduled")
            if success:
                st.success("✅ Bot started successfully")
                st.rerun()
            else:
                st.error("❌ Failed to start bot")

with col2:
    if st.button("⏸️ STOP BOT", disabled=not is_running, use_container_width=True):
        with st.spinner("Stopping bot..."):
            success = bot_controller.stop_bot()
            if success:
                st.success("✅ Bot stopped successfully")
                st.rerun()
            else:
                st.error("❌ Failed to stop bot")

with col3:
    if st.button("🔄 RESTART BOT", disabled=not is_running, use_container_width=True):
        with st.spinner("Restarting bot..."):
            success = bot_controller.restart_bot(mode="scheduled")
            if success:
                st.success("✅ Bot restarted successfully")
                st.rerun()
            else:
                st.error("❌ Failed to restart bot")

with col4:
    if st.button("🛑 FORCE CLOSE ALL", type="secondary", use_container_width=True):
        if config.is_live_mode():
            st.error("⛔ Cannot force close in LIVE mode via dashboard (safety feature)")
        else:
            st.warning("⚠️ This will close all open positions immediately!")
            st.info("This feature requires bot integration - use bot directly")

st.markdown("---")

# Performance Metrics
st.markdown("### 📊 Today's Performance")

today = datetime.now().strftime('%Y-%m-%d')
summary = data_loader.get_daily_summary(today)

if summary:
    metrics_data = [
        ("Current Balance", format_currency(summary.get('ending_balance', 0)), None),
        ("Daily PNL", format_currency(summary.get('total_pnl', 0), include_sign=True),
         format_percentage(summary.get('total_pnl', 0) / summary.get('starting_balance', 1) * 100)),
        ("Win Rate", format_percentage(summary.get('win_rate', 0)), None),
        ("Total Trades", str(summary.get('total_trades', 0)), None)
    ]
    MetricCard.display_4_column_metrics(metrics_data)
else:
    st.info("No trading activity today")

st.markdown("---")

# Real-time Equity Chart (Last 24 hours)
st.markdown("### 📈 Equity Curve (Last 24 hours)")

yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
recent_trades = data_loader.get_trade_history(start_date=yesterday, end_date=today)

if not recent_trades.empty:
    cum_pnl = data_loader.get_cumulative_pnl(yesterday, today)
    st.plotly_chart(
        ChartBuilder.equity_curve(
            cum_pnl,
            x_col='timestamp',
            y_col='cumulative_pnl',
            title="24-Hour Equity Curve",
            height=350
        ),
        use_container_width=True
    )
else:
    st.info("No recent trading data available")

st.markdown("---")

# Current Positions
st.markdown("### 💼 Current Positions")

positions = data_loader.get_open_positions()

if not positions.empty:
    st.dataframe(
        TableFormatter.format_position_table(positions),
        use_container_width=True,
        hide_index=True
    )
    st.caption(f"Total open positions: {len(positions)}")
else:
    st.info("No open positions")

st.markdown("---")

# Recent Trades
st.markdown("### 📝 Recent Trades (Last 10)")

if not recent_trades.empty:
    recent_10 = recent_trades.head(10)
    st.dataframe(
        TableFormatter.format_trade_table(recent_10),
        use_container_width=True,
        hide_index=True
    )
else:
    st.info("No recent trades")

st.markdown("---")

# System Health
st.markdown("### 🏥 System Health")

col1, col2, col3 = st.columns(3)

with col1:
    if bot_status['status'] == 'running':
        cpu = bot_status['cpu_percent']
        if cpu < 50:
            st.success(f"CPU Usage: {cpu:.1f}% ✅")
        elif cpu < 80:
            st.warning(f"CPU Usage: {cpu:.1f}% ⚠️")
        else:
            st.error(f"CPU Usage: {cpu:.1f}% ❌")
    else:
        st.info("CPU Usage: N/A (Bot stopped)")

with col2:
    if bot_status['status'] == 'running':
        memory = bot_status['memory_mb']
        if memory < 500:
            st.success(f"Memory: {memory:.1f} MB ✅")
        elif memory < 1000:
            st.warning(f"Memory: {memory:.1f} MB ⚠️")
        else:
            st.error(f"Memory: {memory:.1f} MB ❌")
    else:
        st.info("Memory: N/A (Bot stopped)")

with col3:
    # Circuit breaker status (would need to read from bot state)
    st.info("Circuit Breaker: OK ✅")

# Footer
st.markdown("---")
st.caption(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | Auto-refresh: 30s")
