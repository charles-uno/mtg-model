"""
We keep track of green, blue, and total/other. This means we potentially
have to look at multiple ways to pay each cost.
"""

import collections

ManaBase = collections.namedtuple("Mana", "blue green total")

class Mana(ManaBase):

    def __new__(cls, expr=""):
        if isinstance(expr, tuple):
            return ManaBase.__new__(cls, *expr)
        blue = expr.count("U")
        green = expr.count("G")
        total = green + blue
        num = expr.replace("G", "").replace("U", "")
        if num:
            total += int(num)
        return ManaBase.__new__(cls, blue, green, total)

    def __add__(self, other):
        if isinstance(other, str):
            other = Mana(other)
        total = self.total + other.total
        green = self.green + other.green
        blue = self.blue + other.blue
        return Mana((blue, green, total))

    def __str__(self):
        expr = ""
        colored = self.green + self.blue
        if self.total > colored or colored == 0:
            expr = str(self.total - colored)
        return "\033[0;35m" + expr + self.green*"G" + self.blue*"U" + "\033[0m"

    def __repr__(self):
        return "Mana(" + repr(str(self)) + ")"

    def __bool__(self):
        return self.total > 0

    def __ge__(self, other):
        return (
            self.green >= other.green and
            self.blue >= other.blue and
            self.total >= other.total
        )

    def __le__(self, other):
        return (
            self.green <= other.green and
            self.blue <= other.blue and
            self.total <= other.total
        )

    def minus(self, cost):
        """Accept a mana cost. Return a list of potential pools
        remaining after paying that cost.
        """
        if not cost <= self:
            return set()
        # Payment with multiple colors is not deterministic. If we start
        # with GGGU and need to pay 1G, we could end up with GG or GU.
        total = self.total - cost.total
        generic_cost = cost.total - cost.green - cost.blue
        generic_self = self.total - self.green - self.blue
        generic_debt = generic_cost - generic_self
        # If we have enough generic sitting around, it's easy
        if generic_debt <= 0:
            blue = self.blue - cost.blue
            green = self.green - cost.green
            total = self.total - cost.total
            return [Mana((blue, green, total))]
        # If we need more generic than we have, there are options
        manas = set()
        for use_green in range(generic_debt+1):
            blue = self.blue - cost.blue - (generic_debt - use_green)
            green = self.green - cost.green - use_green
            total = self.total - cost.total
            # Make sure we're not using more than we have
            if green >= 0 and blue >= 0:
                manas.add(Mana((blue, green, total)))
        return manas
