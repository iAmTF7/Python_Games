"""Item entity model."""

from __future__ import annotations

from typing import Any

from core.base import BaseEntity

from .config import RandomLike
from .effects import ITEM_EFFECTS
from .factory import ItemFactory


class Item(BaseEntity):
    """An item that owns and applies its own effect.

    ``Item(player)`` remains supported for old code. New code should prefer
    ``Item.random_for_player(player)`` or ``Item.from_type("heal")``.
    """

    def __init__(self, player_or_type: Any, rng: RandomLike | None = None) -> None:
        if isinstance(player_or_type, str):
            item_type = player_or_type
        else:
            item_type = ItemFactory(rng).choose_type_for(player_or_type)

        if item_type not in ITEM_EFFECTS:
            raise ValueError(f"Unknown item type: {item_type!r}")

        self.type = item_type
        self.effect = ITEM_EFFECTS[item_type]
        self.picked_up = False

    @classmethod
    def from_type(cls, item_type: str) -> "Item":
        return cls(item_type)

    @classmethod
    def random_for_player(cls, player: Any, rng: RandomLike | None = None) -> "Item":
        return cls(player, rng=rng)

    def apply_to(self, player: Any) -> None:
        self.effect.apply(player)
        self.picked_up = True

    def pickup(self, player: Any) -> None:
        """Alias for readability in gameplay code."""
        self.apply_to(player)

    def is_alive(self) -> bool:
        """Picked-up items should be removed from the world."""
        return not self.picked_up
