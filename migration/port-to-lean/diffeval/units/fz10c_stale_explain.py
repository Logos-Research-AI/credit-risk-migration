"""Fidelity pass 2026-11-20, third attempt (label stale-compositions): the one differing seed of def:run_py_py,
2002107, is the last bit of exp (RULEBOOK 6).

  cd migration/port-to-lean && PYTHONPATH=../../port uv run --project ../../port python diffeval/units/fz10c_stale_explain.py

Inputs taken first hand (eval_decl on def:zz_carrier_fid_2, suite fz10c_stale_narrow, out.txt by script):
  Lean E 2002107 = 5069487142773800831 (Python 5644588794554986009)
  Lean Float.exp at argument bits 4633626959958896978 = 4996001759243522979 (polars 4996001759243522978)
Here: the port's two output frames of seed 2002107, with pd_logistic recomputed from the Lean's exp value on the
rows whose argument is that one (and credit_risk_score = base_score + score_range * (1 - pd) after it, read from
predict.py:405), digested as fz10_run_py_py does. EQUAL means the one-ulp exp difference accounts for the
whole difference of the seed. Also prints the seed's inputs (rows, model) for the minimal-case record.
"""
from __future__ import annotations

import struct
import sys
import tempfile
from pathlib import Path

import polars as pl

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))
import fz10_run_py_py_gen  # noqa: E402,F401
import b4_gen as b4  # noqa: E402

g = sys.modules["fz10_run_py_py_impl"]
fb = lambda b: struct.unpack("<d", struct.pack("<Q", b))[0]  # noqa: E731
bt = lambda x: struct.unpack("<Q", struct.pack("<d", x))[0]  # noqa: E731
S, ARG, PY, LEAN_EXP, LEAN_E = 2002107, 4633626959958896978, 4996001759243522978, 4996001759243522979, 5069487142773800831

rec = g.pyrun(S, Path(tempfile.mkdtemp()) / str(S))
assert rec["outcome"] == "files", rec["outcome"]
logit = rec["locals"]["test_scored_temp"]["predicted_logit"].to_list()
hit = 0
files = []
for name, df in rec["files"]:
    new = []
    for x, p in zip(logit, df["pd_logistic"].to_list()):
        if x is not None and bt(-x) == ARG:
            assert bt(pl.Series([-x]).exp().item()) == PY
            assert bt(1 / (1 + fb(PY))) == bt(p)          # the port's value comes from polars' exp
            p = 1 / (1 + fb(LEAN_EXP))
            hit += 1
        new.append(p)
    df = df.with_columns(pl.Series("pd_logistic", new, dtype=pl.Float64))
    if "credit_risk_score" in df.columns:
        df = df.with_columns(credit_risk_score=pl.col("base_score") + pl.col("score_range") * (1 - pl.col("pd_logistic"))) \
            if "base_score" in df.columns else df.with_columns(credit_risk_score=600.0 + 250.0 * (1 - pl.col("pd_logistic")))
    files.append((name, df))
got = b4.w([1] + [g.file_digest(f, df) for f, df in files])
print("seed", S, "rows with the argument:", hit, "| python", g.expected(rec), "| python with the Lean's exp", got,
      "| Lean", LEAN_E, "->", "EQUAL" if got == LEAN_E else "DIFFERENT")
print("argument", fb(ARG), "exp python", fb(PY), "exp Lean", fb(LEAN_EXP), "differ by", LEAN_EXP - PY, "ulp")
co, ic = g.coefs(S)
print("intercept", ic, "coefficients", co, "| full", S % 2 == 0)
print("test rows", rec["locals"]["test_scored_temp"].height, "| files", [(f, d.height) for f, d in rec["files"]])
print(rec["locals"]["test_scored_temp"].select([c for c in ("predicted_logit",) + tuple(n for n, _ in co) if c in rec["locals"]["test_scored_temp"].columns]))
