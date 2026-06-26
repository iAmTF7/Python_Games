"""Protocol-based contracts for the game architecture.

Protocols keep systems loosely coupled: any object with the right public methods
can participate without being forced into a deep inheritance tree.
"""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class Updatable(Protocol):
    def update(self, state: Any) -> None:
        ...


@runtime_checkable
class Drawable(Protocol):
    def draw(self, surface: Any, state: Any | None = None) -> None:
        ...


@runtime_checkable
class Damageable(Protocol):
    def take_damage(self, amount: int | float) -> None:
        ...

    def is_alive(self) -> bool:
        ...


@runtime_checkable
class EntityLike(Updatable, Drawable, Damageable, Protocol):
    pass


@runtime_checkable
class SystemLike(Protocol):
    def handle_event(self, event: Any, state: Any) -> None:
        ...

    def update(self, state: Any) -> None:
        ...

    def draw(self, surface: Any, state: Any) -> None:
        ...
