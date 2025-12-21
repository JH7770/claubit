"""
Design Tokens - Design System

Centralized design tokens that combine colors, typography, and spacing.
Import this module to access all design constants.
"""

from .colors import Colors
from .typography import Typography
from .spacing import Spacing


class DesignTokens:
    """
    Unified design tokens for the dashboard.

    Usage:
        from dashboard.design_system.tokens import DesignTokens as DT

        # Access colors
        primary_color = DT.COLOR_PRIMARY

        # Access typography
        h1_size = DT.FONT_SIZE_H1

        # Access spacing
        padding = DT.SPACE_4
    """

    # ============================================================================
    # COLORS - Re-export from Colors class
    # ============================================================================

    # Primary colors
    COLOR_PRIMARY = Colors.BLUE_500
    COLOR_PRIMARY_LIGHT = Colors.BLUE_400
    COLOR_PRIMARY_DARK = Colors.BLUE_600

    # Semantic colors
    COLOR_SUCCESS = Colors.SUCCESS_500
    COLOR_WARNING = Colors.WARNING_500
    COLOR_ERROR = Colors.ERROR_500
    COLOR_INFO = Colors.INFO_500

    # Trading colors
    COLOR_PROFIT_LIGHT = Colors.PROFIT_LIGHT
    COLOR_PROFIT_DARK = Colors.PROFIT_DARK
    COLOR_LOSS_LIGHT = Colors.LOSS_LIGHT
    COLOR_LOSS_DARK = Colors.LOSS_DARK

    # Backgrounds
    BG_PRIMARY_LIGHT = Colors.BG_PRIMARY_LIGHT
    BG_PRIMARY_DARK = Colors.BG_PRIMARY_DARK
    BG_SECONDARY_LIGHT = Colors.BG_SECONDARY_LIGHT
    BG_SECONDARY_DARK = Colors.BG_SECONDARY_DARK

    # Text
    TEXT_PRIMARY_LIGHT = Colors.TEXT_PRIMARY_LIGHT
    TEXT_PRIMARY_DARK = Colors.TEXT_PRIMARY_DARK
    TEXT_SECONDARY_LIGHT = Colors.TEXT_SECONDARY_LIGHT
    TEXT_SECONDARY_DARK = Colors.TEXT_SECONDARY_DARK

    # Borders
    BORDER_LIGHT = Colors.BORDER_LIGHT
    BORDER_DARK = Colors.BORDER_DARK

    # ============================================================================
    # TYPOGRAPHY - Re-export from Typography class
    # ============================================================================

    # Font families
    FONT_FAMILY = Typography.FONT_FAMILY_PRIMARY
    FONT_MONO = Typography.FONT_FAMILY_MONO

    # Font sizes
    FONT_SIZE_H1 = Typography.FONT_SIZE_H1
    FONT_SIZE_H2 = Typography.FONT_SIZE_H2
    FONT_SIZE_H3 = Typography.FONT_SIZE_H3
    FONT_SIZE_H4 = Typography.FONT_SIZE_H4
    FONT_SIZE_BODY = Typography.FONT_SIZE_BODY
    FONT_SIZE_CAPTION = Typography.FONT_SIZE_CAPTION

    # Font weights
    FONT_WEIGHT_REGULAR = Typography.FONT_WEIGHT_REGULAR
    FONT_WEIGHT_MEDIUM = Typography.FONT_WEIGHT_MEDIUM
    FONT_WEIGHT_SEMIBOLD = Typography.FONT_WEIGHT_SEMIBOLD
    FONT_WEIGHT_BOLD = Typography.FONT_WEIGHT_BOLD

    # Chart text sizes
    FONT_SIZE_CHART_TITLE = Typography.FONT_SIZE_CHART_TITLE
    FONT_SIZE_CHART_AXIS = Typography.FONT_SIZE_CHART_AXIS
    FONT_SIZE_CHART_TICK = Typography.FONT_SIZE_CHART_TICK

    # ============================================================================
    # SPACING - Re-export from Spacing class
    # ============================================================================

    # Spacing scale
    SPACE_0 = Spacing.SPACE_0
    SPACE_1 = Spacing.SPACE_1
    SPACE_2 = Spacing.SPACE_2
    SPACE_3 = Spacing.SPACE_3
    SPACE_4 = Spacing.SPACE_4
    SPACE_6 = Spacing.SPACE_6
    SPACE_8 = Spacing.SPACE_8
    SPACE_12 = Spacing.SPACE_12
    SPACE_16 = Spacing.SPACE_16

    # Border radius
    RADIUS_SMALL = Spacing.RADIUS_SMALL
    RADIUS_MEDIUM = Spacing.RADIUS_MEDIUM
    RADIUS_LARGE = Spacing.RADIUS_LARGE
    RADIUS_CARD = Spacing.RADIUS_CARD
    RADIUS_BUTTON = Spacing.RADIUS_BUTTON

    # Shadows
    SHADOW_SMALL = Spacing.SHADOW_SMALL
    SHADOW_MEDIUM = Spacing.SHADOW_MEDIUM
    SHADOW_LARGE = Spacing.SHADOW_LARGE
    SHADOW_CARD = Spacing.SHADOW_CARD

    # Z-index
    Z_INDEX_MODAL = Spacing.Z_INDEX_MODAL
    Z_INDEX_TOOLTIP = Spacing.Z_INDEX_TOOLTIP

    # ============================================================================
    # THEME HELPERS
    # ============================================================================

    @staticmethod
    def get_theme_colors(dark_mode: bool = False) -> dict:
        """
        Get all theme colors based on dark mode.

        Args:
            dark_mode: Whether to return dark mode colors

        Returns:
            Dictionary with theme colors
        """
        return {
            'background': Colors.get_bg_primary(dark_mode),
            'background_secondary': Colors.get_bg_secondary(dark_mode),
            'text': Colors.get_text_primary(dark_mode),
            'border': Colors.get_border(dark_mode),
            'profit': Colors.get_profit_color(dark_mode),
            'loss': Colors.get_loss_color(dark_mode),
            'primary': Colors.BLUE_500,
            'success': Colors.SUCCESS_500,
            'warning': Colors.WARNING_500,
            'error': Colors.ERROR_500,
        }

    @staticmethod
    def get_metric_card_style(dark_mode: bool = False) -> dict:
        """
        Get metric card styling.

        Args:
            dark_mode: Whether to return dark mode styles

        Returns:
            Dictionary with CSS properties
        """
        return {
            'background-color': Colors.get_bg_secondary(dark_mode),
            'border': f'1px solid {Colors.get_border(dark_mode)}',
            'border-radius': f'{Spacing.RADIUS_CARD}px',
            'padding': Spacing.PADDING_CARD,
            'box-shadow': Spacing.SHADOW_CARD,
        }

    @staticmethod
    def get_button_style(variant: str = 'primary', dark_mode: bool = False) -> dict:
        """
        Get button styling.

        Args:
            variant: Button variant ('primary', 'secondary', 'danger')
            dark_mode: Whether to return dark mode styles

        Returns:
            Dictionary with CSS properties
        """
        if variant == 'primary':
            bg_color = Colors.BLUE_500
            hover_color = Colors.BLUE_600
        elif variant == 'secondary':
            bg_color = Colors.GRAY_600 if dark_mode else Colors.GRAY_200
            hover_color = Colors.GRAY_700 if dark_mode else Colors.GRAY_300
        elif variant == 'danger':
            bg_color = Colors.ERROR_500
            hover_color = Colors.ERROR_600
        else:
            bg_color = Colors.BLUE_500
            hover_color = Colors.BLUE_600

        return {
            'background-color': bg_color,
            'color': Colors.TEXT_PRIMARY_DARK if variant == 'primary' else Colors.get_text_primary(dark_mode),
            'border-radius': f'{Spacing.RADIUS_BUTTON}px',
            'padding': Spacing.PADDING_BUTTON,
            'font-size': f'{Typography.FONT_SIZE_BODY_SMALL}px',
            'font-weight': Typography.FONT_WEIGHT_SEMIBOLD,
            'box-shadow': Spacing.SHADOW_BUTTON,
            'hover-background': hover_color,
        }


# Convenience exports
__all__ = ['DesignTokens', 'Colors', 'Typography', 'Spacing']
