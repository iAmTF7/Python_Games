"""Level progression configuration."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class LevelConfig:
    """Tunable values for level progression; defaults preserve the original behavior."""

    exp_growth: float = 1.3
    stat_points_per_level: int = 1
    restore_hp_on_level: bool = True
    restore_armor_on_level: bool = True
    max_level_ups_per_add: int = 1
