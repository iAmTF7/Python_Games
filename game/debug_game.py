"""Integrated debug runner for the refactored project.

Run with:
    python -m game.main

This intentionally wires every gameplay module together in one place so you can
smoke-test player, map, monster, weapon, item, and level mechanics without each
module needing its own fake test foundation.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pygame

from game.state import GameState
from game.hud import GameHUD
from game.high_scores import HighScoreTable
from item import DropTable, Item, ItemPickupSystem
from level import LevelSystem, StatUpgradeSystem
from map import MapSystem, TileMap
from monster import MonsterSpawner
from player import Player
from weapon import WeaponSystem


HUD_WIDTH = 340
FPS = 60
PLAYER_COLOR = (0, 200, 255)
ITEM_COLORS = {
    "heal": (80, 230, 100),
    "armor": (100, 170, 255),
    "energy": (255, 220, 80),
    "regen_hp": (0, 255, 120),
    "regen_armor": (90, 220, 255),
    "regen_energy": (255, 180, 60),
}


@dataclass
class DebugMessage:
    text: str
    timer: int = 180

    def tick(self) -> bool:
        self.timer -= 1
        return self.timer > 0


class IntegratedDebugGame:
    """One-window integration test for every module.

    This class is deliberately explicit instead of clever. It shows exactly how
    the modules are expected to talk to the shared ``GameState``.
    """

    def __init__(self) -> None:
        pygame.init()
        self.state = GameState(debug=True)

        self.tile_map = TileMap(level=0)
        map_width, map_height = self.tile_map.screen_size
        self.map_rect = pygame.Rect(0, 0, map_width, map_height)
        self.screen = pygame.display.set_mode((map_width + HUD_WIDTH, map_height))
        pygame.display.set_caption("Integrated Debug Runner")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 24)
        self.small_font = pygame.font.Font(None, 18)
        self.game_over_font = pygame.font.Font(None, 74)
        self.restart_font = pygame.font.Font(None, 30)
        self.hud = GameHUD(map_width, HUD_WIDTH, self.font, self.small_font)

        self.player = Player(width=32, height=32)
        self.tile_map.place_player_at_start(self.player)

        self.map_system = MapSystem(self.tile_map)
        self.weapon_system = WeaponSystem()
        self.item_pickup_system = ItemPickupSystem()
        self.drop_table = DropTable()
        self.level_system = LevelSystem(self.player)
        self.stat_system = StatUpgradeSystem(self.player)
        self.monster_spawner = MonsterSpawner.with_defaults(map_width, map_height)

        self.state.player = self.player
        self.state.tile_map = self.tile_map
        self.state.level = 1
        self.state.monsters = []
        self.state.projectiles = []  # monster projectiles
        self.state.items = []
        self.state.score = 0
        self.state.room_reached = self.tile_map.level + 1
        self.high_scores = HighScoreTable()
        self.run_recorded = False
        self.messages: list[DebugMessage] = []
        self.regen_timer = 0
        self.game_over = False

        self.spawn_wave()
        self.log("Debug HUD ready")

    # ------------------------------------------------------------------
    # Setup helpers
    # ------------------------------------------------------------------
    def log(self, text: str, timer: int = 180) -> None:
        self.messages.append(DebugMessage(text, timer))
        self.messages = self.messages[-6:]

    def spawn_wave(self) -> None:
        self.state.projectiles.clear()
        self.tile_map.close_exit()
        wave_level = max(1, self.tile_map.level + 1)
        self.state.monsters = self.monster_spawner.spawn_wave(
            wave_level,
            self.player.x,
            self.player.y,
            self.tile_map,
        )
        if not self.state.monsters:
            self.tile_map.open_exit()
            self.log("No monsters spawned; exit opened")
        else:
            self.log(
                f"Spawned {len(self.state.monsters)} monsters for room {wave_level}; exit locked"
            )

    def submit_current_run(self) -> None:
        if self.run_recorded:
            return
        room_reached = max(1, int(getattr(self.state, "room_reached", self.tile_map.level + 1)))
        self.high_scores.submit(room_reached)
        self.run_recorded = True

    def reset_debug_world(self) -> None:
        self.submit_current_run()
        self.game_over = False
        self.state.paused = False
        self.tile_map.load_level(0)
        self.tile_map.place_player_at_start(self.player)
        self.player.restore_full()
        self.player.exp = 0
        self.player.level = 1
        self.player.exp_need = 100
        self.player.stat_points = 0
        self.state.items.clear()
        self.state.score = 0
        self.state.room_reached = self.tile_map.level + 1
        self.run_recorded = False
        self.spawn_wave()
        self.log("World reset")

    # ------------------------------------------------------------------
    # Event/input
    # ------------------------------------------------------------------
    def handle_events(self) -> None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.submit_current_run()
                self.state.running = False
                continue

            if event.type == pygame.KEYDOWN:
                self.handle_keydown(event)
                continue

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                self.use_current_weapon()

    def handle_keydown(self, event: pygame.event.Event) -> None:
        key = event.key

        if self.game_over:
            if key == pygame.K_ESCAPE:
                self.submit_current_run()
                self.state.running = False
            elif key == pygame.K_r:
                self.reset_debug_world()
            return

        if key == pygame.K_ESCAPE:
            self.submit_current_run()
            self.state.running = False
        elif key == pygame.K_p:
            self.state.paused = not self.state.paused
            self.log("Paused" if self.state.paused else "Unpaused")
        elif key == pygame.K_F1:
            self.state.debug = not self.state.debug
            self.log(f"Debug hitboxes: {self.state.debug}")
        elif key == pygame.K_r:
            self.reset_debug_world()
        elif key == pygame.K_m:
            self.spawn_wave()
        elif key == pygame.K_l:
            if self.level_system.add_exp(self.player.exp_need):
                self.log(f"Level up! Player level {self.player.level}")
            else:
                self.log("Added EXP")
        elif key == pygame.K_h:
            self.spawn_item_at_player(Item.random_for_player(self.player))
            self.log("Spawned test item")
        elif key in (pygame.K_SPACE, pygame.K_RETURN):
            self.use_current_weapon()
        elif pygame.K_1 <= key <= pygame.K_9:
            index = key - pygame.K_1
            self.weapon_system.equip(index)
            self.log(f"Equipped {self.weapon_system.current.name}")
        elif key == pygame.K_i:
            self.weapon_system.weapon_list_open = not self.weapon_system.weapon_list_open
        elif key == pygame.K_z:
            self.try_upgrade("hp")
        elif key == pygame.K_x:
            self.try_upgrade("damage")
        elif key == pygame.K_c:
            self.try_upgrade("speed")
        elif key == pygame.K_v:
            self.try_upgrade("armor")

    def try_upgrade(self, stat_name: str) -> None:
        if self.stat_system.upgrade(stat_name):
            self.log(f"Upgraded {stat_name}")
        else:
            self.log("No stat points available")

    def update_mouse_aim(self) -> None:
        mx, my = pygame.mouse.get_pos()
        if not self.map_rect.collidepoint(mx, my):
            return
        dx = mx - self.player.x
        dy = my - self.player.y
        if dx or dy:
            self.player.set_direction(dx, dy)

    # ------------------------------------------------------------------
    # Gameplay integration
    # ------------------------------------------------------------------
    def use_current_weapon(self) -> None:
        if self.state.paused or not self.player.is_alive():
            return
        self.weapon_system.use_weapon(
            self.player,
            self.player.direction,
            self.state.monsters,
            self.damage_monster,
            self.map_rect,
            self.map_rect.width,
            self.map_rect.height,
            self.tile_map,
        )

    def damage_monster(self, monster: Any, amount: int | float) -> None:
        was_alive = monster.is_alive() if hasattr(monster, "is_alive") else True
        if hasattr(monster, "take_damage"):
            monster.take_damage(int(amount))
        elif isinstance(monster, dict):
            monster["hp"] = max(0, monster.get("hp", 0) - amount)
            monster["alive"] = monster["hp"] > 0

        now_alive = monster.is_alive() if hasattr(monster, "is_alive") else monster.get("alive", False)
        if was_alive and not now_alive:
            self.on_monster_killed(monster)

    def on_monster_killed(self, monster: Any) -> None:
        self.state.score += 1
        if self.level_system.add_exp(25):
            self.log(f"Level up! Player level {self.player.level}")

        drop = self.drop_table.roll(self.player)
        if drop is not None:
            rect = monster.get_rect() if hasattr(monster, "get_rect") else monster.rect
            self.spawn_item(drop, rect.centerx, rect.centery)

    def spawn_item_at_player(self, item: Item) -> None:
        self.spawn_item(item, self.player.x, self.player.y)

    def spawn_item(self, item: Item, x: int, y: int) -> None:
        item.rect = pygame.Rect(int(x) - 10, int(y) - 10, 20, 20)
        self.state.items.append(item)

    def update(self) -> None:
        if self.game_over:
            self.messages = [m for m in self.messages if m.tick()]
            return

        if self.state.paused:
            self.messages = [m for m in self.messages if m.tick()]
            return

        keys = pygame.key.get_pressed()
        self.tile_map.update_player_from_keys(self.player, keys)
        self.update_mouse_aim()
        self.state.tile_map = self.tile_map
        self.state.level = self.tile_map.level + 1

        # Hold mouse/space for repeated fire; weapon cooldowns control rate.
        mouse_buttons = pygame.mouse.get_pressed()
        if keys[pygame.K_SPACE] or mouse_buttons[0]:
            self.use_current_weapon()

        self.update_monsters()
        if self.game_over:
            return
        self.update_monster_projectiles()
        if self.game_over:
            return
        self.weapon_system.update(
            self.player,
            self.player.direction,
            self.state.monsters,
            self.damage_monster,
            self.map_rect,
            self.tile_map,
        )
        self.item_pickup_system.update(self.state)
        self.update_room_completion()
        self.update_level_exit()
        self.update_player_timers()
        self.check_player_death()
        self.messages = [m for m in self.messages if m.tick()]

    def check_player_death(self) -> None:
        if not self.game_over and not self.player.is_alive():
            self.game_over = True
            self.state.projectiles.clear()
            self.submit_current_run()
            self.log("Game Over", timer=FPS * 5)

    def update_monsters(self) -> None:
        for monster in list(self.state.monsters):
            if not monster.is_alive():
                continue
            monster.update(self.player, self.state.projectiles, self.tile_map)
            self.check_player_death()
            if self.game_over:
                break
            monster.separate_from_others(self.state.monsters, self.tile_map)

        self.state.monsters = [monster for monster in self.state.monsters if monster.is_alive()]

    def update_room_completion(self) -> None:
        self.state.monsters = [monster for monster in self.state.monsters if monster.is_alive()]
        if self.state.monsters or self.tile_map.exit_open:
            return
        self.state.projectiles.clear()
        self.tile_map.open_exit()
        self.log("Room clear! Exit opened")

    def update_monster_projectiles(self) -> None:
        live_projectiles = []
        for projectile in self.state.projectiles:
            projectile.update()
            if projectile.is_out_of_bounds():
                continue
            if projectile.is_blocked_by_wall(self.tile_map):
                continue
            if projectile.check_hit(self.player):
                self.player.take_damage(projectile.damage)
                self.log(f"Player hit for {projectile.damage}", timer=70)
                self.check_player_death()
                if self.game_over:
                    self.state.projectiles.clear()
                    return
                continue
            live_projectiles.append(projectile)
        self.state.projectiles = live_projectiles

    def update_level_exit(self) -> None:
        if self.tile_map.reached_exit(self.player.map_x, self.player.map_y):
            self.tile_map.load_level(self.tile_map.level + 1)
            self.tile_map.place_player_at_start(self.player)
            self.state.items.clear()
            self.state.level = self.tile_map.level + 1
            self.state.room_reached = max(self.state.room_reached, self.state.level)
            self.spawn_wave()
            self.log(f"Entered room {self.tile_map.level + 1}")

    def update_player_timers(self) -> None:
        self.player.update()
        self.regen_timer += 1
        if self.regen_timer >= FPS:
            self.regen_timer = 0
            self.player.update_regen()

    # ------------------------------------------------------------------
    # Drawing
    # ------------------------------------------------------------------
    def draw(self) -> None:
        self.screen.fill((0, 0, 0))
        self.tile_map.draw(self.screen)
        self.draw_items()
        self.draw_monsters()
        self.draw_projectiles()
        self.weapon_system.draw_projectiles(self.screen, self.state.debug)
        self.weapon_system.draw_attacks(self.screen, self.state.debug)
        self.player.draw(self.screen, PLAYER_COLOR)
        self.weapon_system.draw_weapon_icon(self.screen, self.player, self.player.direction)
        if self.weapon_system.weapon_list_open:
            self.weapon_system.draw_weapon_list(
                self.screen,
                self.font,
                self.small_font,
                self.screen.get_width(),
                self.screen.get_height(),
            )
        self.hud.draw(
            self.screen,
            player=self.player,
            tile_map=self.tile_map,
            weapon_system=self.weapon_system,
            monsters=self.state.monsters,
            monster_projectiles=self.state.projectiles,
            items=self.state.items,
            score=self.state.score,
            messages=self.messages,
            room_reached=self.state.room_reached,
            leaderboard=self.high_scores.display_entries(),
        )
        if self.game_over:
            self.draw_game_over_overlay()
        pygame.display.flip()

    def draw_game_over_overlay(self) -> None:
        overlay = pygame.Surface(self.screen.get_size(), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 185))
        self.screen.blit(overlay, (0, 0))

        title = self.game_over_font.render("Game Over", True, (255, 245, 245))
        prompt = self.restart_font.render("Press R to restart or Esc to quit", True, (255, 230, 120))

        center_x = self.screen.get_width() // 2
        center_y = self.screen.get_height() // 2
        self.screen.blit(title, title.get_rect(center=(center_x, center_y - 36)))
        self.screen.blit(prompt, prompt.get_rect(center=(center_x, center_y + 28)))

    def draw_items(self) -> None:
        for item in self.state.items:
            rect = getattr(item, "rect", None)
            if rect is None:
                continue
            pygame.draw.rect(self.screen, ITEM_COLORS.get(item.type, (255, 255, 255)), rect)
            if self.state.debug:
                pygame.draw.rect(self.screen, (255, 255, 255), rect, 1)

    def draw_monsters(self) -> None:
        for monster in self.state.monsters:
            monster.draw(self.screen)
            if self.state.debug:
                pygame.draw.rect(self.screen, (255, 255, 255), monster.get_rect(), 1)

    def draw_projectiles(self) -> None:
        for projectile in self.state.projectiles:
            projectile.draw(self.screen)
            if self.state.debug:
                pygame.draw.rect(self.screen, (255, 255, 255), projectile.get_rect(), 1)

    def run(self) -> None:
        while self.state.running:
            self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(FPS)
        pygame.quit()


def main() -> None:
    IntegratedDebugGame().run()


if __name__ == "__main__":
    main()
