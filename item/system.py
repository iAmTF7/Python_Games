"""Item drop and pickup systems."""

from __future__ import annotations

import random
from typing import Any

from core.base import BaseSystem

from .base import Item
from .config import RandomLike


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

    def update(self, state: Any) -> None:
        """Pick up colliding items when runtime rect data is available."""
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
