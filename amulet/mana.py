
# For the moment, just look at scalars
def Mana(expr=""):
    if expr is None:
        return None
    m = expr.count("G")
    if len(expr) > m:
        m += int(expr.strip("G"))
    return m
