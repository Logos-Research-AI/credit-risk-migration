import sys, collections
sys.path.insert(0, "diffeval/units")
import fz5_s10_gen as g
C = collections.Counter()
for s in range(50000, 50900):
    c = g.build(s)
    if (c["icpt"] is None and c["fin"] and not c["coefs"]) or not c["fin"]:
        continue
    res, _ = g.run_py(c)
    for v in res.get_column("pd_logistic").to_list():
        if v is None: C["null"] += 1
        elif v == 0.5: C["0.5"] += 1
        elif 0.49 < v < 0.5: C["just below .5"] += 1
        elif 0.5 < v < 0.51: C["just above .5"] += 1
print(dict(C))
