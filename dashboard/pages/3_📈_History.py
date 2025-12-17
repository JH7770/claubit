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


st.set_page_config(page_title="기록 및 분석", page_icon="📈", layout="wide")

# Title
st.title("📈 기록 및 분석")
st.markdown("과거 거래 성과 및 상세 거래 기록 분석")
st.markdown("---")

# Initialize data loader
if 'data_loader' not in st.session_state:
    config = Config()
    st.session_state.data_loader = DashboardDataLoader(config.DB_PATH)

data_loader = st.session_state.data_loader

# Filters Section
st.markdown("### 🔍 필터")

col1, col2, col3, col4 = st.columns(4)

with col1:
    start_date = st.date_input(
        "시작 날짜",
        value=datetime.now() - timedelta(days=30),
        max_value=datetime.now()
    )

with col2:
    end_date = st.date_input(
        "종료 날짜",
        value=datetime.now(),
        max_value=datetime.now()
    )

with col3:
    # Get unique symbols
    symbols = data_loader.get_unique_symbols()
    symbol_filter = st.selectbox(
        "심볼",
        options=["All"] + symbols,
        index=0
    )

with col4:
    # Get unique strategies
    strategies = data_loader.get_unique_strategies()
    strategy_filter = st.selectbox(
        "전략",
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
st.markdown("### 📊 성과 요약")

if not trades.empty:
    stats = data_loader.get_trade_statistics(start_date_str, end_date_str)

    metrics_data = [
        ("총 거래", str(stats['total_trades']), None),
        ("총 PNL", format_currency(stats['total_pnl'], include_sign=True), None),
        ("승률", format_percentage(stats['win_rate']), None),
        ("평균 PNL", format_currency(stats['avg_pnl'], include_sign=True), None)
    ]

    MetricCard.display_4_column_metrics(metrics_data)

    col1, col2 = st.columns(2)
    with col1:
        st.metric("최고 거래", format_currency(stats['best_trade'], include_sign=True))
    with col2:
        st.metric("최악 거래", format_currency(stats['worst_trade'], include_sign=True))

else:
    st.info("선택된 필터에 대한 거래가 없습니다")

st.markdown("---")

# Cumulative Return Chart
st.markdown("### 📈 누적 수익률")

if not trades.empty:
    cum_pnl = data_loader.get_cumulative_pnl(start_date_str, end_date_str)

    if not cum_pnl.empty:
        st.plotly_chart(
            ChartBuilder.equity_curve(
                cum_pnl,
                x_col='timestamp',
                y_col='cumulative_pnl',
                title="시간에 따른 누적 PNL",
                height=400
            ),
            use_container_width=True
        )
    else:
        st.info("누적 PNL 데이터 없음")
else:
    st.info("표시할 거래 데이터 없음")

st.markdown("---")

# Daily PNL Chart
st.markdown("### 📊 일일 PNL")

if not daily_summaries.empty:
    st.plotly_chart(
        ChartBuilder.daily_pnl_bar(
            daily_summaries,
            date_col='date',
            pnl_col='total_pnl',
            title="일일 손익",
            height=400
        ),
        use_container_width=True
    )
else:
    st.info("일일 요약 데이터 없음")

st.markdown("---")

# Exit Reason Distribution
st.markdown("### 🎯 종료 사유 분포")

if not trades.empty and 'exit_reason' in trades.columns:
    col1, col2 = st.columns([2, 1])

    with col1:
        st.plotly_chart(
            ChartBuilder.exit_reason_pie(
                trades,
                reason_col='exit_reason',
                title="거래 종료 사유",
                height=400
            ),
            use_container_width=True
        )

    with col2:
        st.markdown("#### 종료 사유")
        reason_counts = trades['exit_reason'].value_counts()
        for reason, count in reason_counts.items():
            st.write(f"**{reason}**: {count} ({count/len(trades)*100:.1f}%)")

else:
    st.info("종료 사유 데이터 없음")

st.markdown("---")

# Trade Log Table
st.markdown("### 📋 거래 로그")

if not trades.empty:
    # Format trade table
    trades_display = TableFormatter.format_trade_table(trades)

    # Pagination
    page_size = 50
    total_trades = len(trades_display)
    total_pages = (total_trades + page_size - 1) // page_size

    col1, col2, col3 = st.columns([2, 1, 1])

    with col1:
        st.caption(f"총 거래: {total_trades}")

    with col2:
        page = st.number_input(
            "페이지",
            min_value=1,
            max_value=max(1, total_pages),
            value=1,
            step=1
        )

    with col3:
        csv = trades.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 CSV 다운로드",
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

    st.caption(f"{total_trades} 건 중 {start_idx + 1}-{end_idx} 건 표시 중")

else:
    st.info("표시할 거래 없음")

st.markdown("---")

# Additional Analytics
with st.expander("📊 추가 분석"):
    if not trades.empty:
        st.markdown("#### 거래 기간 분석")

        if 'duration_seconds' in trades.columns:
            trades['duration_minutes'] = trades['duration_seconds'] / 60
            avg_duration = trades['duration_minutes'].mean()
            max_duration = trades['duration_minutes'].max()
            min_duration = trades['duration_minutes'].min()

            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("평균 기간", f"{avg_duration:.1f} 분")
            with col2:
                st.metric("최대 기간", f"{max_duration:.1f} 분")
            with col3:
                st.metric("최소 기간", f"{min_duration:.1f} 분")

        st.markdown("#### PNL 분포")

        if 'pnl' in trades.columns:
            positive_trades = trades[trades['pnl'] > 0]
            negative_trades = trades[trades['pnl'] <= 0]

            col1, col2 = st.columns(2)
            with col1:
                st.metric(
                    "평균 수익 거래",
                    format_currency(positive_trades['pnl'].mean() if not positive_trades.empty else 0)
                )
            with col2:
                st.metric(
                    "평균 손실 거래",
                    format_currency(negative_trades['pnl'].mean() if not negative_trades.empty else 0)
                )

        st.markdown("#### 전략 성과 세부 정보")

        if 'strategy_name' in trades.columns and 'pnl' in trades.columns:
            strategy_pnl = trades.groupby('strategy_name')['pnl'].agg(['sum', 'mean', 'count'])
            strategy_pnl.columns = ['총 PNL', '평균 PNL', '거래 횟수']
            strategy_pnl = strategy_pnl.sort_values('총 PNL', ascending=False)

            st.dataframe(strategy_pnl, use_container_width=True)

# Footer
st.markdown("---")
st.caption(f"기간: {start_date_str} ~ {end_date_str} | 마지막 업데이트: {datetime.now().strftime('%H:%M:%S')}")
