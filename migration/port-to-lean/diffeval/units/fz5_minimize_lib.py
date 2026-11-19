"""emulate the Lean at Float (ofInt = correctly rounded conversion, float +,*,/, floor) and search small inputs on which it differs from Python"""
import math, itertools, sys
from pathlib import Path
def lean(blocks, n, g):
    fl = float
    m = math.floor(fl(n) / fl(g) + 0.5)
    m = float(m)
    groups = []; c = 0
    for nj in blocks:
        if c == 0 or (fl(c) < m and fl(c) + float(math.floor(0.5 * fl(nj))) <= m):
            c += nj
        else:
            groups.append(c); c = nj
    groups.append(c)
    if len(groups) > 1 and fl(groups[-1]) <= float(math.floor(0.05 * fl(n))):
        last = groups.pop(); groups[-1] += last
    return groups
