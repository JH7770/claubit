"""
Chart Builder Module

Provides standardized Plotly charts for the dashboard.
All charts use consistent styling and theme.
"""

import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
from typing import Optional, List, Dict


class ChartBuilder:
    """Builds standardized Plotly charts for dashboard."""

    # Color scheme
    COLOR_POSITIVE = '#00CC96'  # Green
    COLOR_NEGATIVE = '#EF553B'  # Red
    COLOR_PRIMARY = '#1f77b4'   # Blue
    COLOR_SECONDARY = '#ff7f0e'  # Orange

    @staticmethod
    def equity_curve(
        df: pd.DataFrame,
        x_col: str = 'timestamp',
        y_col: str = 'cumulative_pnl',
        title: str = "자산 곡선",
        height: int = 400
    ) -> go.Figure:
        """
        Create equity curve line chart with fill.

        Args:
            df: DataFrame with equity data
            x_col: Column name for x-axis (time)
            y_col: Column name for y-axis (equity/PNL)
            title: Chart title
            height: Chart height in pixels

        Returns:
            Plotly Figure object
        """
        if df.empty:
            # Return empty chart with message
            fig = go.Figure()
            fig.add_annotation(
                text="데이터 없음",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False,
                font=dict(size=20, color="gray")
            )
            fig.update_layout(height=height, template='plotly_white')
            return fig

        # Determine fill color based on final value
        final_value = df[y_col].iloc[-1] if len(df) > 0 else 0
        fill_color = ChartBuilder.COLOR_POSITIVE if final_value >= 0 else ChartBuilder.COLOR_NEGATIVE
        # Convert hex to rgba properly
        hex_clean = fill_color.lstrip('#')
        r, g, b = int(hex_clean[0:2], 16), int(hex_clean[2:4], 16), int(hex_clean[4:6], 16)
        fill_color_rgba = f'rgba({r}, {g}, {b}, 0.2)'

        fig = go.Figure()

        # Add line with fill
        fig.add_trace(go.Scatter(
            x=df[x_col],
            y=df[y_col],
            mode='lines',
            name='Equity',
            line=dict(color=ChartBuilder.COLOR_PRIMARY, width=2),
            fill='tozeroy',
            fillcolor=fill_color_rgba
        ))

        fig.update_layout(
            title=title,
            xaxis_title="시간",
            yaxis_title="누적 PNL ($)",
            hovermode='x unified',
            template='plotly_white',
            height=height
        )

        return fig

    @staticmethod
    def daily_pnl_bar(
        df: pd.DataFrame,
        date_col: str = 'date',
        pnl_col: str = 'total_pnl',
        title: str = "일일 PNL",
        height: int = 400
    ) -> go.Figure:
        """
        Create daily PNL bar chart with color coding.

        Args:
            df: DataFrame with daily PNL data
            date_col: Column name for dates
            pnl_col: Column name for PNL values
            title: Chart title
            height: Chart height in pixels

        Returns:
            Plotly Figure object
        """
        if df.empty:
            fig = go.Figure()
            fig.add_annotation(
                text="데이터 없음",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False,
                font=dict(size=20, color="gray")
            )
            fig.update_layout(height=height, template='plotly_white')
            return fig

        # Color bars based on positive/negative
        colors = [ChartBuilder.COLOR_POSITIVE if x >= 0 else ChartBuilder.COLOR_NEGATIVE
                  for x in df[pnl_col]]

        fig = go.Figure(data=[
            go.Bar(
                x=df[date_col],
                y=df[pnl_col],
                marker_color=colors,
                text=df[pnl_col].apply(lambda x: f"${x:.2f}"),
                textposition='outside',
                hovertemplate='<b>%{x}</b><br>PNL: $%{y:.2f}<extra></extra>'
            )
        ])

        fig.update_layout(
            title=title,
            xaxis_title="날짜",
            yaxis_title="PNL ($)",
            template='plotly_white',
            height=height,
            showlegend=False
        )

        # Add horizontal line at y=0
        fig.add_hline(y=0, line_dash="dash", line_color="gray", opacity=0.5)

        return fig

    @staticmethod
    def strategy_comparison_radar(
        metrics: Dict[str, float],
        title: str = "전략 성과",
        height: int = 400
    ) -> go.Figure:
        """
        Create radar chart for strategy metrics comparison.

        Args:
            metrics: Dictionary of metric names and normalized values (0-100)
            title: Chart title
            height: Chart height in pixels

        Returns:
            Plotly Figure object
        """
        if not metrics:
            fig = go.Figure()
            fig.add_annotation(
                text="지표 없음",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False,
                font=dict(size=20, color="gray")
            )
            fig.update_layout(height=height, template='plotly_white')
            return fig

        categories = list(metrics.keys())
        values = list(metrics.values())

        fig = go.Figure(data=go.Scatterpolar(
            r=values,
            theta=categories,
            fill='toself',
            fillcolor=f'rgba{tuple(list(int(ChartBuilder.COLOR_PRIMARY.lstrip("#")[i:i+2], 16) for i in (0, 2, 4)) + [0.3])}',
            line=dict(color=ChartBuilder.COLOR_PRIMARY, width=2)
        ))

        fig.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, 100]
                )
            ),
            showlegend=False,
            title=title,
            template='plotly_white',
            height=height
        )

        return fig

    @staticmethod
    def optimization_contour(
        df: pd.DataFrame,
        x_col: str,
        y_col: str,
        z_col: str = 'score',
        title: Optional[str] = None,
        height: int = 500
    ) -> go.Figure:
        """
        Create contour plot for parameter optimization visualization.

        Args:
            df: DataFrame with optimization results
            x_col: Column name for x-axis parameter
            y_col: Column name for y-axis parameter
            z_col: Column name for score/objective
            title: Chart title
            height: Chart height in pixels

        Returns:
            Plotly Figure object
        """
        if df.empty:
            fig = go.Figure()
            fig.add_annotation(
                text="최적화 데이터 없음",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False,
                font=dict(size=20, color="gray")
            )
            fig.update_layout(height=height, template='plotly_white')
            return fig

        try:
            # Pivot data for contour plot
            pivot = df.pivot_table(index=y_col, columns=x_col, values=z_col, aggfunc='mean')

            fig = go.Figure(data=go.Contour(
                z=pivot.values,
                x=pivot.columns,
                y=pivot.index,
                colorscale='Viridis',
                contours=dict(
                    coloring='heatmap',
                    showlabels=True,
                    labelfont=dict(size=10, color='white')
                ),
                colorbar=dict(title=z_col.capitalize())
            ))

            fig.update_layout(
                title=title or f"{z_col.capitalize()} Optimization: {x_col} vs {y_col}",
                xaxis_title=x_col,
                yaxis_title=y_col,
                template='plotly_white',
                height=height
            )

            return fig

        except Exception as e:
            # Fallback to scatter plot if pivot fails
            return ChartBuilder.parameter_scatter(df, x_col, y_col, z_col, title, height)

    @staticmethod
    def parameter_scatter(
        df: pd.DataFrame,
        x_col: str,
        y_col: str,
        color_col: str = 'score',
        title: Optional[str] = None,
        height: int = 500
    ) -> go.Figure:
        """
        Create scatter plot for parameter visualization.

        Args:
            df: DataFrame with parameter data
            x_col: Column name for x-axis
            y_col: Column name for y-axis
            color_col: Column name for color coding
            title: Chart title
            height: Chart height in pixels

        Returns:
            Plotly Figure object
        """
        if df.empty:
            fig = go.Figure()
            fig.add_annotation(
                text="데이터 없음",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False,
                font=dict(size=20, color="gray")
            )
            fig.update_layout(height=height, template='plotly_white')
            return fig

        fig = px.scatter(
            df,
            x=x_col,
            y=y_col,
            color=color_col,
            color_continuous_scale='Viridis',
            title=title or f"{x_col} vs {y_col}",
            height=height,
            template='plotly_white'
        )

        return fig

    @staticmethod
    def exit_reason_pie(
        df: pd.DataFrame,
        reason_col: str = 'exit_reason',
        title: str = "종료 사유 분포",
        height: int = 400
    ) -> go.Figure:
        """
        Create pie chart for exit reasons distribution.

        Args:
            df: DataFrame with trade data
            reason_col: Column name for exit reasons
            title: Chart title
            height: Chart height in pixels

        Returns:
            Plotly Figure object
        """
        if df.empty:
            fig = go.Figure()
            fig.add_annotation(
                text="데이터 없음",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False,
                font=dict(size=20, color="gray")
            )
            fig.update_layout(height=height, template='plotly_white')
            return fig

        # Count exit reasons
        reason_counts = df[reason_col].value_counts()

        fig = go.Figure(data=[go.Pie(
            labels=reason_counts.index,
            values=reason_counts.values,
            hole=0.3,
            textinfo='label+percent',
            hovertemplate='<b>%{label}</b><br>Count: %{value}<br>Percent: %{percent}<extra></extra>'
        )])

        fig.update_layout(
            title=title,
            template='plotly_white',
            height=height
        )

        return fig

    @staticmethod
    def strategy_ranking_bar(
        df: pd.DataFrame,
        strategy_col: str = 'strategy_name',
        score_col: str = 'score',
        title: str = "전략 순위",
        height: int = 400,
        top_n: int = 10
    ) -> go.Figure:
        """
        Create horizontal bar chart for strategy rankings.

        Args:
            df: DataFrame with strategy data
            strategy_col: Column name for strategy names
            score_col: Column name for scores
            title: Chart title
            height: Chart height in pixels
            top_n: Number of top strategies to display

        Returns:
            Plotly Figure object
        """
        if df.empty:
            fig = go.Figure()
            fig.add_annotation(
                text="데이터 없음",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False,
                font=dict(size=20, color="gray")
            )
            fig.update_layout(height=height, template='plotly_white')
            return fig

        # Take top N strategies
        df_top = df.nlargest(top_n, score_col)

        # Color bars: top 3 in different shades
        colors = []
        for i in range(len(df_top)):
            if i == 0:
                colors.append('#FFD700')  # Gold for 1st
            elif i == 1:
                colors.append('#C0C0C0')  # Silver for 2nd
            elif i == 2:
                colors.append('#CD7F32')  # Bronze for 3rd
            else:
                colors.append(ChartBuilder.COLOR_PRIMARY)

        fig = go.Figure(data=[
            go.Bar(
                y=df_top[strategy_col],
                x=df_top[score_col],
                orientation='h',
                marker_color=colors,
                text=df_top[score_col].apply(lambda x: f"{x:.2f}"),
                textposition='outside',
                hovertemplate='<b>%{y}</b><br>Score: %{x:.2f}<extra></extra>'
            )
        ])

        fig.update_layout(
            title=title,
            xaxis_title="점수",
            yaxis_title="전략",
            template='plotly_white',
            height=height,
            showlegend=False,
            yaxis=dict(autorange="reversed")  # Top strategy at the top
        )

        return fig

    @staticmethod
    def optimization_history_line(
        df: pd.DataFrame,
        trial_col: str = 'trial',
        score_col: str = 'score',
        title: str = "최적화 진행 상황",
        height: int = 400
    ) -> go.Figure:
        """
        Create line chart showing optimization progress over trials.

        Args:
            df: DataFrame with trial data
            trial_col: Column name for trial numbers
            score_col: Column name for scores
            title: Chart title
            height: Chart height in pixels

        Returns:
            Plotly Figure object
        """
        if df.empty:
            fig = go.Figure()
            fig.add_annotation(
                text="최적화 기록 없음",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False,
                font=dict(size=20, color="gray")
            )
            fig.update_layout(height=height, template='plotly_white')
            return fig

        # Calculate best score so far for each trial
        best_so_far = df[score_col].cummax()

        fig = go.Figure()

        # Add all trials
        fig.add_trace(go.Scatter(
            x=df[trial_col],
            y=df[score_col],
            mode='markers',
            name='Trial Score',
            marker=dict(size=6, color=ChartBuilder.COLOR_SECONDARY, opacity=0.6),
            hovertemplate='<b>Trial %{x}</b><br>Score: %{y:.2f}<extra></extra>'
        ))

        # Add best score line
        fig.add_trace(go.Scatter(
            x=df[trial_col],
            y=best_so_far,
            mode='lines',
            name='Best Score',
            line=dict(color=ChartBuilder.COLOR_PRIMARY, width=2),
            hovertemplate='<b>Trial %{x}</b><br>Best: %{y:.2f}<extra></extra>'
        ))

        fig.update_layout(
            title=title,
            xaxis_title="시도 번호",
            yaxis_title="점수",
            template='plotly_white',
            height=height,
            hovermode='x unified'
        )

        return fig
