def upgrade_hp(player):

    if player.stat_points > 0:

        player.max_hp += 20
        player.hp = player.max_hp
        player.stat_points -= 1


def upgrade_damage(player):

    if player.stat_points > 0:

        player.damage += 5
        player.stat_points -= 1


def upgrade_speed(player):

    if player.stat_points > 0:

        player.speed += 0.5
        player.stat_points -= 1


def upgrade_armor(player):

    if player.stat_points > 0:

        player.max_armor += 10
        player.armor = player.max_armor
        player.stat_points -= 1