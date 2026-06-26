"""Compatibility module for the refactored weapon package."""

from .constants import *
from .legacy import *
from .models import *
from .physics import *
from .rendering import *

__all__ = [name for name in globals() if not name.startswith("_")]
