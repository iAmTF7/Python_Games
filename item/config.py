"""Item constants and shared RNG protocol."""

from __future__ import annotations

from typing import Protocol

NORMAL_ITEM_TYPES = ("heal", "armor", "energy")
SPECIAL_ITEM_TYPES = ("regen_hp", "regen_armor", "regen_energy")
ALL_ITEM_TYPES = NORMAL_ITEM_TYPES + SPECIAL_ITEM_TYPES


class RandomLike(Protocol):
    def random(self) -> float:
        ...

    def choice(self, sequence):
        ...
