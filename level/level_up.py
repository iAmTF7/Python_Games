"""Object-oriented level progression module.

This keeps the original mechanics intact:
- EXP is added to ``player.exp``.
- A level-up happens when ``player.exp >= player.exp_need``.
- One level-up is processed per ``add_exp`` call, matching the old early-return behavior.
- Level-up grants 1 stat point.
- Next EXP requirement is multiplied by 1.3 and converted to ``int``.
- HP and armor are restored to their maximum values on level-up.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional


@dataclass(frozen=True)
class LevelConfig:
    """Tunable values for level progression.

    Defaults intentionally match the original module behavior.
    """

    exp_growth: float = 1.3
    stat_points_per_level: int = 1
    restore_hp_on_level: bool = True
    restore_armor_on_level: bool = True
    max_level_ups_per_add: int = 1


@dataclass
class LevelUpResult:
    """Detailed result of an EXP gain.

    ``LevelSystem.add_exp`` still returns ``bool`` for backward compatibility.
    The latest detailed result is stored as ``LevelSystem.last_result``.
    """

    leveled_up: bool = False
    levels_gained: int = 0
    exp_gained: int = 0


class LevelSystem:
    """Owns player EXP and level progression.

    Existing code can keep using:

        level_system = LevelSystem(player)
        did_level_up = level_system.add_exp(amount)
    """

    def __init__(self, player: Any, config: Optional[LevelConfig] = None):
        self.player = player
        self.config = config or LevelConfig()
        self.last_result = LevelUpResult()

    def bind_player(self, player: Any) -> None:
        """Attach this system to a different player object."""
        self.player = player

    def can_level_up(self) -> bool:
        """Return True when the player has enough EXP for a level-up."""
        return self.player.exp >= self.player.exp_need

    def add_exp(self, amount: int) -> bool:
        """Add EXP and process level progression.

        Returns True if at least one level-up occurred, otherwise False.
        The default config processes only one level-up per call, preserving the
        original early-return mechanic.
        """
        self.player.exp += amount
        self.last_result = LevelUpResult(exp_gained=amount)

        level_ups_processed = 0

        while self.can_level_up():
            self._level_up_once()
            level_ups_processed += 1
            self.last_result.leveled_up = True
            self.last_result.levels_gained = level_ups_processed

            if level_ups_processed >= self.config.max_level_ups_per_add:
                return True

        return self.last_result.leveled_up

    def add_experience(self, amount: int) -> bool:
        """Readable alias for ``add_exp``."""
        return self.add_exp(amount)

    def _level_up_once(self) -> None:
        """Apply exactly one level-up using the original stat changes."""
        self.player.exp -= self.player.exp_need
        self.player.level += 1
        self.player.stat_points += self.config.stat_points_per_level
        self.player.exp_need = int(self.player.exp_need * self.config.exp_growth)

        if self.config.restore_hp_on_level:
            self.player.hp = self.player.max_hp

        if self.config.restore_armor_on_level:
            self.player.armor = self.player.max_armor

    def update(self, state: Any = None) -> None:
        """Compatibility hook for the shared system architecture.

        Level progression is event-driven through ``add_exp``, so the update
        hook intentionally does nothing for now.
        """
        return None
