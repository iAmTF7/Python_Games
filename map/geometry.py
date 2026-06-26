"""Map geometry helpers."""

from __future__ import annotations

def clamp(value, minimum, maximum):
    return max(minimum, min(value, maximum))
