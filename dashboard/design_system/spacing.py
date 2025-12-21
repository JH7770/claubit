"""
Spacing System - Design System

Defines consistent spacing values for margins, paddings, and gaps.
Uses an 8px base unit for a harmonious spacing scale.
"""


class Spacing:
    """Spacing definitions for the dashboard."""

    # ============================================================================
    # BASE UNIT
    # ============================================================================

    BASE_UNIT = 8  # 8px base

    # ============================================================================
    # SPACING SCALE (in pixels)
    # ============================================================================

    # Extra small
    SPACE_0 = 0
    SPACE_1 = BASE_UNIT * 0.5   # 4px
    SPACE_2 = BASE_UNIT * 1     # 8px
    SPACE_3 = BASE_UNIT * 1.5   # 12px
    SPACE_4 = BASE_UNIT * 2     # 16px

    # Small
    SPACE_5 = BASE_UNIT * 2.5   # 20px
    SPACE_6 = BASE_UNIT * 3     # 24px
    SPACE_7 = BASE_UNIT * 3.5   # 28px
    SPACE_8 = BASE_UNIT * 4     # 32px

    # Medium
    SPACE_10 = BASE_UNIT * 5    # 40px
    SPACE_12 = BASE_UNIT * 6    # 48px
    SPACE_14 = BASE_UNIT * 7    # 56px
    SPACE_16 = BASE_UNIT * 8    # 64px

    # Large
    SPACE_20 = BASE_UNIT * 10   # 80px
    SPACE_24 = BASE_UNIT * 12   # 96px
    SPACE_32 = BASE_UNIT * 16   # 128px

    # ============================================================================
    # SEMANTIC SPACING (component-specific)
    # ============================================================================

    # Padding
    PADDING_BUTTON_SMALL = f'{SPACE_2}px {SPACE_4}px'
    PADDING_BUTTON = f'{SPACE_3}px {SPACE_6}px'
    PADDING_BUTTON_LARGE = f'{SPACE_4}px {SPACE_8}px'

    PADDING_CARD_SMALL = f'{SPACE_4}px'
    PADDING_CARD = f'{SPACE_6}px'
    PADDING_CARD_LARGE = f'{SPACE_8}px'

    PADDING_CONTAINER = f'{SPACE_6}px'
    PADDING_SECTION = f'{SPACE_8}px'

    # Margin
    MARGIN_SECTION = f'{SPACE_8}px 0'
    MARGIN_BLOCK_SMALL = f'{SPACE_2}px 0'
    MARGIN_BLOCK = f'{SPACE_4}px 0'
    MARGIN_BLOCK_LARGE = f'{SPACE_6}px 0'

    # Gap (for flexbox/grid)
    GAP_SMALL = f'{SPACE_2}px'
    GAP_MEDIUM = f'{SPACE_4}px'
    GAP_LARGE = f'{SPACE_6}px'

    # ============================================================================
    # BORDER RADIUS
    # ============================================================================

    RADIUS_NONE = 0
    RADIUS_SMALL = 4
    RADIUS_MEDIUM = 8
    RADIUS_LARGE = 12
    RADIUS_XLARGE = 16
    RADIUS_FULL = 9999  # For pills/circles

    # ============================================================================
    # COMPONENT-SPECIFIC RADIUS
    # ============================================================================

    RADIUS_BUTTON = RADIUS_MEDIUM
    RADIUS_CARD = RADIUS_LARGE
    RADIUS_INPUT = RADIUS_MEDIUM
    RADIUS_BADGE = RADIUS_FULL
    RADIUS_MODAL = RADIUS_LARGE

    # ============================================================================
    # SHADOWS
    # ============================================================================

    SHADOW_NONE = 'none'
    SHADOW_SMALL = '0 1px 2px 0 rgba(0, 0, 0, 0.05)'
    SHADOW_MEDIUM = '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)'
    SHADOW_LARGE = '0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)'
    SHADOW_XLARGE = '0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)'

    # Component-specific shadows
    SHADOW_CARD = SHADOW_MEDIUM
    SHADOW_BUTTON = SHADOW_SMALL
    SHADOW_MODAL = SHADOW_XLARGE

    # ============================================================================
    # Z-INDEX LAYERS
    # ============================================================================

    Z_INDEX_BASE = 0
    Z_INDEX_DROPDOWN = 1000
    Z_INDEX_STICKY = 1100
    Z_INDEX_MODAL_BACKDROP = 1200
    Z_INDEX_MODAL = 1300
    Z_INDEX_POPOVER = 1400
    Z_INDEX_TOOLTIP = 1500

    # ============================================================================
    # HELPER METHODS
    # ============================================================================

    @classmethod
    def get_space(cls, multiplier: float) -> int:
        """Get space value using base unit multiplier."""
        return int(cls.BASE_UNIT * multiplier)

    @classmethod
    def get_padding(cls, top: int = 0, right: int = 0, bottom: int = 0, left: int = 0) -> str:
        """Get padding value in CSS format."""
        return f'{top}px {right}px {bottom}px {left}px'

    @classmethod
    def get_margin(cls, top: int = 0, right: int = 0, bottom: int = 0, left: int = 0) -> str:
        """Get margin value in CSS format."""
        return f'{top}px {right}px {bottom}px {left}px'
