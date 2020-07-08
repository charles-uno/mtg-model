#!/usr/bin/env python3

import argparse
import io
import multiprocessing as mp
import os
import random
import sys

import mtg

def main():
    args = parse_args()
    # If reporting results, do so.
    if args.results:
        return mtg.print_results(args.decks)
    # If given multiple names, choose randomly each time.
    trial = 0
    while True:
        if args.jobs > 1:
            batch_size = 10*args.jobs
            pool = mp.Pool(processes=args.jobs)
            jobs = []
            for _ in range(batch_size):
                trial += 1
                name = random.choice(args.decks)
                jobs.append(
                    pool.apply_async(mtg.simulate, (name, trial, 3))
                )
            results = [x.get() for x in jobs]
            if any(results) and args.debug:
                for result in results:
                    if not result:
                        continue
                    print(result)
                    return
            if args.ntrials and trial >= args.ntrials:
                return
        else:
            trial += 1
            name = random.choice(args.decks)
            result = mtg.simulate(name, trial, 3)
            if result and args.debug:
                print(result)
                return
            if args.ntrials and trial >= args.ntrials:
                return


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
        action="store_true",
        help="Run until we find a hand that works, then print it out",
    )
    parser.add_argument(
        "-j",
        "--jobs",
        type=int,
        default=1,
        help="Run in parallel using this many threads",
    )
    parser.add_argument(
        "-n",
        "--ntrials",
        type=int,
        help="Stop after this many trials (default: run until killed)",
    )
    parser.add_argument(
        "--results",
        action="store_true",
        help="Instead of running simulations, print the results for the given decks",
    )
    return parser.parse_args()


class SilenceStderr(object):

    def __enter__(self):
        self.stderr = sys.stderr
        sys.stderr = io.StringIO()

    def __exit__(self, *args):
        sys.stderr = self.stderr


if __name__ == "__main__":
    # Suppress the multiprocess pool yelling about KeyboardInterrupt
    with SilenceStderr():
        try:
            main()
        except KeyboardInterrupt:
            print("Killed")
            sys.exit(1)
