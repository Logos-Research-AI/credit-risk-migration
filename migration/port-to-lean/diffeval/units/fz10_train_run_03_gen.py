"""Fidelity pass 2026-11-20 (label train-b): def:train_run_03_fit_global_rsquare (train.py:159-292, port HEAD 4a757fb),
including the X28 path (train.py:206-210: a fit variable that is a linear combination of the others is left out of
X'X by _kept, counts in no DF, and is passed to global_wald as `dependent`).

STATUS: Python side only. The unit was NOT evaluated in Lean: its result type List (String x Tabular.Table Float) has
no Repr, so eval_decl on def:train_run_03_fit_global_rsquare fails as a whole (tool error "Structured content does
not match the tool's output schema"; the same for def:run_py_py_py, the only other item that has the unit in scope),
and no carrier item (an identity List Int -> List Int depending on the unit, as def:zz_carrier_t was) exists on
blueprint 5365851c. The brief forbids adding one: it is reported. With such a carrier `C`, the suite below runs as
`eval_decl(item_id=C, inputs=[lean_text(...)])` through the Lean lets of fz3_s03_gen.py (LEAN_PRE, mk, SWof, TDN),
extended with the X28 frame of `x28_frame`.

Cases: fz3_s03_gen.case(s) (synthetic stepwise results of 0..3 steps over columns a..d, pools of edge values for
beta, cov (Wald thresholds), loglik, m2ll0, ybar, y, frame cells; candidates rotations of a..e) and, for
seeds with hsh(s, 900) % 3 != 0, the X28 frame: column d := a + b and, when hsh(s, 901) % 2 == 0, column c := a
(computed in float on the generated cells), so that steps naming a, b and d (or a and c) have X'X exactly singular
and _kept leaves the dependent column out. Expected: the CURRENT source lines train.py:163-292 executed on the
case (`run_slice`), with the REAL sas_compat._kept, _solve_sas, _left_out and global_wald and the stand-ins of
fz3_s03_gen (Gaussian solve, sequential matmul / matvec / dot, chi2 = x * 0.5 + df, formatters = injective
encodings of t18_gen), `final` = the last step's fit (None when there is no step).

  cd migration/port-to-lean && PYTHONPATH=../../port uv run --project ../../port python diffeval/units/fz10_train_run_03_gen.py [A B]
      prints the classes and how many steps reach X28; writes work/fz10_train_run_03.py.json (per seed: class,
      dependent lists, output digest)
"""
from __future__ import annotations

import json
import math
import sys
import textwrap
import types
from collections import Counter
from pathlib import Path

import numpy as np
import polars as pl

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))
import fz3_s03_gen as f3  # noqa: E402
import kit  # noqa: E402
import t18_gen as t  # noqa: E402
from credit_risk import sas_compat as sc  # noqa: E402
from credit_risk import train  # noqa: E402

W = HERE.parent / "work"
SRC = Path(train.__file__).read_text().splitlines()
assert SRC[162].strip() == 'fs_step: list[str] = ["0"]', SRC[162]
assert "printed_rsquare.csv" in SRC[291], SRC[291]
CODE = textwrap.dedent("\n".join(SRC[162:292]))


def x28_frame(s, frame):
    if kit.hsh(s, 900) % 3 == 0 or not frame:
        return frame, False
    f = dict(frame)
    if "a" in f and "b" in f and "d" in f:
        f["d"] = [x + y for x, y in zip(f["a"], f["b"])]
    if kit.hsh(s, 901) % 2 == 0 and "a" in f and "c" in f:
        f["c"] = list(f["a"])
    return f, True


def run_slice(stepwise, L, final):
    writes, deps = [], []
    o_kept = sc._kept  # pyright: ignore[reportPrivateUsage]

    def kept_rec(a):
        k = o_kept(a)
        deps.append(len(k) < a.shape[0])
        return k
    proxy = types.SimpleNamespace(sas_d12_3=t.ENCODERS["sas_d12_3"], fmt_wd=t.ENCODERS["fmt_wd"], sas_pvalue=t.ENCODERS["sas_pvalue"],
                                  chi2_sf=f3.chi2_st, write_sas_csv=lambda df, path, formats=None: writes.append((Path(path).name, df.clone())),
                                  global_wald=sc.global_wald, _kept=kept_rec, _solve_sas=sc._solve_sas)  # pyright: ignore[reportPrivateUsage]
    ns = {"sas_compat": proxy, "np": np, "pl": pl, "math": math, "stepwise": stepwise, "output_dir": Path("out"), "final": final,
          "candidates": L["cand"], **{k: L[k] for k in ("m2ll0", "n_obs", "fit_frame", "y_train", "ybar")}}
    o_solve, o_cs = np.linalg.solve, np.column_stack
    np.linalg.solve = f3.solve_sa
    np.column_stack = lambda cols: f3.na(o_cs(cols))
    try:
        exec(compile(CODE, "train.py:163-292", "exec"), ns)  # noqa: S102
    finally:
        np.linalg.solve, np.column_stack = o_solve, o_cs
    return writes, deps


def py_case(s):
    c = f3.case(s)
    c["frame"], x28 = x28_frame(s, c["frame"])
    fits = [sc.LogisticFit(names=list(nm), beta=f3.na(np.array(b, dtype=np.float64)),
                           cov=f3.na(np.array(cv, dtype=np.float64).reshape(len(nm), len(nm))), loglik=ll, n_iter=0, converged=True,
                           separation=None) for nm, b, cv, ll in c["steps"]]
    steps = [sc.StepwiseStep(step=j + 1, entered=None, removed=None, df=1, number_in_model=0, score_chisq=None, wald_chisq=None,
                             p_value=0.5, fit=f) for j, f in enumerate(fits)]
    sw = sc.StepwiseResult(steps, fits[-1] if fits else None, None)
    admits = f3.pre(c, steps)
    ff = pl.DataFrame({k: pl.Series(v, dtype=pl.Float64) for k, v in c["frame"].items()}) if c["frame"] else pl.DataFrame()
    L = dict(m2ll0=c["m0"], n_obs=c["n"], fit_frame=ff, y_train=f3.na(np.array(c["y"], dtype=np.float64)), ybar=c["ybar"], cand=c["cand"])
    f3.FLAG["zero_pivot"] = False
    try:
        with np.errstate(all="ignore"):
            ws, deps = run_slice(sw, L, sw.final)
    except Exception as e:  # noqa: BLE001
        return {"cls": "raise_in_pre" if admits else "dropped", "ex": f"{type(e).__name__}: {str(e)[:60]}", "x28_frame": x28}
    d = t.w([len(ws)] + [x for n_, df in ws for x in t.tdn(n_, df)])
    cls = "linalg" if f3.FLAG["zero_pivot"] else ("kept" if admits else "rejected")
    return {"cls": cls, "digest": d, "x28_frame": x28, "steps_x28": sum(deps), "steps_q": len(deps)}


def main():
    a, b = (int(sys.argv[1]), int(sys.argv[2])) if len(sys.argv) > 2 else (0, 3000)
    out = {s: py_case(s) for s in range(a, b)}
    st = Counter(v["cls"] for v in out.values())
    kept = [v for v in out.values() if v["cls"] == "kept"]
    print("classes", dict(st))
    print("kept cases with an X28 step:", sum(v["steps_x28"] > 0 for v in kept), "steps reaching X28:", sum(v["steps_x28"] for v in kept),
          "of", sum(v["steps_q"] for v in kept), "steps with q != 0")
    print("raises inside the precondition:", Counter(v.get("ex") for v in out.values() if v["cls"] == "raise_in_pre"))
    (W / "fz10_train_run_03.py.json").write_text(json.dumps({str(k): v for k, v in out.items()}))


if __name__ == "__main__":
    main()
