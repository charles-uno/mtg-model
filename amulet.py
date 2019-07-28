#!/usr/bin/env python3

import amulet

# ----------------------------------------------------------------------

def main():

    name = "debug"

    infile = "decks/%s.in" % name
    outfile = "out/%s.out" % name

    manager = amulet.GameStateManager(infile)

    done_state = None
    while done_state is None and manager.turn < 4:

        try:
            done_state = manager.next_turn()
        except amulet.TooManyStates:
            save("- too many states", outfile)

    if done_state:
        done_state.report()
        print(done_state.summary())

    else:
        def key(x): return len(x.lines)
        sorted(manager.states, key=key)[-1].report()
        save("- no solution", outfile)

# ----------------------------------------------------------------------

def save(line, path):
    print(line)
    with open(path, "a") as handle:
        handle.write(line + "\n")

# ----------------------------------------------------------------------

if __name__ == "__main__":
    main()
