import sys, json
sys.path.insert(0, "diffeval/units")
import numpy as np
import fz3_train_run_gen as g
from credit_risk import sas_compat as sc
a, b = int(sys.argv[1]), int(sys.argv[2])
out = []
for s in range(a, b):
    st, r = g.run_seed(s)
    if st == "raised":
        out.append((s, "raised", r[:60])); continue
    ok, why = g.pre(r)
    if not ok:
        out.append((s, "rej", why)); continue
    L, sw = r["locals"], r["stepwise"]
    cls = []
    if not sw.steps: cls.append("nostep")
    if len(sw.final.names) == 1: cls.append("iconly")
    if any(len(x.fit.names) == 1 for x in sw.steps): cls.append("q0")
    if not L["roc_valid_created"]: cls.append("v1class")
    if any(x.fit.separation for x in sw.steps): cls.append("sep")
    if L["hl_table"].height < 3: cls.append("hl<3")
    lo = 0; piv = 0
    for x in sw.steps:
        if len(x.fit.names) == 1: continue
        if any(float(x.fit.cov[i, i]) == 0.0 for i in range(1, len(x.fit.names))): lo += 1
        else:
            import math
            w, df = sc.global_wald(x.fit, L["candidates"])
    if lo: cls.append("leftout")
    lets, body, _, _ = g.lean_input(s, r)
    out.append((s, "kept", cls, len(lets) - len(g.PREFIX) + len(body), L["hl_table"].height))
json.dump(out, open("diffeval/work/fz3_scan_%d_%d.json" % (a, b), "w"))
from collections import Counter
c = Counter()
for o in out:
    if o[1] == "kept":
        c["kept"] += 1
        for k in o[2]: c[k] += 1
    else: c[o[1] + ":" + o[2][:30]] += 1
print(c)
