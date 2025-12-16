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


st.set_page_config(page_title="Today's Strategy", page_icon="🎯", layout="wide")

# Title
st.title("🎯 Today's Champion Strategy")
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
        "Select Date",
        value=datetime.now(),
        max_value=datetime.now()
    )
with col2:
    if st.button("🔄 Refresh"):
        data_loader.clear_cache()
        st.rerun()

date_str = selected_date.strftime('%Y-%m-%d')

# Load today's strategy
strategy = data_loader.get_today_strategy(date_str)

if not strategy:
    st.warning(f"⚠️ No strategy selected for {date_str}")
    st.info("""
    **No strategy data found for this date.**

    Possible reasons:
    - Strategy selection hasn't run yet for this date
    - Database doesn't have backtest results for this date
    - Bot is not configured for automatic strategy selection

    **Next Steps:**
    - Try a different date
    - Run strategy selection manually: `python main_bot.py --mode select`
    - Check bot logs for errors
    """)
    st.stop()

# Champion Strategy Card
st.markdown("### 🏆 Selected Strategy")

col1, col2, col3 = st.columns([2, 1, 1])

with col1:
    st.markdown(f"#### {strategy['strategy_name']}")
    st.caption(f"Selected on: {strategy.get('date', date_str)}")

with col2:
    st.metric("Composite Score", f"{strategy.get('score', 0):.2f}")

with col3:
    rank = strategy.get('rank', 1)
    medal = "🥇" if rank == 1 else "🥈" if rank == 2 else "🥉" if rank == 3 else f"#{rank}"
    st.metric("Rank", medal)

st.markdown("---")

# Performance Metrics Grid
st.markdown("### 📊 Backtest Performance Metrics")

metrics_data = [
    ("Total Return", format_percentage(strategy.get('total_return', 0)), None),
    ("Win Rate", format_percentage(strategy.get('win_rate', 0)), None),
    ("Profit Factor", f"{strategy.get('profit_factor', 0):.2f}", None),
    ("Sharpe Ratio", f"{strategy.get('sharpe_ratio', 0):.2f}", None)
]

MetricCard.display_4_column_metrics(metrics_data)

col1, col2 = st.columns(2)
with col1:
    st.metric("Max Drawdown", format_percentage(abs(strategy.get('max_drawdown', 0))))
with col2:
    st.metric("Total Trades", strategy.get('total_trades', 0))

st.markdown("---")

# Applied Parameters
st.markdown("### ⚙️ Applied Parameters")

params_str = strategy.get('params', '{}')
try:
    if isinstance(params_str, str):
        params = json.loads(params_str)
    else:
        params = params_str if isinstance(params_str, dict) else {}

    if params:
        # Create parameter table
        param_descriptions = {
            'k': 'Volatility multiplier for breakout detection',
            'lookback_period': 'Number of periods to calculate volatility',
            'ma_period': 'Moving average period for trend filter',
            'use_ma_filter': 'Enable moving average trend filter',
            'stop_loss_percent': 'Stop loss threshold percentage',
            'take_profit_percent': 'Take profit target percentage',
            'rsi_period': 'RSI calculation period',
            'rsi_buy_threshold': 'RSI oversold threshold (buy signal)',
            'rsi_sell_threshold': 'RSI overbought threshold (sell signal)',
            'bb_period': 'Bollinger Bands period',
            'bb_stddev': 'Bollinger Bands standard deviation multiplier',
            'short_window': 'Short moving average window',
            'long_window': 'Long moving average window',
            'vol_lookback': 'Volume lookback period',
            'vol_multiplier': 'Volume surge multiplier'
        }

        param_data = []
        for key, value in params.items():
            description = param_descriptions.get(key, 'Parameter for strategy configuration')
            param_data.append({
                'Parameter': key,
                'Value': str(value),
                'Description': description
            })

        param_df = pd.DataFrame(param_data)
        st.dataframe(param_df, use_container_width=True, hide_index=True)
    else:
        st.info("No parameters specified for this strategy")

except json.JSONDecodeError:
    st.error(f"Error parsing parameters: {params_str}")

st.markdown("---")

# Strategy Comparison - Top Alternatives
st.markdown("### 📈 Strategy Rankings (All Tested)")

rankings = data_loader.get_strategy_rankings(date_str)

if not rankings.empty:
    # Show ranking chart
    st.plotly_chart(
        ChartBuilder.strategy_ranking_bar(
            rankings,
            strategy_col='strategy_name',
            score_col='score',
            title="Strategy Performance Comparison",
            top_n=10
        ),
        use_container_width=True
    )

    # Show detailed table
    st.markdown("#### Detailed Rankings")

    # Format ranking table
    rankings_display = TableFormatter.format_strategy_ranking(rankings)

    # Display table
    st.dataframe(rankings_display, use_container_width=True, hide_index=True)

    # Download button
    csv = rankings.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Download Rankings CSV",
        data=csv,
        file_name=f"strategy_rankings_{date_str}.csv",
        mime="text/csv"
    )

else:
    st.info("No ranking data available for this date")

st.markdown("---")

# Radar Chart for Multi-Metric Comparison
st.markdown("### 🎯 Multi-Metric Performance Radar")

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
                title="Strategy Performance Metrics (Normalized)",
                height=400
            ),
            use_container_width=True
        )

    with col2:
        st.markdown("#### Metric Interpretation")
        st.markdown("""
        **Normalized metrics (0-100 scale):**

        - **Return**: Total return % scaled
        - **Win Rate**: Percentage of winning trades
        - **Sharpe**: Risk-adjusted return quality
        - **Profit Factor**: Profit/Loss ratio
        - **Drawdown**: Capital preservation (inverted)

        A well-rounded strategy shows balanced
        performance across all metrics.
        """)

# Footer
st.markdown("---")
st.caption(f"Strategy selection date: {date_str} | Last updated: {datetime.now().strftime('%H:%M:%S')}")
