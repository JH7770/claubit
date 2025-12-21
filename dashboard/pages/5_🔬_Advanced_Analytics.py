"""
Advanced Analytics Page

Deep dive analysis with advanced metrics, risk analysis, and pattern discovery.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from dashboard.utils.data_loader import DashboardDataLoader
from dashboard.components.charts import ChartBuilder
from dashboard.components.metrics import MetricCard
from dashboard.utils.formatters import format_currency, format_percentage
from dashboard.utils.theme import apply_dark_mode_css, initialize_dark_mode
from config.config import Config


st.set_page_config(page_title="고급 분석", page_icon="🔬", layout="wide")

# Initialize dark mode immediately to prevent flash
initialize_dark_mode()

# Apply dark mode CSS
apply_dark_mode_css()

# Title
st.title("🔬 고급 분석")
st.markdown("심층 전략 분석, 리스크 지표, 패턴 발견")
st.markdown("---")

# Initialize
if 'data_loader' not in st.session_state:
    config = Config()
    st.session_state.data_loader = DashboardDataLoader(config.DB_PATH)

data_loader = st.session_state.data_loader
dark_mode = st.session_state.get('dark_mode', False)

# Date Range Selector
col1, col2 = st.columns(2)
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

start_date_str = start_date.strftime('%Y-%m-%d')
end_date_str = end_date.strftime('%Y-%m-%d')

# Load data
trades = data_loader.get_trade_history(start_date=start_date_str, end_date=end_date_str)

if trades.empty:
    st.warning("⚠️ 선택한 기간에 거래 데이터가 없습니다")
    st.stop()

st.markdown("---")

# =============================================================================
# SECTION 1: 전략별 고급 성과 지표
# =============================================================================
st.markdown("### 📊 전략별 고급 성과 지표")

# Calculate advanced metrics for each strategy
def calculate_sharpe_ratio(returns, risk_free_rate=0.0):
    """Calculate Sharpe Ratio."""
    if len(returns) == 0 or returns.std() == 0:
        return 0
    return (returns.mean() - risk_free_rate) / returns.std() * np.sqrt(252)  # Annualized

def calculate_sortino_ratio(returns, risk_free_rate=0.0):
    """Calculate Sortino Ratio (only downside deviation)."""
    if len(returns) == 0:
        return 0
    downside_returns = returns[returns < 0]
    if len(downside_returns) == 0 or downside_returns.std() == 0:
        return 0
    return (returns.mean() - risk_free_rate) / downside_returns.std() * np.sqrt(252)

def calculate_calmar_ratio(returns, max_drawdown):
    """Calculate Calmar Ratio."""
    if max_drawdown == 0:
        return 0
    annual_return = returns.mean() * 252
    return annual_return / abs(max_drawdown)

# Group by strategy
if 'strategy_name' in trades.columns and 'pnl' in trades.columns:
    strategy_metrics = []

    for strategy in trades['strategy_name'].unique():
        strategy_trades = trades[trades['strategy_name'] == strategy]

        # Calculate metrics
        pnl_series = strategy_trades['pnl']
        total_return = pnl_series.sum()
        win_rate = (pnl_series > 0).sum() / len(pnl_series) * 100 if len(pnl_series) > 0 else 0

        # Calculate drawdown
        cumulative = pnl_series.cumsum()
        running_max = cumulative.cummax()
        drawdown = (cumulative - running_max)
        max_drawdown = drawdown.min()

        # Advanced ratios
        sharpe = calculate_sharpe_ratio(pnl_series)
        sortino = calculate_sortino_ratio(pnl_series)
        calmar = calculate_calmar_ratio(pnl_series, max_drawdown)

        # Profit factor
        wins = pnl_series[pnl_series > 0].sum()
        losses = abs(pnl_series[pnl_series < 0].sum())
        profit_factor = wins / losses if losses != 0 else 0

        strategy_metrics.append({
            'Strategy': strategy,
            'Total Return': total_return,
            'Win Rate (%)': win_rate,
            'Sharpe Ratio': sharpe,
            'Sortino Ratio': sortino,
            'Calmar Ratio': calmar,
            'Profit Factor': profit_factor,
            'Max Drawdown': max_drawdown,
            'Trade Count': len(strategy_trades)
        })

    metrics_df = pd.DataFrame(strategy_metrics)

    if not metrics_df.empty:
        # Display metrics comparison chart
        st.plotly_chart(
            ChartBuilder.metric_comparison_bar(
                metrics_df,
                category_col='Strategy',
                metrics=['Sharpe Ratio', 'Sortino Ratio', 'Calmar Ratio'],
                title="전략별 리스크 조정 수익률 지표",
                height=400,
                dark_mode=dark_mode
            ),
            use_container_width=True
        )

        # Display table
        st.markdown("#### 📋 상세 지표 테이블")
        st.dataframe(
            metrics_df.style.format({
                'Total Return': '${:.2f}',
                'Win Rate (%)': '{:.1f}%',
                'Sharpe Ratio': '{:.2f}',
                'Sortino Ratio': '{:.2f}',
                'Calmar Ratio': '{:.2f}',
                'Profit Factor': '{:.2f}',
                'Max Drawdown': '${:.2f}',
                'Trade Count': '{:.0f}'
            }),
            use_container_width=True,
            hide_index=True
        )

        # Explanation
        with st.expander("📖 지표 설명"):
            st.markdown("""
            **Sharpe Ratio**: 총 변동성 대비 초과 수익률 (높을수록 좋음, >1이면 양호)

            **Sortino Ratio**: 하방 변동성만 고려한 리스크 조정 수익률 (Sharpe보다 더 실용적)

            **Calmar Ratio**: 최대 낙폭(MDD) 대비 연간 수익률 (높을수록 좋음)

            **Profit Factor**: 총 이익 / 총 손실 (>1이면 수익, >2면 우수)

            **Max Drawdown**: 고점 대비 최대 낙폭 (손실 금액)
            """)

st.markdown("---")

# =============================================================================
# SECTION 2: 리스크 분석 (VaR, CVaR)
# =============================================================================
st.markdown("### ⚠️ 리스크 분석")

if 'pnl' in trades.columns:
    pnl_data = trades['pnl']

    # Calculate VaR and CVaR at different confidence levels
    confidence_levels = [0.90, 0.95, 0.99]

    col1, col2, col3 = st.columns(3)

    for i, conf in enumerate(confidence_levels):
        var = np.percentile(pnl_data, (1 - conf) * 100)
        cvar = pnl_data[pnl_data <= var].mean()

        with [col1, col2, col3][i]:
            st.metric(
                f"VaR ({int(conf*100)}%)",
                format_currency(var, include_sign=True),
                help=f"{int(conf*100)}% 확률로 손실이 이 금액을 초과하지 않음"
            )
            st.metric(
                f"CVaR ({int(conf*100)}%)",
                format_currency(cvar, include_sign=True),
                help=f"VaR을 초과하는 경우의 평균 손실"
            )

    # PNL Distribution Box Plot
    st.markdown("#### 📦 PNL 분포 분석")

    if 'strategy_name' in trades.columns:
        st.plotly_chart(
            ChartBuilder.box_plot(
                trades,
                x_col='strategy_name',
                y_col='pnl',
                title="전략별 PNL 분포 (Box Plot)",
                height=400,
                dark_mode=dark_mode
            ),
            use_container_width=True
        )

    with st.expander("📖 리스크 지표 설명"):
        st.markdown("""
        **VaR (Value at Risk)**: 특정 신뢰수준에서 예상되는 최대 손실

        예: VaR(95%) = -$50 의미는 "95% 확률로 손실이 $50을 초과하지 않음"

        **CVaR (Conditional VaR / Expected Shortfall)**: VaR을 초과하는 손실의 평균

        VaR보다 극단적 손실을 더 잘 반영하므로 더 보수적인 리스크 측정치

        **Box Plot**: 분포의 중앙값, 사분위수, 이상치를 시각화
        - 박스: 25% ~ 75% 구간
        - 중앙선: 중앙값
        - 수염: 최소/최대 (이상치 제외)
        - 점: 이상치
        """)

st.markdown("---")

# =============================================================================
# SECTION 3: 심볼별 성과 비교
# =============================================================================
st.markdown("### 💱 심볼별 성과 비교")

if 'symbol' in trades.columns and 'pnl' in trades.columns:
    symbol_performance = trades.groupby('symbol').agg({
        'pnl': ['sum', 'mean', 'count', lambda x: (x > 0).sum() / len(x) * 100]
    }).reset_index()

    symbol_performance.columns = ['Symbol', 'Total PNL', 'Avg PNL', 'Trade Count', 'Win Rate (%)']

    col1, col2 = st.columns(2)

    with col1:
        st.metric("BTC/USDT 거래",
                  f"{symbol_performance[symbol_performance['Symbol']=='BTC/USDT']['Trade Count'].values[0] if 'BTC/USDT' in symbol_performance['Symbol'].values else 0:.0f}건")
        st.metric("BTC 총 PNL",
                  format_currency(symbol_performance[symbol_performance['Symbol']=='BTC/USDT']['Total PNL'].values[0] if 'BTC/USDT' in symbol_performance['Symbol'].values else 0))

    with col2:
        st.metric("ETH/USDT 거래",
                  f"{symbol_performance[symbol_performance['Symbol']=='ETH/USDT']['Trade Count'].values[0] if 'ETH/USDT' in symbol_performance['Symbol'].values else 0:.0f}건")
        st.metric("ETH 총 PNL",
                  format_currency(symbol_performance[symbol_performance['Symbol']=='ETH/USDT']['Total PNL'].values[0] if 'ETH/USDT' in symbol_performance['Symbol'].values else 0))

    # Symbol comparison bar chart
    st.plotly_chart(
        ChartBuilder.metric_comparison_bar(
            symbol_performance,
            category_col='Symbol',
            metrics=['Total PNL', 'Avg PNL'],
            title="심볼별 성과 비교",
            height=350,
            dark_mode=dark_mode
        ),
        use_container_width=True
    )

st.markdown("---")

# =============================================================================
# SECTION 4: 시간대별 성과 패턴
# =============================================================================
st.markdown("### ⏰ 시간대별 성과 패턴")

if 'entry_time' in trades.columns and 'pnl' in trades.columns:
    # Parse timestamps
    trades_copy = trades.copy()
    trades_copy['entry_time'] = pd.to_datetime(trades_copy['entry_time'])
    trades_copy['hour'] = trades_copy['entry_time'].dt.hour
    trades_copy['day_of_week'] = trades_copy['entry_time'].dt.day_name()

    # Hourly performance
    hourly_perf = trades_copy.groupby('hour')['pnl'].mean().reset_index()
    hourly_perf.columns = ['Hour', 'Avg PNL']

    st.markdown("#### 📅 시간대별 평균 PNL")
    st.plotly_chart(
        ChartBuilder.daily_pnl_bar(
            hourly_perf,
            date_col='Hour',
            pnl_col='Avg PNL',
            title="시간대별 평균 PNL (KST)",
            height=350,
            dark_mode=dark_mode
        ),
        use_container_width=True
    )

    # Highlight US market hours
    st.info("🇺🇸 **미국 시장 개장 시간**: KST 22:30 ~ 05:00 (여름 23:30 ~ 06:00)")

    # Day of week vs Hour heatmap
    if len(trades_copy) > 20:  # Need enough data for heatmap
        st.markdown("#### 🔥 요일 × 시간 히트맵")

        day_hour_perf = trades_copy.groupby(['day_of_week', 'hour'])['pnl'].mean().reset_index()

        # Reorder days
        day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        day_hour_perf['day_of_week'] = pd.Categorical(
            day_hour_perf['day_of_week'],
            categories=day_order,
            ordered=True
        )
        day_hour_perf = day_hour_perf.sort_values('day_of_week')

        st.plotly_chart(
            ChartBuilder.performance_heatmap(
                day_hour_perf,
                x_col='hour',
                y_col='day_of_week',
                z_col='pnl',
                title="요일별 × 시간대별 평균 PNL",
                height=400,
                dark_mode=dark_mode
            ),
            use_container_width=True
        )

st.markdown("---")

# =============================================================================
# SECTION 5: 월별 성과 추세
# =============================================================================
st.markdown("### 📆 월별 성과 추세")

if 'entry_time' in trades.columns:
    trades_copy = trades.copy()
    trades_copy['entry_time'] = pd.to_datetime(trades_copy['entry_time'])
    trades_copy['month'] = trades_copy['entry_time'].dt.to_period('M').astype(str)

    monthly_perf = trades_copy.groupby('month').agg({
        'pnl': ['sum', 'mean', 'count'],
        'strategy_name': 'first'
    }).reset_index()

    monthly_perf.columns = ['Month', 'Total PNL', 'Avg PNL', 'Trade Count', 'Strategy']

    col1, col2 = st.columns(2)

    with col1:
        st.plotly_chart(
            ChartBuilder.daily_pnl_bar(
                monthly_perf,
                date_col='Month',
                pnl_col='Total PNL',
                title="월별 총 PNL",
                height=350,
                dark_mode=dark_mode
            ),
            use_container_width=True
        )

    with col2:
        st.dataframe(
            monthly_perf[['Month', 'Total PNL', 'Trade Count']].style.format({
                'Total PNL': '${:.2f}',
                'Trade Count': '{:.0f}'
            }),
            use_container_width=True,
            hide_index=True
        )

st.markdown("---")

# =============================================================================
# SECTION 6: 상관관계 분석
# =============================================================================
st.markdown("### 🔗 성과 지표 상관관계")

if len(metrics_df) > 1:
    # Select numeric columns for correlation
    numeric_cols = ['Total Return', 'Win Rate (%)', 'Sharpe Ratio', 'Sortino Ratio', 'Profit Factor', 'Max Drawdown']
    corr_data = metrics_df[numeric_cols]

    if len(corr_data) > 1:
        correlation_matrix = corr_data.corr()

        st.plotly_chart(
            ChartBuilder.correlation_heatmap(
                correlation_matrix,
                title="성과 지표 간 상관관계",
                height=500,
                dark_mode=dark_mode
            ),
            use_container_width=True
        )

        with st.expander("📖 상관관계 해석"):
            st.markdown("""
            **상관계수 범위**: -1 ~ +1
            - **+1**: 완벽한 양의 상관관계 (함께 증가)
            - **0**: 상관관계 없음
            - **-1**: 완벽한 음의 상관관계 (반대로 움직임)

            **일반적 패턴**:
            - Sharpe와 Sortino는 보통 강한 양의 상관관계
            - Win Rate와 Profit Factor는 보통 양의 상관관계
            - Max Drawdown(손실)은 다른 지표들과 음의 상관관계
            """)
else:
    st.info("상관관계 분석을 위해서는 2개 이상의 전략 데이터가 필요합니다")

st.markdown("---")

# Footer
st.markdown("---")
st.caption(f"""
**데이터 기간**: {start_date_str} ~ {end_date_str} |
**총 거래**: {len(trades)}건 |
**마지막 업데이트**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
""")
