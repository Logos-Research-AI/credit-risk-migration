"""Fidelity pass 2026-11-20, third attempt (label stale-compositions): narrow the one differing block of suite
fz10_run_py_py (kept seeds of 2002100..2002124) to its seed(s), and test whether the difference is the last bit
of exp (RULEBOOK 6, "Outside the model altogether: the last bit of exp and log").

  cd migration/port-to-lean && PYTHONPATH=../../port uv run --project ../../port python diffeval/units/fz10c_stale_narrow_gen.py
      -> diffeval/work/fz10c_stale_narrow.{json,inputs.json}, prints the per-seed Python values and the exp arguments

Suite fz10c_stale_narrow (carrier def:zz_carrier_fid_2), one input:
  cases 0..k-1  E s for every kept seed s of the block (the same E as fz10_run_py_py: predict.run's files digested)
  cases k..     for every row of every kept seed whose run completes: the bits of the Lean evaluator's
                Float.exp at the argument -predicted_logit (the argument sas_exp gets at predict.py:393), compared
                with the bits of polars' exp of the same argument (the value predict.run computed)
The Lean side of the second group evaluates Float.exp, the function the prelude's RealLike Float instance
uses for exp (RULEBOOK 6: "RealLike.exp / RealLike.log are abstract in the statements").
"""
from __future__ import annotations

import json
import shutil
import struct
import sys
import tempfile
from pathlib import Path

import polars as pl

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))
import fz10_run_py_py_gen  # noqa: E402,F401  (builds the 2026-11-20 module fz10_run_py_py_impl)
import kit  # noqa: E402
import re  # noqa: E402
from suite import Suite  # noqa: E402
from credit_risk import sas_compat as sc  # noqa: E402

g = sys.modules["fz10_run_py_py_impl"]
bt = lambda x: struct.unpack("<Q", struct.pack("<d", x))[0]  # noqa: E731
LO, HI = 2002100, 2002125


def doubles():
    texts = sorted({t for p in g.PC + g.PD for t in p if t != ""} | {str(i) for i in range(1, 10)})
    nums6_11 = sorted({g.pf(t) for r in (6, 11) for t in g.PC[r] + g.PD[r] if t != "" and g.pf(t) is not None})
    sbt = {g.lt.bits(v): sc.sas_best12(v) for v in nums6_11}
    texts = sorted(set(texts) | set(sbt.values()))
    real = pl.DataFrame({"s": texts}, schema={"s": pl.String}).select(sc.input_best32(pl.col("s"))).to_series().to_list()
    pf = g.pf
    ibx = {t: v for t, v in zip(texts, real) if not ((v is None and pf(t) is None) or (v is not None and pf(t) is not None and g.lt.bits(v) == g.lt.bits(pf(t))))}
    return ibx, sbt


def main() -> None:
    ibx, sbt = doubles()
    base = Path(tempfile.mkdtemp(prefix="fz10c_narrow_"))
    seeds, exps = [], []
    st = Suite("fz10c_stale_narrow", generator="port-to-lean/diffeval/units/fz10c_stale_narrow_gen.py")
    st.item, st.decl = "def:zz_carrier_fid_2", "zz_carrier_fid_2"
    cases = []
    for s in range(LO, HI):
        rec = g.pyrun(s, base / str(s))
        if not (g.precond(s, rec) and not rec["outcome"].startswith("raises")):
            continue
        seeds.append(s)
        cases.append((f"seed {s}: E ({rec['outcome']})", g.U, g.expected(rec), {"fz": "kept"}))
        if rec["outcome"] == "files":
            for x in rec["locals"]["test_scored_temp"]["predicted_logit"].to_list():
                if x is None:
                    continue
                arg = -x
                v = pl.Series([arg], dtype=pl.Float64).exp().item()
                exps.append((s, bt(arg), bt(v)))
    shutil.rmtree(base, ignore_errors=True)
    for s, a, v in exps:
        cases.append((f"seed {s}: exp at argument bits {a}", g.U, v, {"fz": "kept"}))
    body = ("[" + ", ".join(f"E {s}" for s in seeds) + "] ++ "
            + "[" + ", ".join(f"((Float.exp (Float.ofBits {a})).toBits.toNat : Int)" for _, a, _ in exps) + "]")
    st.ints(g.lets(ibx, sbt), body, cases, gen=True, table=True)
    st.write()
    print("kept seeds", seeds)
    print("exp arguments", len(exps))
    print(json.dumps({"ibx": {k: v for k, v in ibx.items()}, "n_sbt": len(sbt)}))


if __name__ == "__main__":
    main()
