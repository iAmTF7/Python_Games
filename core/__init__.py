"""Shared object-oriented contracts and tiny base adapters."""

from .base import BaseEntity, BaseSystem
from .protocols import Damageable, Drawable, EntityLike, SystemLike, Updatable

__all__ = [
    "BaseEntity",
    "BaseSystem",
    "Damageable",
    "Drawable",
    "EntityLike",
    "SystemLike",
    "Updatable",
]
