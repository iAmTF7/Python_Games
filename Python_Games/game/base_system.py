"""Common interface for modules/systems.

Weapons, maps, UI, level-up logic, spawning, and dev panels can all be
wrapped as systems so the main Game loop can call them consistently.
"""

from __future__ import annotations

from typing import Any


class BaseSystem:
    def handle_event(self, event: Any, state: Any) -> None:
        """Handle a single Pygame event."""
        pass

    def update(self, state: Any) -> None:
        """Update this system by one frame."""
        pass

    def draw(self, surface: Any, state: Any) -> None:
        """Draw this system by one frame."""
        pass
