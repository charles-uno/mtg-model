"""
We keep track of green, blue, and total/other. This means we potentially
have to look at multiple ways to pay each cost.
"""


class Mana(object):

    def __init__(self, expr=""):
        self.green = expr.count("G")
        self.blue = expr.count("U")
        self.total = self.green + self.blue
        num = expr.replace("G", "").replace("U", "")
        if num:
            self.total += int(num)

    def __str__(self):
        expr = ""
        colored = self.green + self.blue
        if self.total > colored or colored == 0:
            expr = str(self.total - colored)
        return expr + self.green*"G" + self.blue*"U"

    def __bool__(self):
        return self.total > 0

    def __add__(self, other):
        m = Mana()
        if isinstance(other, str):
            other = Mana(other)
        m.total = self.total + other.total
        m.green = self.green + other.green
        m.blue = self.blue + other.blue
        return m

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
            raise ValueError("Can't pay " + str(cost) + " from " + str(self))
        # Payment with multiple colors is not deterministic. If we start
        # with GGGU and need to pay 1G, we could end up with GG or GU.
        total = self.total - cost.total
        generic_cost = cost.total - cost.green - cost.blue
        generic_self = self.total - self.green - self.blue
        generic_debt = generic_cost - generic_self
        # If we have enough generic sitting around, it's easy
        if generic_debt <= 0:
            m = Mana()
            m.green = self.green - cost.green
            m.blue = self.blue - cost.blue
            m.total = self.total - cost.total
            return {m}
        # If we need more generic than we have, there are options
        manas = set()
        for use_green in range(generic_debt+1):
            m = Mana()
            m.total = self.total - cost.total
            m.green = self.green - cost.green - use_green
            m.blue = self.blue - cost.blue - (generic_debt - use_green)
            # Make sure we're not using more than we have
            if m.green >= 0 and m.blue >= 0:
                manas.add(m)
        return manas
