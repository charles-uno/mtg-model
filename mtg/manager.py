import random
import time

from . import state, output, helpers


def simulate(name, trial=0, max_turns=4, opponent=False):
    # Keep track of the initial game state. If we fail to converge, this
    # is what we'll return so we know if we were on the play or draw.
    starttime = time.time()
    on_the_play = bool(random.randrange(2))
    gs0 = state.GameState(
        deck_list=load_deck(name),
        on_the_play=on_the_play,
        reset_clock=True,
        opponent=opponent,
    ).draw(7)
    # Keep track of data turn-by-turn. If we hit an overflow while computing
    # turn 4, we at least know there are no solutions for turn 3.
    summary = {"on_the_play": on_the_play, "turns": {}, "opponent": opponent}
    # Keep track of the initial game state in case we hit an overflow
    gs = gs0.pass_turn()
    try:
        for turn in range(1, max_turns+1):
            gs = gs.next_turn(max_turns=max_turns)
            # Internally, we keep track of whether or not this titan can have
            # haste. But if we want to store that data, we'll need to come back
            # and re-finagle the data structure.
            if gs.done:
                summary["turns"][str(turn)] = True
            else:
                summary["turns"][str(turn)] = False
    except state.TooManyStates:
        for t in range(turn, max_turns+1):
            summary["turns"][str(turn)] = None
        gs = gs0.overflow()
    tally = str(trial).ljust(5)
    # If we found a solution or overflowed, we'll have just one state.
    # Multiple states means there's no solution.
    dt = time.time() - starttime
    if len(gs) == 1 and gs.done:
        output.save(name, summary)
        print(tally, name.ljust(12), summarize(summary), gs.performance)
        return gs.pop().report()
    else:
        output.save(name, summary)
        print(tally, name.ljust(12), summarize(summary), gs0.performance)
        return None


def summarize(summary):
    play_draw = "on the play" if summary["on_the_play"] else "on the draw"
    for turn, outcome in summary["turns"].items():
        if outcome is True:
            return f"turn {turn} " + helpers.highlight("titan", "green") + f" {play_draw}"
        elif outcome is None:
            return f"turn {turn} " + helpers.highlight("OVERFLOW", "red") + f" {play_draw}"
    return f"turn {turn} " + helpers.highlight("whiff", "brown") + f" {play_draw}"


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
