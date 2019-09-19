import collections
import sys
import yaml

from .mana import Mana


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
        if isinstance(other, (str, Card)):
            other = [other]
        return Cards(sorted(list(self) + list(other)))



    def __sub__(self, other):
        if isinstance(other, (str, Card)):
            other = (other,)
        new_seq = list(self)
        [new_seq.remove(Card(x)) for x in other]
        return Cards(sorted(new_seq))


    @property
    def creatures(self):
        return {x for x in self if x.is_creature}

    @property
    def basic_lands(self):
        return {x for x in self if x.is_basic_land}

    @property
    def lands(self):
        """For fetching and searching, we never want to take a worse
        card. But with bounce lands, deciding which land to bounce is
        nontrivial. With a bunch of Amulets on the table, bouncing
        Khalni Garden can be better than bouncing Forest, etc.
        """
        return {x for x in self if x.is_land}

    @property
    def creatures_lands(self):
        return {x for x in self if x.is_creature or x.is_land}

    @property
    def green_creatures(self):
        return {x for x in self if x.is_green and x.is_creature}

    @property
    def permanents(self):
        return {x for x in self if x.is_permanent}

    @property
    def colorless(self):
        return {x for x in self if x.is_colorless}

    @property
    def trinkets(self):
        return {x for x in self if x.is_artifact and x.cmc < 2}

    @property
    def zeros(self):
        return {x for x in self if x.cmc == 0}










CardBase = collections.namedtuple("CardBase", "name slug show")



class Card(CardBase):

    _instances = {}

    def __new__(cls, name):
        if isinstance(name, Card):
            return name
        if name not in cls._instances:
            slug = rmchars(name, "',").lower().replace(" ", "_").replace("-", "_")
            show = rmchars(name, "-' ,.")
            cls._instances[name] = CardBase.__new__(cls, name, slug, show)
        return cls._instances[name]

    def __repr__(self):
        return "Card(" + repr(self.name) + ")"

    def __str__(self):
        if self.is_green:
            return highlight(self.show, "green")
        elif self.is_colorless:
            return highlight(self.show, "brown")
        elif self.is_blue:
            return highlight(self.show, "blue")
        elif self.is_red:
            return highlight(self.show, "red")
        else:
            return self.show

    # TODO -- Generate the fields in the named tuple dynamically so we don't have to spell this all out.


    @property
    def is_artifact(self):
        return "artifact" in self.types

    @property
    def is_basic_land(self):
        return "basic" in self.types and "land" in self.types

    @property
    def is_blue(self):
        return "blue" in self.colors

    @property
    def is_colorless(self):
        return not self.colors

    @property
    def is_creature(self):
        return "creature" in self.types

    @property
    def is_green(self):
        return "green" in self.colors

    @property
    def is_land(self):
        return "land" in self.types

    @property
    def is_permanent(self):
        types = ("artifact", "creature", "enchantment", "land")
        return any(x in self.types for x in types)

    @property
    def is_red(self):
        return "red" in self.colors


    @property
    def colors(self):
        colors = CARDS[self.name].get("color")
        return colors.split(",") if colors else ()

    @property
    def types(self):
        return set(CARDS[self.name]["type"].split(","))

    @property
    def cycle_cost(self):
        cost = CARDS[self.name].get("cycle_cost")
        return cost if cost is None else Mana(cost)

    @property
    def cycle_verb(self):
        return CARDS[self.name].get("cycle_verb", "discard")

    @property
    def sacrifice_cost(self):
        cost = CARDS[self.name].get("sacrifice_cost")
        return cost if cost is None else Mana(cost)

    @property
    def cost(self):
        try:
            cost = CARDS[self.name].get("cost")
        except KeyError:
            print(self, repr(self))
            raise
        return cost if cost is None else Mana(cost)

    @property
    def cmc(self):
        if self.cost is None:
            return 0
        else:
            return self.cost.total

    @property
    def taps_for(self):
        if CARDS[self.name].get("taps_for") is None:
            return None
        return [Mana(x) for x in CARDS[self.name].get("taps_for").split(",")]

    def enters_tapped(self):
        return CARDS[self.name].get("enters_tapped")






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




def rmchars(text, chars):
    for c in chars:
        text = text.replace(c, "")
    return text
