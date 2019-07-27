import random
import yaml

# ----------------------------------------------------------------------

with open("data/cards.yaml") as handle:
    CARDS = yaml.safe_load(handle)

def is_colorless(card):
    return CARDS[card]["is_colorless"]

def is_creature(card):
    return CARDS[card]["is_creature"]

def is_green(card):
    return CARDS[card]["is_green"]

def is_land(card):
    return CARDS[card]["is_land"]

def get_cost(card):
    raw_cost = CARDS[card]["cost"]
    if raw_cost is None:
        return None
    else:
        cost = raw_cost.count("G")
        if len(raw_cost) > cost:
            cost += int(raw_cost.strip("G"))
        return cost

# ----------------------------------------------------------------------

def slug(card):
    return rmchars(card, "'-").lower().replace(" ", "_")

def display(*cards):
    blurbs = []
    for card in sorted(set(cards)):
        blurbs.append(str(cards.count(card)) + "*" + disp(card))
    return " ".join(blurbs)

def disp(card):
    try:
        return CARDS[card]["display"]
    except KeyError:
        return rmchars(card, "-' ")

def rmchars(text, chars):
    for c in chars:
        text = text.replace(c, "")
    return text

# ----------------------------------------------------------------------

def load(name):
    cards = []
    with open(name, "r") as handle:
        for line in handle:
            n, name = line.rstrip().split(None, 1)
            cards += int(n) * [name]
    random.shuffle(cards)
    return cards
