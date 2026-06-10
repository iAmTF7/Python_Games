import random
from .item import Item


def create_drop(player):

    if random.random() < 0.6:
        return Item(player)

    return None


def pickup_item(player, item):

    if item is None:
        return

    if item.type == "heal":

        player.hp = min(
            player.max_hp,
            player.hp + 20
        )

    elif item.type == "armor":

        player.armor = min(
            player.max_armor,
            player.armor + 20
        )

    elif item.type == "energy":

        player.energy = min(
            player.max_energy,
            player.energy + 30
        )

    elif item.type == "regen_hp":

        if item.type not in player.special_items:

            player.hp_regen = 0.2
            player.special_items.append(item.type)

    elif item.type == "regen_armor":

        if item.type not in player.special_items:

            player.armor_regen = 0.2
            player.special_items.append(item.type)

    elif item.type == "regen_energy":

        if item.type not in player.special_items:

            player.energy_regen = 0.25
            player.special_items.append(item.type)