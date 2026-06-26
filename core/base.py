"""Concrete no-op base adapters used by legacy code and smoke tests.

The canonical contracts live in :mod:`core.protocols`.  These classes remain
instantiable for backwards compatibility with the original project while still
providing a consistent superclass for concrete objects that want one.
"""

from __future__ import annotations

from typing import Any


class BaseEntity:
    def update(self, state: Any) -> None:
        """Advance this entity by one frame."""
        return None

    def draw(self, surface: Any) -> None:
        """Draw this entity to a Pygame surface."""
        return None

    def take_damage(self, amount: int | float) -> None:
        """Apply damage to this entity."""
        return None

    def is_alive(self) -> bool:
        """Return whether this entity should remain in the world."""
        return True


class BaseSystem:
    def handle_event(self, event: Any, state: Any) -> None:
        """Handle a single Pygame event."""
        return None

    def update(self, state: Any) -> None:
        """Update this system by one frame."""
        return None

    def draw(self, surface: Any, state: Any) -> None:
        """Draw this system by one frame."""
        return None
