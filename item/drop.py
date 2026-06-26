"""Compatibility module for item drops and pickup."""

from .legacy import DEFAULT_DROP_TABLE, DEFAULT_PICKUP_SYSTEM, create_drop, pickup_item
from .system import DropTable, ItemPickupSystem

__all__ = [
    "DEFAULT_DROP_TABLE",
    "DEFAULT_PICKUP_SYSTEM",
    "DropTable",
    "ItemPickupSystem",
    "create_drop",
    "pickup_item",
]
