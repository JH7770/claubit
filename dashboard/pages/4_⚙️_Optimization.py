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
from config.config import Config


st.set_page_config(page_title="Optimization", page_icon="⚙️", layout="wide")

# Title
st.title("⚙️ Optimization Results")
st.markdown("Explore strategy parameter optimization and backtest analysis")
st.markdown("---")

# Initialize data loader
if 'data_loader' not in st.session_state:
    config = Config()
    st.session_state.data_loader = DashboardDataLoader(config.DB_PATH)

data_loader = st.session_state.data_loader

# Load optimization runs
optimization_runs = data_loader.get_optimization_runs(limit=50)

if optimization_runs.empty:
    st.warning("⚠️ No optimization runs found in database")
    st.info("""
    **No optimization data available.**

    Optimization runs are created when:
    - Running strategy selection in 'comprehensive' mode
    - Manual Optuna optimization is executed

    **To generate optimization data:**
    - Set `SELECTOR_MODE=comprehensive` in .env
    - Run: `python main_bot.py --mode select`
    - Or use the optimizer module directly

    **Note:** Quick selection mode uses predefined parameters and doesn't run Optuna.
    """)
    st.stop()

# Optimization Run Selector
st.markdown("### 📋 Select Optimization Run")

# Group by date and strategy
run_options = []
for idx, row in optimization_runs.iterrows():
    date_str = row['date'].strftime('%Y-%m-%d') if pd.notna(row['date']) else 'Unknown'
    label = f"{date_str} - {row['strategy_name']} ({row.get('n_trials', 0)} trials)"
    run_options.append((label, idx))

if run_options:
    selected_label = st.selectbox(
        "Optimization Run",
        options=[label for label, _ in run_options],
        index=0
    )

    # Get selected run index
    selected_idx = [idx for label, idx in run_options if label == selected_label][0]
    selected_run = optimization_runs.iloc[selected_idx]

    st.markdown("---")

    # Optimization Summary
    st.markdown("### 📊 Optimization Summary")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Strategy", selected_run['strategy_name'])

    with col2:
        st.metric("Best Score", f"{selected_run.get('best_score', 0):.2f}")

    with col3:
        st.metric("Trials Completed", selected_run.get('n_trials', 0))

    with col4:
        duration_sec = selected_run.get('duration_seconds', 0)
        st.metric("Duration", format_duration(duration_sec))

    st.markdown("---")

    # Best Parameters
    st.markdown("### 🏆 Best Parameters Found")

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
            st.info("No parameters data available")

    except json.JSONDecodeError:
        st.error(f"Error parsing best parameters: {best_params_str}")

    st.markdown("---")

    # Parameter Exploration (using backtest results from same date)
    st.markdown("### 🔍 Parameter Exploration")

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
            st.markdown("#### Parameter vs Score Analysis")

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
                        x_param = st.selectbox("X-axis Parameter", varying_params, index=0)

                    with col2:
                        y_param = st.selectbox(
                            "Y-axis Parameter",
                            [p for p in varying_params if p != x_param],
                            index=0
                        )

                    st.plotly_chart(
                        ChartBuilder.optimization_contour(
                            param_df,
                            x_col=x_param,
                            y_col=y_param,
                            z_col='score',
                            height=500
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
                            height=400
                        ),
                        use_container_width=True
                    )

                else:
                    st.info("No varying parameters found for visualization")

            else:
                st.info("Unable to parse parameter data for visualization")

        else:
            st.info("Not enough backtest results for parameter exploration (need > 5 data points)")

    st.markdown("---")

    # Detailed Backtest Report
    with st.expander("📊 Detailed Backtest Results"):
        if date_str:
            st.markdown(f"#### All Strategy Variants Tested on {date_str}")

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
                    label="📥 Download Full Results CSV",
                    data=csv,
                    file_name=f"optimization_results_{date_str}_{strategy_name}.csv",
                    mime="text/csv"
                )

            else:
                st.info("No backtest results found for this date")

else:
    st.error("No optimization runs available to select")

# Footer
st.markdown("---")
st.caption(f"Last updated: {datetime.now().strftime('%H:%M:%S')}")
