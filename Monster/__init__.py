# MonsterCombat Package - Cơ chế Combat của Quái
"""
Package chứa toàn bộ cơ chế combat của quái vật.
Phần của: Thanh (Combat của quái)

Cấu trúc Package theo mô hình OOP:
    MonsterCombat/
    ├── __init__.py          ← File này
    ├── Entity/              ← Sub-Package: Base class
    │   └── base.py          ← Lớp Entity (base class)
    ├── Monster/             ← Sub-Package: Các loại quái
    │   ├── base.py          ← Lớp Monster (kế thừa Entity)
    │   ├── melee.py         ← MeleeMonster (cận chiến)
    │   └── ranged.py        ← RangedMonster (tầm xa)
    ├── Combat/              ← Sub-Package: Cơ chế chiến đấu
    │   ├── projectile.py    ← Đạn ma thuật
    │   └── spawner.py       ← Spawn + Factory Pattern
    └── Config/              ← Sub-Package: Cấu hình
        └── settings.py      ← Hằng số, màu sắc

OOP Principles:
    - Kế thừa (Inheritance):     Entity → Monster → MeleeMonster/RangedMonster
    - Đóng gói (Encapsulation):  _private attributes + @property
    - Đa hình (Polymorphism):    attack(), move_towards(), draw()
    - Trừu tượng (Abstraction):  Monster.attack() abstract-like
    - Factory Pattern:           MonsterSpawner.create_monster()
"""

__version__ = "1.0.0"
__author__ = "Thanh"
__part__ = "Combat của quái"
