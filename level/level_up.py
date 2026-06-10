class LevelSystem:

    def __init__(self, player):

        self.player = player

    def add_exp(self, amount):

        self.player.exp += amount

        while self.player.exp >= self.player.exp_need:

            self.player.exp -= self.player.exp_need

            self.player.level += 1
            self.player.stat_points += 1

            self.player.exp_need = int(
                self.player.exp_need * 1.3
            )

            self.player.hp = self.player.max_hp
            self.player.armor = self.player.max_armor

            return True

        return False