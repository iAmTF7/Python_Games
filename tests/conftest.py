"""Universal pytest foundation for the project."""

import os

import pygame
import pytest

from game.testing.factories import make_test_state


@pytest.fixture(scope="session", autouse=True)
def pygame_session():
    """Initialize pygame once using a headless video driver for tests."""
    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    pygame.init()
    yield
    pygame.quit()


@pytest.fixture
def state():
    """Shared clean GameState fixture for every test."""
    return make_test_state()
