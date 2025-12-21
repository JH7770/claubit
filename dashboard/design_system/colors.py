"""
Color Palette - Design System

Centralized color definitions using Tailwind CSS color palette.
All colors support both light and dark modes.
"""


class Colors:
    """Color palette for the dashboard."""

    # ============================================================================
    # PRIMARY COLORS
    # ============================================================================

    # Blue - Primary brand color
    BLUE_50 = '#eff6ff'
    BLUE_100 = '#dbeafe'
    BLUE_200 = '#bfdbfe'
    BLUE_300 = '#93c5fd'
    BLUE_400 = '#60a5fa'
    BLUE_500 = '#3b82f6'  # Primary
    BLUE_600 = '#2563eb'
    BLUE_700 = '#1d4ed8'
    BLUE_800 = '#1e40af'
    BLUE_900 = '#1e3a8a'

    # ============================================================================
    # SEMANTIC COLORS - Light Mode
    # ============================================================================

    # Success (Green)
    SUCCESS_50 = '#ecfdf5'
    SUCCESS_100 = '#d1fae5'
    SUCCESS_200 = '#a7f3d0'
    SUCCESS_300 = '#6ee7b7'
    SUCCESS_400 = '#34d399'
    SUCCESS_500 = '#10b981'  # Main success
    SUCCESS_600 = '#059669'
    SUCCESS_700 = '#047857'
    SUCCESS_800 = '#065f46'
    SUCCESS_900 = '#064e3b'

    # Warning (Amber)
    WARNING_50 = '#fffbeb'
    WARNING_100 = '#fef3c7'
    WARNING_200 = '#fde68a'
    WARNING_300 = '#fcd34d'
    WARNING_400 = '#fbbf24'
    WARNING_500 = '#f59e0b'  # Main warning
    WARNING_600 = '#d97706'
    WARNING_700 = '#b45309'
    WARNING_800 = '#92400e'
    WARNING_900 = '#78350f'

    # Error (Red)
    ERROR_50 = '#fef2f2'
    ERROR_100 = '#fee2e2'
    ERROR_200 = '#fecaca'
    ERROR_300 = '#fca5a5'
    ERROR_400 = '#f87171'
    ERROR_500 = '#ef4444'  # Main error
    ERROR_600 = '#dc2626'
    ERROR_700 = '#b91c1c'
    ERROR_800 = '#991b1b'
    ERROR_900 = '#7f1d1d'

    # Info (Blue - same as primary)
    INFO_50 = BLUE_50
    INFO_100 = BLUE_100
    INFO_200 = BLUE_200
    INFO_300 = BLUE_300
    INFO_400 = BLUE_400
    INFO_500 = BLUE_500  # Main info
    INFO_600 = BLUE_600
    INFO_700 = BLUE_700
    INFO_800 = BLUE_800
    INFO_900 = BLUE_900

    # ============================================================================
    # NEUTRAL COLORS (Gray)
    # ============================================================================

    GRAY_50 = '#f9fafb'
    GRAY_100 = '#f3f4f6'
    GRAY_200 = '#e5e7eb'
    GRAY_300 = '#d1d5db'
    GRAY_400 = '#9ca3af'
    GRAY_500 = '#6b7280'
    GRAY_600 = '#4b5563'
    GRAY_700 = '#374151'
    GRAY_800 = '#1f2937'
    GRAY_900 = '#111827'

    # ============================================================================
    # TRADING-SPECIFIC COLORS
    # ============================================================================

    # Profit/Loss
    PROFIT_LIGHT = SUCCESS_500  # Green for light mode
    PROFIT_DARK = SUCCESS_400   # Lighter green for dark mode

    LOSS_LIGHT = ERROR_500      # Red for light mode
    LOSS_DARK = ERROR_400       # Lighter red for dark mode

    # Long/Short positions
    LONG_COLOR = BLUE_500
    SHORT_COLOR = WARNING_500

    # ============================================================================
    # BACKGROUND COLORS
    # ============================================================================

    # Light mode backgrounds
    BG_PRIMARY_LIGHT = '#ffffff'
    BG_SECONDARY_LIGHT = GRAY_50
    BG_TERTIARY_LIGHT = GRAY_100

    # Dark mode backgrounds
    BG_PRIMARY_DARK = GRAY_900
    BG_SECONDARY_DARK = GRAY_800
    BG_TERTIARY_DARK = GRAY_700

    # ============================================================================
    # TEXT COLORS
    # ============================================================================

    # Light mode text
    TEXT_PRIMARY_LIGHT = GRAY_900
    TEXT_SECONDARY_LIGHT = GRAY_600
    TEXT_TERTIARY_LIGHT = GRAY_500

    # Dark mode text
    TEXT_PRIMARY_DARK = GRAY_50
    TEXT_SECONDARY_DARK = GRAY_400
    TEXT_TERTIARY_DARK = GRAY_500

    # ============================================================================
    # BORDER COLORS
    # ============================================================================

    BORDER_LIGHT = GRAY_200
    BORDER_DARK = GRAY_700

    # ============================================================================
    # SPECIAL COLORS
    # ============================================================================

    # Medal colors for rankings
    GOLD = '#FFD700'
    SILVER = '#C0C0C0'
    BRONZE = '#CD7F32'

    # Chart colors (for multi-series charts)
    CHART_PALETTE = [
        BLUE_500,
        SUCCESS_500,
        WARNING_500,
        ERROR_500,
        BLUE_300,
        SUCCESS_300,
        WARNING_300,
        ERROR_300
    ]

    @classmethod
    def get_profit_color(cls, dark_mode: bool = False) -> str:
        """Get profit color based on theme."""
        return cls.PROFIT_DARK if dark_mode else cls.PROFIT_LIGHT

    @classmethod
    def get_loss_color(cls, dark_mode: bool = False) -> str:
        """Get loss color based on theme."""
        return cls.LOSS_DARK if dark_mode else cls.LOSS_LIGHT

    @classmethod
    def get_bg_primary(cls, dark_mode: bool = False) -> str:
        """Get primary background color based on theme."""
        return cls.BG_PRIMARY_DARK if dark_mode else cls.BG_PRIMARY_LIGHT

    @classmethod
    def get_bg_secondary(cls, dark_mode: bool = False) -> str:
        """Get secondary background color based on theme."""
        return cls.BG_SECONDARY_DARK if dark_mode else cls.BG_SECONDARY_LIGHT

    @classmethod
    def get_text_primary(cls, dark_mode: bool = False) -> str:
        """Get primary text color based on theme."""
        return cls.TEXT_PRIMARY_DARK if dark_mode else cls.TEXT_PRIMARY_LIGHT

    @classmethod
    def get_border(cls, dark_mode: bool = False) -> str:
        """Get border color based on theme."""
        return cls.BORDER_DARK if dark_mode else cls.BORDER_LIGHT
