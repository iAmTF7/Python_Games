"""Factories used by tests and temporary teammate demos.

Do not let each module invent its own fake player/world foundation.
Put shared test objects here.
"""

from __future__ import annotations

from game.state import GameState


def make_test_state() -> GameState:
    state = GameState()
    state.level = 1
    state.debug = True
    return state
