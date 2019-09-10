import sys
import yaml

from .mana import Mana


with open("carddata.yaml") as handle:
    CARDS = yaml.safe_load(handle)


def best_options(cards):
    """If Ancient Stirrings shows Gemstone Mine and Radiant Fountain,
    there's no reason for the model to ever take Radiant Fountain. This
    has a big impact on performance -- we're kneecapping the exponential
    explosion. Notably, the possibility of multiple Amulets means we do
    sometimes prefer tapped lands over untapped.
    """
    if "Gemstone Mine" in cards:
        cards -= {
            "Forest",
            "Island",
            "Radiant Fountain",
        }
    if "Forest" in cards:
        cards -= {
            "Radiant Fountain",
        }
    if "Island" in cards:
        cards -= {
            "Radiant Fountain",
        }
    if "Khalni Garden" in cards:
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


def lands(cards, best=False):
    """For fetching and searching, we never want to take a worse card.
    But with bounce lands, deciding which land to bounce is nontrivial.
    With a bunch of Amulets on the table, bouncing Khalni Garden can be
    better than bouncing Forest, etc.
    """
    if best:
        return best_options({x for x in set(cards) if is_land(x)})
    else:
        return {x for x in set(cards) if is_land(x)}


def creatures(cards, best=False):
    return {x for x in set(cards) if is_creature(x)}


def creatures_lands(cards, best=False):
    if best:
        return best_options({x for x in set(cards) if is_creature(x) or is_land(x)})
    else:
        return {x for x in set(cards) if is_creature(x) or is_land(x)}

def green_creatures(cards, best=False):
    return {x for x in set(cards) if is_green(x) and is_creature(x)}


def permanents(cards, best=False):
    if best:
        return best_options({x for x in set(cards) if is_permanent(x)})
    else:
        return {x for x in set(cards) if is_permanent(x)}


def colorless(cards, best=False):
    if best:
        return best_options({x for x in set(cards) if is_colorless(x)})
    else:
        return {x for x in set(cards) if is_colorless(x)}


def trinkets(cards, best=False):
    return {x for x in set(cards) if is_artifact(x) and cmc(x) < 2}


def zeros(cards, best=False):
    if best:
        return best_options({x for x in set(cards) if cmc(x) == 0})
    else:
        return {x for x in set(cards) if cmc(x) == 0}


def is_artifact(card):
    return "artifact" in types(card)


def is_basic_land(card):
    return "basic" in types(card) and "land" in types(card)


def is_colorless(card):
    return not CARDS[card].get("color")


def is_creature(card):
    return "creature" in types(card)


def is_blue(card):
    return CARDS[card].get("color") == "blue"


def is_green(card):
    return CARDS[card].get("color") == "green"


def is_red(card):
    return CARDS[card].get("color") == "red"


def is_land(card):
    return "land" in types(card)


def is_permanent(card):
    permanents = ("artifact", "creature", "enchantment", "land")
    return any(x in types(card) for x in permanents)


def cycle_cost(card):
    cost = CARDS[card].get("cycle_cost")
    return cost if cost is None else Mana(cost)


def cycle_verb(card):
    return CARDS[card].get("cycle_verb", "discard")


def sacrifice_cost(card):
    cost = CARDS[card].get("sacrifice_cost")
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
    if CARDS[card].get("taps_for") is None:
        return None
    return [Mana(x) for x in CARDS[card].get("taps_for").split(",")]


def enters_tapped(card):
    return CARDS[card].get("enters_tapped")
