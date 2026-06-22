"""Object-oriented item model.

The original mechanics are intentionally preserved:
- Drops still choose between heal / armor / energy most of the time.
- There is still a 2% roll for special regen items.
- Special regen items are only selected if the player does not already own them.
- Item effects still restore the exact same amounts and regen values.

Backward compatibility:
- ``Item(player)`` still creates a random item for that player, like before.
- ``item.type`` is still a plain string, like before.
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Any, Protocol

try:
    from game.base_entity import BaseEntity
except ModuleNotFoundError:  # Allows this module to be tested standalone.
    class BaseEntity:  # type: ignore[no-redef]
        pass


NORMAL_ITEM_TYPES = ("heal", "armor", "energy")
SPECIAL_ITEM_TYPES = ("regen_hp", "regen_armor", "regen_energy")
ALL_ITEM_TYPES = NORMAL_ITEM_TYPES + SPECIAL_ITEM_TYPES


class RandomLike(Protocol):
    def random(self) -> float:
        ...

    def choice(self, sequence):
        ...


@dataclass(frozen=True)
class ItemEffect:
    """Base class for an item effect."""

    item_type: str

    def apply(self, player: Any) -> None:
        raise NotImplementedError("Item effects must implement apply().")


@dataclass(frozen=True)
class RestoreStatEffect(ItemEffect):
    """Restores a stat without passing its maximum value."""

    stat_name: str
    max_stat_name: str
    amount: int | float

    def apply(self, player: Any) -> None:
        current_value = getattr(player, self.stat_name)
        max_value = getattr(player, self.max_stat_name)
        setattr(player, self.stat_name, min(max_value, current_value + self.amount))


@dataclass(frozen=True)
class UnlockRegenEffect(ItemEffect):
    """Unlocks a regen upgrade once per player."""

    regen_stat_name: str
    regen_value: int | float

    def apply(self, player: Any) -> None:
        if self.item_type in player.special_items:
            return

        setattr(player, self.regen_stat_name, self.regen_value)
        player.special_items.append(self.item_type)


ITEM_EFFECTS: dict[str, ItemEffect] = {
    "heal": RestoreStatEffect("heal", "hp", "max_hp", 20),
    "armor": RestoreStatEffect("armor", "armor", "max_armor", 20),
    "energy": RestoreStatEffect("energy", "energy", "max_energy", 30),
    "regen_hp": UnlockRegenEffect("regen_hp", "hp_regen", 0.2),
    "regen_armor": UnlockRegenEffect("regen_armor", "armor_regen", 0.2),
    "regen_energy": UnlockRegenEffect("regen_energy", "energy_regen", 0.25),
}


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
        return Item.from_type(self.choose_type_for(player))


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
