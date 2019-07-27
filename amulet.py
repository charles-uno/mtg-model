#!/usr/bin/env python3

import amulet

# ----------------------------------------------------------------------

def main():

    manager = amulet.GameStateManager("decks/debug.in")

    manager.next_turn()
    manager.next_turn()

    print(len(manager.states), "states")

    for state in manager.states:
        print("---------------")
        state.report()



# ----------------------------------------------------------------------

if __name__ == "__main__":
    main()
