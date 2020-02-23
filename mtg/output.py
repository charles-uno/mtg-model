import collections
import json
import math
import os


def save(name, summary):
    filename = f"output/{name}.json"
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    with open(filename, "a") as handle:
        handle.write(json.dumps(summary) + "\n")


def print_results(names):
    # If no names are given, grab them all
    if not names:
        names = sorted(x.split(".")[0] for x in os.listdir("output"))
    namewidth = max(len(x) for x in names) + 1
    header = "name".ljust(namewidth)
    colwidth = 18
    for tmo in range(4):
        header += f"| turn {tmo+1} ".ljust(colwidth)
    print(header)
    for name in names:
        if os.path.exists(f"output/{name}.json"):
            with open(f"output/{name}.json", "r") as handle:
                docs = [json.loads(x) for x in handle]
        else:
            docs = []
        line = name.ljust(namewidth)
        total = max(len(docs), 1)
        # Turns index from 1. Index arrays buy TMO (turn minus one)
        for tmo in range(4):
            success = sum(1 for d in docs if d["turns"][tmo] is True)
            overflow = sum(1 for d in docs if d["turns"][tmo] is None)
            success_rate = pcts(success, total, z=2)
            overflows = pct(overflow/total)
            line += f"| {success_rate} ({overflows}) "
        print(line)
    return


def pcts(m, n, z=1):
    """Use a normal approximation to see what range of probabilities
    we're looking at based on the number of trials and the number of
    hits. One standard deviation by default.
    M = NP +- z sqrt((1-P)NP)
    Turn this inside out and we get a quadratic in P:
    0 = (NN + zzN)PP + (-zzN - 2MN)P + (NN + zzN)
    """
    a = float(n*n + z*z*n)
    b = float(-z*z*n - 2*m*n)
    c = float(m*m)
    pp = (-b + math.sqrt(b*b-4*a*c))/(2*a)
    pm = (-b - math.sqrt(b*b-4*a*c))/(2*a)
    # For large samples, both ways give the same value. For small sample
    # sizes, make sure we say zero when we've seen zero.
#    p = (pp+pm)/2
    p = m/n
    dp = (pp-pm)/2
    return pct(p) + " ± " + pct(dp)


def pct(x):
    return "%2.0f" % (100*x) + "%"
