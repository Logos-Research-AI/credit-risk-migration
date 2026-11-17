"""Fuzz of 2026-11-17 (fz_ctable): which clause of the precondition rejects each generated input on
which Python returns, and whether the Lean equals Python there (narrowing) or not.

  cd migration/port-to-lean && PYTHONPATH=../../port uv run --project ../../port python experiments/fz_ctable_rejected.py
"""
import collections
import json
import math
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "diffeval" / "units"))
import fz_ctable_gen as g  # noqa: E402

W = HERE.parent / "diffeval" / "work"
suite = json.loads((W / "fz_ctable.json").read_text())
res = json.loads((W / "fz_ctable.result.json").read_text())


def why_core(y, ps, icpt):
    n = len(y)
    if icpt and n - 1.0 == 0.0:
        return "(6') one row"
    if any(t != t for t in ps):
        return "(7) NaN in ps"
    tol = 1e-9 if icpt else 0.0
    a, b = min(ps) / 0.02 + tol, -(max(ps) / 0.02 - tol)
    if not (math.isfinite(a) and math.isfinite(b)):
        return "(7) infinite ps"
    klo, khi = math.floor(a), -math.floor(b)
    if klo < 0:
        return "(7) klo < 0"
    if khi > 50:
        return "(7) khi > 50"
    n1 = float(np.sum(y))
    if not math.isfinite(n1) or math.floor(n1) != n1:
        return "(8) sum of y not integral"
    return "?"


out = collections.defaultdict(lambda: {"equal": 0, "different": 0, "example equal": None, "example different": None})
for c, r in zip(suite["cases"], res, strict=True):
    if c.get("fz") != "rejected":
        continue
    seed = int(c["id"].split("seed ")[1])
    if "/IR " in c["id"]:
        y = np.array(g.ri_y(seed))
        with np.errstate(all="ignore"):
            ps = (float(y.sum()) - y) / (len(y) - 1.0)
        why, desc = why_core(y, [float(t) for t in ps], True), f"y = {[float(v) for v in y]}"
    elif "/V " in c["id"]:
        _, _, _, ps = g.rv_py(seed)
        a = g.AP[g.h(seed, 2) % 8]
        why, desc = f"(6) 1 - h_i = 0 (a = {a})", f"seed {seed}"
    else:
        _, _, ok, ps, var = g.r8_py(seed)
        if ps is None:
            why = "step 08: a complete case with a null pd_logistic" + (" (with a variable)" if var else " (intercept only)")
        elif var:
            a = g.AP[g.h(seed, 7) % 8]
            why = f"with a variable: (6) or (7), a = {a}"
        else:
            why = "intercept only: (7) ps outside [0, 1] (a y equal to 2)"
        desc = f"seed {seed}"
    k = (c["primitive"], why)
    key = "equal" if r["status"] == "PASS" else "different"
    out[k][key] += 1
    if out[k]["example " + key] is None:
        out[k]["example " + key] = f"{c['id'].split('/')[1]}: {desc}"
for k, v in sorted(out.items()):
    print(k, v)
