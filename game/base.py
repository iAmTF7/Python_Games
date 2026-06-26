"""Game package base contracts."""

from core.base import BaseEntity, BaseSystem
from core.protocols import Damageable, Drawable, EntityLike, SystemLike, Updatable

__all__ = [
    "BaseEntity",
    "BaseSystem",
    "Damageable",
    "Drawable",
    "EntityLike",
    "SystemLike",
    "Updatable",
]
