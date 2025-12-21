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
from dashboard.utils.theme import apply_dark_mode_css, initialize_dark_mode


# Page configuration
st.set_page_config(
    page_title="변동성 헌터 대시보드",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize dark mode immediately to prevent flash
initialize_dark_mode()

# Enhanced Custom CSS
st.markdown("""
<style>
    /* ==================== Global Styles ==================== */

    /* Main container */
    .main {
        background-color: #fafafa;
    }

    /* Headers */
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f2937;
        margin-bottom: 1rem;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }

    h1, h2, h3 {
        color: #1f2937;
        font-weight: 600;
    }

    /* ==================== Metric Cards ==================== */

    .stMetric {
        background: white;
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        border: 1px solid #e5e7eb;
        transition: all 0.3s ease;
    }

    .stMetric:hover {
        box-shadow: 0 4px 12px rgba(0,0,0,0.12);
        transform: translateY(-2px);
    }

    .stMetric label {
        font-size: 0.875rem;
        color: #6b7280;
        font-weight: 500;
    }

    .stMetric [data-testid="stMetricValue"] {
        font-size: 1.875rem;
        color: #1f2937;
        font-weight: 700;
    }

    .stMetric [data-testid="stMetricDelta"] {
        font-size: 0.875rem;
        font-weight: 600;
    }

    /* ==================== Buttons ==================== */

    .stButton button {
        border-radius: 8px;
        font-weight: 600;
        border: none;
        padding: 0.5rem 1.5rem;
        transition: all 0.2s ease;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }

    .stButton button:hover {
        box-shadow: 0 4px 8px rgba(0,0,0,0.15);
        transform: translateY(-1px);
    }

    /* Primary button */
    .stButton button[kind="primary"] {
        background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
    }

    .stButton button[kind="primary"]:hover {
        background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%);
    }

    /* Secondary button */
    .stButton button[kind="secondary"] {
        background-color: #f3f4f6;
        color: #374151;
    }

    .stButton button[kind="secondary"]:hover {
        background-color: #e5e7eb;
    }

    /* ==================== Status Boxes ==================== */

    .element-container:has(> .stAlert) {
        margin: 0.5rem 0;
    }

    /* Success box */
    .stSuccess {
        background-color: #d1fae5;
        border-left: 4px solid #10b981;
        border-radius: 8px;
        padding: 1rem;
    }

    /* Warning box */
    .stWarning {
        background-color: #fef3c7;
        border-left: 4px solid #f59e0b;
        border-radius: 8px;
        padding: 1rem;
    }

    /* Error box */
    .stError {
        background-color: #fee2e2;
        border-left: 4px solid #ef4444;
        border-radius: 8px;
        padding: 1rem;
    }

    /* Info box */
    .stInfo {
        background-color: #dbeafe;
        border-left: 4px solid #3b82f6;
        border-radius: 8px;
        padding: 1rem;
    }

    /* ==================== Tabs ==================== */

    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: #f9fafb;
        padding: 0.5rem;
        border-radius: 12px;
    }

    .stTabs [data-baseweb="tab"] {
        border-radius: 8px;
        padding: 0.75rem 1.5rem;
        font-weight: 600;
        color: #6b7280;
        background-color: transparent;
        border: none;
    }

    .stTabs [aria-selected="true"] {
        background-color: white;
        color: #3b82f6;
        box-shadow: 0 2px 4px rgba(0,0,0,0.08);
    }

    /* ==================== Dataframes/Tables ==================== */

    .stDataFrame {
        border-radius: 12px;
        overflow: hidden;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
    }

    /* ==================== Expander ==================== */

    .streamlit-expanderHeader {
        background-color: #f9fafb;
        border-radius: 8px;
        font-weight: 600;
        color: #1f2937;
        padding: 0.75rem 1rem;
    }

    .streamlit-expanderHeader:hover {
        background-color: #f3f4f6;
    }

    /* ==================== Sidebar ==================== */

    [data-testid="stSidebar"] {
        background-color: #f9fafb;
        border-right: 1px solid #e5e7eb;
    }

    [data-testid="stSidebar"] .stMarkdown {
        padding: 0.5rem 0;
    }

    /* ==================== Divider ==================== */

    hr {
        margin: 2rem 0;
        border: none;
        border-top: 2px solid #e5e7eb;
    }

    /* ==================== Card Container ==================== */

    .card {
        background: white;
        padding: 1.5rem;
        border-radius: 12px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        margin-bottom: 1.5rem;
        border: 1px solid #e5e7eb;
    }

    /* ==================== Compact Mode ==================== */

    .compact-mode .stMetric {
        padding: 12px;
    }

    .compact-mode .stMetric [data-testid="stMetricValue"] {
        font-size: 1.5rem;
    }

    .compact-mode .stButton button {
        padding: 0.375rem 1rem;
        font-size: 0.875rem;
    }

    .compact-mode hr {
        margin: 1rem 0;
    }

    /* ==================== Animations ==================== */

    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }

    .element-container {
        animation: fadeIn 0.3s ease-out;
    }

    /* ==================== Page Links ==================== */

    .stPageLink {
        text-decoration: none;
    }

    .stPageLink button {
        width: 100%;
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)


def initialize_session_state():
    """Initialize session state variables."""
    if 'data_loader' not in st.session_state:
        config = Config()
        st.session_state.data_loader = DashboardDataLoader(config.DB_PATH)

    if 'bot_controller' not in st.session_state:
        st.session_state.bot_controller = BotController()

    if 'last_refresh' not in st.session_state:
        st.session_state.last_refresh = datetime.now()

    if 'auto_refresh_enabled' not in st.session_state:
        st.session_state.auto_refresh_enabled = True

    if 'refresh_interval' not in st.session_state:
        st.session_state.refresh_interval = 30  # seconds

    if 'compact_mode' not in st.session_state:
        st.session_state.compact_mode = False

    if 'dark_mode' not in st.session_state:
        st.session_state.dark_mode = False


def render_sidebar():
    """Render sidebar with bot status and navigation."""
    with st.sidebar:
        st.markdown("## 🤖 봇 상태")

        # Get bot status
        bot_controller = st.session_state.bot_controller
        is_running = bot_controller.is_running()

        # Display status badge
        if is_running:
            st.success("🟢 실행 중")
            status = bot_controller.get_status()

            if status['status'] == 'running':
                st.caption(f"PID: {status['pid']}")
                st.caption(f"CPU: {status['cpu_percent']:.1f}%")
                st.caption(f"Memory: {status['memory_mb']:.1f} MB")

                if status['started_at']:
                    st.caption(f"시작 시간: {status['started_at'].strftime('%H:%M:%S')}")
        else:
            st.error("🔴 중지됨")

        st.markdown("---")

        # Quick stats
        st.markdown("## 📊 빠른 통계")

        try:
            # Get today's summary
            today = datetime.now().strftime('%Y-%m-%d')
            summary = st.session_state.data_loader.get_daily_summary(today)

            if summary:
                st.metric(
                    "오늘의 PNL",
                    f"${summary.get('total_pnl', 0):.2f}",
                    delta=f"승률 {summary.get('win_rate', 0):.1f}%"
                )
                st.metric(
                    "거래 횟수",
                    summary.get('total_trades', 0)
                )
            else:
                st.info("오늘 거래 데이터 없음")

            # Get strategy info
            strategy = st.session_state.data_loader.get_today_strategy(today)
            if strategy:
                st.markdown("**오늘의 전략:**")
                st.caption(strategy.get('strategy_name', 'N/A'))
                st.caption(f"점수: {strategy.get('score', 0):.2f}")

        except Exception as e:
            st.caption(f"통계 로드 오류: {e}")

        st.markdown("---")

        # Settings
        st.markdown("## ⚙️ 설정")

        # Dark mode toggle
        dark_mode = st.checkbox(
            "🌙 다크 모드",
            value=st.session_state.dark_mode,
            key="dark_mode_checkbox",
            help="어두운 테마로 전환하여 눈의 피로를 줄입니다"
        )
        if dark_mode != st.session_state.dark_mode:
            st.session_state.dark_mode = dark_mode
            # Save to localStorage before rerun
            save_script = f"""
            <script>
                localStorage.setItem('claubit_dark_mode', '{str(dark_mode).lower()}');
            </script>
            """
            st.markdown(save_script, unsafe_allow_html=True)
            st.rerun()

        # Compact mode toggle
        compact_mode = st.checkbox(
            "📏 컴팩트 모드",
            value=st.session_state.compact_mode,
            key="compact_mode_checkbox",
            help="UI 요소의 크기와 간격을 줄여 더 많은 정보를 화면에 표시합니다"
        )
        st.session_state.compact_mode = compact_mode

        auto_refresh = st.checkbox(
            "자동 새로고침",
            value=st.session_state.auto_refresh_enabled,
            key="auto_refresh_checkbox"
        )
        st.session_state.auto_refresh_enabled = auto_refresh

        if auto_refresh:
            refresh_interval = st.slider(
                "새로고침 간격 (초)",
                min_value=10,
                max_value=120,
                value=st.session_state.refresh_interval,
                step=10,
                key="refresh_interval_slider"
            )
            st.session_state.refresh_interval = refresh_interval

        # Manual refresh button
        if st.button("🔄 지금 새로고침", use_container_width=True):
            st.session_state.data_loader.clear_cache()
            st.rerun()

        st.markdown("---")

        # About
        st.markdown("## ℹ️ 정보")
        st.caption("미국 시장 변동성 헌터")
        st.caption("고배율 스캐핑 봇")
        st.caption("Dashboard v1.0.0")


def render_home_page():
    """Render the home/landing page."""
    st.markdown('<div class="main-header">📈 미국 시장 변동성 헌터</div>', unsafe_allow_html=True)
    st.markdown("### 실시간 트레이딩 대시보드")

    st.markdown("---")

    # ==========================================================================
    # SECTION 1: ALERT CENTER (경고/알림 센터)
    # ==========================================================================
    st.markdown("### 🔔 경고 및 알림 센터")

    try:
        # Get current data
        today = datetime.now().strftime('%Y-%m-%d')
        summary = st.session_state.data_loader.get_daily_summary(today)
        positions = st.session_state.data_loader.get_open_positions()
        bot_controller = st.session_state.bot_controller
        bot_status = bot_controller.get_status()

        # Calculate alerts
        open_positions_count = len(positions) if not positions.empty else 0
        losing_positions = 0
        total_unrealized_pnl = 0

        if not positions.empty and 'unrealized_pnl' in positions.columns:
            losing_positions = len(positions[positions['unrealized_pnl'] < 0])
            total_unrealized_pnl = positions['unrealized_pnl'].sum()

        # Today's PNL percentage
        today_pnl_pct = 0
        if summary and summary.get('starting_balance', 0) > 0:
            today_pnl_pct = (summary.get('total_pnl', 0) / summary.get('starting_balance', 1)) * 100

        # Display alerts in 4 columns
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            if bot_status['status'] == 'running':
                st.success("🟢 봇 상태: 실행 중")
            else:
                st.error("🔴 봇 상태: 중지됨")

        with col2:
            if open_positions_count > 0:
                if losing_positions > 0:
                    st.warning(f"⚠️ 오픈 포지션: {open_positions_count}개\n손실 포지션: {losing_positions}개")
                else:
                    st.info(f"📊 오픈 포지션: {open_positions_count}개")
            else:
                st.info("✅ 포지션 없음")

        with col3:
            if today_pnl_pct < -3:
                st.error(f"📉 오늘 PNL: {today_pnl_pct:.2f}%\n주의 필요!")
            elif today_pnl_pct < 0:
                st.warning(f"📊 오늘 PNL: {today_pnl_pct:.2f}%")
            elif today_pnl_pct > 0:
                st.success(f"📈 오늘 PNL: +{today_pnl_pct:.2f}%")
            else:
                st.info("📊 오늘 PNL: 0.00%")

        with col4:
            # Circuit breaker status (simplified)
            if today_pnl_pct < -5:
                st.error("🚨 서킷 브레이커: 경고")
            else:
                st.success("✅ 서킷 브레이커: OK")

    except Exception as e:
        st.error(f"경고 센터 로드 오류: {e}")

    st.markdown("---")

    # ==========================================================================
    # SECTION 2: QUICK ACTIONS (빠른 실행)
    # ==========================================================================
    st.markdown("### 🚀 빠른 실행")

    col1, col2, col3, col4 = st.columns(4)

    try:
        is_running = bot_controller.is_running()

        with col1:
            if st.button("▶️ 봇 시작", use_container_width=True, disabled=is_running, type="primary"):
                success = bot_controller.start_bot(mode="scheduled")
                if success:
                    st.success("✅ 봇이 시작되었습니다!")
                    st.rerun()
                else:
                    st.error("❌ 봇 시작 실패")

        with col2:
            if st.button("⏸️ 봇 중지", use_container_width=True, disabled=not is_running):
                success = bot_controller.stop_bot()
                if success:
                    st.success("✅ 봇이 중지되었습니다!")
                    st.rerun()
                else:
                    st.error("❌ 봇 중지 실패")

        with col3:
            if st.button("🔄 새로고침", use_container_width=True):
                st.session_state.data_loader.clear_cache()
                st.rerun()

        with col4:
            # Link to dashboard page
            st.page_link("pages/1_📊_Dashboard.py", label="📊 대시보드로", use_container_width=True)

    except Exception as e:
        st.error(f"빠른 실행 오류: {e}")

    st.markdown("---")

    # ==========================================================================
    # SECTION 3: CORE KPI METRICS (핵심 성과 지표)
    # ==========================================================================
    st.markdown("### 📊 핵심 성과 지표")

    col1, col2, col3, col4 = st.columns(4)

    try:
        with col1:
            if summary:
                st.metric(
                    "오늘의 PNL",
                    f"${summary.get('total_pnl', 0):,.2f}",
                    delta=f"{summary.get('total_pnl', 0):+.2f}"
                )
            else:
                st.metric("오늘의 PNL", "$0.00")

        with col2:
            if summary:
                st.metric("오늘 거래 횟수", summary.get('total_trades', 0))
            else:
                st.metric("오늘 거래 횟수", "0")

        with col3:
            if summary:
                st.metric("승률", f"{summary.get('win_rate', 0):.1f}%")
            else:
                st.metric("승률", "0%")

        with col4:
            st.metric("오픈 포지션", open_positions_count)

    except Exception as e:
        st.error(f"KPI 지표 로드 오류: {e}")

    st.markdown("---")

    # ==========================================================================
    # SECTION 4: RECENT ACTIVITY (최근 활동)
    # ==========================================================================
    st.markdown("### 📋 최근 활동 (최근 5개)")

    try:
        data_loader = st.session_state.data_loader
        recent_activities = data_loader.get_recent_activity(limit=5)

        if not recent_activities.empty:
            for idx, activity in recent_activities.iterrows():
                # Format timestamp
                timestamp = activity.get('timestamp', 'N/A')
                if hasattr(timestamp, 'strftime'):
                    time_str = timestamp.strftime('%H:%M:%S')
                else:
                    time_str = str(timestamp)

                # Get event details
                event_type = activity.get('event_type', 'unknown')
                message = activity.get('message', '이벤트 없음')
                severity = activity.get('severity', 'info')

                # Choose emoji based on severity
                emoji_map = {
                    'error': '❌',
                    'warning': '⚠️',
                    'success': '✅',
                    'info': 'ℹ️'
                }
                emoji = emoji_map.get(severity, 'ℹ️')

                # Display activity
                if severity == 'error':
                    st.error(f"{emoji} **{time_str}** - {message}")
                elif severity == 'warning':
                    st.warning(f"{emoji} **{time_str}** - {message}")
                elif severity == 'success':
                    st.success(f"{emoji} **{time_str}** - {message}")
                else:
                    st.info(f"{emoji} **{time_str}** - {message}")
        else:
            st.info("최근 활동이 없습니다.")

    except Exception as e:
        st.error(f"최근 활동 로드 오류: {e}")

    st.markdown("---")

    # ==========================================================================
    # SECTION 5: QUICK LINKS (빠른 링크)
    # ==========================================================================
    st.markdown("### 🔗 빠른 링크")

    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        st.page_link("pages/1_📊_Dashboard.py", label="📊 실시간 대시보드", use_container_width=True)

    with col2:
        st.page_link("pages/2_🎯_Today_Strategy.py", label="🎯 오늘의 전략", use_container_width=True)

    with col3:
        st.page_link("pages/3_📈_History.py", label="📈 거래 기록", use_container_width=True)

    with col4:
        st.page_link("pages/4_⚙️_Optimization.py", label="⚙️ 최적화", use_container_width=True)

    with col5:
        st.page_link("pages/5_🔬_Advanced_Analytics.py", label="🔬 고급 분석", use_container_width=True)


def main():
    """Main application entry point."""
    # Initialize session state
    initialize_session_state()

    # Apply dark mode CSS
    apply_dark_mode_css()

    # Apply compact mode if enabled
    if st.session_state.compact_mode:
        st.markdown("""
        <style>
            /* Compact mode overrides */
            .main .block-container {
                padding-top: 2rem;
                padding-bottom: 2rem;
            }
            .stMetric {
                padding: 12px !important;
            }
            .stMetric [data-testid="stMetricValue"] {
                font-size: 1.5rem !important;
            }
            .stButton button {
                padding: 0.375rem 1rem !important;
                font-size: 0.875rem !important;
            }
            hr {
                margin: 1rem 0 !important;
            }
            .stMarkdown h3 {
                font-size: 1.25rem !important;
                margin-top: 1rem !important;
                margin-bottom: 0.5rem !important;
            }
            .stTabs [data-baseweb="tab"] {
                padding: 0.5rem 1rem !important;
            }
        </style>
        """, unsafe_allow_html=True)

    # Render sidebar
    render_sidebar()

    # Render home page
    render_home_page()

    # Footer
    st.markdown("---")
    st.caption(f"마지막 업데이트: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == "__main__":
    main()
