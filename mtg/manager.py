import random
import time

from . import state, output


def simulate(name, trial=0, max_turns=4):
    # Keep track of the initial game state. If we fail to converge, this
    # is what we'll return so we know if we were on the play or draw.
    starttime = time.time()
    gs0 = state.GameState(
        deck_list=load_deck(name),
        on_the_play=random.randrange(2),
        reset_clock=True,
    ).draw(7)
    # Keep track of the initial game state in case we hit an overflow
    gs = gs0.pass_turn()
    try:
        for turn in range(max_turns):
            gs = gs.next_turn()
    except state.TooManyStates:
        gs = gs0.overflow()
    tally = str(trial).ljust(5)
    # If we found a solution or overflowed, we'll have just one state.
    # Multiple states means there's no solution.
    dt = time.time() - starttime
    if len(gs) == 1 and gs.done:
        output.save(name, gs.summary)
        print(tally, name.ljust(12), gs.summary, gs.performance)
    else:
        output.save(name, gs0.summary)
        print(tally, name.ljust(12), gs0.summary, gs0.performance)
    # For debug runs, print and bail as soon as a trial works
    if len(gs) == 1 and gs.turn:
        return gs.report()


def load_deck(deckname):
    path = f"decks/{deckname}.in"
    cardnames = []
    with open(path, "r") as handle:
        for line in handle:
            if not line.strip() or line.startswith("#"):
                continue
            line = line.split("#")[0]
            n, cardname = line.rstrip().split(None, 1)
            cardnames += int(n) * [cardname]
    if len(cardnames) != 60:
        print("WARNING:", len(cardnames), "in", deckname)
    random.shuffle(cardnames)
    return cardnames
