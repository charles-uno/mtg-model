#!/usr/bin/env python3

import amulet

# ----------------------------------------------------------------------

def main():

    manager = amulet.GameStateManager("decks/debug.in")

    manager.next_turn()

    manager.peek()


# ----------------------------------------------------------------------

if __name__ == "__main__":
    main()
