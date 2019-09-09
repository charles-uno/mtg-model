import collections
import math
import os


def save(name, summary):
    os.makedirs(os.path.dirname(outfile(name)), exist_ok=True)
    with open(outfile(name), "a") as handle:
        handle.write(summary + "\n")


def print_stats(names):
    if not names:
        names = sorted(x.split(".")[0] for x in os.listdir("decks"))
    namewidth = max(len(x) for x in names) + 1
    colwidth = 9
    turns = [2, 3, 4]
    header = "name".ljust(namewidth)
    for t in turns:
        header += "   " + ("turn %d" % t).rjust(colwidth)
    header += "  |   overflow"
    print(header)
    for name in names:
        lines = read(outfile(name))
        total = max(len(lines), 1)
        tally = collections.defaultdict(int)
        for line in lines:
            if not line:
                continue
            t = int(line.split(",")[0])
            tally[t] += 1
        line = name.ljust(namewidth)
        n = 0
        for t in turns:
            n += tally[t]
            line += "   " + pcts(n, total, z=2)
        overflows = sum(1 for x in lines if x.endswith("1"))
        line += "  |  " + pcts(overflows, total, z=2)
        print(line)


def outfile(name):
    return "output/%s.csv" % name


def read(path):
    try:
        with open(path, "r") as handle:
            return [x.split("#")[0].rstrip() for x in handle]
    except FileNotFoundError:
        return []


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
