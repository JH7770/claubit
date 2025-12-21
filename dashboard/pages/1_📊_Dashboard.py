"""
Real-time Dashboard Page

Real-time monitoring, bot controls, and position tracking.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import streamlit as st
import pandas as pd
import json
from datetime import datetime, timedelta
from streamlit_autorefresh import st_autorefresh

from dashboard.utils.data_loader import DashboardDataLoader
from dashboard.utils.bot_controller import BotController
from dashboard.components.charts import ChartBuilder
from dashboard.components.metrics import MetricCard
from dashboard.components.tables import TableFormatter
from dashboard.components.activity_monitor import ActivityMonitor
from dashboard.utils.formatters import format_currency, format_percentage, format_duration
from dashboard.utils.theme import apply_dark_mode_css, initialize_dark_mode
from config.config import Config


st.set_page_config(page_title="대시보드", page_icon="📊", layout="wide")

# Initialize dark mode immediately to prevent flash
initialize_dark_mode()

# Apply dark mode CSS
apply_dark_mode_css()

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
st.title("📊 실시간 대시보드")
st.markdown("봇 성능 모니터링 및 트레이딩 제어")
st.markdown("---")

# Create tabs for better organization
tab1, tab2, tab3, tab4 = st.tabs(["📊 개요", "💼 포지션", "🎬 활동", "🏥 시스템"])

# =============================================================================
# TAB 1: OVERVIEW (개요)
# =============================================================================
with tab1:
    st.markdown("### 🤖 봇 제어 패널")

    is_running = bot_controller.is_running()
    bot_status = bot_controller.get_status()

    col1, col2, col3 = st.columns(3)

    with col1:
        if is_running:
            st.success("🟢 봇 실행 중")
            if bot_status['status'] == 'running':
                st.caption(f"PID: {bot_status['pid']}")
                st.caption(f"가동 시간: {format_duration(bot_status['uptime_seconds'])}")
                st.caption(f"메모리: {bot_status['memory_mb']:.1f} MB")
        else:
            st.error("🔴 봇 중지됨")

    with col2:
        st.metric("트레이딩 모드", config.TRADING_MODE)
        st.metric("레버리지", f"{config.LEVERAGE}x")

    with col3:
        st.metric("주요 심볼", config.PRIMARY_SYMBOL)

    # Control Buttons
    st.markdown("#### 비상 제어")

    # Strategy selection option (before immediate trade button)
    strategy_option = st.radio(
        "전략 선택 옵션",
        ["🔄 새 전략 선택 (백테스트 실행)", "♻️ 이전 전략 사용"],
        horizontal=True,
        help="새 전략 선택: 백테스트를 실행하여 최적의 전략을 선택합니다 (시간 소요)\n이전 전략 사용: 가장 최근에 선택된 전략을 바로 사용합니다 (빠름)"
    )

    skip_selection = (strategy_option == "♻️ 이전 전략 사용")

    # Row 1: Start buttons
    col1, col2 = st.columns(2)

    with col1:
        if st.button("🚀 즉시 거래 시작", disabled=is_running, use_container_width=True, type="primary"):
            if skip_selection:
                with st.spinner("전체 사이클 시작 중 (데이터 동기화 → 이전 전략 로드 → 거래)..."):
                    success = bot_controller.start_bot(mode="once", skip_selection=True)
                    if success:
                        st.success("✅ 즉시 거래가 시작되었습니다 (이전 전략 사용)")
                        st.info("📊 전체 사이클이 완료되면 봇이 자동으로 중지됩니다")
                        st.rerun()
                    else:
                        st.error("❌ 거래 시작 실패")
            else:
                with st.spinner("전체 사이클 시작 중 (데이터 동기화 → 전략 선택 → 거래)..."):
                    success = bot_controller.start_bot(mode="once", skip_selection=False)
                    if success:
                        st.success("✅ 즉시 거래가 시작되었습니다 (새 전략 선택)")
                        st.info("📊 전체 사이클이 완료되면 봇이 자동으로 중지됩니다")
                        st.rerun()
                    else:
                        st.error("❌ 거래 시작 실패")

    with col2:
        if st.button("⏰ 스케줄 봇 시작", disabled=is_running, use_container_width=True):
            with st.spinner("스케줄 봇 시작 중..."):
                success = bot_controller.start_bot(mode="scheduled")
                if success:
                    st.success("✅ 스케줄 봇이 시작되었습니다")
                    st.info("📅 매일 22:30 KST에 자동으로 거래가 실행됩니다")
                    st.rerun()
                else:
                    st.error("❌ 봇 시작 실패")

    # Row 2: Control buttons
    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("⏸️ 봇 중지", disabled=not is_running, use_container_width=True):
            with st.spinner("봇 중지 중..."):
                success = bot_controller.stop_bot()
                if success:
                    st.success("✅ 봇이 성공적으로 중지되었습니다")
                    st.rerun()
                else:
                    st.error("❌ 봇 중지 실패")

    with col2:
        if st.button("🔄 봇 재시작", disabled=not is_running, use_container_width=True):
            with st.spinner("봇 재시작 중..."):
                success = bot_controller.restart_bot(mode="scheduled")
                if success:
                    st.success("✅ 봇이 성공적으로 재시작되었습니다")
                    st.rerun()
                else:
                    st.error("❌ 봇 재시작 실패")

    with col3:
        # Check for open positions
        open_positions = data_loader.get_open_positions()
        has_positions = len(open_positions) > 0

        # Button always visible, disabled if no positions
        if st.button("🛑 강제 종료 (전체)", type="secondary", use_container_width=True, disabled=not has_positions):

            if config.is_live_mode():
                # LIVE MODE - 2-step confirmation
                st.warning("⚠️ 라이브 모드에서 모든 포지션을 강제 종료합니다!")
                st.error(f"현재 오픈 포지션: {len(open_positions)}개")

                # Show position preview
                if has_positions:
                    st.dataframe(
                        open_positions[['symbol', 'side', 'entry_price', 'amount']],
                        use_container_width=True
                    )

                # Text confirmation
                confirm_text = st.text_input(
                    "확인을 위해 'FORCE CLOSE'를 입력하세요:",
                    key="force_close_confirm"
                )

                if confirm_text == "FORCE CLOSE":
                    if st.button("✅ 최종 확인 - 모든 포지션 종료", type="primary"):
                        with st.spinner("포지션 종료 중..."):
                            result = bot_controller.force_close_all_positions(
                                reason="dashboard_live_manual"
                            )

                            if result['success']:
                                st.success(
                                    f"✅ {result['positions_closed']}개 포지션이 종료되었습니다. "
                                    f"총 PNL: ${result['total_pnl']:,.2f}"
                                )
                                st.rerun()
                            else:
                                st.error(f"❌ 종료 실패: {result['message']}")
                elif confirm_text:
                    st.error("'FORCE CLOSE'를 정확히 입력하세요.")

            else:
                # PAPER MODE - Single confirmation
                st.warning(f"⚠️ {len(open_positions)}개의 포지션이 즉시 종료됩니다!")

                if st.button("확인 - 종료 실행", type="primary"):
                    with st.spinner("포지션 종료 중..."):
                        result = bot_controller.force_close_all_positions(
                            reason="dashboard_paper_manual"
                        )

                        if result['success']:
                            st.success(
                                f"✅ {result['positions_closed']}개 포지션이 종료되었습니다. "
                                f"총 PNL: ${result['total_pnl']:,.2f}"
                            )
                            if result['positions_closed'] > 0:
                                st.metric(
                                    label="Total PNL",
                                    value=f"${result['total_pnl']:,.2f}",
                                    delta=f"{result['positions_closed']} positions"
                                )
                            st.rerun()
                        else:
                            st.error(f"❌ 종료 실패: {result['message']}")

        # Helper text when no positions
        if not has_positions:
            st.caption("현재 오픈 포지션이 없습니다")

    st.markdown("---")

    # Performance Metrics
    st.markdown("### 📊 오늘의 성과")

    today = datetime.now().strftime('%Y-%m-%d')
    summary = data_loader.get_daily_summary(today)

    if summary:
        metrics_data = [
            ("현재 잔고", format_currency(summary.get('ending_balance', 0)), None),
            ("일일 PNL", format_currency(summary.get('total_pnl', 0), include_sign=True),
             format_percentage(summary.get('total_pnl', 0) / summary.get('starting_balance', 1) * 100)),
            ("승률", format_percentage(summary.get('win_rate', 0)), None),
            ("총 거래", str(summary.get('total_trades', 0)), None)
        ]
        MetricCard.display_4_column_metrics(metrics_data)
    else:
        st.info("오늘 거래 활동 없음")

    st.markdown("---")

    # Real-time Equity Chart (Last 24 hours)
    st.markdown("### 📈 자산 곡선 (최근 24시간)")

    yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
    recent_trades = data_loader.get_trade_history(start_date=yesterday, end_date=today)

    if not recent_trades.empty:
        cum_pnl = data_loader.get_cumulative_pnl(yesterday, today)
        # Get dark mode from session state (default False if not set)
        dark_mode = st.session_state.get('dark_mode', False)
        st.plotly_chart(
            ChartBuilder.equity_curve(
                cum_pnl,
                x_col='timestamp',
                y_col='cumulative_pnl',
                title="24시간 자산 곡선",
                height=350,
                dark_mode=dark_mode
            ),
            use_container_width=True
        )
    else:
        st.info("최근 거래 데이터 없음")

    st.markdown("---")

    # Recent Trades (최근 5개)
    st.markdown("### 📝 최근 거래 (최근 5개)")

    if not recent_trades.empty:
        recent_5 = recent_trades.head(5)
        st.dataframe(
            TableFormatter.format_trade_table(recent_5),
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("최근 거래 없음")

# =============================================================================
# TAB 2: POSITIONS (포지션)
# =============================================================================
with tab2:
    st.markdown("### 💼 현재 포지션")

    positions = data_loader.get_open_positions()

    if not positions.empty:
        # Main position table with enhanced columns
        st.dataframe(
            TableFormatter.format_position_table(positions),
            use_container_width=True,
            hide_index=True
        )
        st.caption(f"총 오픈 포지션: {len(positions)}")

        # Expandable details for each position
        st.markdown("#### 📊 상세 정보")
        for idx, pos in positions.iterrows():
            with st.expander(f"📊 {pos['symbol']} {pos['side']} 포지션 상세"):
                col1, col2, col3 = st.columns(3)

                with col1:
                    st.markdown("**포지션 정보**")
                    position_value = pos.get('position_value', 0)
                    margin_used = pos.get('margin_used', 0)
                    leverage = pos.get('leverage', 10)

                    st.metric("포지션 가치", f"${position_value:,.2f}")
                    st.metric("사용 마진", f"${margin_used:,.2f}")
                    st.metric("레버리지", f"{leverage}x")

                with col2:
                    st.markdown("**리스크 지표**")
                    max_risk = pos.get('max_risk', 0)
                    potential_profit = pos.get('potential_profit', 0)
                    rr_ratio = pos.get('rr_ratio', 0)

                    st.metric("최대 리스크", f"${max_risk:,.2f}")
                    st.metric("예상 수익", f"${potential_profit:,.2f}")
                    st.metric("손익비", f"1:{rr_ratio:.2f}" if rr_ratio > 0 else "N/A")

                with col3:
                    st.markdown("**거리 지표**")
                    sl_dist = abs(pos.get('distance_to_sl_percent', 0))
                    tp_dist = abs(pos.get('distance_to_tp_percent', 0))
                    duration_minutes = pos.get('duration_minutes', 0)

                    st.metric("SL까지", f"{sl_dist:.2f}%")
                    st.metric("TP까지", f"{tp_dist:.2f}%")
                    hours = int(duration_minutes // 60)
                    minutes = int(duration_minutes % 60)
                    st.metric("지속 시간", f"{hours}h {minutes}m")

                # Strategy parameters if available
                if 'id' in pos:
                    position_details = data_loader.get_position_details(pos['id'])
                    if position_details:
                        if position_details.get('strategy_params'):
                            st.markdown("**전략 파라미터**")
                            try:
                                params = json.loads(position_details['strategy_params'])
                                st.json(params)
                            except:
                                st.text(position_details['strategy_params'])

                        # Entry indicators if available
                        if position_details.get('entry_indicators'):
                            st.markdown("**진입 시점 지표**")
                            try:
                                indicators = json.loads(position_details['entry_indicators'])
                                st.json(indicators)
                            except:
                                st.text(position_details['entry_indicators'])

    else:
        st.info("오픈 포지션 없음")

# =============================================================================
# TAB 3: ACTIVITY (활동)
# =============================================================================
with tab3:
    st.markdown("### 🎬 봇 활동 모니터")

    # Get bot status from database (not just process status)
    db_bot_status = data_loader.get_bot_status()

    # Current Task Status
    st.markdown("#### 현재 작업")
    ActivityMonitor.display_task_status(db_bot_status)

    st.markdown("---")

    # Next Scheduled Task
    st.markdown("#### 다음 예정 작업")
    ActivityMonitor.display_next_task(db_bot_status)

    st.markdown("---")

    # Real-time Signal Status (if trading)
    if db_bot_status and db_bot_status.get('current_task') == 'trading':
        latest_signals = data_loader.get_latest_signals(config.PRIMARY_SYMBOL, limit=5)
        ActivityMonitor.display_signal_status(latest_signals)
        st.markdown("---")

    # Activity Timeline
    st.markdown("#### 활동 기록")
    col1, col2 = st.columns([3, 1])

    with col1:
        filter_category = st.selectbox(
            "카테고리 필터",
            ['전체', '봇', '거래', '전략', '시스템'],
            key='activity_filter'
        )

    with col2:
        max_items = st.number_input("표시 개수", 10, 100, 20, 10, key='activity_max_items')

    category_map = {
        '전체': None,
        '봇': 'bot',
        '거래': 'trading',
        '전략': 'strategy',
        '시스템': 'system'
    }

    recent_activities = data_loader.get_recent_activity(
        limit=max_items,
        event_category=category_map[filter_category]
    )

    ActivityMonitor.display_activity_timeline(recent_activities, max_items)

# =============================================================================
# TAB 4: SYSTEM (시스템)
# =============================================================================
with tab4:
    st.markdown("### 🏥 시스템 상태")

    # Get bot status
    is_running = bot_controller.is_running()
    bot_status = bot_controller.get_status()

    # Bot Process Information
    st.markdown("#### 🤖 봇 프로세스 정보")

    col1, col2, col3 = st.columns(3)

    with col1:
        if is_running and bot_status['status'] == 'running':
            st.metric("프로세스 상태", "🟢 실행 중")
            st.caption(f"PID: {bot_status['pid']}")
        else:
            st.metric("프로세스 상태", "🔴 중지됨")
            st.caption("PID: N/A")

    with col2:
        if is_running and bot_status['status'] == 'running':
            st.metric("가동 시간", format_duration(bot_status['uptime_seconds']))
            if bot_status.get('started_at'):
                st.caption(f"시작: {bot_status['started_at'].strftime('%H:%M:%S')}")
        else:
            st.metric("가동 시간", "0h 0m")
            st.caption("시작: N/A")

    with col3:
        st.metric("트레이딩 모드", config.TRADING_MODE)
        st.caption(f"레버리지: {config.LEVERAGE}x")

    st.markdown("---")

    # Resource Usage
    st.markdown("#### 💻 리소스 사용량")

    col1, col2, col3 = st.columns(3)

    with col1:
        if bot_status['status'] == 'running':
            cpu = bot_status['cpu_percent']
            if cpu < 50:
                st.success(f"CPU 사용량: {cpu:.1f}% ✅")
            elif cpu < 80:
                st.warning(f"CPU 사용량: {cpu:.1f}% ⚠️")
            else:
                st.error(f"CPU 사용량: {cpu:.1f}% ❌")
        else:
            st.info("CPU 사용량: N/A (봇 중지됨)")

    with col2:
        if bot_status['status'] == 'running':
            memory = bot_status['memory_mb']
            if memory < 500:
                st.success(f"메모리: {memory:.1f} MB ✅")
            elif memory < 1000:
                st.warning(f"메모리: {memory:.1f} MB ⚠️")
            else:
                st.error(f"메모리: {memory:.1f} MB ❌")
        else:
            st.info("메모리: N/A (봇 중지됨)")

    with col3:
        # Circuit breaker status (would need to read from bot state)
        st.info("서킷 브레이커: OK ✅")

    st.markdown("---")

    # Configuration
    st.markdown("#### ⚙️ 현재 설정")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**거래 설정**")
        st.text(f"거래소: {config.EXCHANGE_NAME}")
        st.text(f"주요 심볼: {config.PRIMARY_SYMBOL}")
        st.text(f"보조 심볼: {config.SECONDARY_SYMBOL}")
        st.text(f"타임존: {config.TIMEZONE}")

    with col2:
        st.markdown("**리스크 관리**")
        st.text(f"일일 손실 한도: {config.MAX_DAILY_LOSS_PERCENT}%")
        st.text(f"레버리지: {config.LEVERAGE}x")
        st.text(f"최대 포지션 크기: ${config.MAX_POSITION_SIZE_USDT}")
        st.text(f"전략 선택 모드: {config.SELECTOR_MODE}")

# Footer
st.markdown("---")
st.caption(f"마지막 업데이트: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | 자동 새로고침: 30s")
