import collections
import math
import os


def print_summary(names):
    if not names:
        names = sorted( x.split(".")[0] for x in os.listdir("decks") )
    namewidth = max( len(x) for x in names ) + 1
    colwidth = 9
    turns = [2, 3, 4]
    header = "name".ljust(namewidth)
    for t in turns:
        header += "   " + ("turn %d" % t).rjust(colwidth)
    print(header)
    for name in names:
        lines = read("out/%s.out" % name)
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
            line += "   " + pcts(n, total)
        print(line)


def read(path):
    try:
        with open(path, "r") as handle:
            return [ x.split("#")[0].rstrip() for x in handle ]
    except FileNotFoundError:
        return []


def pcts(m, n, z=1):
    """Use a normal approximation to see what range of probabilities
    we're looking at based on the number of trials and the number of
    hits. One standard deviation by default.
    M = NP +- z*sqrt( NP*(1-P) ) so...
    P = (Nzz + 2MN) +- sqrt( (Nzz + 2MN)**2 - 4MM(NN+zzN) )/2*(NN+zzN)
    """
    a = float(n*n + z*z*n)
    b = float(-z*z*n - 2*m*n)
    c = float(m*m)
    pp = (-b + math.sqrt(b*b-4*a*c))/(2*a)
    pm = (-b - math.sqrt(b*b-4*a*c))/(2*a)
    p = (pp+pm)/2
    dp = (pp-pm)/2
    return pct(p) + " ± " + pct(dp)


def pct(x):
    return "%2.0f" % (100*x) + "%"
