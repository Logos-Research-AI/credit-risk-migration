"""Real-data input of def:classification_is_made (fidelity pass 2026-11-20, label train-c).

  cd migration/port-to-lean && PYTHONPATH=../../port uv run --project ../../port python diffeval/units/fz10_cim_real_gen.py
      -> diffeval/work/fz10_cim_real.json, diffeval/work/fz10_cim_real.inputs.json

Runs the REAL port at HEAD: feature_engineering.run(legacy/data, split_ids=inputs/split_ids.csv), then train.run on its
output, with sas_compat.classification_is_made wrapped to record its arguments (fit, x_final) and its real result.
The unit is then evaluated on that real call:
  - Python expected = the real classification_is_made on (fit, x_final) with np.linalg.solve replaced by the
    stand-in Gaussian elimination and x.T @ x by the sequential product (fz4_cim_gen.solve_sa / NA), and also with
    real numpy (reported; the routines are explicit parameters of the unit, RULEBOOK §3).
  - Lean: x_final has about 10^5 rows: too large for an eval input. The unit reads x only through
    `matmul xT rows` (def:classification_is_made: rows -> xT -> matmul; nothing else reads rows), so the Lean is
    given the real fit, ncols = x.shape[1], rows = [] and `matmul` = the constant function returning the Gram
    matrix G that the sequential product computes on the real x_final (bits passed exactly). `solve` and `dot`
    are the stand-ins of fz4_cim_gen. This exercises everything of the unit after the product, on the real values.
    Note: with rows = [] the precondition clause "every row has length ncols" holds vacuously; the substitution
    is equal for the unit's result by the text quoted above, not by evaluation.
"""
from __future__ import annotations

import json
import struct
import sys
import tempfile
import warnings
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import fz4_cim_gen as g  # noqa: E402

from credit_risk import feature_engineering, sas_compat as sc, train  # noqa: E402

ROOT = HERE.parents[3]
WORK = HERE.parent / "work"
BLUEPRINT = "5365851c-5549-44b7-9207-4bd4c422031d"


def fb(x):
    return 0x7FF8000000000000 if x != x else struct.unpack("<Q", struct.pack("<d", float(x)))[0]


def lf(x):
    return f"(Float.ofBits {fb(x)})"


def main():
    rec = []
    orig = sc.classification_is_made

    def wrap(fit, x):
        r = orig(fit, x)
        rec.append((fit, np.array(x, dtype=np.float64), bool(r)))
        return r

    with tempfile.TemporaryDirectory(dir=WORK) as td:
        td = Path(td)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            feature_engineering.run(ROOT / "legacy" / "data", td / "fe", split_ids=HERE.parents[1] / "inputs" / "split_ids.csv")
            sc.classification_is_made = wrap
            try:
                train.run(td / "fe", td / "tr")
            finally:
                sc.classification_is_made = orig
            made = (td / "tr" / "printed_classification.csv").exists()
    assert len(rec) == 1, len(rec)
    fit, x, r_real = rec[0]
    n, k = x.shape
    # stand-in expected
    G = np.asarray(g.na(x).T.view(g.NA) @ g.na(x))
    g.FLAG["zero_pivot"] = False
    o = np.linalg.solve
    np.linalg.solve = g.solve_sa
    try:
        with np.errstate(all="ignore"):
            r_std = bool(sc.classification_is_made(fit, g.na(x)))
    finally:
        np.linalg.solve = o
    lo = sc._left_out(fit)
    names = "[" + ", ".join(json.dumps(s) for s in fit.names) + "]"
    cov = "[" + ", ".join("[" + ", ".join(lf(v) for v in row) + "]" for row in np.asarray(fit.cov)) + "]"
    beta = "[" + ", ".join(lf(v) for v in np.asarray(fit.beta)) + "]"
    Gt = "[" + ", ".join("[" + ", ".join(lf(v) for v in row) + "]" for row in G) + "]"
    solve = g.LEAN.split("let solve := ")[1].split("; let dot := ")[0]
    dot = g.LEAN.split("let dot := ")[1].split("; let matmul := ")[0]
    term = (f"({solve}) (fun (_ _ : List (List Float)) => ({Gt} : List (List Float))) ({dot}) "
            f"({{ names := {names}, beta := Np.NDArray.d1 {beta}, cov := Np.NDArray.d2 {cov}, loglik := {lf(fit.loglik)}, "
            f"n_iter := {int(fit.n_iter)}, converged := {'true' if fit.converged else 'false'} }} : LogisticFit Float) "
            f"(Np.NDArray.d2 []) {k}")
    out = {"blueprint": BLUEPRINT, "n_rows": n, "ncols": k, "names": list(fit.names), "left_out": lo,
           "cov_diag": [float(np.asarray(fit.cov)[i, i]) for i in range(len(fit.names))],
           "expected_standin": r_std, "real_numpy": r_real, "zero_pivot": g.FLAG["zero_pivot"],
           "printed_classification_written": made, "input": term}
    (WORK / "fz10_cim_real.json").write_text(json.dumps(out))
    (WORK / "fz10_cim_real.inputs.json").write_text(json.dumps([{"item": "def:classification_is_made",
                                                                  "decl": "classification_is_made", "inputs": [term]}]))
    print({k_: v for k_, v in out.items() if k_ != "input"})
    print(term)


if __name__ == "__main__":
    main()
