"""
US Market Volatility Hunter - Trading Dashboard

Main entry point for the Streamlit dashboard.
Provides real-time monitoring and control interface for the trading bot.
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
from datetime import datetime

from config.config import Config
from dashboard.utils.data_loader import DashboardDataLoader
from dashboard.utils.bot_controller import BotController
from dashboard.components.metrics import MetricCard


# Page configuration
st.set_page_config(
    page_title="Volatility Hunter Dashboard",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        margin-bottom: 1rem;
    }
    .stMetric {
        background-color: #f0f2f6;
        padding: 10px;
        border-radius: 5px;
    }
</style>
""", unsafe_allow_html=True)


def initialize_session_state():
    """Initialize session state variables."""
    if 'data_loader' not in st.session_state:
        config = Config()
        st.session_state.data_loader = DashboardDataLoader(config.DB_PATH)
        st.session_state.bot_controller = BotController()
        st.session_state.last_refresh = datetime.now()
        st.session_state.auto_refresh_enabled = True
        st.session_state.refresh_interval = 30  # seconds


def render_sidebar():
    """Render sidebar with bot status and navigation."""
    with st.sidebar:
        st.markdown("## 🤖 Bot Status")

        # Get bot status
        bot_controller = st.session_state.bot_controller
        is_running = bot_controller.is_running()

        # Display status badge
        if is_running:
            st.success("🟢 Running")
            status = bot_controller.get_status()

            if status['status'] == 'running':
                st.caption(f"PID: {status['pid']}")
                st.caption(f"CPU: {status['cpu_percent']:.1f}%")
                st.caption(f"Memory: {status['memory_mb']:.1f} MB")

                if status['started_at']:
                    st.caption(f"Started: {status['started_at'].strftime('%H:%M:%S')}")
        else:
            st.error("🔴 Stopped")

        st.markdown("---")

        # Quick stats
        st.markdown("## 📊 Quick Stats")

        try:
            # Get today's summary
            today = datetime.now().strftime('%Y-%m-%d')
            summary = st.session_state.data_loader.get_daily_summary(today)

            if summary:
                st.metric(
                    "Today's PNL",
                    f"${summary.get('total_pnl', 0):.2f}",
                    delta=f"{summary.get('win_rate', 0):.1f}% Win Rate"
                )
                st.metric(
                    "Trades",
                    summary.get('total_trades', 0)
                )
            else:
                st.info("No trading data for today")

            # Get strategy info
            strategy = st.session_state.data_loader.get_today_strategy(today)
            if strategy:
                st.markdown("**Today's Strategy:**")
                st.caption(strategy.get('strategy_name', 'N/A'))
                st.caption(f"Score: {strategy.get('score', 0):.2f}")

        except Exception as e:
            st.caption(f"Error loading stats: {e}")

        st.markdown("---")

        # Settings
        st.markdown("## ⚙️ Settings")

        auto_refresh = st.checkbox(
            "Auto-refresh",
            value=st.session_state.auto_refresh_enabled,
            key="auto_refresh_checkbox"
        )
        st.session_state.auto_refresh_enabled = auto_refresh

        if auto_refresh:
            refresh_interval = st.slider(
                "Refresh interval (seconds)",
                min_value=10,
                max_value=120,
                value=st.session_state.refresh_interval,
                step=10,
                key="refresh_interval_slider"
            )
            st.session_state.refresh_interval = refresh_interval

        # Manual refresh button
        if st.button("🔄 Refresh Now"):
            st.session_state.data_loader.clear_cache()
            st.rerun()

        st.markdown("---")

        # About
        st.markdown("## ℹ️ About")
        st.caption("US Market Volatility Hunter")
        st.caption("High-Leverage Scalping Bot")
        st.caption("Dashboard v1.0.0")


def render_home_page():
    """Render the home/landing page."""
    st.markdown('<div class="main-header">📈 US Market Volatility Hunter</div>', unsafe_allow_html=True)
    st.markdown("### Real-time Trading Dashboard")

    st.markdown("---")

    # Welcome message
    st.markdown("""
    Welcome to the **Volatility Hunter Dashboard**! This dashboard provides comprehensive
    monitoring and control capabilities for your algorithmic trading bot.

    ### 📌 Available Pages:

    **1. 📊 Dashboard** - Real-time monitoring, bot controls, and position tracking
    **2. 🎯 Today's Strategy** - View today's selected strategy and performance metrics
    **3. 📈 History & Analysis** - Analyze historical performance and trade records
    **4. ⚙️ Optimization** - Explore strategy optimization results and parameter tuning

    ### 🚀 Quick Start:

    1. Use the **sidebar navigation** to switch between pages
    2. Check the **bot status** in the sidebar (running/stopped)
    3. Enable **auto-refresh** for real-time updates
    4. Use the **Dashboard** page to start/stop the bot

    ---
    """)

    # Current status overview
    col1, col2, col3, col4 = st.columns(4)

    try:
        # Get current stats
        today = datetime.now().strftime('%Y-%m-%d')
        summary = st.session_state.data_loader.get_daily_summary(today)
        strategy = st.session_state.data_loader.get_today_strategy(today)
        positions = st.session_state.data_loader.get_open_positions()

        with col1:
            if summary:
                st.metric(
                    "Today's PNL",
                    f"${summary.get('total_pnl', 0):,.2f}",
                    delta=f"{summary.get('total_pnl', 0):+.2f}"
                )
            else:
                st.metric("Today's PNL", "$0.00")

        with col2:
            if summary:
                st.metric("Trades Today", summary.get('total_trades', 0))
            else:
                st.metric("Trades Today", "0")

        with col3:
            if summary:
                st.metric("Win Rate", f"{summary.get('win_rate', 0):.1f}%")
            else:
                st.metric("Win Rate", "0%")

        with col4:
            st.metric("Open Positions", len(positions))

    except Exception as e:
        st.error(f"Error loading dashboard data: {e}")

    st.markdown("---")

    # System information
    st.markdown("### 🖥️ System Information")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Trading Configuration:**")
        config = Config()
        st.write(f"- Exchange: {config.EXCHANGE_NAME}")
        st.write(f"- Trading Mode: {config.TRADING_MODE}")
        st.write(f"- Primary Symbol: {config.PRIMARY_SYMBOL}")
        st.write(f"- Leverage: {config.LEVERAGE}x")

    with col2:
        st.markdown("**Bot Information:**")
        bot_controller = st.session_state.bot_controller
        status = bot_controller.get_status()

        if status['status'] == 'running':
            st.write(f"- Status: 🟢 Running")
            st.write(f"- PID: {status['pid']}")
            st.write(f"- Uptime: {status['uptime_seconds'] / 3600:.1f} hours")
            st.write(f"- Memory: {status['memory_mb']:.1f} MB")
        else:
            st.write(f"- Status: 🔴 Stopped")
            st.write("- PID: N/A")
            st.write("- Uptime: 0 hours")
            st.write("- Memory: 0 MB")

    st.markdown("---")

    # Tips
    st.markdown("### 💡 Tips")
    st.info("""
    - **Dashboard Page**: Monitor real-time performance and control the bot
    - **Today's Strategy**: Review the auto-selected strategy and its backtest results
    - **History**: Analyze past performance with advanced filtering
    - **Optimization**: Explore parameter optimization results
    """)


def main():
    """Main application entry point."""
    # Initialize session state
    initialize_session_state()

    # Render sidebar
    render_sidebar()

    # Render home page
    render_home_page()

    # Footer
    st.markdown("---")
    st.caption(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == "__main__":
    main()
