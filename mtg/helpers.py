def slug(card):
    """Arboreal Grazer -> arboreal_grazer"""
    return rmchars(card, "',").lower().replace(" ", "_").replace("-", "_")

def pretty(*cards):
    """Turns your hand into something like:
    AmuletofVigor 2*Forest 2*PrimevalTitan RadiantFountain SakuraTribeScout
    """
    blurbs = []
    for card in sorted(set(cards)):
        pretty_card = rmchars(card, "-' ,.")
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

def tup_add(seq, elt):
    return tup(seq + (elt,))

def tup_sub(seq, elt):
    new_seq = list(seq)
    new_seq.remove(elt)
    return tup(new_seq)
