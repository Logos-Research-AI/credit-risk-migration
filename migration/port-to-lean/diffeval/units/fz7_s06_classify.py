"""Classify the inputs the precondition of step 06 rejects while Python returns (narrowings), by first failing clause."""
import sys, math
from collections import Counter
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parent))
import fz5_s06_gen as g
sc = g.sc
N = int(sys.argv[1])
cnt = Counter(); ex = {}
for s in range(N):
    c = g.case(s)
    if g.pre(c): continue
    res, err = g.py_run(c)
    if res is None: continue
    why = "?"
    if len(c["fidx"]) != len(c["effects"]): why = "len"
    elif any(i == 0 for i in c["fidx"]): why = "idx0"
    else:
        for idx in [0] + c["fidx"]:
            if idx in c["lo"]: continue
            if c["rankbad"]: why = "rank"; break
            bv, cv = c["betaL"][idx], c["rows"][idx][idx]
            if cv < 0: why = "cv<0"; break
            se = math.sqrt(cv) if cv == cv else math.nan
            if se == 0.0: why = "se0"; break
            r = bv/se
            if math.isfinite(r) and not math.isfinite(r*r): why = "sq"; break
            if idx != 0:
                for a in (bv, bv - sc.Z975*se, bv + sc.Z975*se):
                    try:
                        if not math.isfinite(math.exp(a)): why = "exp-nonfinite(nan/+inf)"; break
                    except OverflowError: why = "exp"; break
                if why != "?": break
    cnt[why] += 1; ex.setdefault(why, s)
print(dict(cnt), ex)
