"""
Today's Strategy Page

Displays the champion strategy selected for today,
including backtest performance and applied parameters.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import streamlit as st
import pandas as pd
import json
from datetime import datetime

from dashboard.utils.data_loader import DashboardDataLoader
from dashboard.components.charts import ChartBuilder
from dashboard.components.metrics import MetricCard
from dashboard.components.tables import TableFormatter
from dashboard.utils.formatters import format_percentage, format_timestamp
from config.config import Config


st.set_page_config(page_title="오늘의 전략", page_icon="🎯", layout="wide")

# Title
st.title("🎯 오늘의 챔피언 전략")
st.markdown("---")

# Initialize data loader
if 'data_loader' not in st.session_state:
    config = Config()
    st.session_state.data_loader = DashboardDataLoader(config.DB_PATH)

data_loader = st.session_state.data_loader

# Date selector
col1, col2 = st.columns([3, 1])
with col1:
    selected_date = st.date_input(
        "날짜 선택",
        value=datetime.now(),
        max_value=datetime.now()
    )
with col2:
    if st.button("🔄 새로고침"):
        data_loader.clear_cache()
        st.rerun()

date_str = selected_date.strftime('%Y-%m-%d')

# Load today's strategy
strategy = data_loader.get_today_strategy(date_str)

if not strategy:
    st.warning(f"⚠️ {date_str}에 선택된 전략이 없습니다")
    st.info("""
    **이 날짜에 대한 전략 데이터를 찾을 수 없습니다.**

    가능한 원인:
    - 이 날짜에 대한 전략 선택이 아직 실행되지 않았습니다
    - 데이터베이스에 이 날짜에 대한 백테스트 결과가 없습니다
    - 봇이 자동 전략 선택을 위해 구성되지 않았습니다

    **다음 단계:**
    - 다른 날짜를 시도해 보세요
    - 수동으로 전략 선택 실행: `python main_bot.py --mode select`
    - 오류에 대한 봇 로그 확인
    """)
    st.stop()

# Champion Strategy Card
st.markdown("### 🏆 선택된 전략")

col1, col2, col3 = st.columns([2, 1, 1])

with col1:
    st.markdown(f"#### {strategy['strategy_name']}")
    st.caption(f"선택일: {strategy.get('date', date_str)}")

with col2:
    st.metric("종합 점수", f"{strategy.get('score', 0):.2f}")

with col3:
    rank = strategy.get('rank', 1)
    medal = "🥇" if rank == 1 else "🥈" if rank == 2 else "🥉" if rank == 3 else f"#{rank}"
    st.metric("순위", medal)

st.markdown("---")

# Performance Metrics Grid
st.markdown("### 📊 백테스트 성과 지표")

metrics_data = [
    ("총 수익률", format_percentage(strategy.get('total_return', 0)), None),
    ("승률", format_percentage(strategy.get('win_rate', 0)), None),
    ("수익 팩터", f"{strategy.get('profit_factor', 0):.2f}", None),
    ("샤프 지수", f"{strategy.get('sharpe_ratio', 0):.2f}", None)
]

MetricCard.display_4_column_metrics(metrics_data)

col1, col2 = st.columns(2)
with col1:
    st.metric("최대 낙폭", format_percentage(abs(strategy.get('max_drawdown', 0))))
with col2:
    st.metric("총 거래", strategy.get('total_trades', 0))

st.markdown("---")

# Applied Parameters
st.markdown("### ⚙️ 적용된 파라미터")

params_str = strategy.get('params', '{}')
try:
    if isinstance(params_str, str):
        params = json.loads(params_str)
    else:
        params = params_str if isinstance(params_str, dict) else {}

    if params:
        # Create parameter table
        param_descriptions = {
            'k': '돌파 감지를 위한 변동성 승수',
            'lookback_period': '변동성 계산을 위한 룩백 기간',
            'ma_period': '추세 필터를 위한 이동 평균 기간',
            'use_ma_filter': '이동 평균 추세 필터 활성화',
            'stop_loss_percent': '손절매 임계값 비율',
            'take_profit_percent': '이익 실현 목표 비율',
            'rsi_period': 'RSI 계산 기간',
            'rsi_buy_threshold': 'RSI 과매도 임계값 (매수 신호)',
            'rsi_sell_threshold': 'RSI 과매수 임계값 (매도 신호)',
            'bb_period': '볼린저 밴드 기간',
            'bb_stddev': '볼린저 밴드 표준 편차 승수',
            'short_window': '단기 이동 평균 윈도우',
            'long_window': '장기 이동 평균 윈도우',
            'vol_lookback': '거래량 룩백 기간',
            'vol_multiplier': '거래량 급증 승수'
        }

        param_data = []
        for key, value in params.items():
            description = param_descriptions.get(key, '전략 구성을 위한 파라미터')
            param_data.append({
                'Parameter': key,
                'Value': str(value),
                'Description': description
            })

        param_df = pd.DataFrame(param_data)
        st.dataframe(param_df, use_container_width=True, hide_index=True)
    else:
        st.info("이 전략에 지정된 파라미터가 없습니다")

except json.JSONDecodeError:
    st.error(f"파라미터 파싱 오류: {params_str}")

st.markdown("---")

# Strategy Comparison - Top Alternatives
st.markdown("### 📈 전략 순위 (모든 테스트됨)")

rankings = data_loader.get_strategy_rankings(date_str)

if not rankings.empty:
    # Show ranking chart
    st.plotly_chart(
        ChartBuilder.strategy_ranking_bar(
            rankings,
            strategy_col='strategy_name',
            score_col='score',
            title="전략 성과 비교",
            top_n=10
        ),
        use_container_width=True
    )

    # Show detailed table
    st.markdown("#### 상세 순위")

    # Format ranking table
    rankings_display = TableFormatter.format_strategy_ranking(rankings)

    # Display table
    st.dataframe(rankings_display, use_container_width=True, hide_index=True)

    # Download button
    csv = rankings.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 순위 CSV 다운로드",
        data=csv,
        file_name=f"strategy_rankings_{date_str}.csv",
        mime="text/csv"
    )

else:
    st.info("이 날짜에 대한 순위 데이터가 없습니다")

st.markdown("---")

# Radar Chart for Multi-Metric Comparison
st.markdown("### 🎯 다중 지표 성과 레이더")

if strategy:
    # Normalize metrics to 0-100 scale for radar chart
    metrics_radar = {
        'Return': min(100, max(0, (strategy.get('total_return', 0) + 10) / 20 * 100)),
        'Win Rate': strategy.get('win_rate', 0),
        'Sharpe': min(100, max(0, (strategy.get('sharpe_ratio', 0) + 2) / 4 * 100)),
        'Profit Factor': min(100, max(0, (strategy.get('profit_factor', 0)) / 3 * 100)),
        'Drawdown': min(100, max(0, (1 - abs(strategy.get('max_drawdown', 0)) / 20) * 100))
    }

    col1, col2 = st.columns([2, 1])

    with col1:
        st.plotly_chart(
            ChartBuilder.strategy_comparison_radar(
                metrics_radar,
                title="전략 성과 지표 (정규화됨)",
                height=400
            ),
            use_container_width=True
        )

    with col2:
        st.markdown("#### 지표 해석")
        st.markdown("""
        **정규화된 지표 (0-100 스케일):**

        - **Return**: 총 수익률 (스케일됨)
        - **Win Rate**: 승리한 거래의 비율
        - **Sharpe**: 위험 조정 수익 품질
        - **Profit Factor**: 손익 비율
        - **Drawdown**: 자본 보존 (반전됨)

        균형 잡힌 전략은 모든 지표에서
        고른 성과를 보여줍니다.
        """)

# Footer
st.markdown("---")
st.caption(f"전략 선택일: {date_str} | 마지막 업데이트: {datetime.now().strftime('%H:%M:%S')}")
