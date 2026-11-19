"""Python-only scan (NO Lean evaluation: the blueprint has no carrier item, eval_decl cannot print a Frame).
Seeds -> (y, pd) with edge pools; precondition (new, no 2^52 bounds) mirrored in Python; real
sc.hosmer_lemeshow run; a float transcription of the Lean body (o1 = float sum, o0 = size - o1 in float) compared."""
import sys, math, struct, random
from collections import Counter
from pathlib import Path
import numpy as np, polars as pl
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "port"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from credit_risk import sas_compat as sc
from fz5_hl_small import pre, bits, Chi2
sc.chi2 = Chi2
nan, inf = float("nan"), float("inf"); nx = math.nextafter
PDP = [None, 0.0, -0.0, 1.0, 0.5, nx(.5,1), nx(.5,0), 1e-6, nx(1e-6,1), nx(1e-6,0), 5e-7, .999999, nx(.999999,1), nx(.999999,0), nan, inf, -inf, 2.0, -1.0, 1e-300]
YP = [None, 0.0, 1.0, 1.0, 0.0, 2.0**52, 2.0**52+1, 2.0**53, 2.0**53+2, 2.0**62, -2.0**62, 2.0**63, -2.0**63, 2.0**64, 1e19, 1e300, nan, inf, 0.5, -1.0, 3.0]
NS = [0,1,2,3,4,5,9,10,11,15,19,20,21,24,25,35,40,45,55,60,100]
def gen(seed):
    r = random.Random(seed); n = r.choice(NS)
    mode = r.choice(["tame", "pdwild", "ywild", "both"]); chain = r.random() < .5
    p = []
    for i in range(n):
        u = r.random()
        if i and chain and u < .3: v = p[-1]; v = None if v is None else (v + 1e-6 if r.random()<.5 else v)
        elif i and u < .4: v = p[-1]
        elif mode in ("pdwild","both") and u < .7: v = r.choice(PDP)
        else: v = None if r.random() < .05 else r.randint(0, 64)/64
        if v is not None and isinstance(v,float) and math.isfinite(v) and chain and r.random()<.2: v = nx(v, r.choice([0.,1.]))
        p.append(v)
    q = r.randint(0, 8)
    y = [(None if r.random()<.05 else (r.choice(YP) if mode in ("ywild","both") and r.random()<.2 else float(r.randint(0,8) < q))) for _ in range(n)]
    return y, p
def model(y, p):
    """float transcription of def:hosmer_lemeshow's loop (what Lean computes), rows as (size, o1, e1, o0, e0), chisq"""
    d = [(a, b) for a, b in zip(y, p) if a is not None and b is not None]
    n = len(d)
    p0 = np.array([b for _, b in d]); y0 = np.array([a for a, _ in d]); o = np.argsort(p0, kind="stable"); pp, yy = p0[o], y0[o]
    blocks, i = [], 0
    while i < n:
        j = int(pp.searchsorted(float(pp[i]) + 1e-6, side="right")); blocks.append(j - i); i = j
    st = np.concatenate([[0], np.cumsum(blocks)[:-1]]).astype(np.int64); pp = np.repeat(pp[st], blocks)
    s = 0; chisq = 0.0; rows = []
    for size in sc._hl_groups(blocks, n, 10):
        o1 = float(yy[s:s+size].sum()); avg = float(pp[s:s+size].sum()) / size
        lo = 1e-6 if avg < 1e-6 else avg; hi = 0.999999 if 0.999999 < lo else lo
        e1 = size * hi; s += size; o0 = size - o1; e0 = size - e1
        chisq = None if chisq is None or e1 <= 0 or e0 <= 0 else chisq + (o1 - e1)**2/e1 + (o0 - e0)**2/e0
        rows.append((size, o1, e1, o0, e0))
    return rows, chisq
def same(a, b): return (a is None and b is None) or (a is not None and b is not None and bits(a) == bits(b))
C = Counter(); diffs = []; defects = []
kept = 0; seed = 0
while kept < 2000:
    seed += 1; y, p = gen(seed)
    C["generated"] += 1
    ok = pre(y, p)
    if not ok: C["rejected"] += 1; continue
    kept += 1
    try:
        t, c, dof, pv = sc.hosmer_lemeshow(pl.Series(y, dtype=pl.Float64), pl.Series(p, dtype=pl.Float64))
    except Exception as e:
        C["kept_python_raises"] += 1; defects.append((seed, len(y), f"{type(e).__name__}: {str(e)[:40]}", y, p)); continue
    if t.height == 0: C["empty"] += 1; continue
    rows, mc = model(y, p)
    bad = None
    for (size, o1, e1, o0, e0), r in zip(rows, t.iter_rows()):
        if not (size == r[1] and bits(o1) == bits(float(r[2])) and bits(e1) == bits(r[3]) and bits(o0) == bits(float(r[4])) and bits(e0) == bits(r[5])): bad = ("row", size, o1, r[2])
    if len(rows) != t.height: bad = ("ngroups",)
    if not same(mc, c): bad = ("chisq", mc, c)
    if bad: diffs.append((seed, bad, len(y)))
    else: C["match"] += 1
print(dict(C), "diffs", len(diffs), "defects", len(defects))
for d in diffs[:10]: print("DIFF", d)
seen = set()
for s, n, m, y, p in defects:
    if m.split(":")[0] in seen and len(seen) > 6: continue
    seen.add(m.split(":")[0]); print("DEFECT seed", s, "n", n, m)
if defects:
    s, n, m, y, p = min(defects, key=lambda t: t[1]); print("smallest", m, y, p)
