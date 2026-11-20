"""Fidelity pass 2026-11-20c (train-b): explain the 3 kept seeds of fz10_train_run_03 whose Lean digest differs
(136, 1493, 1846). Hypothesis: the last bit of exp (RULEBOOK.md, "Known limits", the last bit of `exp`; recorded for
this unit at seed 136 by the fuzz of 2026-11-18). Check: rerun the CURRENT train.py:163-292 on the same case with
math.exp replaced by a table holding the Lean evaluator's Float.exp bits for the arguments where they differ (taken
from eval_decl on def:zz_carrier_fid_2, 2026-11-20); the Python digest must then equal the Lean digest. Also prints
which of the two values is correctly rounded (Decimal exp at 60 digits).

  cd migration/port-to-lean && PYTHONPATH=../../port uv run --project ../../port python diffeval/units/fz10c_train_run_03_explain.py
"""
from __future__ import annotations

import math
import struct
import sys
import types
from decimal import Decimal, getcontext
from pathlib import Path

import numpy as np
import polars as pl

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))
import fz3_s03_gen as f3  # noqa: E402
import fz10_train_run_03_gen as g  # noqa: E402
import t18_gen as t  # noqa: E402
from credit_risk import sas_compat as sc  # noqa: E402

B = lambda x: struct.unpack("<Q", struct.pack("<d", x))[0]  # noqa: E731
F = lambda u: struct.unpack("<d", struct.pack("<Q", u))[0]  # noqa: E731
# argument bits -> Lean Float.exp bits, where they differ from CPython math.exp (eval_decl output, 2026-11-20)
LEAN_EXP = {0x405A26DB6DB6DB6E: 5286717714475752482, 0x4085910000000000: 9090778126006073288, 0x400D000000000000: 4630477952598210645}
LEAN_DIGEST = {136: 17253971896078617335, 1493: 17180254920879192241, 1846: 7807394984494220557}


def run(s, exp):
    c = f3.case(s)
    c["frame"], _ = g.x28_frame(s, c["frame"])
    fits = [sc.LogisticFit(names=list(nm), beta=f3.na(np.array(b, dtype=np.float64)),
                           cov=f3.na(np.array(cv, dtype=np.float64).reshape(len(nm), len(nm))), loglik=ll, n_iter=0, converged=True,
                           separation=None) for nm, b, cv, ll in c["steps"]]
    steps = [sc.StepwiseStep(step=j + 1, entered=None, removed=None, df=1, number_in_model=0, score_chisq=None, wald_chisq=None,
                             p_value=0.5, fit=f) for j, f in enumerate(fits)]
    sw = sc.StepwiseResult(steps, fits[-1] if fits else None, None)
    ff = pl.DataFrame({k: pl.Series(v, dtype=pl.Float64) for k, v in c["frame"].items()})
    L = dict(m2ll0=c["m0"], n_obs=c["n"], fit_frame=ff, y_train=f3.na(np.array(c["y"], dtype=np.float64)), ybar=c["ybar"], cand=c["cand"])
    mm = types.SimpleNamespace(**{k: getattr(math, k) for k in dir(math) if not k.startswith("_")})
    mm.exp = exp
    o_math = g.math
    g.math = mm  # run_slice puts g.math in the namespace of the executed source lines
    try:
        with np.errstate(all="ignore"):
            ws, _ = g.run_slice(sw, L, sw.final)
    finally:
        g.math = o_math
    return t.w([len(ws)] + [x for n_, df in ws for x in t.tdn(n_, df)])


def lean_exp(x):
    u = B(x)
    return F(LEAN_EXP[u]) if u in LEAN_EXP else math.exp(x)


def main():
    getcontext().prec = 60
    for u, lb in LEAN_EXP.items():
        x = F(u)
        exact = Decimal(x).exp()
        py, le = math.exp(x), F(lb)
        print(f"exp({x!r}) [{hex(u)}]: CPython bits {B(py)} err {abs((Decimal(py) - exact) / (Decimal(math.ulp(py)))):.4f} ulp; "
              f"Lean bits {lb} err {abs((Decimal(le) - exact) / Decimal(math.ulp(le))):.4f} ulp")
    for s, d in LEAN_DIGEST.items():
        a, b = run(s, math.exp), run(s, lean_exp)
        print(f"seed {s}: python {a}  python-with-Lean-exp {b}  Lean {d}  -> explained: {b == d}")


if __name__ == "__main__":
    main()
