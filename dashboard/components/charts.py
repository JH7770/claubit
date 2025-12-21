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

# Import design system
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from dashboard.design_system import Colors, Typography


class ChartBuilder:
    """Builds standardized Plotly charts for dashboard using design system."""

    # Import colors from design system - Light Mode
    COLOR_PROFIT = Colors.PROFIT_LIGHT
    COLOR_LOSS = Colors.LOSS_LIGHT
    COLOR_PRIMARY = Colors.BLUE_500
    COLOR_SECONDARY = Colors.WARNING_500
    COLOR_WARNING = Colors.WARNING_500
    COLOR_NEUTRAL = Colors.GRAY_500

    # Dark Mode colors from design system
    COLOR_PROFIT_DARK = Colors.PROFIT_DARK
    COLOR_LOSS_DARK = Colors.LOSS_DARK
    COLOR_PRIMARY_DARK = Colors.BLUE_400
    COLOR_SECONDARY_DARK = Colors.WARNING_400
    COLOR_WARNING_DARK = Colors.WARNING_400
    COLOR_NEUTRAL_DARK = Colors.GRAY_400

    # Legacy names for backward compatibility
    COLOR_POSITIVE = Colors.PROFIT_LIGHT
    COLOR_NEGATIVE = Colors.LOSS_LIGHT

    # Font sizes from design system
    FONT_TITLE = Typography.FONT_SIZE_CHART_TITLE
    FONT_AXIS = Typography.FONT_SIZE_CHART_AXIS
    FONT_TICK = Typography.FONT_SIZE_CHART_TICK
    FONT_LEGEND = Typography.FONT_SIZE_CHART_LEGEND

    @staticmethod
    def get_base_layout(title: str, height: int = 400, dark_mode: bool = False) -> dict:
        """
        Get base layout configuration for all charts.

        Args:
            title: Chart title
            height: Chart height in pixels
            dark_mode: Whether to use dark mode colors

        Returns:
            Dictionary with base layout configuration
        """
        if dark_mode:
            title_color = '#f9fafb'
            font_color = '#f9fafb'
            grid_color = 'rgba(255,255,255,0.1)'
            template = 'plotly_dark'
        else:
            title_color = '#1f2937'
            font_color = '#1f2937'
            grid_color = 'rgba(0,0,0,0.1)'
            template = 'plotly_white'

        return dict(
            title=dict(
                text=title,
                font=dict(size=ChartBuilder.FONT_TITLE, family="Arial, sans-serif", color=title_color)
            ),
            font=dict(size=ChartBuilder.FONT_TICK, family="Arial, sans-serif", color=font_color),
            template=template,
            height=height,
            margin=dict(l=60, r=40, t=80, b=60),  # Increased margins
            hovermode='x unified',
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            xaxis=dict(
                title_font=dict(size=ChartBuilder.FONT_AXIS, color=font_color),
                tickfont=dict(size=ChartBuilder.FONT_TICK, color=font_color),
                gridcolor=grid_color
            ),
            yaxis=dict(
                title_font=dict(size=ChartBuilder.FONT_AXIS, color=font_color),
                tickfont=dict(size=ChartBuilder.FONT_TICK, color=font_color),
                gridcolor=grid_color
            )
        )

    @staticmethod
    def equity_curve(
        df: pd.DataFrame,
        x_col: str = 'timestamp',
        y_col: str = 'cumulative_pnl',
        title: str = "자산 곡선",
        height: int = 400,
        dark_mode: bool = False
    ) -> go.Figure:
        """
        Create equity curve line chart with fill.

        Args:
            df: DataFrame with equity data
            x_col: Column name for x-axis (time)
            y_col: Column name for y-axis (equity/PNL)
            title: Chart title
            height: Chart height in pixels
            dark_mode: Whether to use dark mode colors

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
            template = 'plotly_dark' if dark_mode else 'plotly_white'
            fig.update_layout(height=height, template=template)
            return fig

        # Determine fill color based on final value and dark mode
        final_value = df[y_col].iloc[-1] if len(df) > 0 else 0
        if dark_mode:
            fill_color = ChartBuilder.COLOR_PROFIT_DARK if final_value >= 0 else ChartBuilder.COLOR_LOSS_DARK
            line_color = ChartBuilder.COLOR_PRIMARY_DARK
        else:
            fill_color = ChartBuilder.COLOR_POSITIVE if final_value >= 0 else ChartBuilder.COLOR_NEGATIVE
            line_color = ChartBuilder.COLOR_PRIMARY

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
            line=dict(color=line_color, width=2),
            fill='tozeroy',
            fillcolor=fill_color_rgba
        ))

        # Apply base layout and customize
        layout = ChartBuilder.get_base_layout(title, height, dark_mode)
        layout['xaxis']['title'] = '시간'
        layout['yaxis']['title'] = '누적 PNL ($)'
        fig.update_layout(**layout)

        return fig

    @staticmethod
    def daily_pnl_bar(
        df: pd.DataFrame,
        date_col: str = 'date',
        pnl_col: str = 'total_pnl',
        title: str = "일일 PNL",
        height: int = 400,
        dark_mode: bool = False
    ) -> go.Figure:
        """
        Create daily PNL bar chart with color coding.

        Args:
            df: DataFrame with daily PNL data
            date_col: Column name for dates
            pnl_col: Column name for PNL values
            title: Chart title
            height: Chart height in pixels
            dark_mode: Whether to use dark mode colors

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
            template = 'plotly_dark' if dark_mode else 'plotly_white'
            fig.update_layout(height=height, template=template)
            return fig

        # Color bars based on positive/negative and dark mode
        if dark_mode:
            colors = [ChartBuilder.COLOR_PROFIT_DARK if x >= 0 else ChartBuilder.COLOR_LOSS_DARK
                      for x in df[pnl_col]]
            zero_line_color = ChartBuilder.COLOR_NEUTRAL_DARK
        else:
            colors = [ChartBuilder.COLOR_POSITIVE if x >= 0 else ChartBuilder.COLOR_NEGATIVE
                      for x in df[pnl_col]]
            zero_line_color = ChartBuilder.COLOR_NEUTRAL

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

        # Apply base layout and customize
        layout = ChartBuilder.get_base_layout(title, height, dark_mode)
        layout['xaxis']['title'] = '날짜'
        layout['yaxis']['title'] = 'PNL ($)'
        layout['showlegend'] = False
        fig.update_layout(**layout)

        # Add horizontal line at y=0 with improved styling
        fig.add_hline(y=0, line_dash="dash", line_color=zero_line_color, line_width=2, opacity=0.6)

        return fig

    @staticmethod
    def strategy_comparison_radar(
        metrics: Dict[str, float],
        title: str = "전략 성과",
        height: int = 400,
        dark_mode: bool = False
    ) -> go.Figure:
        """
        Create radar chart for strategy metrics comparison.

        Args:
            metrics: Dictionary of metric names and normalized values (0-100)
            title: Chart title
            height: Chart height in pixels
            dark_mode: Whether to use dark mode colors

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
            template = 'plotly_dark' if dark_mode else 'plotly_white'
            fig.update_layout(height=height, template=template)
            return fig

        categories = list(metrics.keys())
        values = list(metrics.values())

        # Use appropriate color based on dark mode
        line_color = ChartBuilder.COLOR_PRIMARY_DARK if dark_mode else ChartBuilder.COLOR_PRIMARY
        hex_clean = line_color.lstrip('#')
        r, g, b = int(hex_clean[0:2], 16), int(hex_clean[2:4], 16), int(hex_clean[4:6], 16)
        fill_color = f'rgba({r}, {g}, {b}, 0.3)'

        fig = go.Figure(data=go.Scatterpolar(
            r=values,
            theta=categories,
            fill='toself',
            fillcolor=fill_color,
            line=dict(color=line_color, width=2)
        ))

        template = 'plotly_dark' if dark_mode else 'plotly_white'
        fig.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, 100]
                )
            ),
            showlegend=False,
            title=title,
            template=template,
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
        height: int = 500,
        dark_mode: bool = False
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
            dark_mode: Whether to use dark mode colors

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
            template = 'plotly_dark' if dark_mode else 'plotly_white'
            fig.update_layout(height=height, template=template)
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

            template = 'plotly_dark' if dark_mode else 'plotly_white'
            fig.update_layout(
                title=title or f"{z_col.capitalize()} Optimization: {x_col} vs {y_col}",
                xaxis_title=x_col,
                yaxis_title=y_col,
                template=template,
                height=height
            )

            return fig

        except Exception as e:
            # Fallback to scatter plot if pivot fails
            return ChartBuilder.parameter_scatter(df, x_col, y_col, z_col, title, height, dark_mode)

    @staticmethod
    def parameter_scatter(
        df: pd.DataFrame,
        x_col: str,
        y_col: str,
        color_col: str = 'score',
        title: Optional[str] = None,
        height: int = 500,
        dark_mode: bool = False
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
            dark_mode: Whether to use dark mode colors

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
            template = 'plotly_dark' if dark_mode else 'plotly_white'
            fig.update_layout(height=height, template=template)
            return fig

        template = 'plotly_dark' if dark_mode else 'plotly_white'
        fig = px.scatter(
            df,
            x=x_col,
            y=y_col,
            color=color_col,
            color_continuous_scale='Viridis',
            title=title or f"{x_col} vs {y_col}",
            height=height,
            template=template
        )

        return fig

    @staticmethod
    def exit_reason_pie(
        df: pd.DataFrame,
        reason_col: str = 'exit_reason',
        title: str = "종료 사유 분포",
        height: int = 400,
        dark_mode: bool = False
    ) -> go.Figure:
        """
        Create pie chart for exit reasons distribution.

        Args:
            df: DataFrame with trade data
            reason_col: Column name for exit reasons
            title: Chart title
            height: Chart height in pixels
            dark_mode: Whether to use dark mode colors

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
            template = 'plotly_dark' if dark_mode else 'plotly_white'
            fig.update_layout(height=height, template=template)
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

        template = 'plotly_dark' if dark_mode else 'plotly_white'
        fig.update_layout(
            title=title,
            template=template,
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
        top_n: int = 10,
        dark_mode: bool = False
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
            dark_mode: Whether to use dark mode colors

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
            template = 'plotly_dark' if dark_mode else 'plotly_white'
            fig.update_layout(height=height, template=template)
            return fig

        # Take top N strategies
        df_top = df.nlargest(top_n, score_col)

        # Color bars: top 3 in different shades
        primary_color = ChartBuilder.COLOR_PRIMARY_DARK if dark_mode else ChartBuilder.COLOR_PRIMARY
        colors = []
        for i in range(len(df_top)):
            if i == 0:
                colors.append('#FFD700')  # Gold for 1st
            elif i == 1:
                colors.append('#C0C0C0')  # Silver for 2nd
            elif i == 2:
                colors.append('#CD7F32')  # Bronze for 3rd
            else:
                colors.append(primary_color)

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

        # Apply base layout and customize
        layout = ChartBuilder.get_base_layout(title, height, dark_mode)
        layout['xaxis']['title'] = '점수'
        layout['yaxis']['title'] = '전략'
        layout['yaxis']['autorange'] = "reversed"  # Top strategy at the top
        layout['showlegend'] = False
        fig.update_layout(**layout)

        return fig

    @staticmethod
    def optimization_history_line(
        df: pd.DataFrame,
        trial_col: str = 'trial',
        score_col: str = 'score',
        title: str = "최적화 진행 상황",
        height: int = 400,
        dark_mode: bool = False
    ) -> go.Figure:
        """
        Create line chart showing optimization progress over trials.

        Args:
            df: DataFrame with trial data
            trial_col: Column name for trial numbers
            score_col: Column name for scores
            title: Chart title
            height: Chart height in pixels
            dark_mode: Whether to use dark mode colors

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
            template = 'plotly_dark' if dark_mode else 'plotly_white'
            fig.update_layout(height=height, template=template)
            return fig

        # Calculate best score so far for each trial
        best_so_far = df[score_col].cummax()

        # Use appropriate colors based on dark mode
        if dark_mode:
            primary_color = ChartBuilder.COLOR_PRIMARY_DARK
            secondary_color = ChartBuilder.COLOR_SECONDARY_DARK
            neutral_color = ChartBuilder.COLOR_NEUTRAL_DARK
            legend_bg = 'rgba(31, 41, 55, 0.8)'
        else:
            primary_color = ChartBuilder.COLOR_PRIMARY
            secondary_color = ChartBuilder.COLOR_SECONDARY
            neutral_color = ChartBuilder.COLOR_NEUTRAL
            legend_bg = 'rgba(255, 255, 255, 0.8)'

        fig = go.Figure()

        # Add all trials
        fig.add_trace(go.Scatter(
            x=df[trial_col],
            y=df[score_col],
            mode='markers',
            name='Trial Score',
            marker=dict(size=6, color=secondary_color, opacity=0.6),
            hovertemplate='<b>Trial %{x}</b><br>Score: %{y:.2f}<extra></extra>'
        ))

        # Add best score line
        fig.add_trace(go.Scatter(
            x=df[trial_col],
            y=best_so_far,
            mode='lines',
            name='Best Score',
            line=dict(color=primary_color, width=2),
            hovertemplate='<b>Trial %{x}</b><br>Best: %{y:.2f}<extra></extra>'
        ))

        # Apply base layout and customize
        layout = ChartBuilder.get_base_layout(title, height, dark_mode)
        layout['xaxis']['title'] = '시도 번호'
        layout['yaxis']['title'] = '점수'
        layout['legend'] = dict(
            font=dict(size=ChartBuilder.FONT_LEGEND),
            bgcolor=legend_bg,
            bordercolor=neutral_color,
            borderwidth=1
        )
        fig.update_layout(**layout)

        return fig

    @staticmethod
    def performance_heatmap(
        df: pd.DataFrame,
        x_col: str,
        y_col: str,
        z_col: str,
        title: str = "성과 히트맵",
        height: int = 400,
        dark_mode: bool = False
    ) -> go.Figure:
        """
        Create heatmap for performance analysis (e.g., day of week vs hour).

        Args:
            df: DataFrame with performance data
            x_col: Column name for x-axis
            y_col: Column name for y-axis
            z_col: Column name for values (performance metric)
            title: Chart title
            height: Chart height in pixels
            dark_mode: Whether to use dark mode colors

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
            template = 'plotly_dark' if dark_mode else 'plotly_white'
            fig.update_layout(height=height, template=template)
            return fig

        # Pivot data for heatmap
        try:
            pivot = df.pivot_table(index=y_col, columns=x_col, values=z_col, aggfunc='mean')

            fig = go.Figure(data=go.Heatmap(
                z=pivot.values,
                x=pivot.columns,
                y=pivot.index,
                colorscale='RdYlGn',  # Red-Yellow-Green for performance
                hoverongaps=False,
                hovertemplate='%{y}, %{x}<br>값: %{z:.2f}<extra></extra>'
            ))

            template = 'plotly_dark' if dark_mode else 'plotly_white'
            font_color = '#f9fafb' if dark_mode else '#1f2937'

            fig.update_layout(
                title=dict(text=title, font=dict(size=ChartBuilder.FONT_TITLE, color=font_color)),
                template=template,
                height=height,
                xaxis_title=x_col,
                yaxis_title=y_col
            )

            return fig

        except Exception as e:
            # Return empty chart on error
            fig = go.Figure()
            fig.add_annotation(
                text=f"히트맵 생성 실패: {str(e)}",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False,
                font=dict(size=16, color="gray")
            )
            template = 'plotly_dark' if dark_mode else 'plotly_white'
            fig.update_layout(height=height, template=template)
            return fig

    @staticmethod
    def box_plot(
        df: pd.DataFrame,
        x_col: str,
        y_col: str,
        title: str = "분포 분석",
        height: int = 400,
        dark_mode: bool = False
    ) -> go.Figure:
        """
        Create box plot for distribution analysis.

        Args:
            df: DataFrame with data
            x_col: Column name for categories (x-axis)
            y_col: Column name for values (y-axis)
            title: Chart title
            height: Chart height in pixels
            dark_mode: Whether to use dark mode colors

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
            template = 'plotly_dark' if dark_mode else 'plotly_white'
            fig.update_layout(height=height, template=template)
            return fig

        # Use appropriate color based on dark mode
        marker_color = ChartBuilder.COLOR_PRIMARY_DARK if dark_mode else ChartBuilder.COLOR_PRIMARY

        fig = go.Figure()

        # Get unique categories
        categories = df[x_col].unique()

        for category in categories:
            category_data = df[df[x_col] == category][y_col]
            fig.add_trace(go.Box(
                y=category_data,
                name=str(category),
                marker_color=marker_color,
                boxmean='sd'  # Show mean and standard deviation
            ))

        # Apply base layout and customize
        layout = ChartBuilder.get_base_layout(title, height, dark_mode)
        layout['xaxis']['title'] = x_col
        layout['yaxis']['title'] = y_col
        fig.update_layout(**layout)

        return fig

    @staticmethod
    def metric_comparison_bar(
        df: pd.DataFrame,
        category_col: str,
        metrics: List[str],
        title: str = "지표 비교",
        height: int = 400,
        dark_mode: bool = False
    ) -> go.Figure:
        """
        Create grouped bar chart for multiple metrics comparison.

        Args:
            df: DataFrame with metrics data
            category_col: Column name for categories
            metrics: List of metric column names to compare
            title: Chart title
            height: Chart height in pixels
            dark_mode: Whether to use dark mode colors

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
            template = 'plotly_dark' if dark_mode else 'plotly_white'
            fig.update_layout(height=height, template=template)
            return fig

        # Use chart palette colors
        colors = Colors.CHART_PALETTE

        fig = go.Figure()

        for i, metric in enumerate(metrics):
            if metric in df.columns:
                fig.add_trace(go.Bar(
                    x=df[category_col],
                    y=df[metric],
                    name=metric,
                    marker_color=colors[i % len(colors)],
                    hovertemplate=f'<b>%{{x}}</b><br>{metric}: %{{y:.2f}}<extra></extra>'
                ))

        # Apply base layout and customize
        layout = ChartBuilder.get_base_layout(title, height, dark_mode)
        layout['barmode'] = 'group'
        layout['xaxis']['title'] = category_col
        layout['yaxis']['title'] = '값'
        layout['legend'] = dict(
            orientation='h',
            yanchor='bottom',
            y=1.02,
            xanchor='right',
            x=1
        )
        fig.update_layout(**layout)

        return fig

    @staticmethod
    def correlation_heatmap(
        corr_matrix: pd.DataFrame,
        title: str = "상관관계 분석",
        height: int = 500,
        dark_mode: bool = False
    ) -> go.Figure:
        """
        Create correlation heatmap.

        Args:
            corr_matrix: Correlation matrix (DataFrame)
            title: Chart title
            height: Chart height in pixels
            dark_mode: Whether to use dark mode colors

        Returns:
            Plotly Figure object
        """
        if corr_matrix.empty:
            fig = go.Figure()
            fig.add_annotation(
                text="상관관계 데이터 없음",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False,
                font=dict(size=20, color="gray")
            )
            template = 'plotly_dark' if dark_mode else 'plotly_white'
            fig.update_layout(height=height, template=template)
            return fig

        fig = go.Figure(data=go.Heatmap(
            z=corr_matrix.values,
            x=corr_matrix.columns,
            y=corr_matrix.index,
            colorscale='RdBu',
            zmid=0,
            text=corr_matrix.values,
            texttemplate='%{text:.2f}',
            textfont={"size": 10},
            hovertemplate='%{y} vs %{x}<br>상관계수: %{z:.3f}<extra></extra>'
        ))

        template = 'plotly_dark' if dark_mode else 'plotly_white'
        font_color = '#f9fafb' if dark_mode else '#1f2937'

        fig.update_layout(
            title=dict(text=title, font=dict(size=ChartBuilder.FONT_TITLE, color=font_color)),
            template=template,
            height=height
        )

        return fig
