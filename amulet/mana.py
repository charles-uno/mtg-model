
"""
Note: for the moment, we only keep track of green and total. Things will
get a lot dicier when we have two colors, neither of which is "better"
than the other.
"""

class Mana(object):

    def __init__(self, expr=""):
        self.green = expr.count("G")
        self.total = self.green + expr.count("U")
        num = expr.replace("G", "").replace("U", "")
        if num:
            self.total += int(num)

    def __str__(self):
        expr = ""
        if self.total > self.green or self.green == 0:
            expr = str(self.total - self.green)
        return expr + self.green*"G"

    def __bool__(self):
        return self.total > 0


    def __sub__(self, other):
        m = Mana()
        m.total = self.total - other.total
        m.green = min(self.green - other.green, m.total)
        return m

    def __add__(self, other):
        m = Mana()
        m.total = self.total + other.total
        m.green = self.green + other.green
        return m

    def __ge__(self, other):
        return self.green >= other.green and self.total >= other.total

    def __le__(self, other):
        return self.green <= other.green and self.total <= other.total
