"""Backward-compatible item functions."""

from __future__ import annotations

from typing import Any

from .base import Item
from .system import DropTable, ItemPickupSystem

DEFAULT_DROP_TABLE = DropTable()
DEFAULT_PICKUP_SYSTEM = ItemPickupSystem()


def create_drop(player: Any) -> Item | None:
    """Backward-compatible wrapper for old code."""
    return DEFAULT_DROP_TABLE.roll(player)


def pickup_item(player: Any, item: Item | None) -> None:
    """Backward-compatible wrapper for old code."""
    DEFAULT_PICKUP_SYSTEM.pickup(player, item)
