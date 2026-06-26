"""Compatibility module for item entities/effects."""

from .base import Item
from .config import ALL_ITEM_TYPES, NORMAL_ITEM_TYPES, SPECIAL_ITEM_TYPES, RandomLike
from .effects import ITEM_EFFECTS, ItemEffect, RestoreStatEffect, UnlockRegenEffect
from .factory import ItemFactory

__all__ = [
    "ALL_ITEM_TYPES",
    "ITEM_EFFECTS",
    "NORMAL_ITEM_TYPES",
    "SPECIAL_ITEM_TYPES",
    "Item",
    "ItemEffect",
    "ItemFactory",
    "RandomLike",
    "RestoreStatEffect",
    "UnlockRegenEffect",
]
