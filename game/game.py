"""The one real game controller.

Subsystem modules should not create their own Pygame windows or infinite loops.
They should plug into this Game class through BaseSystem-compatible objects.
"""

from __future__ import annotations

import pygame

from game.settings import BACKGROUND_COLOR, FPS, SCREEN_HEIGHT, SCREEN_WIDTH
from game.state import GameState


class Game:
    def __init__(self) -> None:
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Pygame Baseline System")
        self.clock = pygame.time.Clock()
        self.state = GameState(debug=True)
        self.systems = []

    def add_system(self, system) -> None:
        """Register a system that has handle_event/update/draw methods."""
        self.systems.append(system)

    def handle_events(self) -> None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.state.running = False

            for system in self.systems:
                system.handle_event(event, self.state)

    def update(self) -> None:
        if self.state.paused:
            return

        for system in self.systems:
            system.update(self.state)

    def draw(self) -> None:
        self.screen.fill(BACKGROUND_COLOR)

        for system in self.systems:
            system.draw(self.screen, self.state)

        pygame.display.flip()

    def run(self) -> None:
        while self.state.running:
            self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(FPS)

        pygame.quit()
