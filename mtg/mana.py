"""
We keep track of green, blue, and total/other. This means we potentially
have to look at multiple ways to pay each cost.
"""

import collections
import itertools

from . import helpers


IGNORE_COLORS = ("W", "B", "R")


ManaBase = collections.namedtuple("Mana", "wubrg total")

class Mana(ManaBase):

    def __new__(cls, expr=""):
        if isinstance(expr, tuple):
            return ManaBase.__new__(cls, *expr)
        # For colors we ignore, swap out that mana symbol for a "1"
        for ic in IGNORE_COLORS:
            expr = expr.replace(ic, "1")
        wubrg = tuple(expr.count(m) for m in "WUBRG")
        # Total comes from colored mana as well as generic (or ignored). Sum
        # each digit individually. Multi-digit numbers are not allowed.
        total = sum(wubrg) + sum(int(c) for c in expr if c.isdigit())
        # Optimization: do we really need to track more than 3 mana per color?
#        wubrg = tuple(min(x, 3) for x in wubrg)
        return ManaBase.__new__(cls, wubrg, total)

    @property
    def colored(self):
        return sum(self.wubrg)

    @property
    def colorless(self):
        return self.total - self.colored

    def __add__(self, other):
        if isinstance(other, str):
            other = Mana(other)
        wubrg = tuple(s+o for s, o in zip(self.wubrg, other.wubrg))
        # Optimization: do we really need to track more than 3 mana per color?
#        wubrg = tuple(min(x, 3) for x in wubrg)
        total = self.total + other.total
        return Mana((wubrg, total))

    def name(self):
        expr = ""
        if self.colorless or not self.colored:
            expr = str(self.colorless)
        for n, m in zip(self.wubrg, "WUBRG"):
            expr += n*m
        return expr

    def __str__(self):
        return helpers.highlight(self.name(), "magenta")

    def __repr__(self):
        return "Mana(" + repr(self.name()) + ")"

    def __bool__(self):
        return self.total > 0

    def __ge__(self, other):
        return all(s >= o for s, o in zip(self.wubrg, other.wubrg)) and self.total >= other.total

    def __le__(self, other):
        return all(s <= o for s, o in zip(self.wubrg, other.wubrg)) and self.total <= other.total

    def __sub__(self, other):
        """Only works for paying exactly. Does not allow you to pay a
        generic cost with colored mana.
        """
        if isinstance(other, str):
            other = Mana(other)
        wubrg = tuple(s-o for s, o in zip(self.wubrg, other.wubrg))
        total = self.total - other.total
        if any(x<0 for x in wubrg) or self.colorless < other.colorless:
            raise ValueError(f"ambiguous subtraction {self} - {other}")
        return Mana((wubrg, total))

    def minus(self, cost):
        """Accept a mana cost. Return a list of potential pools
        remaining after paying that cost.
        """
        if isinstance(cost, str):
            cost = Mana(cost)
        if not cost <= self:
            return set()
        # If we can subtract unambiguously, do so. If we make it past
        # here, we know we do not have enough colorless mana to cover
        # the generic cost -- to the resulting mana pool will have zero
        # colorless mana.
        try:
            return {self - cost}
        except ValueError:
            pass
        # How much generic cost do we need to pay with colored mana?
        to_pay = max(cost.colorless - self.colorless, 0)
        # What colored mana do we have sitting around?
        wubrg = [s-c for s, c in zip(self.wubrg, cost.wubrg)]
        spare_mana_str = "".join(n*m for n, m in zip(wubrg, "WUBRG"))
        spare_mana = Mana(spare_mana_str)
        manas = set()
        for m in itertools.combinations(spare_mana_str, to_pay):
            leftover = spare_mana - Mana("".join(m))
            manas.add(leftover)
        return manas
