"""
We keep track of green, blue, and total/other. This means we potentially
have to look at multiple ways to pay each cost.
"""

import collections
import itertools

from . import helpers

ManaBase = collections.namedtuple("Mana", "green total")

class Mana(ManaBase):

    def __new__(cls, expr=""):
        if isinstance(expr, tuple):
            return ManaBase.__new__(cls, *expr)
        # All other colors of mana get cast as colorless. Also allow C as a
        # single colorless mana.
        green, total = 0, 0
        for c in expr:
            if c == "G":
                green += 1
            if c.isdigit():
                total += int(c)
            else:
                total += 1
        return ManaBase.__new__(cls, green, total)

    def __add__(self, other):
        if isinstance(other, str):
            other = Mana(other)
        return Mana((self.green + other.green, self.total + other.total))

    def name(self):
        if self.total == 0:
            return "0"
        if self.total > self.green:
            return str(self.total - self.green) + "G"*self.green
        else:
            return "G"*self.green

    def __str__(self):
        return "\033[0;35m" + self.name() + "\033[0m"

    def __repr__(self):
        return "Mana(" + repr(self.name()) + ")"

    def __bool__(self):
        return self.total > 0

    def __ge__(self, other):
        return self.green >= other.green and self.total >= other.total

    def __le__(self, other):
        return self.green <= other.green and self.total <= other.total

    def __sub__(self, other):
        """Only works for paying exactly. Does not allow you to pay a
        generic cost with colored mana.
        """
        if isinstance(other, str):
            other = Mana(other)
        if not self >= other:
            raise ValueError(f"illegal subtraction: {self} - {other}")
        total = self.total - other.total
        green = min(total, self.green - other.green)
        return Mana((green, total))

    def minus(self, cost):
        """Accept a mana cost. Return a list of potential pools
        remaining after paying that cost.
        """
        if isinstance(cost, str):
            cost = Mana(cost)
        if not cost <= self:
            return set()
        return {self - cost}
