#!/usr/bin/env python3

import argparse
import os
import random

import amulet

# ----------------------------------------------------------------------

MAX_TURNS = 4

def main():

    parser = argparse.ArgumentParser("Amulet Titan Simulation")
    parser.add_argument("n", nargs="?", help="Number of times to run", type=int, default=0)
    parser.add_argument("names", nargs="*", help="Deck names to use", default=all_decks())
    args = parser.parse_args()

    nwidth = len(str(args.n-1))
    if args.n:
        namewidth = max( len(x) for x in args.names )

    # If given multiple names, choose randomly each time
    last_state = None
    for trial in range(args.n):
        name = random.choice(args.names)

        print("[" + str(trial).rjust(nwidth) + "]", end=" ")
        print("[" + name.rjust(namewidth) + "]", end=" ")

        last_state = amulet.simulate(name) or last_state
    if last_state:
        last_state.report()
    # Giving N=0 means we just want a summary of existing data
    if not args.n:
        amulet.print_summary(args.names)

def all_decks():
    return sorted( x.split(".")[0] for x in os.listdir("decks") )


# ----------------------------------------------------------------------

if __name__ == "__main__":
    main()
