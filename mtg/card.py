import collections
import sys
import yaml

from .mana import Mana
from . import helpers


with open("carddata.yaml") as handle:
    CARDS = yaml.safe_load(handle)


class Cards(tuple):

    def __new__(self, names, sort=True):
        cards = [Card(x) for x in names]
        if sort:
            cards = sorted(cards)
        return tuple.__new__(self, cards)

    def __str__(self):
        blurbs = []
        for card in sorted(set(self)):
            n = self.count(card)
            if n > 1:
                blurbs.append(f"{n}*{card}")
            else:
                blurbs.append(str(card))
        return " ".join(blurbs)

    def __add__(self, other):
        if isinstance(other, str):
            other = Card(other)
        if isinstance(other, Card):
            other = [other]
        return Cards(sorted(list(self) + list(other)))

    def __sub__(self, other):
        if isinstance(other, (str, Card)):
            other = (other,)
        new_seq = list(self)
        [new_seq.remove(Card(x)) for x in other]
        return Cards(sorted(new_seq))

    def __contains__(self, card):
        return tuple.__contains__(self, Card(card))

    def count(self, card):
        return tuple.count(self, Card(card))

    @property
    def basic_lands(self):
        return {x for x in self if "basic" in x.types and "land" in x.types}

    @property
    def colorless(self):
        return {x for x in self if not x.colors}

    @property
    def creatures(self):
        return {x for x in self if "creature" in x.types}

    @property
    def creatures_lands(self):
        return self.creatures | self.lands

    @property
    def lands(self):
        return {x for x in self if "land" in x.types}

    @property
    def greens(self):
        return {x for x in self if "green" in x.colors}

    @property
    def green_creatures(self):
        return {x for x in self.creatures & self.greens}

    @property
    def permanents(self):
        types = ("artifact", "creature", "enchantment", "land")
        return {x for x in self if any(t in x.types for t in types)}

    @property
    def trinkets(self):
        return {x for x in self if "artifact" in x.types and x.cmc < 2}

    @property
    def zeros(self):
        return {x for x in self if x.cmc == 0}

    @property
    def best(self):
        """If Ancient Stirrings shows Gemstone Mine and Radiant
        Fountain, there's no reason for the model to ever take Radiant
        Fountain. This has a big impact on performance -- we're
        kneecapping the exponential explosion. Notably, the possibility
        of multiple Amulets means we do sometimes prefer tapped lands
        over untapped.
        """
        cards = set(self)
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
        return Cards(cards)


# ----------------------------------------------------------------------


CardBase = collections.namedtuple("CardBase", "name show slug")


class Card(CardBase):

    _instances = {}

    def __new__(cls, name):
        if isinstance(name, Card):
            return name
        if name not in cls._instances:
            show = helpers.rmchars(name, "-' ,.")
            slug = helpers.rmchars(name, "',").lower().replace(" ", "_").replace("-", "_")
            cls._instances[name] = CardBase.__new__(cls, name, show, slug)
        return cls._instances[name]

    def __repr__(self):
        return "Card(" + repr(self.name) + ")"

    def __str__(self):
        if "green" in self.colors:
            return highlight(self.show, "green")
        elif not self.colors:
            return highlight(self.show, "brown")
        elif "blue" in self.colors:
            return highlight(self.show, "blue")
        elif "red" in self.colors:
            return highlight(self.show, "red")
        else:
            return self.show

    def __hash__(self):
        return tuple.__hash__(self)

    def __eq__(self, other):
        if isinstance(other, str):
            return other == self.name
        else:
            return other.name == self.name


    @property
    def colors(self):
        raw_colors = CARDS[self.name].get("color")
        return raw_colors.split(",") if raw_colors else ()

    @property
    def types(self):
        return CARDS[self.name]["type"].split(",")

    @property
    def cost(self):
        cost = CARDS[self.name].get("cost")
        return None if cost is None else Mana(cost)

    @property
    def cmc(self):
        cost = CARDS[self.name].get("cost")
        return 0 if cost is None else Mana(cost).total

    @property
    def types(self):
        return CARDS[self.name]["type"].split(",")

    @property
    def cycle_cost(self):
        cost = CARDS[self.name].get("cycle_cost")
        return None if cost is None else Mana(cost)

    @property
    def cycle_verb(self):
        return CARDS[self.name].get("cycle_verb", "discard")

    @property
    def enters_tapped(self):
        return CARDS[self.name].get("enters_tapped")

    @property
    def sacrifice_cost(self):
        cost = CARDS[self.name].get("sacrifice_cost")
        return None if cost is None else Mana(cost)

    @property
    def taps_for(self):
        taps_for = CARDS[self.name].get("taps_for")
        if taps_for is None:
            return None
        else:
            return {Mana(x) for x in taps_for.split(",")}


def highlight(text, color=None):
    if color == "green":
        return "\033[32m" + text + "\033[0m"
    if color == "blue":
        return "\033[36m" + text + "\033[0m"
    if color == "brown":
        return "\033[33m" + text + "\033[0m"
    if color == "red":
        return "\033[31m" + text + "\033[0m"
    return text
