import collections

# ----------------------------------------------------------------------

def print_summary(names):

    namewidth = max( len(x) for x in names ) + 1
    colwidth = 9

    turns = [2, 3, 4]

    header = "name".ljust(namewidth)
    for t in turns:
        header += "   " + ("turn %d" % t).rjust(colwidth)

    print(header)

    for name in names:
        outfile = "out/%s.out" % name
        with open(outfile, "r") as handle:
            lines = [ x.split("#")[0].rstrip() for x in handle ]
        total = len(lines)
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
            line += "   " + pct(n/total) + " ± " + pct(n**0.5/total)
        print(line)

# ----------------------------------------------------------------------

def pct(x):
    return "%2.0f" % (100*x) + "%"
