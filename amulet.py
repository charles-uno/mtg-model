#!/usr/bin/env python3

import argparse
import os
import random

import amulet


MAX_TURNS = 4


def main():
    parser = argparse.ArgumentParser(
        "Brute Force MTG Goldfisher"
    )
    parser.add_argument(
        "decks",
        nargs="*",
        help="Deck name(s) to look at. Defaults to all of them.",
        default=all_decks(),
    )
    parser.add_argument(
        "-n",
        "--ntrials",
        help="Stop after this many trials. Default is to run until killed.",
        type=int,
    )
    parser.add_argument(
        "-d",
        "--debug",
        nargs="?",
        const="",
        help="Run until we find a hand that works, then print it out. If given a card name, run until we see that card in the log",
    )
    parser.add_argument(
        "-r",
        "--report",
        action="store_true",
        help="Instead of running simulations, print the results for the given decks.",
    )
    args = parser.parse_args()
    # If reporting results, do so.
    if args.report:
        return amulet.print_stats(args.decks)
    # If given multiple names, choose randomly each time.
    nwidth = 4
    namewidth = max(len(x) for x in args.decks)
    trial = 0
    while True:
        name = random.choice(args.decks)
        print("[" + str(trial).rjust(nwidth) + "]", end=" ")
        print("[" + name.rjust(namewidth) + "]", end=" ")
        state = amulet.simulate(name)
        # If we're on the lookout for a certain card, check that here.
        if state and args.debug in state:
            print(state)
            break
        if args.ntrials and trial > args.ntrials:
            break
        trial += 1


def all_decks():
    return sorted(x.split(".")[0] for x in os.listdir("decks"))


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("Killed")
