import sys
import yaml

from .mana import Mana


with open("carddata.yaml") as handle:
    CARDS = yaml.safe_load(handle)


def best_options(cards):
    """If Ancient Stirrings shows Gemstone Mine and Radiant Fountain,
    there's no reason for the model to ever take Radiant Fountain. This
    has a big impact on performance -- we're kneecapping the exponential
    explosion. 
    """
    if "Gemstone Mine" in cards:
        cards -= {
            "Forest",
            "Island",
            "Khalni Garden",
            "Radiant Fountain",
            "Bojuka Bog",
        }
    if "Forest" in cards:
        cards -= {
            "Khalni Garden",
            "Radiant Fountain",
            "Bojuka Bog",
        }
    if "Island" in cards:
        cards -= {
            "Radiant Fountain",
            "Bojuka Bog",
        }
    if "Khalni Garden" in cards:
        cards -= {
            "Bojuka Bog",
        }
    if "Radiant Fountain" in cards:
        cards -= {
            "Bojuka Bog",
        }
    if "Simic Growth Chamber" in cards:
        cards -= {
            "Selesnya Sanctuary",
            "Boros Garrison",
        }
    if "Selesnya Sanctuary" in cards:
        cards -= {
            "Boros Garrison",
        }
    return cards


def basic_lands(cards):
    return {x for x in set(cards) if is_basic_land(x)}


def lands(cards):
    return best_options({x for x in set(cards) if is_land(x)})


def creatures(cards):
    return {x for x in set(cards) if is_creature(x)}


def creatures_lands(cards):
    return best_options({x for x in set(cards) if is_creature(x) or is_land(x)})


def green_creatures(cards):
    return {x for x in set(cards) if is_green(x) and is_creature(x)}


def permanents(cards):
    return best_options({x for x in set(cards) if is_permanent(x)})


def colorless(cards):
    return best_options({x for x in set(cards) if is_colorless(x)})


def trinkets(cards):
    return {x for x in set(cards) if is_artifact(x) and cmc(x) < 2}


def zeros(cards):
    return best_options({x for x in set(cards) if cmc(x) == 0})


def is_artifact(card):
    return "artifact" in types(card)


def is_basic_land(card):
    return "basic" in types(card) and "land" in types(card)


def is_colorless(card):
    return not CARDS[card].get("color")


def is_creature(card):
    return "creature" in types(card)


def is_green(card):
    return CARDS[card].get("color") == "green"


def is_land(card):
    return "land" in types(card)


def is_permanent(card):
    permanents = ("artifact", "creature", "enchantment", "land")
    return any(x in types(card) for x in permanents)


def discard_cost(card):
    cost = CARDS[card].get("discard_cost")
    return cost if cost is None else Mana(cost)


def cost(card):
    cost = CARDS[card].get("cost")
    return cost if cost is None else Mana(cost)


def cmc(card):
    if cost(card) is None:
        return 0
    else:
        return cost(card).total


def types(card):
    try:
        return CARDS[card]["type"].split(",")
    except KeyError:
        print("Missing types for:", card)
        sys.exit(1)


def taps_for(card):
    if not CARDS[card].get("taps_for"):
        return None
    return [Mana(x) for x in CARDS[card].get("taps_for").split(",")]


def enters_tapped(card):
    return CARDS[card].get("enters_tapped")
