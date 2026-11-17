"""T-A of the update of 2026-11-17: def:classification_table (sas_compat.py:1236-1341, after both
port diffs) and def:train_run_08_ctable (train.py:416-455, resubmitted unchanged) against the port
as it stands. Blueprint 5365851c-... only.

  cd migration/port-to-lean && PYTHONPATH=../../port uv run --project ../../port python diffeval/units/ta_ctable_gen.py
      -> diffeval/work/ta_ct.json, ta_ct.inputs.json      (classification_table, direct calls)
         diffeval/work/ta_real.json, ta_real.inputs.json  (real train.run: classification_table on
                                                           the arguments train.run passed; step 08)
         diffeval/work/ta_coverage.json                    (which branch each case takes)
  eval_decl each input on def:zz_carrier_t; fuzz_collect.py 6 ta_ct ta_real; compare.py

The harness is that of b5_gen.py (ct_case: the frame tokenised by hand, one digest per case; the
library routines are doubles keyed on the bits of the arguments numpy received) and of tc_gen.py
(the real train.run on feature samples, formatters as injective encodings).

Suite ta_ct
  intercept-only (x = one column of ones): every n = 2..11 with every number of events 0..n
      (events first, then non-events; plus alternating orders), n = 26, 51, 101 (the leave-one-out
      means are multiples of 0.04 / 0.02 / 0.01: probabilities equal to printed levels), y with a
      value 2, call shapes kw / inventory order / fit / fit+kw
  fits with effects: the seven data sets of b5_ct (same seeds), and data whose leave-one-out
      probability is exactly 1.0 or above 0.98 (khi = 50: the level printed 1.000 counts nobody)
Python raises (recorded in ta_coverage.json, no Lean case): intercept-only with one row.
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import numpy as np
import polars as pl

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))

import b5_gen as b5  # noqa: E402
import kit  # noqa: E402
import leanterm as lt  # noqa: E402
import tc_gen as tc  # noqa: E402
from suite import Suite  # noqa: E402

from credit_risk import sas_compat as sc  # noqa: E402

WORK = HERE.parent / "work"
BLUEPRINT = "5365851c-5549-44b7-9207-4bd4c422031d"
CB = b5.BI + b5.OF + b5.TS + b5.TCOL + b5.FT + b5.FL + b5.TAB1 + b5.CLET
COV: dict[str, dict] = {}


def coverage(cid: str, y, x, pd=None, fit=None):
    """Which branches the case takes. A replication of sc:1273-1305 for the record only: the
    expected values of the cases come from sc.classification_table itself."""
    y, x = np.asarray(y, dtype=np.float64), np.asarray(x, dtype=np.float64)
    with np.errstate(all="ignore"):
        if pd is not None:
            p = np.asarray(pd, dtype=np.float64)
            eta = np.log(p) - np.log1p(-p)
        else:
            eta = x @ fit.beta
            p = sc._expit(eta)
        w = p * (1.0 - p)
        v = np.linalg.inv(x.T @ (x * w[:, None]))
        q = np.einsum("ij,jk,ik->i", x, v, x)
        ps = sc._expit(eta - (y - p) * q / (1.0 - w * q))
        tol = 0.0
        if x.shape[1] == 1:
            ps = (float(y.sum()) - y) / (len(y) - 1.0)
            tol = 1e-9
    klo = math.floor(float(ps.min()) / 0.02 + tol)
    khi = math.ceil(float(ps.max()) / 0.02 - tol)
    grid = [float(z) for z in np.round(np.arange(klo, khi + 1) * 0.02, 3)]
    COV[cid] = {
        "intercept_only": bool(x.shape[1] == 1), "n": int(len(y)), "klo": klo, "khi": khi, "levels": len(grid),
        "khi_is_50": khi == 50,
        "ps_equal_to_1": int(np.count_nonzero(ps == 1.0)),
        "ps_equal_to_a_printed_level": int(sum(1 for t in ps if float(t) in grid)),
        "ps_within_1e-9_of_a_level_not_equal": int(sum(1 for t in ps if float(t) not in grid and min(abs(float(t) - g) for g in grid) < 1e-9)),
    }


# Intercept-only cases, compact: y as a string of digits, x = n rows [1.0], pd constant. The five
# routines are doubles that return nothing ([] / a sentinel): on this branch the result may not
# depend on them (Python computes the logit step with the real routines and discards it).
ICLET = (b5.BI + b5.OF + b5.TS + b5.TCOL + b5.FT
         + "let NI := fun (_ : List (List Float)) => ([] : List (List Float)); "
         "let NM := fun (_ _ : List (List Float)) => ([] : List (List Float)); "
         "let NV := fun (_ : List (List Float)) (_ : List Float) => ([] : List Float); "
         "let NE := fun (_ _ : List (List Float)) => ([] : List Float); "
         f"let NL := fun (_ : Float) => Float.ofBits {b5.SENT}; "
         "let IC := fun (s : String) (pb bb : UInt64) (sh : Nat) => "
         "let y : FloatArray_ Float := Np.NDArray.d1 (s.toList.map (fun (c : Char) => Float.ofNat (c.toNat - 48))); "
         "let x : FloatArray_ Float := Np.NDArray.d2 (List.replicate s.length [1.0]); "
         "let p : FloatArray_ Float := Np.NDArray.d1 (List.replicate s.length (Float.ofBits pb)); "
         'let f : LogisticFit Float := { names := ["Intercept"], beta := Np.NDArray.d1 [Float.ofBits bb], cov := Np.NDArray.d2 [], loglik := -1.0, n_iter := 1, converged := true }; '
         "ft (if sh == 0 then classification_table (α := Float) NI NM NV NE NL y x none (some p) "
         "else if sh == 1 then classification_table (α := Float) NI NM NV NE NL x y (some (Sum.inr p)) none "
         "else if sh == 2 then classification_table (α := Float) NI NM NV NE NL y x (some (Sum.inl f)) none "
         "else classification_table (α := Float) NI NM NV NE NL y x (some (Sum.inl f)) (some p)); ")
SHAPES = {"kw": 0, "inv": 1, "fit": 2, "fit+kw": 3}


def icpt(cid: str, y: list[float], shape: str = "kw", pdv: float | None = None):
    n = len(y)
    assert all(v == int(v) and 0 <= v <= 9 for v in y)
    x = np.ones((n, 1))
    pdv = 0.3 if pdv is None else pdv
    pd = np.full(n, pdv)
    beta = [math.log(pdv) - math.log1p(-pdv)]
    fit = sc.LogisticFit(["Intercept"], np.array(beta), np.eye(1), -1.0, 1, True)
    ya = np.array(y, dtype=np.float64)
    with np.errstate(all="ignore"):
        if shape == "kw":
            res = sc.classification_table(ya, x, pd=pd)
        elif shape == "inv":
            res = sc.classification_table(x, ya, pd)
        elif shape == "fit":
            res = sc.classification_table(ya, x, fit)
        else:
            res = sc.classification_table(ya, x, fit, pd=pd)
    coverage(cid, y, x, pd=pd if shape != "fit" else None, fit=fit)
    res = res.with_columns(pl.col("CorrectNonevents").cast(pl.Float64), pl.col("IncorrectNonevents").cast(pl.Float64))  # R-F2I
    term = f'IC "{"".join(str(int(v)) for v in y)}" {b5.fb(pdv)} {b5.fb(beta[0])} {SHAPES[shape]}'
    return (cid, "classification_table", term, b5.frame_tok(res))


def suite_ct() -> b5.Cases:
    cs = b5.Cases("ta_ct")
    # ---- intercept only, n = 2..11, every number of events
    ic = []
    for n in range(2, 12):
        ic += [icpt(f"icpt n={n} events={k} (events first)", [1.0] * k + [0.0] * (n - k)) for k in range(n + 1)]
    for n in (2, 3, 5, 6, 10, 11):
        y = [float(i % 2) for i in range(n)]
        ic.append(icpt(f"icpt n={n} alternating 0,1", y, shape="inv"))
        y = [float(i % 3 == 0) for i in range(n)]
        ic.append(icpt(f"icpt n={n} every third an event (fit given)", y, shape="fit", pdv=0.4))
    # ---- intercept only, means equal to printed levels
    for n, ks in ((26, (0, 1, 5, 13, 25, 26)), (51, (1, 10, 15, 25, 35, 50)), (101, (7, 50, 100))):
        for k in ks:
            y = [1.0 if (i * 7) % n < k else 0.0 for i in range(n)]
            assert sum(y) == k
            ic.append(icpt(f"icpt n={n} events={k} (spread)", y, shape="fit+kw" if k == 25 else "kw", pdv=0.6))
    ic += [icpt("icpt n=6 y=[2,0,0,0,1,0]: a value 2, probabilities up to 0.6", [2.0, 0.0, 0.0, 0.0, 1.0, 0.0]),
           icpt("icpt n=4 y=[1,1,0,0], pd 0.999", [1.0, 1.0, 0.0, 0.0], pdv=0.999),
           icpt("icpt n=3 y=[0,1,0], pd 1e-300 (the logit step is discarded)", [0.0, 1.0, 0.0], pdv=1e-300)]
    for i in range(0, len(ic), 36):
        cs.group(ICLET, ic[i:i + 36], gen=False)

    # ---- fits with effects
    def data(sd, n, k, pm, poff, ym=2):
        cols = [[1.0] * n] + [b5.gv(sd + 10 * j, n, 33, 16, 8.0) for j in range(1, k)]
        lx = "(GX [List.replicate " + str(n) + " 1.0" + "".join(f", GV {sd + 10 * j} {n} 33 16 8.0" for j in range(1, k)) + "])"
        x = np.array(cols).T
        y = b5.gv(sd + 1, n, ym, 0, 1.0)
        pd = np.array(b5.gv(sd + 2, n, pm, poff, 100.0))
        return f"(GV {sd + 1} {n} {ym} 0 1.0)", lx, f"(GV {sd + 2} {n} {pm} ({poff}) 100.0)", y, x, pd

    def fitrec(beta, k):
        f = sc.LogisticFit(["Intercept"] + [f"x{j}" for j in range(1, k)], np.array(beta, dtype=np.float64), np.eye(k), -1.0, 1, True)
        lfit = ('({ names := ["Intercept"' + "".join(f', "x{j}"' for j in range(1, k)) + "], beta := Np.NDArray.d1 " + b5.fl(beta)
                + ", cov := Np.NDArray.d2 [], loglik := -1.0, n_iter := 1, converged := true } : LogisticFit Float)")
        return f, lfit

    def eff(cid, d, shape, fit=None, lfit=None):
        coverage(cid, d[3], d[4], pd=None if shape == "fit" else d[5], fit=fit)
        return b5.ct_case(cid, *d, shape, fit=fit, lfit=lfit)

    D1 = data(100, 24, 2, 90, -5)
    D2 = data(200, 40, 3, 60, -20)
    D3 = data(300, 30, 2, 9, -1)
    D4 = data(400, 30, 2, 9, -91)
    D5 = data(500, 16, 2, 98, -1, ym=1)
    D6 = data(600, 28, 3, 50, -25, ym=3)
    D7 = data(700, 20, 2, 1, -50)
    f0, l0 = fitrec([0.0, 0.0], 2)
    f1, l1 = fitrec([-0.75, 0.5], 2)
    ef: list = []
    ef += [eff("effects: kw pd, n=24 k=2", D1, "kw")]
    ef += [eff("effects: inventory order (X, y, pd), n=24 k=2", D1, "inv")]
    ef += [eff("effects: kw pd, n=40 k=3", D2, "kw")]
    ef += [eff("effects: kw pd low, n=30", D3, "kw"), eff("effects: kw pd high, n=30 (khi = 50)", D4, "inv")]
    ef += [eff("effects: y all 0", D5, "kw"), eff("effects: y in {0,1,2}", D6, "kw")]
    ef += [eff("effects: fit beta = 0 (eta = 0, p = 0.5)", D7, "fit", fit=f0, lfit=l0),
                  eff("effects: fit and pd keyword: pd is used", D1, "fit+kw", fit=f1, lfit=l1),
                  eff("effects: positional array and pd keyword", D3, "arr+kw")]
    ef += [eff("effects: fit beta = (-0.75, 0.5)", D1, "fit", fit=f1, lfit=l1)]
    # ---- khi = 50 with probabilities exactly 1.0 on a fit with a variable
    f2, l2 = fitrec([0.0, 20.0], 2)   # eta = 20 * x1, x1 in -2 .. 2: _expit(40) = 1.0
    f3, l3 = fitrec([30.0, 5.0], 2)   # eta in 20 .. 40
    ef += [eff("effects: fit beta = (0, 20): probabilities 0 and 1 (separated)", D1, "fit", fit=f2, lfit=l2)]
    ef += [eff("effects: fit beta = (30, 5): every probability near 1", D1, "fit", fit=f3, lfit=l3)]
    # pd one ulp below 1 on some rows
    n = 12
    x = np.array([[1.0, float(i % 4) - 1.5] for i in range(n)])
    pd = np.array([0.9999999999999999 if i % 3 == 0 else 0.5 + 0.03 * i for i in range(n)])
    y = [float(i % 2) for i in range(n)]
    lx = "[" + ", ".join(b5.fl(r) for r in x) + "]"
    coverage("effects: pd one ulp below 1 on four rows", y, x, pd=pd)
    ef += [b5.ct_case("effects: pd one ulp below 1 on four rows", b5.fl(y), lx, b5.fl(pd), y, x, pd, "kw")]
    for i in range(0, len(ef), 7):
        cs.group(CB, ef[i:i + 7], gen=True)
    note = ("T-A 2026-11-17, blueprint " + BLUEPRINT + ": intercept-only fits (every n = 2..11 with every number of events; "
            "n = 26, 51, 101 with probabilities equal to printed levels; four call shapes), fits with effects (the b5_ct data, "
            "and khi = 50 with probabilities exactly 1.0); routines as keyed doubles (intercept-only: doubles that return nothing); branch facts in work/ta_coverage.json")
    cs.notes = {"classification_table": note}
    return cs


# ---------------------------------------------------------------- real train.run
EFFECTS_PART = (45, 90)  # rows of the training file of tc_gen's scenario `effects` kept in `effects_part`


def scenario_dir(name: str) -> Path:
    """tc_gen's scenarios; `effects_part` is training rows 45..89 of tc_gen's `effects` (90 rows;
    slice chosen by experiments/ta_effects_part_search.py), to keep the step-08 input near 10 000
    characters. The input of the full 90-row sample (21151 characters) was evaluated once and
    came back `notRun`; at that moment def:zz_carrier_t had lost its connection to step 08 (the
    carrier had been cleared by another translator's write), so that run says nothing about
    the Lean, and it was not repeated."""
    if name != "effects_part":
        return tc.scenario_dir(name)
    src, ind = tc.scenario_dir("effects"), tc.DATA / "ta_effects_part"
    if not (ind / "model_features_train.csv").exists():
        ind.mkdir(parents=True, exist_ok=True)
        d = sc.proc_import_csv(src / "model_features_train.csv", guessingrows=None)
        d[EFFECTS_PART[0]:EFFECTS_PART[1]].write_csv(ind / "model_features_train.csv")
        (ind / "model_features_validation.csv").write_bytes((src / "model_features_validation.csv").read_bytes())
    return ind


def suite_real() -> Suite:
    st = Suite("ta_real")
    st.item, st.decl = tc.ITEM, tc.DECL
    for name in ("real", "effects_part", "icpt_only"):
        ind = scenario_dir(name)
        calls = []
        o_ct = sc.classification_table

        def w_ct(*a, _o=o_ct, _c=calls, **k):
            _c.append((a, k))
            return _o(*a, **k)

        sc.classification_table = w_ct
        try:
            r = tc.real_run(ind, True)
        finally:
            sc.classification_table = o_ct
        assert r["raised"] is None, (name, r["raised"])
        assert len(calls) == 1 and list(calls[0][1]) == ["pd"] and len(calls[0][0]) == 2
        (y, x), pd = calls[0][0], calls[0][1]["pd"]
        L = r["locals"]
        fin, mask, nobs = L["final"], [bool(b) for b in L["fit_mask"]], int(L["n_obs"])
        assert np.array_equal(y, L["y_train"]) and x.shape == (nobs, len(fin.names))
        cid = f"{name}: classification_table on the arguments of train.run ({nobs} rows, {x.shape[1]} column(s))"
        coverage(cid, y, x, pd=pd)
        # ---- (a) the unit on the arguments train.run passed (same routine doubles as (b))
        lx = "[" + ", ".join(b5.fl(row) for row in x) + "]"
        res = sc.classification_table(y, x, pd=pd)
        res = res.with_columns(pl.col("CorrectNonevents").cast(pl.Float64), pl.col("IncorrectNonevents").cast(pl.Float64))  # R-F2I
        # ---- (b) step 08 on the values train.run held; routines as in ct_case
        with np.errstate(all="ignore"):
            p = np.asarray(pd, dtype=np.float64)
            l1v = {b5.fb(-v): b5.fb(np.log1p(-v)) for v in p}
            wv = p * (1.0 - p)
            xw = x * wv[:, None]
            mm = x.T @ xw
            v = np.linalg.inv(mm)
            q = np.einsum("ij,jk,ik->i", x, v, x)
        m2 = lambda m: "[" + ", ".join(b5.fl(row) for row in m) + "]"  # noqa: E731
        ff = L["fit_frame"]
        lst = L["logit_scored_train"].get_column("pd_logistic").to_list()
        assert len(lst) == len(mask)
        printed = dict(r["writes"])["printed_classification.csv"]
        lets = (b5.W + CB + b5.FCOL + tc.LETS
                + f"let inv := KINV {b5.mw(mm)} {m2(v)}; let matmul := KMM {b5.mw(x.T)} {b5.mw(xw)} {m2(mm)}; "
                + "let matvec := fun (_ : List (List Float)) (_ : List Float) => ([] : List Float); "
                + f"let einsum := KEQ {b5.mw(x)} {b5.mw(v)} {b5.fl(q)}; "
                + "let log1p := T1 [" + ", ".join(f"({a}, {b})" for a, b in l1v.items()) + "]; "
                + f"let mask : List Bool := [{', '.join('true' if b else 'false' for b in mask)}]; "
                + "let ff : Pl.Frame Float := [" + ", ".join(
                    f"({lt.lean_str(c)}, {b5.fcol(ff.get_column(c).to_list())})" for c in fin.names[1:]) + "]; "
                + f"let fin := mkfit [{', '.join(lt.lean_str(c) for c in fin.names)}] {tc.ul(fin.beta)} "
                  f"[{', '.join(tc.ul(row) for row in np.atleast_2d(fin.cov))}] {b5.fb(fin.loglik)} ({int(fin.n_iter)}) {'true' if fin.converged else 'false'}; "
                + f"let ytr : List Float := {b5.fl(y)}; "
                + f"let lst : Pl.Frame Float := [(\"pd_logistic\", {b5.fcol(lst)})]; ")
        body = f"EF [train_run_08_ctable (α := Float) fw inv matmul matvec einsum log1p mask ff fin ({nobs}) ytr lst]"
        exp = tc.ef([("printed_classification.csv", printed)])
        cases = [(f"{name}: step 08: {lab}", "train_run_08_ctable", val)
                 for lab, val in zip(["number of files", f"printed_classification.csv ({printed.height} rows)"], exp, strict=True)]
        if x.shape[1] == 1:
            # the unit called directly on the same arguments. Only on the intercept-only run: on the
            # two runs with effects step 08 alone carries the table (every value of the frame goes
            # through the injective encoding of fmt_wd), which keeps those inputs a third shorter.
            body += (f" ++ [W (ft (classification_table (α := Float) inv matmul matvec einsum log1p (Np.NDArray.d1 ytr) (Np.NDArray.d2 {lx}) none "
                     f"(some (Np.NDArray.d1 {b5.fl(pd)}))))]")
            cases.append((cid, "classification_table", b5.w(b5.frame_tok(res))))
        st.ints(lets, body, cases, gen=True, table=True)
        print(f"{name}: x_final {x.shape}, final.names {fin.names}, printed_classification {printed.height} rows, {COV[cid]}")
    note = ("T-A 2026-11-17, blueprint " + BLUEPRINT + ": the real train.run on three samples of the real feature files (tc_gen.py; the second is training rows 45..89 of its `effects`: "
            "two models with effects, one intercept-only final model); step 08 on the values train.run held (and, on the intercept-only run, the unit on the arguments train.run passed), fmt_wd as an injective encoding")
    st.notes = {"classification_table": note, "train_run_08_ctable": note}
    return st


def raises():
    out = {}
    for label, y, x, pd in (("intercept-only, one row", [1.0], np.ones((1, 1)), np.array([0.3])),
                            ("intercept-only, no row", [], np.ones((0, 1)), np.array([]))):
        try:
            with np.errstate(all="ignore"):
                sc.classification_table(np.array(y), x, pd=pd)
            out[label] = "returned"
        except Exception as ex:  # noqa: BLE001
            out[label] = f"{type(ex).__name__}: {ex}"
    return out


if __name__ == "__main__":
    a = suite_ct().suite()
    a.item, a.decl = tc.ITEM, tc.DECL
    a.write()
    b = suite_real()
    b.write()
    for st in (a, b):
        print(st.name, len(st.inputs), "inputs;", len(st.cases), "cases; longest input", max(len(i["text"]) for i in st.inputs), "chars")
    rz = raises()
    (WORK / "ta_coverage.json").write_text(json.dumps({"python_raises": rz, "cases": COV}, indent=1) + "\n")
    c = list(COV.values())
    print("python raises:", rz)
    print("coverage:", {
        "cases": len(c), "intercept_only": sum(v["intercept_only"] for v in c),
        "intercept khi=50": sum(v["intercept_only"] and v["khi_is_50"] for v in c),
        "effects khi=50": sum((not v["intercept_only"]) and v["khi_is_50"] for v in c),
        "effects with ps == 1.0": sum((not v["intercept_only"]) and v["ps_equal_to_1"] > 0 for v in c),
        "intercept with ps equal to a level": sum(v["intercept_only"] and v["ps_equal_to_a_printed_level"] > 0 for v in c),
        "ps within 1e-9 of a level, not equal": sum(v["ps_within_1e-9_of_a_level_not_equal"] > 0 for v in c),
    })
