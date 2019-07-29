#!/usr/bin/env python3

import argparse
import random

import amulet

# ----------------------------------------------------------------------

MAX_TURNS = 4

def main():

    parser = argparse.ArgumentParser("Amulet Titan Simulation")
    parser.add_argument("n", nargs="?", help="Number of times to run", type=int, default=0)
    parser.add_argument("names", nargs="*", help="Deck names to use", default=[])
    args = parser.parse_args()

    nwidth = len(str(args.n-1))

    # If given multiple names, choose randomly each time
    last_state = None
    for trial in range(args.n):

        print("[" + str(trial).rjust(nwidth) + "]", end=" ")

        name = random.choice(args.names)
        last_state = amulet.simulate(name) or last_state
    if last_state:
        last_state.report()
    # Giving N=0 means we just want a summary of existing data
    if not args.n:
        amulet.print_summary(args.names)


# ----------------------------------------------------------------------

if __name__ == "__main__":
    main()
