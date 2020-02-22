import collections
import sys
import yaml

from .mana import Mana
from . import helpers


with open("carddata.yaml") as handle:
    CARDS = yaml.safe_load(handle)


class Cards(tuple):

    def __new__(self, names):
        cards = [Card(x) for x in names]
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
        return Cards(list(self) + list(other))

    def __sub__(self, other):
        if isinstance(other, (str, Card)):
            other = (other,)
        new_seq = list(self)
        [new_seq.remove(Card(x)) for x in other]
        return Cards(new_seq)

    def __and__(self, other):
        return Cards(set(self) & set(other))

    def __or__(self, other):
        return self + other

    def __contains__(self, card):
        return tuple.__contains__(self, Card(card))

    def count(self, card):
        return tuple.count(self, Card(card))

    def bounces(self, best=True):
        cards = {x for x in self if "bounce" in x.types}
        return best_cards(cards) if best else Cards(cards)

    def artifacts(self, best=True):
        cards = {x for x in self if "artifact" in x.types}
        return best_cards(cards) if best else Cards(cards)

    def basic_lands(self, best=True):
        cards = {x for x in self if "basic" in x.types and "land" in x.types}
        return best_cards(cards) if best else Cards(cards)

    def colorless(self, best=True):
        cards = {x for x in self if not x.colors}
        return best_cards(cards) if best else Cards(cards)

    def creatures(self, best=True):
        cards = {x for x in self if "creature" in x.types}
        return best_cards(cards) if best else Cards(cards)

    def creatures_lands(self, best=True):
        return self.creatures(best=best) + self.lands(best=best)

    def enchantments(self, best=True):
        cards = {x for x in self if "enchantment" in x.types}
        return best_cards(cards) if best else Cards(cards)

    def forests(self, best=True):
        cards = {x for x in self if "forest" in x.types}
        return best_cards(cards) if best else Cards(cards)

    def lands(self, best=True):
        cards = {x for x in self if "land" in x.types}
        return best_cards(cards) if best else Cards(cards)

    def greens(self, best=True):
        cards = {x for x in self if "green" in x.colors}
        return best_cards(cards) if best else Cards(cards)

    def green_creatures(self, best=True):
        return self.creatures(best=best) & self.greens(best=best)

    def permanents(self, **kwargs):
        return self.creatures(**kwargs) | self.lands(**kwargs) | self.artifacts(**kwargs) | self.enchantments(**kwargs)

    def trinkets(self, best=True):
        cards = {x for x in self if "artifact" in x.types and x.cmc < 2}
        return best_cards(cards) if best else Cards(cards)

    def zeros(self, best=True):
        cards = {x for x in self if x.cmc == 0}
        return best_cards(cards) if best else Cards(cards)


def best_cards(cards):
        """If Ancient Stirrings shows Gemstone Mine and Radiant
        Fountain, there's no reason for the model to ever take Radiant
        Fountain. This has a big impact on performance -- we're
        kneecapping the exponential explosion. Notably, the possibility
        of multiple Amulets means we do sometimes prefer tapped lands
        over untapped.
        """
        cards = set(cards)
        if Card("Blank") in cards:
            cards -= {Card("Blank")}
        if Card("Breeding Pool") in cards:
            cards -= {
                Card("Forest"),
                Card("Island"),
                Card("Radiant Fountain"),
            }
        if Card("Gemstone Mine") in cards:
            cards -= {
                Card("Island"),
                Card("Radiant Fountain"),
            }
        if Card("Forest") in cards:
            cards -= {
                Card("Radiant Fountain"),
            }
        if Card("Island") in cards:
            cards -= {
                Card("Radiant Fountain"),
            }
        if Card("Khalni Garden") in cards:
            cards -= {
                Card("Bojuka Bog"),
            }
        if Card("Tolaria West") in cards:
            cards -= {
                Card("Bojuka Bog"),
            }
        if Card("Simic Growth Chamber") in cards:
            cards -= {
                Card("Selesnya Sanctuary"),
                Card("Boros Garrison"),
            }
        if Card("Selesnya Sanctuary") in cards:
            cards -= {
                Card("Boros Garrison"),
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
            show = helpers.rmchars(name.replace("'", "").title(), "- ,.")
            slug = helpers.slug(name)
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
