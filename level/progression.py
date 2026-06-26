"""Player EXP and level progression."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .config import LevelConfig


@dataclass
class LevelUpResult:
    """Detailed result of an EXP gain."""

    leveled_up: bool = False
    levels_gained: int = 0
    exp_gained: int = 0


class LevelSystem:
    """Owns player EXP and level progression."""

    def __init__(self, player: Any, config: LevelConfig | None = None):
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
        """Compatibility hook for the shared system architecture."""
        return None
