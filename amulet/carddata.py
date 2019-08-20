import random
import sys
import yaml

from . import mana


with open("carddata.yaml") as handle:
    CARDS = yaml.safe_load(handle)


def basic_lands(cards):
    return {x for x in set(cards) if is_basic_land(x)}


def lands(cards):
    return {x for x in set(cards) if is_land(x)}


def creatures(cards):
    return {x for x in set(cards) if is_creature(x)}


def creatures_lands(cards):
    return {x for x in set(cards) if is_creature(x) or is_land(x)}


def green_creatures(cards):
    return {x for x in set(cards) if is_green(x) and is_creature(x)}


def permanents(cards):
    return {x for x in set(cards) if is_permanent(x)}


def colorless(cards):
    return {x for x in set(cards) if is_colorless(x)}


def trinkets(cards):
    return {x for x in set(cards) if is_artifact(x) and cmc(x) < 2}


def zeros(cards):
    return {x for x in set(cards) if cmc(x) == 0}


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


def activation_cost(card):
    cost = CARDS[card].get("activation_cost")
    return cost if cost is None else mana.Mana(cost)


def cost(card):
    cost = CARDS[card].get("cost")
    return cost if cost is None else mana.Mana(cost)


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
    return [mana.Mana(x) for x in CARDS[card].get("taps_for").split(",")]


def enters_tapped(card):
    return CARDS[card].get("enters_tapped")


def slug(card):
    return rmchars(card, "',").lower().replace(" ", "_").replace("-", "_")


def display(*cards):
    blurbs = []
    for card in sorted(set(cards)):
        if cards.count(card) > 1:
            blurbs.append(str(cards.count(card)) + "*" + disp(card))
        else:
            blurbs.append(disp(card))
    return " ".join(blurbs)


def disp(card):
    return rmchars(card, "-' ,.")


def rmchars(text, chars):
    for c in chars:
        text = text.replace(c, "")
    return text
