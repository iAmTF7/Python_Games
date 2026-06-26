"""Item factory and item-selection rules."""

from __future__ import annotations

import random
from typing import Any

from .config import NORMAL_ITEM_TYPES, SPECIAL_ITEM_TYPES, RandomLike


class ItemFactory:
    """Creates item types using the original probability rules."""

    def __init__(self, rng: RandomLike | None = None) -> None:
        self.rng: RandomLike = rng or random

    def choose_type_for(self, player: Any) -> str:
        """Choose an item type using the exact old item-selection logic."""
        owned = player.special_items.copy()

        if self.rng.random() < 0.02:
            possible = [item_type for item_type in SPECIAL_ITEM_TYPES if item_type not in owned]

            if possible:
                return self.rng.choice(possible)

            return self.rng.choice(NORMAL_ITEM_TYPES)

        roll = self.rng.random()

        if roll < 0.34:
            return "heal"

        if roll < 0.67:
            return "armor"

        return "energy"

    def create_for(self, player: Any) -> "Item":
        from .base import Item

        return Item.from_type(self.choose_type_for(player))
