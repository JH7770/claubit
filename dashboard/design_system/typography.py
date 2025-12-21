"""
Typography System - Design System

Defines font sizes, weights, and line heights for consistent typography.
"""


class Typography:
    """Typography definitions for the dashboard."""

    # ============================================================================
    # FONT FAMILIES
    # ============================================================================

    FONT_FAMILY_PRIMARY = "Arial, Helvetica, sans-serif"
    FONT_FAMILY_MONO = "Consolas, Monaco, 'Courier New', monospace"

    # ============================================================================
    # FONT SIZES (in pixels)
    # ============================================================================

    # Display sizes (for hero sections)
    FONT_SIZE_DISPLAY_1 = 48  # Extra large
    FONT_SIZE_DISPLAY_2 = 40  # Very large

    # Heading sizes
    FONT_SIZE_H1 = 32
    FONT_SIZE_H2 = 28
    FONT_SIZE_H3 = 24
    FONT_SIZE_H4 = 20
    FONT_SIZE_H5 = 18
    FONT_SIZE_H6 = 16

    # Body text sizes
    FONT_SIZE_BODY_LARGE = 18
    FONT_SIZE_BODY = 16
    FONT_SIZE_BODY_SMALL = 14

    # UI text sizes
    FONT_SIZE_CAPTION = 12
    FONT_SIZE_SMALL = 11
    FONT_SIZE_TINY = 10

    # Chart text sizes
    FONT_SIZE_CHART_TITLE = 18
    FONT_SIZE_CHART_AXIS = 14
    FONT_SIZE_CHART_TICK = 12
    FONT_SIZE_CHART_LEGEND = 12

    # ============================================================================
    # FONT WEIGHTS
    # ============================================================================

    FONT_WEIGHT_LIGHT = 300
    FONT_WEIGHT_REGULAR = 400
    FONT_WEIGHT_MEDIUM = 500
    FONT_WEIGHT_SEMIBOLD = 600
    FONT_WEIGHT_BOLD = 700
    FONT_WEIGHT_EXTRABOLD = 800

    # ============================================================================
    # LINE HEIGHTS
    # ============================================================================

    LINE_HEIGHT_TIGHT = 1.2
    LINE_HEIGHT_NORMAL = 1.5
    LINE_HEIGHT_RELAXED = 1.75
    LINE_HEIGHT_LOOSE = 2.0

    # ============================================================================
    # LETTER SPACING
    # ============================================================================

    LETTER_SPACING_TIGHT = '-0.02em'
    LETTER_SPACING_NORMAL = '0em'
    LETTER_SPACING_WIDE = '0.02em'
    LETTER_SPACING_WIDER = '0.05em'

    # ============================================================================
    # TEXT STYLES (CSS-like presets)
    # ============================================================================

    @classmethod
    def get_display_1_style(cls) -> dict:
        """Get display 1 text style."""
        return {
            'font-size': f'{cls.FONT_SIZE_DISPLAY_1}px',
            'font-weight': cls.FONT_WEIGHT_BOLD,
            'line-height': cls.LINE_HEIGHT_TIGHT,
            'letter-spacing': cls.LETTER_SPACING_TIGHT
        }

    @classmethod
    def get_h1_style(cls) -> dict:
        """Get H1 heading style."""
        return {
            'font-size': f'{cls.FONT_SIZE_H1}px',
            'font-weight': cls.FONT_WEIGHT_BOLD,
            'line-height': cls.LINE_HEIGHT_TIGHT,
            'letter-spacing': cls.LETTER_SPACING_TIGHT
        }

    @classmethod
    def get_h2_style(cls) -> dict:
        """Get H2 heading style."""
        return {
            'font-size': f'{cls.FONT_SIZE_H2}px',
            'font-weight': cls.FONT_WEIGHT_SEMIBOLD,
            'line-height': cls.LINE_HEIGHT_TIGHT,
            'letter-spacing': cls.LETTER_SPACING_NORMAL
        }

    @classmethod
    def get_h3_style(cls) -> dict:
        """Get H3 heading style."""
        return {
            'font-size': f'{cls.FONT_SIZE_H3}px',
            'font-weight': cls.FONT_WEIGHT_SEMIBOLD,
            'line-height': cls.LINE_HEIGHT_NORMAL,
            'letter-spacing': cls.LETTER_SPACING_NORMAL
        }

    @classmethod
    def get_body_style(cls) -> dict:
        """Get body text style."""
        return {
            'font-size': f'{cls.FONT_SIZE_BODY}px',
            'font-weight': cls.FONT_WEIGHT_REGULAR,
            'line-height': cls.LINE_HEIGHT_NORMAL,
            'letter-spacing': cls.LETTER_SPACING_NORMAL
        }

    @classmethod
    def get_caption_style(cls) -> dict:
        """Get caption text style."""
        return {
            'font-size': f'{cls.FONT_SIZE_CAPTION}px',
            'font-weight': cls.FONT_WEIGHT_REGULAR,
            'line-height': cls.LINE_HEIGHT_NORMAL,
            'letter-spacing': cls.LETTER_SPACING_NORMAL
        }

    @classmethod
    def get_button_style(cls) -> dict:
        """Get button text style."""
        return {
            'font-size': f'{cls.FONT_SIZE_BODY_SMALL}px',
            'font-weight': cls.FONT_WEIGHT_SEMIBOLD,
            'line-height': cls.LINE_HEIGHT_NORMAL,
            'letter-spacing': cls.LETTER_SPACING_WIDE
        }

    @classmethod
    def get_metric_value_style(cls) -> dict:
        """Get metric value text style."""
        return {
            'font-size': f'{cls.FONT_SIZE_H3}px',
            'font-weight': cls.FONT_WEIGHT_BOLD,
            'line-height': cls.LINE_HEIGHT_TIGHT,
            'letter-spacing': cls.LETTER_SPACING_TIGHT
        }

    @classmethod
    def get_metric_label_style(cls) -> dict:
        """Get metric label text style."""
        return {
            'font-size': f'{cls.FONT_SIZE_CAPTION}px',
            'font-weight': cls.FONT_WEIGHT_MEDIUM,
            'line-height': cls.LINE_HEIGHT_NORMAL,
            'letter-spacing': cls.LETTER_SPACING_WIDER
        }
