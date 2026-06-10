class Player:

    def __init__(self):

        # Level
        self.level = 1
        self.exp = 0
        self.exp_need = 100
        self.stat_points = 0

        # Stats
        self.max_hp = 100
        self.hp = 100

        self.max_armor = 50
        self.armor = 50

        self.max_energy = 100
        self.energy = 100

        self.damage = 25
        self.speed = 6

        # Regen
        self.hp_regen = 0
        self.armor_regen = 0
        self.energy_regen = 0

        # Special Items
        self.special_items = []

        # Buff
        self.haste_timer = 0
        self.iron_skin_timer = 0
        self.berserk_timer = 0