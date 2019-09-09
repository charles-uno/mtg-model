from . import carddata


def slug(card):
    """Arboreal Grazer -> arboreal_grazer"""
    return rmchars(card, "',").lower().replace(" ", "_").replace("-", "_")


def pretty(*cards, color=True):
    """Turns your hand into something like:
    AmuletofVigor 2*Forest 2*PrimevalTitan RadiantFountain SakuraTribeScout
    """
    blurbs = []
    for card in sorted(set(cards)):
        pretty_card = rmchars(card, "-' ,.")
        if color:

            if carddata.is_colorless(card.rstrip(".")):
                pretty_card = highlight(pretty_card, "brown")
            if carddata.is_green(card.rstrip(".")):
                pretty_card = highlight(pretty_card, "green")
            if carddata.is_blue(card.rstrip(".")):
                pretty_card = highlight(pretty_card, "blue")
            if carddata.is_red(card.rstrip(".")):
                pretty_card = highlight(pretty_card, "red")

        if cards.count(card) > 1:
            blurbs.append(str(cards.count(card)) + "*" + pretty_card)
        else:
            blurbs.append(pretty_card)
    return " ".join(blurbs)


def rmchars(text, chars):
    for c in chars:
        text = text.replace(c, "")
    return text


def tup(*args, **kwargs):
    return tuple(sorted(*args, **kwargs))


def tup_add(seq, *elts):
    return tup(seq + elts)


def tup_sub(seq, *elts):
    new_seq = list(seq)
    [new_seq.remove(x) for x in elts]
    return tup(new_seq)


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




"""
Black        0;30     Dark Gray     1;30
Red          0;31     Light Red     1;31
Green        0;32     Light Green   1;32
Brown/Orange 0;33     Yellow        1;33
Blue         0;34     Light Blue    1;34
Purple       0;35     Light Purple  1;35
Cyan         0;36     Light Cyan    1;36
Light Gray   0;37     White         1;37
"""
