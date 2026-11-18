"""Fuzz 2026-11-17 of def:train_run_02_stepwise_summary (revision latest), by a non-author.
Suite fz3_s02 on def:zz_carrier_t of blueprint 5365851c-5549-44b7-9207-4bd4c422031d.

  PYTHONPATH=../../port uv run --project ../../port python diffeval/units/fz3_step02_gen.py [first_seed [n_seeds [chunk]]]

The unit has no precondition item: every generated input is inside it (kept).
Seed s -> a StepwiseResult built INSIDE Lean (kit.GEN) and mirrored here (kit.gF / kit.gI):
  k = hsh(s, 0) % 7 steps (0 = no step: the empty table)
  step := gI(8s+5, k, 0, 1000, 500)   (negative, zero, positive; null -> 0)
  entered / removed := POOL[gI(8s+4 / 8s+6, k, 30, 10, 0)]  (null 30 %), POOL has "", a name of 20 characters,
      21, 30, a name with an accent, a name with an emoji, a space, "x"
  df, number_in_model := gI(8s+7, ..., 0, 6, 1) / gI(8s+8, ..., 0, 9, 0)  (df may be -1 or 0)
  score_chisq := gF(8s+1, k, 60, 30, E1)  Option (none, NaN, +-inf, +-0, 1e300, 1e-300, subnormal, 1.5e-16 +- 1 ulp, ...)
  wald_chisq  := gF(8s+2, k, 60, 30, E1)  (the NaN of a removal step with df 0 is in the pool)
  p_value     := gF(8s+3, k, 60, 30, E2)  Float (no none), 1e-4 and 1 and 0.05 each with one ulp either side
  fit := a fixed dummy (step 02 never reads it)
Formatters: injective stand-ins (as t18_gen ENCODERS) on both sides. The Python stand-in encodes NaN as
the canonical NaN bits and distinguishes "fmt_wd called on NaN" from "not called": the Lean stand-in
does the same through Float.toBits. Expected value: the REAL train.run (stepwise_logistic patched to
return the generated result, write_sas_csv recorded, stopped after the first write = stepwise_summary.csv).
One case = one seed: W (TDN (file name, table)) against w(tdn(name, df)).
"""
from __future__ import annotations

import json
import struct
import sys
import warnings
from pathlib import Path

import numpy as np
import polars as pl

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE.parents[3] / "port"))

import kit  # noqa: E402
import t18_gen as t  # noqa: E402
from suite import Suite  # noqa: E402

from credit_risk import sas_compat as sc  # noqa: E402
from credit_risk import train  # noqa: E402

BLUEPRINT = "5365851c-5549-44b7-9207-4bd4c422031d"
POOL = ["", "x", " ", "a" * 20, "b" * 21, "c" * 30, "café_" + "d" * 19, "\U0001F600" * 22]


def ulp(x, k):
    b = struct.unpack("<Q", struct.pack("<d", x))[0]
    return struct.unpack("<d", struct.pack("<Q", b + k))[0]


NAN = float("nan")
INF = float("inf")
E1 = [None, None, NAN, NAN, INF, -INF, 0.0, -0.0, 1e300, -1e300, 1e-300, 5e-324, 1.5e-16, ulp(1.5e-16, 1),
      ulp(1.5e-16, -1), 1.0, ulp(1.0, 1), ulp(1.0, -1), 3.84, 123456789.0, -0.00001, 0.99999999, 1e15, 1e16, 99999.99995]
E2 = [NAN, INF, -INF, 0.0, -0.0, 1e-4, ulp(1e-4, 1), ulp(1e-4, -1), 0.05, ulp(0.05, 1), 1.0, ulp(1.0, 1), ulp(1.0, -1),
      0.99995, 1e-300, 5e-324, 1e300, 0.5, 0.00005, 2.0]


def lf(x):
    if x is None:
        return "none"
    return f"(some (Float.ofBits {t.fb(x)}))"


def lf2(x):
    return f"(Float.ofBits {t.fb(x)})"


LEAN_E1 = "[" + ", ".join("none" if x is None else f"(some (Float.ofBits {t.fb(x)}))" for x in E1) + "]"
LEAN_E2 = "[" + ", ".join(f"(some (Float.ofBits {t.fb(x)}))" for x in E2) + "]"
LEAN_POOL = "[" + ", ".join(json.dumps(p, ensure_ascii=False) for p in POOL) + "]"

# the Lean side of seed s
LETS = (
    t.W + t.BI + t.TS + t.TX + t.TD + t.FMT
    + f"let E1 : List (Option Float) := {LEAN_E1}; let E2 : List (Option Float) := {LEAN_E2}; let POOL : List String := {LEAN_POOL}; "
    + 'let dum : LogisticFit Float := { names := ["Intercept"], beta := Np.NDArray.d1 [], cov := Np.NDArray.d2 [], loglik := Float.ofBits 0, n_iter := 0, converged := true }; '
    + "let mk := fun (s : Nat) => let k := (hsh s 0 % 7).toNat; "
    "let sc := gF (8*s+1) k 60 30 E1; let wd := gF (8*s+2) k 60 30 E1; let pv_ := gF (8*s+3) k 60 30 E2; "
    f"let en_ := gI (8*s+4) k 30 {len(POOL)} 0; let rm := gI (8*s+6) k 30 {len(POOL)} 0; "
    "let sp := gI (8*s+5) k 0 1000 500; let dfv := gI (8*s+7) k 0 6 1; let nim := gI (8*s+8) k 0 9 0; "
    "({ steps := (List.range k).map (fun (i : Nat) => ({ step := (sp.getD i none).getD 0, "
    "entered := (en_.getD i none).map (fun (j : Int) => POOL.getD j.toNat \"\"), "
    "removed := (rm.getD i none).map (fun (j : Int) => POOL.getD j.toNat \"\"), "
    "df := (dfv.getD i none).getD 0, number_in_model := (nim.getD i none).getD 0, "
    "score_chisq := (sc.getD i none), wald_chisq := (wd.getD i none), "
    "p_value := ((pv_.getD i none).getD (Float.ofBits 0)), fit := dum } : StepwiseStep Float)), "
    "final := none, intercept_only := none } : StepwiseResult Float); "
)


def build_result(s: int) -> sc.StepwiseResult:
    k = kit.hsh(s, 0) % 7
    scs = kit.gF(8 * s + 1, k, 60, 30, E1)
    wds = kit.gF(8 * s + 2, k, 60, 30, E1)
    pvs = kit.gF(8 * s + 3, k, 60, 30, E2)
    en = kit.gI(8 * s + 4, k, 30, len(POOL), 0)
    rm = kit.gI(8 * s + 6, k, 30, len(POOL), 0)
    sp = kit.gI(8 * s + 5, k, 0, 1000, 500)
    dfv = kit.gI(8 * s + 7, k, 0, 6, 1)
    nim = kit.gI(8 * s + 8, k, 0, 9, 0)
    dummy = sc.LogisticFit(["Intercept"], np.zeros(0), np.zeros((0, 0)), 0.0, 0, True)
    steps = [sc.StepwiseStep(sp[i], None if en[i] is None else POOL[en[i]], None if rm[i] is None else POOL[rm[i]],
                             dfv[i], nim[i], scs[i], wds[i], pvs[i], dummy) for i in range(k)]
    return sc.StepwiseResult(steps, None, None)


class Stop(Exception):
    pass


def real_step02(res: sc.StepwiseResult, ind: Path, imports: dict, outdir: Path):
    """train.run up to the first write_sas_csv, with the generated stepwise result."""
    got = {}
    base = sc.LogisticFit(["Intercept"], np.zeros(1), np.zeros((1, 1)), -1.0, 0, True)
    full = sc.StepwiseResult(res.steps, base, base)

    def w_write(df, path, formats=None):
        got["name"], got["df"] = Path(path).name, df.clone()
        raise Stop

    keep = (sc.stepwise_logistic, sc.write_sas_csv, sc.proc_import_csv, sc.fmt_wd, sc.sas_pvalue)
    sc.stepwise_logistic = lambda *a, **k: full
    sc.write_sas_csv = w_write
    sc.proc_import_csv = lambda path, guessingrows=20: imports[Path(path).name].clone()
    sc.fmt_wd = t.ENCODERS["fmt_wd"]
    sc.sas_pvalue = t.ENCODERS["sas_pvalue"]
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            try:
                train.run(ind, outdir)
            except Stop:
                pass
    finally:
        sc.stepwise_logistic, sc.write_sas_csv, sc.proc_import_csv, sc.fmt_wd, sc.sas_pvalue = keep
    assert got["name"] == "stepwise_summary.csv", got
    return got["name"], got["df"]


def main():
    first = int(sys.argv[1]) if len(sys.argv) > 1 else 5000
    n = int(sys.argv[2]) if len(sys.argv) > 2 else 2400
    chunk = int(sys.argv[3]) if len(sys.argv) > 3 else 400
    ind = t.sample_inputs()
    imports = {nm: sc.proc_import_csv(ind / nm, guessingrows=None) for nm in
               ("model_features_train.csv", "model_features_validation.csv")}
    # train.run creates output_dir first (mkdir): give it a throwaway one
    import tempfile
    td = tempfile.mkdtemp()
    global real_step02_dir
    s = Suite("fz3_s02")
    s.item, s.decl = "def:zz_carrier_t", "zz_carrier_t"
    stats = {"empty": 0, "nan_wald": 0, "none_wald": 0, "long_names": 0}
    for c0 in range(first, first + n, chunk):
        seeds = list(range(c0, min(c0 + chunk, first + n)))
        exp = []
        for sd in seeds:
            res = build_result(sd)
            name, df = _run(res, ind, imports, td)
            exp.append(t.w(t.tdn(name, df)))
            stats["empty"] += res.steps == []
            stats["nan_wald"] += any(x.wald_chisq is not None and x.wald_chisq != x.wald_chisq for x in res.steps)
            stats["none_wald"] += any(x.wald_chisq is None for x in res.steps)
            stats["long_names"] += any((x.entered or "") != (x.entered or "")[:20] for x in res.steps)
            # NaN wald cells must be empty and none -> "_" in the real run
        body = f"((List.range {len(seeds)}).map (fun (i : Nat) => let s := i + {c0};  W (TDN (train_run_02_stepwise_summary fw pv (mk s)))))"
        cases = [(f"seed{sd}", "train_run_02_stepwise_summary", e, {"fz": "kept"}) for sd, e in zip(seeds, exp)]
        s.ints(LETS, body, cases, gen=True, use_kit=False)
    s.write()
    (HERE.parent / "work" / "fz3_s02.fuzz.json").write_text(json.dumps({
        "fuzzer": "fuzzer-of-step-02", "generator": "diffeval/units/fz3_step02_gen.py", "blueprint": BLUEPRINT,
        "units": {"train_run_02_stepwise_summary": {
            "seeds": f"{first}..{first + n - 1}", "generated": n, "kept": n, "python_raises_inside_precondition": [],
            "note": f"no precondition item; stats {stats}; one case = one seed (W of the table digest)"}}}))
    print(stats)


def _run(res, ind, imports, td):
    global_td = Path(td)
    return real_step02(res, ind, imports, global_td)


if __name__ == "__main__":
    main()
