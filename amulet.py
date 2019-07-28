#!/usr/bin/env python3

import amulet

# ----------------------------------------------------------------------

def main():
    manager = amulet.GameStateManager("decks/debug.in")

    done_state = None
    while done_state is None and manager.turn < 4:

        try:
            done_state = manager.next_turn()
        except amulet.TooManyStates:
            print("- too many states")

    if done_state:
        done_state.report()
        print(done_state.summary())

    else:
        def key(x): return len(x.lines)
        sorted(manager.states, key=key)[-1].report()
        print("- no solution")


# ----------------------------------------------------------------------

if __name__ == "__main__":
    main()
