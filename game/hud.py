"""Reusable HUD drawing module for the integrated debug runner.

The HUD keeps gameplay status readable without coupling UI layout to the
main debug game loop.  It draws player vitals as visual sliders and shows
input help as icon groups instead of long instructional text lines.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Iterable, Sequence

import pygame


@dataclass(frozen=True)
class HudStat:
    """One player resource displayed as an icon + slider."""

    icon: str
    current_attr: str
    max_attr: str
    color: tuple[int, int, int]


@dataclass(frozen=True)
class HudLayout:
    """Computed HUD layout for the current display height.

    The gameplay resolution can now change independently from the HUD. This
    layout object keeps HUD cards inside the visible display surface instead of
    relying on one fixed 768px-tall window.
    """

    panel_padding: int
    card_gap: int
    status_card_height: int
    run_card_height: int
    controls_card_height: int
    control_row_height: int
    show_messages: bool


class GameHUD:
    """Right-side game HUD with status sliders and icon-only controls."""

    PANEL_BG = (22, 22, 26)
    CARD_BG = (32, 34, 42)
    CARD_BORDER = (70, 74, 86)
    TRACK = (48, 50, 60)
    TRACK_BORDER = (92, 96, 110)
    TEXT = (244, 246, 252)
    MUTED = (156, 162, 176)
    WARNING = (255, 230, 120)

    STATS: Sequence[HudStat] = (
        HudStat("heart", "hp", "max_hp", (230, 72, 82)),
        HudStat("shield", "armor", "max_armor", (82, 160, 255)),
        HudStat("bolt", "energy", "max_energy", (255, 205, 75)),
    )

    PANEL_PADDING = 18
    CARD_PADDING_X = 14
    CARD_TITLE_HEIGHT = 40
    CARD_GAP = 14
    STATUS_CARD_HEIGHT = 168
    RUN_CARD_HEIGHT = 268
    CONTROLS_CARD_HEIGHT = 254
    STAT_ROW_HEIGHT = 38
    STAT_ICON_SIZE = 30
    STAT_TRACK_HEIGHT = 18
    CONTROL_ROW_HEIGHT = 34
    CONTROL_ITEM_GAP = 8

    MIN_STATUS_CARD_HEIGHT = 138
    MIN_RUN_CARD_HEIGHT = 150
    MIN_CONTROLS_CARD_HEIGHT = 192
    MIN_CONTROL_ROW_HEIGHT = 27
    MIN_BOTTOM_PADDING = 16
    MESSAGE_AREA_HEIGHT = 42

    def __init__(
        self,
        map_width: int,
        width: int,
        font: pygame.font.Font,
        small_font: pygame.font.Font,
    ) -> None:
        self.map_width = map_width
        self.width = width
        self.font = font
        self.small_font = small_font
        self.control_rows = self._build_control_rows()

    # ------------------------------------------------------------------
    # Public draw entry point
    # ------------------------------------------------------------------
    def draw(
        self,
        surface: pygame.Surface,
        *,
        player: object,
        tile_map: object,
        weapon_system: object,
        monsters: Sequence[object],
        monster_projectiles: Sequence[object],
        items: Sequence[object],
        score: int,
        messages: Iterable[object],
        room_reached: int = 1,
        leaderboard: Sequence[object] = (),
    ) -> None:
        self._draw_panel(surface)
        layout = self._make_layout(surface.get_height())
        x = self.map_width + layout.panel_padding
        y = layout.panel_padding
        content_width = self.width - layout.panel_padding * 2
        panel_bottom = surface.get_height() - layout.panel_padding

        y = self._draw_status_card(
            surface,
            x,
            y,
            content_width,
            player,
            height=layout.status_card_height,
        )
        y = self._draw_run_card(
            surface,
            x,
            y + layout.card_gap,
            content_width,
            player,
            tile_map,
            weapon_system,
            monsters,
            monster_projectiles,
            items,
            score,
            room_reached,
            leaderboard,
            height=layout.run_card_height,
        )
        y = self._draw_controls_card(
            surface,
            x,
            y + layout.card_gap,
            content_width,
            height=layout.controls_card_height,
            row_height=layout.control_row_height,
        )
        if layout.show_messages:
            self._draw_messages(surface, x, y + layout.card_gap, messages, max_y=panel_bottom)

    # ------------------------------------------------------------------
    # Cards / layout
    # ------------------------------------------------------------------
    def _make_layout(self, surface_height: int) -> HudLayout:
        """Return a HUD layout that fits inside the current display height.

        The HUD must fit inside the Pygame display surface, not merely inside
        the OS window around it.  This method keeps top/bottom padding
        mandatory and, on compact resolutions, stops the run-info card from
        expanding just because spare pixels exist.  That leaves visible room
        below the controls card instead of making the bottom shortcut row feel
        clipped against the window edge.
        """
        if surface_height <= 0:
            return HudLayout(
                panel_padding=0,
                card_gap=0,
                status_card_height=0,
                run_card_height=0,
                controls_card_height=0,
                control_row_height=self.MIN_CONTROL_ROW_HEIGHT,
                show_messages=False,
            )

        panel_padding = min(self.PANEL_PADDING, max(8, surface_height // 48))
        bottom_padding = min(self.MIN_BOTTOM_PADDING, panel_padding)
        card_gap = 12 if surface_height >= 760 else 10 if surface_height >= 650 else 8
        card_budget = max(0, surface_height - panel_padding - bottom_padding - card_gap * 2)

        full_controls_height = self._controls_card_height_for(self.CONTROL_ROW_HEIGHT)
        full_cards_height = self.STATUS_CARD_HEIGHT + self.RUN_CARD_HEIGHT + full_controls_height
        if card_budget >= full_cards_height + self.MESSAGE_AREA_HEIGHT:
            return HudLayout(
                panel_padding=panel_padding,
                card_gap=card_gap,
                status_card_height=self.STATUS_CARD_HEIGHT,
                run_card_height=self.RUN_CARD_HEIGHT,
                controls_card_height=full_controls_height,
                control_row_height=self.CONTROL_ROW_HEIGHT,
                show_messages=True,
            )

        # Compact presets: keep the controls fully visible, but avoid using the
        # entire vertical budget for the cards.  The spare pixels become real
        # bottom breathing room (and, when enough exists, a message area).
        if surface_height >= 760:
            control_row_height = 31
            status_height = 158
            run_height = 232
        elif surface_height >= 720:
            control_row_height = 30
            status_height = 150
            run_height = 224
        elif surface_height >= 680:
            control_row_height = 28
            status_height = 144
            run_height = 212
        else:
            control_row_height = self.MIN_CONTROL_ROW_HEIGHT
            status_height = self.MIN_STATUS_CARD_HEIGHT
            run_height = 198

        controls_height = self._controls_card_height_for(control_row_height)
        status_height = max(self.MIN_STATUS_CARD_HEIGHT, min(self.STATUS_CARD_HEIGHT, status_height))
        run_height = max(self.MIN_RUN_CARD_HEIGHT, min(self.RUN_CARD_HEIGHT, run_height))

        total_cards = status_height + run_height + controls_height
        if total_cards > card_budget:
            overflow = total_cards - card_budget
            reducible_run = max(0, run_height - self.MIN_RUN_CARD_HEIGHT)
            reduction = min(reducible_run, overflow)
            run_height -= reduction
            overflow -= reduction

            if overflow:
                reducible_status = max(0, status_height - self.MIN_STATUS_CARD_HEIGHT)
                reduction = min(reducible_status, overflow)
                status_height -= reduction
                overflow -= reduction

            # Last resort for very small windows: shrink the control rows and
            # recalculate the card height, but never below the minimum row size.
            while overflow > 0 and control_row_height > self.MIN_CONTROL_ROW_HEIGHT:
                control_row_height -= 1
                new_controls_height = self._controls_card_height_for(control_row_height)
                overflow -= controls_height - new_controls_height
                controls_height = new_controls_height

            if overflow > 0:
                controls_height = max(self.MIN_CONTROLS_CARD_HEIGHT, controls_height - overflow)

        used_height = status_height + card_gap + run_height + card_gap + controls_height
        spare_after_cards = surface_height - panel_padding - used_height
        show_messages = spare_after_cards >= self.MESSAGE_AREA_HEIGHT

        return HudLayout(
            panel_padding=panel_padding,
            card_gap=card_gap,
            status_card_height=status_height,
            run_card_height=run_height,
            controls_card_height=controls_height,
            control_row_height=control_row_height,
            show_messages=show_messages,
        )

    def _controls_card_height_for(self, row_height: int) -> int:
        """Return the smallest safe card height for all configured control rows."""
        return self.CARD_TITLE_HEIGHT + len(self.control_rows) * row_height + 10

    def _draw_panel(self, surface: pygame.Surface) -> None:
        panel = pygame.Rect(self.map_width, 0, self.width, surface.get_height())
        pygame.draw.rect(surface, self.PANEL_BG, panel)
        pygame.draw.line(
            surface,
            (90, 90, 90),
            (self.map_width, 0),
            (self.map_width, surface.get_height()),
            2,
        )

    def _draw_card(
        self,
        surface: pygame.Surface,
        rect: pygame.Rect,
        title: str,
    ) -> int:
        pygame.draw.rect(surface, self.CARD_BG, rect, border_radius=10)
        pygame.draw.rect(surface, self.CARD_BORDER, rect, 1, border_radius=10)
        self._text(
            surface,
            title,
            rect.x + self.CARD_PADDING_X,
            rect.y + 11,
            self.TEXT,
            self.small_font,
        )
        return rect.y + self.CARD_TITLE_HEIGHT

    def _draw_status_card(
        self,
        surface: pygame.Surface,
        x: int,
        y: int,
        width: int,
        player: object,
        *,
        height: int,
    ) -> int:
        card = pygame.Rect(x, y, width, height)
        row_y = self._draw_card(surface, card, "PLAYER HUD")
        for stat in self.STATS:
            current = float(getattr(player, stat.current_attr, 0))
            maximum = float(getattr(player, stat.max_attr, 1))
            self._draw_stat_slider(
                surface,
                icon=stat.icon,
                x=x + self.CARD_PADDING_X,
                y=row_y,
                width=width - self.CARD_PADDING_X * 2,
                current=current,
                maximum=maximum,
                color=stat.color,
            )
            row_y += self.STAT_ROW_HEIGHT

        points_y = card.bottom - 21
        # Compact HUD heights prioritize the sliders; draw upgrade shortcuts only
        # when there is enough vertical room to avoid text overlapping a bar.
        if points_y >= row_y - 8:
            points = max(0, int(getattr(player, "stat_points", 0)))
            points_color = self.WARNING if points else self.MUTED
            self._text(
                surface,
                f"UPGRADE PTS {points}   Z HP  X AR  C EN",
                x + self.CARD_PADDING_X,
                points_y,
                points_color,
                self.small_font,
            )
        return card.bottom

    def _draw_run_card(
        self,
        surface: pygame.Surface,
        x: int,
        y: int,
        width: int,
        player: object,
        tile_map: object,
        weapon_system: object,
        monsters: Sequence[object],
        monster_projectiles: Sequence[object],
        items: Sequence[object],
        score: int,
        room_reached: int,
        leaderboard: Sequence[object],
        *,
        height: int,
    ) -> int:
        card = pygame.Rect(x, y, width, height)
        row_y = self._draw_card(surface, card, "RUN INFO")
        rows = [
            ("ROOM", str(getattr(tile_map, "level", 0) + 1)),
            (
                "LV",
                f"{getattr(player, 'level', 1)}  XP {getattr(player, 'exp', 0)}/{getattr(player, 'exp_need', 0)}",
            ),
            ("DMG", f"{getattr(player, 'damage', 0)}  SPD {getattr(player, 'speed', 0)}"),
            ("BAG", f"{len(items)}  KILLS {score}"),
        ]
        for label, value in rows:
            self._text(surface, label, x + self.CARD_PADDING_X, row_y, self.MUTED, self.small_font)
            self._text(surface, value, x + 80, row_y, self.TEXT, self.small_font)
            row_y += 20

        self._draw_leaderboard(
            surface,
            x + self.CARD_PADDING_X,
            row_y + 8,
            width - self.CARD_PADDING_X * 2,
            room_reached,
            leaderboard,
            max_y=card.bottom - 8,
        )
        return card.bottom

    def _draw_leaderboard(
        self,
        surface: pygame.Surface,
        x: int,
        y: int,
        width: int,
        room_reached: int,
        leaderboard: Sequence[object],
        *,
        max_y: int | None = None,
    ) -> None:
        previous_clip = surface.get_clip()
        if max_y is not None:
            clip_height = max(0, max_y - y)
            surface.set_clip(pygame.Rect(x, y, width, clip_height))

        try:
            self._text(surface, "LEADERBOARD", x, y, self.TEXT, self.small_font)
            y += 20
            self._text(surface, "RUN", x, y, self.MUTED, self.small_font)
            self._text(surface, f"Room {max(1, int(room_reached))}", x + 80, y, self.WARNING, self.small_font)
            y += 20

            if not leaderboard:
                self._text(surface, "No saved runs yet", x, y, self.MUTED, self.small_font)
                return

            entries = list(leaderboard)
            omitted = 0
            if max_y is not None:
                available_rows = max(0, (max_y - y) // 18)
                if len(entries) > available_rows:
                    if available_rows >= 2:
                        visible_count = available_rows - 1
                        omitted = len(entries) - visible_count
                        entries = entries[:visible_count]
                    else:
                        omitted = len(entries)
                        entries = []

            for rank, entry in enumerate(entries, start=1):
                room = self._entry_room(entry)
                self._text(surface, f"#{rank}", x, y, self.MUTED, self.small_font)
                self._text(surface, f"Room {room}", x + 80, y, self.TEXT, self.small_font)
                y += 18

            if omitted:
                self._text(surface, f"+{omitted} more saved", x, y, self.MUTED, self.small_font)
        finally:
            if max_y is not None:
                surface.set_clip(previous_clip)

    @staticmethod
    def _entry_room(entry: object) -> int:
        if isinstance(entry, dict):
            value = entry.get("room_reached", 1)
        else:
            value = getattr(entry, "room_reached", 1)
        try:
            return max(1, int(value))
        except (TypeError, ValueError):
            return 1

    def _draw_controls_card(
        self,
        surface: pygame.Surface,
        x: int,
        y: int,
        width: int,
        *,
        height: int,
        row_height: int,
    ) -> int:
        card = pygame.Rect(x, y, width, height)
        previous_clip = surface.get_clip()
        surface.set_clip(card)
        try:
            row_y = self._draw_card(surface, card, "CONTROLS")
            row_bg_width = width - self.CARD_PADDING_X * 2
            max_row_y = card.bottom - 6
            for row in self.control_rows:
                if row_y + 18 > max_row_y:
                    break
                row_bg = pygame.Rect(
                    x + self.CARD_PADDING_X - 4,
                    row_y - 2,
                    row_bg_width + 8,
                    max(18, row_height - 2),
                )
                pygame.draw.rect(surface, (28, 30, 38), row_bg, border_radius=8)
                self._draw_control_row(surface, x + self.CARD_PADDING_X, row_y, row)
                row_y += row_height
        finally:
            surface.set_clip(previous_clip)
        return card.bottom

    def _draw_messages(
        self,
        surface: pygame.Surface,
        x: int,
        y: int,
        messages: Iterable[object],
        *,
        max_y: int,
    ) -> None:
        for msg in list(messages)[-4:]:
            if y + 16 > max_y:
                break
            text = str(getattr(msg, "text", msg))
            self._text(surface, text, x, y, self.WARNING, self.small_font)
            y += 18

    # ------------------------------------------------------------------
    # Vitals
    # ------------------------------------------------------------------
    def _draw_stat_slider(
        self,
        surface: pygame.Surface,
        *,
        icon: str,
        x: int,
        y: int,
        width: int,
        current: float,
        maximum: float,
        color: tuple[int, int, int],
    ) -> None:
        icon_rect = pygame.Rect(x, y + 2, self.STAT_ICON_SIZE, self.STAT_ICON_SIZE)
        self._draw_resource_icon(surface, icon, icon_rect, color)

        track_x = icon_rect.right + 14
        track_y = y + (self.STAT_ICON_SIZE - self.STAT_TRACK_HEIGHT) // 2 + 2
        track = pygame.Rect(track_x, track_y, width - (track_x - x), self.STAT_TRACK_HEIGHT)
        pct = 0 if maximum <= 0 else max(0.0, min(1.0, current / maximum))
        pygame.draw.rect(surface, self.TRACK, track, border_radius=8)
        if pct > 0:
            fill = track.copy()
            fill.width = max(5, int(track.width * pct))
            pygame.draw.rect(surface, color, fill, border_radius=8)
        pygame.draw.rect(surface, self.TRACK_BORDER, track, 1, border_radius=8)

        value = f"{int(current)}/{int(maximum)}"
        value_surface = self.small_font.render(value, True, self.TEXT)
        value_rect = value_surface.get_rect(center=track.center)
        surface.blit(value_surface, value_rect)

    def _draw_resource_icon(
        self,
        surface: pygame.Surface,
        kind: str,
        rect: pygame.Rect,
        color: tuple[int, int, int],
    ) -> None:
        pygame.draw.rect(surface, (20, 22, 28), rect, border_radius=7)
        pygame.draw.rect(surface, self.CARD_BORDER, rect, 1, border_radius=7)
        cx, cy = rect.center

        if kind == "heart":
            pygame.draw.circle(surface, color, (cx - 5, cy - 4), 5)
            pygame.draw.circle(surface, color, (cx + 5, cy - 4), 5)
            pygame.draw.polygon(surface, color, [(cx - 11, cy), (cx + 11, cy), (cx, cy + 12)])
        elif kind == "shield":
            points = [
                (cx, rect.y + 5),
                (rect.right - 6, rect.y + 9),
                (rect.right - 8, cy + 7),
                (cx, rect.bottom - 4),
                (rect.x + 8, cy + 7),
                (rect.x + 6, rect.y + 9),
            ]
            pygame.draw.polygon(surface, color, points)
            pygame.draw.line(surface, (215, 235, 255), (cx, rect.y + 8), (cx, rect.bottom - 8), 2)
        elif kind == "bolt":
            points = [
                (cx + 2, rect.y + 4),
                (cx - 8, cy + 2),
                (cx - 1, cy + 2),
                (cx - 4, rect.bottom - 4),
                (cx + 10, cy - 3),
                (cx + 2, cy - 3),
            ]
            pygame.draw.polygon(surface, color, points)

    # ------------------------------------------------------------------
    # Control icons
    # ------------------------------------------------------------------
    def _build_control_rows(self) -> list[tuple[tuple[str, object], ...]]:
        return [
            (("wasd", None), ("mouse", "aim")),
            (("mouse", "left"), ("key", "SPACE"), ("icon", "sword")),
            (("keys", ("1", "7")), ("key", "I"), ("icon", "list")),
            (("key", "F1"), ("icon", "target"), ("key", "P"), ("icon", "pause"), ("key", "R"), ("icon", "reset")),
            (("key", "M"), ("icon", "monster"), ("key", "H"), ("icon", "gem"), ("key", "L"), ("icon", "star")),
            (("key", "Z"), ("icon", "heart"), ("key", "X"), ("icon", "shield"), ("key", "C"), ("icon", "bolt")),
        ]

    def _draw_control_row(
        self,
        surface: pygame.Surface,
        x: int,
        y: int,
        row: Sequence[tuple[str, object]],
    ) -> None:
        cursor_x = x
        for kind, payload in row:
            if kind == "key":
                cursor_x = self._draw_keycap(surface, str(payload), cursor_x, y) + self.CONTROL_ITEM_GAP
            elif kind == "keys":
                first, last = payload  # type: ignore[misc]
                cursor_x = self._draw_key_range(surface, str(first), str(last), cursor_x, y) + self.CONTROL_ITEM_GAP
            elif kind == "key_group":
                cursor_x = self._draw_key_group(surface, payload, cursor_x, y) + self.CONTROL_ITEM_GAP
            elif kind == "wasd":
                cursor_x = self._draw_wasd(surface, cursor_x, y) + self.CONTROL_ITEM_GAP + 2
            elif kind == "mouse":
                cursor_x = self._draw_mouse_icon(surface, cursor_x, y, str(payload)) + self.CONTROL_ITEM_GAP
            elif kind == "icon":
                cursor_x = self._draw_action_icon(surface, cursor_x, y, str(payload)) + self.CONTROL_ITEM_GAP

    def _draw_keycap(self, surface: pygame.Surface, label: str, x: int, y: int) -> int:
        width = max(26, self.small_font.size(label)[0] + 14)
        rect = pygame.Rect(x, y + 2, width, 24)
        pygame.draw.rect(surface, (46, 48, 58), rect, border_radius=6)
        pygame.draw.rect(surface, (118, 122, 138), rect, 1, border_radius=6)
        self._centered_text(surface, label, rect, self.TEXT, self.small_font)
        return rect.right

    def _draw_key_range(
        self,
        surface: pygame.Surface,
        first: str,
        last: str,
        x: int,
        y: int,
    ) -> int:
        end = self._draw_keycap(surface, first, x, y)
        self._text(surface, "–", end + 3, y + 5, self.MUTED, self.small_font)
        end = self._draw_keycap(surface, last, end + 13, y)
        return end


    def _draw_key_group(
        self,
        surface: pygame.Surface,
        labels: object,
        x: int,
        y: int,
    ) -> int:
        cursor_x = x
        for label in labels:  # type: ignore[union-attr]
            cursor_x = self._draw_keycap(surface, str(label), cursor_x, y) + 2
        return cursor_x - 2

    def _draw_wasd(self, surface: pygame.Surface, x: int, y: int) -> int:
        positions = {
            "W": (x + 23, y),
            "A": (x, y + 16),
            "S": (x + 23, y + 16),
            "D": (x + 46, y + 16),
        }
        for label, pos in positions.items():
            rect = pygame.Rect(pos[0], pos[1], 22, 18)
            pygame.draw.rect(surface, (46, 48, 58), rect, border_radius=4)
            pygame.draw.rect(surface, (118, 122, 138), rect, 1, border_radius=4)
            self._centered_text(surface, label, rect, self.TEXT, self.small_font)
        return x + 68

    def _draw_mouse_icon(self, surface: pygame.Surface, x: int, y: int, mode: str) -> int:
        body = pygame.Rect(x, y + 2, 28, 27)
        pygame.draw.ellipse(surface, (46, 48, 58), body)
        pygame.draw.ellipse(surface, (118, 122, 138), body, 1)
        pygame.draw.line(surface, (118, 122, 138), (x + 14, y + 4), (x + 14, y + 13), 1)
        pygame.draw.circle(surface, self.TEXT, (x + 14, y + 9), 2)
        if mode == "left":
            pygame.draw.arc(surface, (255, 255, 255), pygame.Rect(x + 4, y + 5, 12, 12), 1.6, 4.7, 2)
        elif mode == "aim":
            self._draw_crosshair(surface, x + 40, y + 16, 8)
            return x + 50
        return x + 30

    def _draw_action_icon(self, surface: pygame.Surface, x: int, y: int, kind: str) -> int:
        rect = pygame.Rect(x, y + 2, 26, 24)
        pygame.draw.rect(surface, (36, 38, 48), rect, border_radius=6)
        pygame.draw.rect(surface, (92, 96, 110), rect, 1, border_radius=6)
        cx, cy = rect.center

        if kind == "sword":
            pygame.draw.line(surface, (230, 235, 245), (cx - 6, cy + 7), (cx + 7, cy - 7), 3)
            pygame.draw.line(surface, (180, 120, 65), (cx - 8, cy + 2), (cx - 1, cy + 9), 3)
            pygame.draw.circle(surface, (255, 220, 120), (cx - 7, cy + 8), 2)
        elif kind == "list":
            for i in range(3):
                row_y = rect.y + 7 + i * 5
                pygame.draw.circle(surface, self.TEXT, (rect.x + 8, row_y), 1)
                pygame.draw.line(surface, self.TEXT, (rect.x + 12, row_y), (rect.right - 6, row_y), 2)
        elif kind == "target":
            self._draw_crosshair(surface, cx, cy, 8)
        elif kind == "pause":
            pygame.draw.rect(surface, self.TEXT, pygame.Rect(cx - 6, cy - 8, 4, 16), border_radius=1)
            pygame.draw.rect(surface, self.TEXT, pygame.Rect(cx + 2, cy - 8, 4, 16), border_radius=1)
        elif kind == "reset":
            pygame.draw.arc(surface, self.TEXT, pygame.Rect(cx - 8, cy - 8, 16, 16), 0.3, 5.2, 2)
            pygame.draw.polygon(surface, self.TEXT, [(cx - 7, cy - 8), (cx - 1, cy - 8), (cx - 4, cy - 13)])
        elif kind == "monster":
            pygame.draw.circle(surface, (120, 240, 145), (cx, cy), 8)
            pygame.draw.circle(surface, (20, 22, 28), (cx - 3, cy - 2), 2)
            pygame.draw.circle(surface, (20, 22, 28), (cx + 3, cy - 2), 2)
            pygame.draw.line(surface, (20, 22, 28), (cx - 4, cy + 4), (cx + 4, cy + 4), 2)
        elif kind == "gem":
            pygame.draw.polygon(
                surface,
                (110, 210, 255),
                [(cx, rect.y + 5), (rect.right - 6, cy), (cx, rect.bottom - 5), (rect.x + 6, cy)],
            )
        elif kind == "star":
            self._draw_star(surface, cx, cy, 8, (255, 220, 90))
        elif kind == "upgrade":
            pygame.draw.polygon(surface, (120, 240, 145), [(cx, cy - 9), (cx + 8, cy), (cx + 3, cy), (cx + 3, cy + 9), (cx - 3, cy + 9), (cx - 3, cy), (cx - 8, cy)])
        elif kind == "heart":
            self._draw_resource_icon(surface, "heart", rect.inflate(-2, -2), (230, 72, 82))
        elif kind == "shield":
            self._draw_resource_icon(surface, "shield", rect.inflate(-2, -2), (82, 160, 255))
        elif kind == "bolt":
            self._draw_resource_icon(surface, "bolt", rect.inflate(-2, -2), (255, 205, 75))
        return rect.right

    def _draw_crosshair(self, surface: pygame.Surface, cx: int, cy: int, radius: int) -> None:
        pygame.draw.circle(surface, self.TEXT, (cx, cy), radius, 1)
        pygame.draw.line(surface, self.TEXT, (cx - radius - 3, cy), (cx - 2, cy), 1)
        pygame.draw.line(surface, self.TEXT, (cx + 2, cy), (cx + radius + 3, cy), 1)
        pygame.draw.line(surface, self.TEXT, (cx, cy - radius - 3), (cx, cy - 2), 1)
        pygame.draw.line(surface, self.TEXT, (cx, cy + 2), (cx, cy + radius + 3), 1)

    def _draw_star(
        self,
        surface: pygame.Surface,
        cx: int,
        cy: int,
        radius: int,
        color: tuple[int, int, int],
    ) -> None:
        points = []
        for i in range(10):
            angle = -1.5708 + i * 0.62832
            r = radius if i % 2 == 0 else radius // 2
            points.append((cx + int(r * math.cos(angle)), cy + int(r * math.sin(angle))))
        pygame.draw.polygon(surface, color, points)

    # ------------------------------------------------------------------
    # Text helpers
    # ------------------------------------------------------------------
    def _text(
        self,
        surface: pygame.Surface,
        text: str,
        x: int,
        y: int,
        color: tuple[int, int, int],
        font: pygame.font.Font,
    ) -> None:
        rendered = font.render(text, True, color)
        surface.blit(rendered, (x, y))

    def _centered_text(
        self,
        surface: pygame.Surface,
        text: str,
        rect: pygame.Rect,
        color: tuple[int, int, int],
        font: pygame.font.Font,
    ) -> None:
        rendered = font.render(text, True, color)
        surface.blit(rendered, rendered.get_rect(center=rect.center))
