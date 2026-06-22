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
from item import DropTable, Item, ItemPickupSystem
from level import LevelSystem, StatUpgradeSystem
from map import MapSystem, TileMap
from monster import MonsterSpawner
from player import Player
from weapon import WeaponSystem


HUD_WIDTH = 340
FPS = 60

WHITE = (255, 255, 255)
PLAYER_COLOR = (0, 200, 255)
INVINCIBLE_COLOR = (80, 255, 255)

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

        self.player = Player(width=32, height=32)
        self.tile_map.place_player_at_start(self.player)

        # Bật/tắt bằng phím B.
        # invincible_cheat = trạng thái debug/cheat.
        # invincible = trạng thái thật để Player.take_damage() chặn damage.
        self.player.invincible = False
        self.player.invincible_cheat = False

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
        self.messages: list[DebugMessage] = []
        self.regen_timer = 0

        self.spawn_wave()
        self.log("Debug ready: WASD move, mouse aim, click/space attack, B immortal")

    # ------------------------------------------------------------------
    # Setup helpers
    # ------------------------------------------------------------------
    def log(self, text: str, timer: int = 180) -> None:
        self.messages.append(DebugMessage(text, timer))
        self.messages = self.messages[-6:]

    def spawn_wave(self) -> None:
        self.state.projectiles.clear()
        wave_level = max(1, self.tile_map.level + 1)
        self.state.monsters = self.monster_spawner.spawn_wave(
            wave_level,
            self.player.x,
            self.player.y,
        )
        self.log(f"Spawned {len(self.state.monsters)} monsters for map level {wave_level}")

    def reset_debug_world(self) -> None:
        self.tile_map.load_level(0)
        self.tile_map.place_player_at_start(self.player)

        self.player.restore_full()
        self.player.exp = 0
        self.player.level = 1
        self.player.exp_need = 100
        self.player.stat_points = 0

        # Reset bất tử.
        self.player.invincible = False
        self.player.invincible_cheat = False

        if hasattr(self.weapon_system, "invincible_timer"):
            self.weapon_system.invincible_timer = 0

        self.state.items.clear()
        self.state.score = 0
        self.spawn_wave()
        self.log("World reset")

    # ------------------------------------------------------------------
    # Invincible helpers
    # ------------------------------------------------------------------
    def toggle_invincible(self) -> None:
        """Toggle permanent invincibility with the B key."""
        self.player.invincible_cheat = not getattr(self.player, "invincible_cheat", False)

        if self.player.invincible_cheat:
            self.player.invincible = True
            self.log("Invincible ON")
        else:
            self.player.invincible = False

            if hasattr(self.weapon_system, "invincible_timer"):
                self.weapon_system.invincible_timer = 0

            self.log("Invincible OFF")

    def apply_invincible_cheat(self) -> None:
        """Keep debug invincibility enabled even if weapon timers update."""
        if getattr(self.player, "invincible_cheat", False):
            self.player.invincible = True

    # ------------------------------------------------------------------
    # Event/input
    # ------------------------------------------------------------------
    def handle_events(self) -> None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.state.running = False
                continue

            if event.type == pygame.KEYDOWN:
                self.handle_keydown(event)
                continue

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                self.use_current_weapon()

    def handle_keydown(self, event: pygame.event.Event) -> None:
        key = event.key

        if key == pygame.K_ESCAPE:
            self.state.running = False
        elif key == pygame.K_p:
            self.state.paused = not self.state.paused
            self.log("Paused" if self.state.paused else "Unpaused")
        elif key == pygame.K_F1:
            self.state.debug = not self.state.debug
            self.log(f"Debug hitboxes: {self.state.debug}")
        elif key == pygame.K_b:
            self.toggle_invincible()
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
        if self.state.paused:
            self.messages = [m for m in self.messages if m.tick()]
            return

        keys = pygame.key.get_pressed()
        self.tile_map.update_player_from_keys(self.player, keys)
        self.update_mouse_aim()

        self.state.tile_map = self.tile_map
        self.state.level = self.tile_map.level + 1

        # Giữ bất tử trước khi quái/projectile gây damage.
        self.apply_invincible_cheat()

        # Hold mouse/space for repeated fire; weapon cooldowns control rate.
        mouse_buttons = pygame.mouse.get_pressed()
        if keys[pygame.K_SPACE] or mouse_buttons[0]:
            self.use_current_weapon()

        self.update_monsters()
        self.update_monster_projectiles()

        self.weapon_system.update(
            self.player,
            self.player.direction,
            self.state.monsters,
            self.damage_monster,
            self.map_rect,
        )

        # WeaponSystem có thể tắt invincible khi timer hết,
        # nên nếu cheat B đang bật thì bật lại ngay.
        self.apply_invincible_cheat()

        self.item_pickup_system.update(self.state)
        self.update_level_exit()
        self.update_player_timers()

        self.messages = [m for m in self.messages if m.tick()]

        if not self.state.monsters:
            self.spawn_wave()

    def update_monsters(self) -> None:
        for monster in list(self.state.monsters):
            if not monster.is_alive():
                continue

            monster.update(self.player, self.state.projectiles)
            monster.separate_from_others(self.state.monsters)

        self.state.monsters = [monster for monster in self.state.monsters if monster.is_alive()]

    def update_monster_projectiles(self) -> None:
        live_projectiles = []

        for projectile in self.state.projectiles:
            projectile.update()

            if projectile.is_out_of_bounds():
                continue

            if projectile.check_hit(self.player):
                if getattr(self.player, "invincible", False):
                    self.log("Blocked damage: invincible", timer=50)
                else:
                    self.player.take_damage(projectile.damage)
                    self.log(f"Player hit for {projectile.damage}", timer=70)

                continue

            live_projectiles.append(projectile)

        self.state.projectiles = live_projectiles

    def update_level_exit(self) -> None:
        if self.tile_map.reached_exit(self.player.map_x, self.player.map_y):
            self.tile_map.load_level(self.tile_map.level + 1)
            self.tile_map.place_player_at_start(self.player)
            self.state.items.clear()
            self.spawn_wave()
            self.log(f"Entered map level {self.tile_map.level + 1}")

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
        self.draw_invincible_effect()

        self.weapon_system.draw_weapon_icon(self.screen, self.player, self.player.direction)

        if self.weapon_system.weapon_list_open:
            self.weapon_system.draw_weapon_list(
                self.screen,
                self.font,
                self.small_font,
                self.screen.get_width(),
                self.screen.get_height(),
            )

        self.draw_hud()
        pygame.display.flip()

    def draw_invincible_effect(self) -> None:
        if not getattr(self.player, "invincible", False):
            return

        rect = self.player.get_rect()
        radius = max(rect.width, rect.height) + 10

        pygame.draw.circle(self.screen, INVINCIBLE_COLOR, rect.center, radius, 3)
        pygame.draw.circle(self.screen, WHITE, rect.center, radius + 6, 1)

    def draw_items(self) -> None:
        for item in self.state.items:
            rect = getattr(item, "rect", None)

            if rect is None:
                continue

            pygame.draw.rect(self.screen, ITEM_COLORS.get(item.type, (255, 255, 255)), rect)

            if self.state.debug:
                pygame.draw.rect(self.screen, WHITE, rect, 1)

    def draw_monsters(self) -> None:
        for monster in self.state.monsters:
            monster.draw(self.screen)

            if self.state.debug:
                pygame.draw.rect(self.screen, WHITE, monster.get_rect(), 1)

    def draw_projectiles(self) -> None:
        for projectile in self.state.projectiles:
            projectile.draw(self.screen)

            if self.state.debug:
                pygame.draw.rect(self.screen, WHITE, projectile.get_rect(), 1)

    def draw_hud(self) -> None:
        x = self.map_rect.width + 12
        y = 12

        panel = pygame.Rect(self.map_rect.width, 0, HUD_WIDTH, self.screen.get_height())
        pygame.draw.rect(self.screen, (22, 22, 26), panel)
        pygame.draw.line(
            self.screen,
            (90, 90, 90),
            (self.map_rect.width, 0),
            (self.map_rect.width, self.screen.get_height()),
            2,
        )

        invincible_on = getattr(self.player, "invincible", False)
        invincible_cheat_on = getattr(self.player, "invincible_cheat", False)
        invincible_timer = getattr(self.weapon_system, "invincible_timer", 0)
        weapon_count = min(9, len(getattr(self.weapon_system, "weapons", [])))

        lines = [
            "INTEGRATED DEBUG",
            f"Map level: {self.tile_map.level + 1}",
            f"Player LV: {self.player.level}  EXP: {self.player.exp}/{self.player.exp_need}",
            f"HP: {int(self.player.hp)}/{self.player.max_hp}",
            f"Armor: {int(self.player.armor)}/{self.player.max_armor}",
            f"Energy: {int(self.player.energy)}/{self.player.max_energy}",
            f"Damage: {self.player.damage}  Speed: {self.player.speed}",
            f"Stat points: {self.player.stat_points}",
            f"Weapon: {self.weapon_system.current.name}",
            f"Invincible: {'ON' if invincible_on else 'OFF'}",
            f"B immortal: {'ON' if invincible_cheat_on else 'OFF'}",
            f"Immortal timer: {invincible_timer}",
            f"Monsters: {len(self.state.monsters)}",
            f"Monster projectiles: {len(self.state.projectiles)}",
            f"Weapon projectiles: {self.weapon_system.projectile_count()}",
            f"Items: {len(self.state.items)}  Score: {self.state.score}",
            "",
            "Controls:",
            "WASD move | mouse aim",
            "LMB/Space attack",
            f"1-{weapon_count} equip weapon | I list",
            "B immortal | F1 hitboxes",
            "P pause | R reset",
            "M spawn wave | H item | L exp",
            "Z/X/C/V upgrade stats",
        ]

        for line in lines:
            color = WHITE

            if line.startswith("Invincible: ON") or line.startswith("B immortal: ON"):
                color = INVINCIBLE_COLOR
            elif line.startswith("HP:"):
                color = (255, 120, 120)
            elif line.startswith("Armor:"):
                color = (120, 180, 255)
            elif line.startswith("Energy:"):
                color = (255, 220, 80)
            elif line.startswith("Weapon:"):
                color = (255, 230, 120)

            rendered = self.small_font.render(line, True, color)
            self.screen.blit(rendered, (x, y))
            y += 20

        y += 8

        for msg in self.messages[-6:]:
            rendered = self.small_font.render(msg.text, True, (255, 230, 120))
            self.screen.blit(rendered, (x, y))
            y += 18

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