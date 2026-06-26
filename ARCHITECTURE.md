# Refactored OOP architecture

This project keeps the original gameplay mechanisms intact while standardizing the major modules around the same shape:

- `config.py` / `constants.py` for data and tuning values.
- `base.py` / entity files for object models and abstract-ish contracts.
- `system.py` for game-loop adapters/managers.
- `legacy.py` for backward-compatible module functions and globals.
- `__init__.py` for stable public exports.

The old import paths are intentionally preserved where practical. For example, `from map import TileMap`, `from item.drop import create_drop`, `from level.stats import upgrade_hp`, and `from weapon.weapons import WeaponSystem` still work.

The most important rule for this refactor was behavior preservation: stats, damage values, item probabilities, level-up math, map generation rules, movement/collision behavior, monster AI, and weapon mechanics were kept as close to the uploaded project as possible.
