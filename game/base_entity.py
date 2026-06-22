"""Common interface for long-lived game objects.

Player, monsters, projectiles, and items can inherit from this directly,
or simply implement the same methods.
"""

from __future__ import annotations

from typing import Any


class BaseEntity:
    def update(self, state: Any) -> None:
        """Advance this entity by one frame."""
        pass

    def draw(self, surface: Any) -> None:
        """Draw this entity to a Pygame surface."""
        pass

    def take_damage(self, amount: int | float) -> None:
        """Apply damage to this entity."""
        pass

    def is_alive(self) -> bool:
        """Return whether this entity should remain in the world."""
        return True
