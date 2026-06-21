"""Object-oriented item drop and pickup system.

The old public functions are still present:
- ``create_drop(player)``
- ``pickup_item(player, item)``

Internally, they now delegate to objects so the module can plug into the shared
baseline architecture cleanly.
"""

from __future__ import annotations

import random
from typing import Any, Protocol

try:
    from game.base_system import BaseSystem
except ModuleNotFoundError:  # Allows this module to be tested standalone.
    class BaseSystem:  # type: ignore[no-redef]
        pass

from .item import Item, RandomLike


class DropTable:
    """Rolls item drops using the original 60% drop chance."""

    def __init__(self, drop_chance: float = 0.6, rng: RandomLike | None = None) -> None:
        self.drop_chance = drop_chance
        self.rng: RandomLike = rng or random

    def roll(self, player: Any) -> Item | None:
        if self.rng.random() < self.drop_chance:
            return Item.random_for_player(player, rng=self.rng)

        return None


class ItemPickupSystem(BaseSystem):
    """Applies item effects and can be registered as a game system later."""

    def pickup(self, player: Any, item: Item | None) -> None:
        if item is None:
            return

        item.apply_to(player)

    def handle_event(self, event: Any, state: Any) -> None:
        pass

    def update(self, state: Any) -> None:
        """Optional GameState integration.

        If items have ``rect`` attributes and the player has a ``rect``, this
        will pick up colliding items. If not, it safely does nothing, so the old
        manual ``pickup_item(player, item)`` flow still works.
        """
        player = getattr(state, "player", None)
        items = getattr(state, "items", None)

        if player is None or items is None or not hasattr(player, "rect"):
            return

        for item in list(items):
            item_rect = getattr(item, "rect", None)
            if item_rect is None:
                continue

            if player.rect.colliderect(item_rect):
                self.pickup(player, item)
                items.remove(item)

    def draw(self, surface: Any, state: Any) -> None:
        pass


DEFAULT_DROP_TABLE = DropTable()
DEFAULT_PICKUP_SYSTEM = ItemPickupSystem()


def create_drop(player: Any) -> Item | None:
    """Backward-compatible wrapper for old code."""
    return DEFAULT_DROP_TABLE.roll(player)


def pickup_item(player: Any, item: Item | None) -> None:
    """Backward-compatible wrapper for old code."""
    DEFAULT_PICKUP_SYSTEM.pickup(player, item)
