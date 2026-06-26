"""Backward-compatible stat upgrade functions."""

from __future__ import annotations

from typing import Any

from .upgrades import StatUpgradeSystem


def upgrade_hp(player: Any) -> None:
    StatUpgradeSystem(player).upgrade_hp()


def upgrade_damage(player: Any) -> None:
    StatUpgradeSystem(player).upgrade_damage()


def upgrade_speed(player: Any) -> None:
    StatUpgradeSystem(player).upgrade_speed()


def upgrade_armor(player: Any) -> None:
    StatUpgradeSystem(player).upgrade_armor()


def upgrade_energy(player: Any) -> None:
    StatUpgradeSystem(player).upgrade_energy()
