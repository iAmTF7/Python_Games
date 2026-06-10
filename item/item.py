import random

class Item:

    def __init__(self, player):

        special_types = [
            "regen_hp",
            "regen_armor",
            "regen_energy"
        ]

        owned = player.special_items.copy()

        if random.random() < 0.02:

            possible = [
                t for t in special_types
                if t not in owned
            ]

            if possible:
                self.type = random.choice(possible)
            else:
                self.type = random.choice(
                    ["heal","armor","energy"]
                )

        else:

            r = random.random()

            if r < 0.34:
                self.type = "heal"

            elif r < 0.67:
                self.type = "armor"

            else:
                self.type = "energy"