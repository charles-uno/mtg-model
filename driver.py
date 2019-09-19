#!/usr/bin/env python3

import argparse
import os
import random
import sys

import mtg

def main():
    args = parse_args()
    # If reporting results, do so.
    if args.results:
        return mtg.print_stats(args.decks, verbose=args.verbose)
    # If given multiple names, choose randomly each time.
    namewidth = max(len(x) for x in args.decks)
    trial = 0
    while True:
        trial += 1
        name = random.choice(args.decks)
        print(str(trial).rjust(4), end=" ")
        print(name.rjust(namewidth), end=" ")
        sys.stdout.flush()
        # If we're debugging, just converge once
        if mtg.simulate(name, debug=args.debug):
            break
        if args.ntrials and trial >= args.ntrials:
            break


def all_decks():
    decks = {x.split(".")[0] for x in os.listdir("decks")}
    return sorted(decks - {"debug"})


def parse_args():
    parser = argparse.ArgumentParser(
        "Brute Force MTG Goldfisher"
    )
    parser.add_argument(
        "decks",
        nargs="*",
        help="Deck name(s) to look at",
        default=all_decks(),
    )
    parser.add_argument(
        "-d",
        "--debug",
        default=None,
        nargs="?",
        const="",
        help="Run until we find a hand that works, then print it out. If given a card name, keep going until we see a line that uses this card",
    )
    parser.add_argument(
        "-n",
        "--ntrials",
        type=int,
        help="Stop after this many trials (default: run until killed)",
    )
    parser.add_argument(
        "-r",
        "--results",
        action="store_true",
        help="Instead of running simulations, print the results for the given decks",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Verbose output",
    )
    return parser.parse_args()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("Killed")
