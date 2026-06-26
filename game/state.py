"""Shared world state.

All major systems should receive this object instead of creating their own
fake player, monster list, projectile list, or debug state.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class GameState:
    player: Any = None
    tile_map: Any = None

    monsters: list[Any] = field(default_factory=list)
    projectiles: list[Any] = field(default_factory=list)
    items: list[Any] = field(default_factory=list)

    level: int = 1
    room_reached: int = 1
    score: int = 0
    running: bool = True
    paused: bool = False
    debug: bool = False

    def reset_runtime_lists(self) -> None:
        """Clear temporary world objects without replacing the state object."""
        self.monsters.clear()
        self.projectiles.clear()
        self.items.clear()
