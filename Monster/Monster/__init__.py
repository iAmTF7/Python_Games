# Monster Sub-Package - Các loại quái vật
"""
Chứa lớp Monster (base) và các class con: MeleeMonster, RangedMonster.
Thể hiện Kế thừa (Inheritance), Đa hình (Polymorphism), Đóng gói (Encapsulation).
"""

from .base import Monster
from .melee import MeleeMonster
from .ranged import RangedMonster
