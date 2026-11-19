"""emulate the Lean at Float (ofInt = correctly rounded conversion, float +,*,/, floor) and search small inputs on which it differs from Python"""
import math, itertools, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "port"))
from credit_risk import sas_compat as sc
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
vals = [0, 1, 2, 3, 5, 2**53 - 1, 2**53, 2**53 + 1, 2**53 + 2, 2**54 + 1, 2**55 + 3]
nvals = [0, 1, 2, 2**53, 2**53 + 1, 2**53 + 2, 2**54 + 1, 2**54 + 3, 2**55 + 1, 2**60 + 1]
gvals = [1, 2, 3, 10]
best = None
for L in (1, 2, 3):
    for bl in itertools.product(vals, repeat=L):
        for n in nvals + [sum(bl)]:
            for g in gvals:
                try: p = sc._hl_groups(list(bl), n, g)
                except Exception: continue
                if lean(list(bl), n, g) != p:
                    key = (L, sum(len(str(b)) for b in bl) + len(str(n)))
                    if best is None or key < best[0]: best = (key, bl, n, g, p, lean(list(bl), n, g))
    if best: break
print(best)
