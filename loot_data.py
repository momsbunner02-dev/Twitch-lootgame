import random

LOOT_POOLS = {
    "common": ["Glorpshake","GuangGuang Bible","alienboogie"],
    "uncommon": ["Glorpscheme","glorpshiz","glorppray"],
    "rare": ["soul sword","glorp glasses","glorp gun"],
    "epic": ["glorptwerk","glorp griddy","glorp rainbow"],
    "legendary": ["GLORIOUS GLORP","glorp miku","glorp doobie"]
}

RARITY_STATS = {
    "common": {"atk":1,"def":1,"hp":5},
    "uncommon": {"atk":2,"def":2,"hp":10},
    "rare": {"atk":3,"def":3,"hp":15},
    "epic": {"atk":5,"def":5,"hp":25},
    "legendary": {"atk":8,"def":8,"hp":50}
}

def generate_loot():
    rarity_roll = random.choices(
        ["common","uncommon","rare","epic","legendary"],
        weights=[50,25,15,7,3],
        k=1
    )[0]
    item = random.choice(LOOT_POOLS[rarity_roll])
    return item, rarity_roll
