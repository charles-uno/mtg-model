import random
import time

from . import state, output


def simulate(name, max_turns=4):
    print("starting a run on", name)

    # Keep track of the initial game state. If we fail to converge, this
    # is what we'll return so we know if we were on the play or draw.
    starttime = time.time()
    gs0 = state.GameState(
        deck_list=load_deck(name),
        on_the_play=random.randrange(2),
        reset_clock=True,
    ).draw(7)
    # Draw opening hand and start turn 1.
    gs = gs0.pass_turn()
    try:
        for turn in range(max_turns):
            gs = gs.next_turn()
    except state.TooManyStates:
        gs = gs0.overflow()
    # If we found a solution or overflowed, we'll have just one state.
    # Multiple states means there's no solution.
    dt = time.time() - starttime
    if len(gs) != 1 or not gs.done:
        output.save(name, gs0.summary)
        print(name.ljust(12), gs0.summary, gs0.performance)
    else:
        output.save(name, gs.summary)
        print(name.ljust(12), gs.summary, gs.performance)
    # For debug runs, print and bail as soon as a trial works
    if len(gs) == 1 and gs.turn:
#        gs.report()
        return True


def load_deck(deckname):
    path = f"decks/{deckname}.in"
    cardnames = []
    with open(path, "r") as handle:
        for line in handle:
            if not line.strip() or line.startswith("#"):
                continue
            n, cardname = line.rstrip().split(None, 1)
            cardnames += int(n) * [cardname]
    random.shuffle(cardnames)
    return cardnames
