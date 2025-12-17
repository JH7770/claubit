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
    page_title="변동성 헌터 대시보드",
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
        if st.button("🔄 지금 새로고침"):
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

    # Welcome message
    st.markdown("""
    **변동성 헌터 대시보드**에 오신 것을 환영합니다! 이 대시보드는 
    알고리즘 트레이딩 봇에 대한 포괄적인 모니터링 및 제어 기능을 제공합니다.

    ### 📌 사용 가능한 페이지:

    **1. 📊 대시보드** - 실시간 모니터링, 봇 제어 및 포지션 추적
    **2. 🎯 오늘의 전략** - 오늘 선택된 전략 및 성과 지표 보기
    **3. 📈 기록 및 분석** - 과거 성과 및 거래 기록 분석
    **4. ⚙️ 최적화** - 전략 최적화 결과 및 파라미터 조정 탐색

    ### 🚀 빠른 시작:

    1. **사이드바 탐색**을 사용하여 페이지 전환
    2. 사이드바에서 **봇 상태** 확인 (실행 중/중지됨)
    3. 실시간 업데이트를 위해 **자동 새로고침** 활성화
    4. **대시보드** 페이지를 사용하여 봇 시작/중지

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
            st.metric("오픈 포지션", len(positions))

    except Exception as e:
        st.error(f"대시보드 데이터 로드 오류: {e}")

    st.markdown("---")

    # System information
    st.markdown("### 🖥️ 시스템 정보")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**트레이딩 구성:**")
        config = Config()
        st.write(f"- 거래소: {config.EXCHANGE_NAME}")
        st.write(f"- 트레이딩 모드: {config.TRADING_MODE}")
        st.write(f"- 주요 심볼: {config.PRIMARY_SYMBOL}")
        st.write(f"- 레버리지: {config.LEVERAGE}x")

    with col2:
        st.markdown("**봇 정보:**")
        bot_controller = st.session_state.bot_controller
        status = bot_controller.get_status()

        if status['status'] == 'running':
            st.write(f"- 상태: 🟢 실행 중")
            st.write(f"- PID: {status['pid']}")
            st.write(f"- 가동 시간: {status['uptime_seconds'] / 3600:.1f} 시간")
            st.write(f"- 메모리: {status['memory_mb']:.1f} MB")
        else:
            st.write(f"- 상태: 🔴 중지됨")
            st.write("- PID: N/A")
            st.write("- 가동 시간: 0 시간")
            st.write("- 메모리: 0 MB")

    st.markdown("---")

    # Tips
    st.markdown("### 💡 팁")
    st.info("""
    - **대시보드 페이지**: 실시간 성과 모니터링 및 봇 제어
    - **오늘의 전략**: 자동 선택된 전략 및 백테스트 결과 검토
    - **기록 및 분석**: 고급 필터링을 통한 과거 성과 분석
    - **최적화**: 파라미터 최적화 결과 탐색
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
    st.caption(f"마지막 업데이트: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == "__main__":
    main()
