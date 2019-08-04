import random
import sys
import yaml

from . import mana

# ----------------------------------------------------------------------

with open("data/cards.yaml") as handle:
    CARDS = yaml.safe_load(handle)

def get_types(card):
    try:
        return CARDS[card]["type"].split(",")
    except KeyError:
        print("Missing types for:", card)
        sys.exit(1)

def is_artifact(card):
    return "artifact" in get_types(card)

def is_basic_land(card):
    return "basic" in get_types(card) and "land" in get_types(card)

def is_colorless(card):
    return not CARDS[card].get("color")

def is_creature(card):
    return "creature" in get_types(card)

def is_green(card):
    return CARDS[card].get("color") == "green"

def is_land(card):
    return "land" in get_types(card)

def is_permanent(card):
    return any( t in get_types(card) for t in ("artifact", "creature", "enchantment", "land") )

def get_activation_cost(card):
    cost = CARDS[card].get("activation_cost")
    return cost if cost is None else mana.Mana(cost)

def get_cost(card):
    cost = CARDS[card].get("cost")
    return cost if cost is None else mana.Mana(cost)

def get_cmc(card):
    cost = get_cost(card)
    if cost is None:
        return 0
    else:
        return cost.total

def taps_for(card):
    return [ mana.Mana(x) for x in CARDS[card].get("taps_for").split(",") ]

def enters_tapped(card):
    return CARDS[card].get("enters_tapped")

# ----------------------------------------------------------------------

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

# ----------------------------------------------------------------------

def load(name):
    path = "decks/%s.in" % name
    cards = []
    with open(path, "r") as handle:
        for line in handle:
            if not line.strip() or line.startswith("#"):
                continue
            n, name = line.rstrip().split(None, 1)
            cards += int(n) * [name]
    random.shuffle(cards)
    return cards
