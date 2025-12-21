"""
Optimization Viewer Page

Explore strategy optimization results and parameter tuning visualizations.
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
from dashboard.utils.formatters import format_duration
from dashboard.utils.theme import apply_dark_mode_css, initialize_dark_mode
from config.config import Config


st.set_page_config(page_title="최적화", page_icon="⚙️", layout="wide")

# Initialize dark mode immediately to prevent flash
initialize_dark_mode()

# Apply dark mode CSS
apply_dark_mode_css()

# Title
st.title("⚙️ 최적화 결과")
st.markdown("전략 파라미터 최적화 및 백테스트 분석 탐색")
st.markdown("---")

# Initialize data loader
if 'data_loader' not in st.session_state:
    config = Config()
    st.session_state.data_loader = DashboardDataLoader(config.DB_PATH)

data_loader = st.session_state.data_loader

# Get dark mode from session state (default False if not set)
dark_mode = st.session_state.get('dark_mode', False)

# Load optimization runs
optimization_runs = data_loader.get_optimization_runs(limit=50)

if optimization_runs.empty:
    st.warning("⚠️ 데이터베이스에서 최적화 실행을 찾을 수 없습니다")
    st.info("""
    **최적화 데이터가 없습니다.**

    최적화 실행은 다음과 같은 경우에 생성됩니다:
    - 'comprehensive' 모드로 전략 선택 실행 시
    - 수동 Optuna 최적화 실행 시

    **최적화 데이터 생성 방법:**
    - .env에서 `SELECTOR_MODE=comprehensive` 설정
    - 실행: `python main_bot.py --mode select`
    - 또는 optimizer 모듈 직접 사용

    **참고:** 빠른 선택 모드는 사전 정의된 파라미터를 사용하며 Optuna를 실행하지 않습니다.
    """)
    st.stop()

# Optimization Run Selector
st.markdown("### 📋 최적화 실행 선택")

# Group by date and strategy
run_options = []
for idx, row in optimization_runs.iterrows():
    date_str = row['date'].strftime('%Y-%m-%d') if pd.notna(row['date']) else 'Unknown'
    label = f"{date_str} - {row['strategy_name']} ({row.get('n_trials', 0)} trials)"
    run_options.append((label, idx))

if run_options:
    selected_label = st.selectbox(
        "최적화 실행",
        options=[label for label, _ in run_options],
        index=0
    )

    # Get selected run index
    selected_idx = [idx for label, idx in run_options if label == selected_label][0]
    selected_run = optimization_runs.iloc[selected_idx]

    st.markdown("---")

    # Optimization Summary
    st.markdown("### 📊 최적화 요약")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("전략", selected_run['strategy_name'])

    with col2:
        st.metric("최고 점수", f"{selected_run.get('best_score', 0):.2f}")

    with col3:
        st.metric("완료된 시도", selected_run.get('n_trials', 0))

    with col4:
        duration_sec = selected_run.get('duration_seconds', 0)
        st.metric("기간", format_duration(duration_sec))

    st.markdown("---")

    # Best Parameters
    st.markdown("### 🏆 발견된 최고의 파라미터")

    best_params_str = selected_run.get('best_params', '{}')
    try:
        if isinstance(best_params_str, str):
            best_params = json.loads(best_params_str)
        else:
            best_params = best_params_str if isinstance(best_params_str, dict) else {}

        if best_params:
            param_df = pd.DataFrame([
                {'Parameter': k, 'Value': str(v)}
                for k, v in best_params.items()
            ])
            st.dataframe(param_df, use_container_width=True, hide_index=True)
        else:
            st.info("파라미터 데이터 없음")

    except json.JSONDecodeError:
        st.error(f"최고 파라미터 파싱 오류: {best_params_str}")

    st.markdown("---")

    # Parameter Exploration (using backtest results from same date)
    st.markdown("### 🔍 파라미터 탐색")

    date_str = selected_run['date'].strftime('%Y-%m-%d') if pd.notna(selected_run['date']) else None

    if date_str:
        # Get all backtest results for this strategy on this date
        all_results = data_loader.get_strategy_rankings(date_str)

        # Filter for this strategy
        strategy_name = selected_run['strategy_name']
        strategy_results = all_results[
            all_results['strategy_name'].str.contains(strategy_name.split('_')[0], case=False, na=False)
        ]

        if not strategy_results.empty and len(strategy_results) > 5:
            st.markdown("#### 파라미터 대 점수 분석")

            # Try to extract parameters and create contour/scatter plot
            # This requires parsing params column
            param_data = []
            for idx, row in strategy_results.iterrows():
                try:
                    params_str = row.get('params', '{}')
                    if isinstance(params_str, str):
                        params = json.loads(params_str)
                    else:
                        params = params_str if isinstance(params_str, dict) else {}

                    param_data.append({
                        'score': row.get('score', 0),
                        **params
                    })
                except:
                    continue

            if param_data:
                param_df = pd.DataFrame(param_data)

                # Find parameters that vary
                varying_params = []
                for col in param_df.columns:
                    if col != 'score' and param_df[col].nunique() > 1:
                        varying_params.append(col)

                if len(varying_params) >= 2:
                    # Create contour plot
                    col1, col2 = st.columns(2)

                    with col1:
                        x_param = st.selectbox("X축 파라미터", varying_params, index=0)

                    with col2:
                        y_param = st.selectbox(
                            "Y축 파라미터",
                            [p for p in varying_params if p != x_param],
                            index=0
                        )

                    st.plotly_chart(
                        ChartBuilder.optimization_contour(
                            param_df,
                            x_col=x_param,
                            y_col=y_param,
                            z_col='score',
                            height=500,
                            dark_mode=dark_mode
                        ),
                        use_container_width=True
                    )

                elif len(varying_params) == 1:
                    # Single parameter - use line plot
                    param = varying_params[0]
                    st.plotly_chart(
                        ChartBuilder.parameter_scatter(
                            param_df,
                            x_col=param,
                            y_col='score',
                            color_col='score',
                            title=f"Score vs {param}",
                            height=400,
                            dark_mode=dark_mode
                        ),
                        use_container_width=True
                    )

                else:
                    st.info("시각화를 위해 변동하는 파라미터가 없습니다")

            else:
                st.info("시각화를 위한 파라미터 데이터를 파싱할 수 없습니다")

        else:
            st.info("파라미터 탐색을 위한 백테스트 결과가 충분하지 않습니다 (> 5개의 데이터 포인트 필요)")

    st.markdown("---")

    # Detailed Backtest Report
    with st.expander("📊 상세 백테스트 결과"):
        if date_str:
            st.markdown(f"#### {date_str}에 테스트된 모든 전략 변형")

            rankings = data_loader.get_strategy_rankings(date_str)

            if not rankings.empty:
                # Show top 20 results
                top_results = rankings.head(20)

                st.dataframe(
                    top_results[[
                        'rank', 'strategy_name', 'score', 'total_return',
                        'win_rate', 'profit_factor', 'max_drawdown', 'total_trades'
                    ]],
                    use_container_width=True,
                    hide_index=True
                )

                # Download button
                csv = rankings.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="📥 전체 결과 CSV 다운로드",
                    data=csv,
                    file_name=f"optimization_results_{date_str}_{strategy_name}.csv",
                    mime="text/csv"
                )

            else:
                st.info("이 날짜에 대한 백테스트 결과가 없습니다")

else:
    st.error("선택할 수 있는 최적화 실행이 없습니다")

# Footer
st.markdown("---")
st.caption(f"마지막 업데이트: {datetime.now().strftime('%H:%M:%S')}")
