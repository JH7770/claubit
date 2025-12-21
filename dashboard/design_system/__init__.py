"""
Design System Package

Centralized design tokens for consistent UI/UX across the dashboard.

Usage:
    # Import design tokens
    from dashboard.design_system import DesignTokens, Colors, Typography, Spacing

    # Or use the shorthand
    from dashboard.design_system.tokens import DesignTokens as DT

    # Access design values
    primary_color = DT.COLOR_PRIMARY
    heading_size = DT.FONT_SIZE_H1
    card_padding = DT.SPACE_6
"""

from .colors import Colors
from .typography import Typography
from .spacing import Spacing
from .tokens import DesignTokens

__all__ = ['DesignTokens', 'Colors', 'Typography', 'Spacing']
