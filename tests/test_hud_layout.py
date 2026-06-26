"""Responsive HUD layout tests.

These checks protect smaller window presets from clipping the lower controls
section off the bottom of the display surface.
"""

from game.hud import GameHUD


def _layout_bottom(layout):
    return (
        layout.panel_padding
        + layout.status_card_height
        + layout.card_gap
        + layout.run_card_height
        + layout.card_gap
        + layout.controls_card_height
    )


def test_hud_layout_fits_672px_compact_window():
    hud = GameHUD(map_width=1008, width=300, font=None, small_font=None)

    layout = hud._make_layout(672)

    assert _layout_bottom(layout) <= 672 - layout.panel_padding
    assert layout.run_card_height >= hud.MIN_RUN_CARD_HEIGHT
    assert layout.control_row_height >= hud.MIN_CONTROL_ROW_HEIGHT
    assert layout.show_messages


def test_hud_uses_original_card_sizes_when_space_allows():
    hud = GameHUD(map_width=1152, width=340, font=None, small_font=None)

    layout = hud._make_layout(900)

    assert layout.status_card_height == hud.STATUS_CARD_HEIGHT
    assert layout.run_card_height == hud.RUN_CARD_HEIGHT
    assert layout.controls_card_height == hud.CONTROLS_CARD_HEIGHT
    assert layout.control_row_height == hud.CONTROL_ROW_HEIGHT
    assert layout.show_messages


def test_hud_layout_keeps_bottom_padding_at_744px_window():
    hud = GameHUD(map_width=1116, width=300, font=None, small_font=None)

    layout = hud._make_layout(744)

    assert _layout_bottom(layout) <= 744 - layout.panel_padding
    assert layout.controls_card_height >= hud.MIN_CONTROLS_CARD_HEIGHT
    assert layout.control_row_height >= hud.MIN_CONTROL_ROW_HEIGHT
    assert layout.show_messages
