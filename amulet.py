#!/usr/bin/env python3

import amulet

# ----------------------------------------------------------------------

def main():

    manager = amulet.GameStateManager("decks/debug.in")

    done_state = None
    while done_state is None and manager.turn < 4:
        done_state = manager.next_turn()

    if done_state:
        done_state.report()
    else:
        def key(x): return len(x.lines)
        sorted(manager.states, key=key)[-1].report()


# ----------------------------------------------------------------------

if __name__ == "__main__":
    main()
