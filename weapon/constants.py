"""Weapon constants and original weapon data."""

# =========================
# COLORS
# =========================
YELLOW = (255, 230, 0)
WHITE = (255, 255, 255)
GREEN = (0, 220, 80)
ORANGE = (255, 140, 0)
GRAY = (120, 120, 120)
LIGHT_GRAY = (170, 170, 170)
DARK_GRAY = (45, 45, 45)
PURPLE = (160, 80, 255)
BROWN = (130, 80, 35)

FLAG_RED = (255, 60, 60)
FLAG_LIGHT = (255, 150, 150)
FLAG_DARK = (170, 30, 30)

SPEAR_COLOR = (80, 220, 255)
SPEAR_TIP = (230, 230, 255)
SPEAR_SPLASH = (60, 130, 180)

DUAL_LONG = (180, 220, 255)
DUAL_SHORT = (255, 220, 120)
DUAL_SLASH = (120, 210, 255)

# =========================
# ORIGINAL WEAPON DATA
# =========================
DEFAULT_RANGED_ENERGY_COST = 2
ENERGY_AMMO_WEAPON_TYPES = {"ranged", "thrown_spear", "returning"}

WEAPON_DATA = [
    {
        "name": "Sword",
        "type": "melee",
        "damage": 25,
        "range": 120,
        "size": 16,
        "color": YELLOW,
        "cooldown": 30,
    },
    {
        "name": "Gun",
        "type": "ranged",
        "damage": 20,
        "range": 0,
        "size": 10,
        "color": ORANGE,
        "cooldown": 30,
    },
    {
        "name": "Flag",
        "type": "melee",
        "damage": 9,
        "range": 75,
        "size": 48,
        "color": FLAG_RED,
        "cooldown": 20,
    },
    {
        "name": "Spear",
        "type": "thrown_spear",
        "damage": 10,
        "splash_damage": 3,
        "splash_chance": 12,
        "splash_range": 162,
        "speed": 13,
        "size": 12,
        "color": SPEAR_COLOR,
        "cooldown": 45,
    },
    {
        "name": "Dual Blades",
        "type": "dash_slash",
        "damage": 18,
        "dash_distance": 140,
        "slash_width": 42,
        "color": DUAL_SLASH,
        "cooldown": 45,
    },
    {
        "name": "Boomerang",
        "type": "returning",
        "damage": 15,
        "speed": 14,
        "return_speed": 16,
        "out_duration": 25,
        "size": 24,
        "color": PURPLE,
        "cooldown": 45,
    },
    {
        "name": "Earthshaker",
        "type": "shockwave",
        "damage": 25,
        "max_radius": 160,
        "expansion_speed": 12,
        "knockback": 40,
        "color": BROWN,
        "cooldown": 60,
    },
]
