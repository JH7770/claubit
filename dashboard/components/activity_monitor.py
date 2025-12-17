"""
Activity Monitor Components

봇의 실시간 활동, 작업 상태, 이벤트 타임라인 표시
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, Optional


class ActivityMonitor:
    """봇 활동 모니터링 컴포넌트"""

    # Task name mapping (Korean)
    TASK_NAMES_KR = {
        'idle': '대기 중',
        'data_sync': '데이터 동기화',
        'strategy_selection': '전략 선택',
        'trading': '거래 중',
        'cleanup': '정리 중'
    }

    # Task emoji mapping
    TASK_EMOJIS = {
        'idle': '⏸️',
        'data_sync': '📥',
        'strategy_selection': '🧠',
        'trading': '💹',
        'cleanup': '🧹'
    }

    # Severity emoji mapping
    SEVERITY_EMOJIS = {
        'INFO': 'ℹ️',
        'SUCCESS': '✅',
        'WARNING': '⚠️',
        'ERROR': '❌'
    }

    # Event type emoji mapping
    EVENT_EMOJIS = {
        'task_start': '▶️',
        'task_end': '⏹️',
        'signal': '📊',
        'position_open': '🔓',
        'position_close': '🔒',
        'error': '❌',
        'info': 'ℹ️'
    }

    @staticmethod
    def display_task_status(bot_status: Optional[Dict]):
        """
        현재 작업 상태 표시.

        Args:
            bot_status: bot_status 테이블의 데이터 딕셔너리
        """
        if not bot_status:
            st.info("봇 상태 정보 없음")
            return

        current_task = bot_status.get('current_task', 'idle')
        task_start = bot_status.get('task_start_time')
        active_positions = bot_status.get('active_positions', 0)

        task_display = ActivityMonitor.TASK_NAMES_KR.get(current_task, current_task)
        task_emoji = ActivityMonitor.TASK_EMOJIS.get(current_task, '❓')

        col1, col2, col3 = st.columns([2, 1, 1])

        with col1:
            if current_task != 'idle':
                st.markdown(f"### {task_emoji} {task_display}")
                if task_start:
                    try:
                        start_dt = datetime.fromisoformat(task_start) if isinstance(task_start, str) else task_start
                        elapsed = (datetime.now() - start_dt).total_seconds()
                        mins = int(elapsed // 60)
                        secs = int(elapsed % 60)
                        st.caption(f"경과 시간: {mins}분 {secs}초")
                    except Exception:
                        pass
            else:
                st.success(f"### {task_emoji} {task_display}")

        with col2:
            if current_task != 'idle' and task_start:
                st.metric("상태", "진행 중")

        with col3:
            if active_positions > 0:
                st.metric("오픈 포지션", active_positions)

    @staticmethod
    def display_next_task(bot_status: Optional[Dict]):
        """
        다음 예정 작업 표시.

        Args:
            bot_status: bot_status 테이블의 데이터 딕셔너리
        """
        if not bot_status:
            return

        next_task = bot_status.get('next_task')
        next_time = bot_status.get('next_task_time')

        if not next_task or not next_time:
            st.info("다음 예약된 작업 없음")
            return

        # Task name mapping for display
        task_names_kr = {
            'Data Synchronization': '데이터 동기화',
            'Strategy Selection': '전략 선택',
            'Trading Session': '거래 세션',
            'Session Cleanup': '세션 정리',
            'Heartbeat': '하트비트'
        }

        try:
            next_time_dt = datetime.fromisoformat(next_time) if isinstance(next_time, str) else next_time
            time_until = next_time_dt - datetime.now()

            col1, col2 = st.columns(2)

            with col1:
                display_name = task_names_kr.get(next_task, next_task)
                st.metric("다음 작업", display_name)

            with col2:
                if time_until.total_seconds() > 0:
                    hours = int(time_until.total_seconds() // 3600)
                    minutes = int((time_until.total_seconds() % 3600) // 60)
                    st.metric("남은 시간", f"{hours}시간 {minutes}분")
                else:
                    st.metric("예정 시간", next_time_dt.strftime('%H:%M'))
        except Exception as e:
            st.warning(f"다음 작업 정보 파싱 오류: {e}")

    @staticmethod
    def display_activity_timeline(activities: pd.DataFrame, max_items: int = 20):
        """
        활동 타임라인 표시.

        Args:
            activities: activity_log 테이블의 데이터프레임
            max_items: 표시할 최대 항목 수
        """
        if activities.empty:
            st.info("최근 활동 없음")
            return

        st.markdown("### 📋 활동 타임라인")

        for idx, row in activities.head(max_items).iterrows():
            severity = row.get('severity', 'INFO')
            event_type = row.get('event_type', 'info')
            timestamp_val = row.get('timestamp')
            message = row.get('message', '')

            # Parse timestamp
            try:
                if isinstance(timestamp_val, str):
                    timestamp = datetime.fromisoformat(timestamp_val)
                elif isinstance(timestamp_val, pd.Timestamp):
                    timestamp = timestamp_val.to_pydatetime()
                else:
                    timestamp = datetime.now()
            except Exception:
                timestamp = datetime.now()

            # Create timeline entry
            severity_emoji = ActivityMonitor.SEVERITY_EMOJIS.get(severity, '')
            event_emoji = ActivityMonitor.EVENT_EMOJIS.get(event_type, '')
            emoji = f"{severity_emoji} {event_emoji}"
            time_str = timestamp.strftime('%H:%M:%S')

            # Display with severity-based styling
            display_text = f"{emoji} **{time_str}** - {message}"

            if severity == 'ERROR':
                st.error(display_text, icon="❌")
            elif severity == 'WARNING':
                st.warning(display_text, icon="⚠️")
            elif severity == 'SUCCESS':
                st.success(display_text, icon="✅")
            else:
                st.info(display_text, icon="ℹ️")

    @staticmethod
    def display_signal_status(latest_signals: pd.DataFrame):
        """
        최근 거래 신호 표시.

        Args:
            latest_signals: trading_signals 테이블의 데이터프레임
        """
        if latest_signals.empty:
            st.info("최근 신호 없음")
            return

        st.markdown("### 📊 최근 거래 신호")

        signal_labels = {
            1: '🟢 LONG',
            -1: '🔴 SHORT',
            0: '⚪ HOLD'
        }

        # Create table
        for idx, row in latest_signals.head(5).iterrows():
            timestamp_val = row.get('timestamp')
            signal = row.get('signal', 0)
            symbol = row.get('symbol', 'N/A')
            price = row.get('current_price', 0)
            opened = row.get('position_opened', False)

            # Parse timestamp
            try:
                if isinstance(timestamp_val, str):
                    timestamp = datetime.fromisoformat(timestamp_val)
                elif isinstance(timestamp_val, pd.Timestamp):
                    timestamp = timestamp_val.to_pydatetime()
                else:
                    timestamp = datetime.now()
            except Exception:
                timestamp = datetime.now()

            col1, col2, col3, col4 = st.columns([2, 1, 1, 1])

            with col1:
                st.caption(timestamp.strftime('%H:%M:%S'))

            with col2:
                st.text(symbol)

            with col3:
                st.markdown(signal_labels.get(signal, '❓'))

            with col4:
                if opened:
                    st.success(f"${price:.2f} ✓")
                else:
                    st.text(f"${price:.2f}")
