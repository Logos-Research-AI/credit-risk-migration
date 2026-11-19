"""x27 evaluation (2026-11-18, after the fifth port diff): def:run_py_py_py (train.py:20-987) on
def:zz_carrier_e, against the REAL train.run at HEAD. Built on t18_gen.py / u18b_gen.py (helpers
imported); what changes for the fifth diff:
  - model.json is written only when final is not None: the expected second component is `none`
    (Lean `Option`) or `some (intercept : Option, coefficients)`;
  - the numeric routines are tables keyed on the digests of their arguments, built GENERICALLY:
    every np.linalg.solve and np.linalg.inv call made outside stepwise_logistic is recorded (they
    now also come from sas_compat._kept, _solve_sas, _inv_sas, global_wald, classification_is_made);
    `dot` holds (b, r, b @ r) for every recorded solve (each solve in the port is followed by that
    dot); `matmul` holds x_k' x_k of every step with a variable, x_final' x_final and the ctable's
    x' (x w); `matvec` x_k' (y - ybar); `einsum` the ctable's leverage term; log1p / pow2 / chi2 /
    fsum as in t18.
Scenarios:
  C60     port/tests/data/x27_one_class/C60 model_features_{train,validation}.csv (42 / 18 rows; one
          outcome in training: stepwise.final None, no step)
  real    the T18 sample (60 / 25 rows of the real feature files, planted nulls): a fitted model

  PYTHONPATH=../../port uv run --project ../../port python diffeval/units/x27_train_gen.py [C60|real ...]
      -> diffeval/work/x27_train_<scenario>.json, .inputs.json, .in.txt
  ... --mask <scenario> <integer>   names the bits of the localisation mask
"""
from __future__ import annotations

import contextlib
import datetime as dt
import io
import json
import math
import sys
import tempfile
import warnings
from pathlib import Path

import numpy as np
import polars as pl

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))

import t18_gen as b  # noqa: E402
import u18b_gen as u  # noqa: E402
from suite import Suite  # noqa: E402

from credit_risk import sas_compat as sc  # noqa: E402
from credit_risk import train  # noqa: E402

ROOT = HERE.parents[3]
WORK = HERE.parent / "work"
fb, w, ts, o = b.fb, b.w, b.ts, b.o
BLUEPRINT = "5365851c-5549-44b7-9207-4bd4c422031d"


def real_run(ind: Path, encoded: bool) -> dict:
    """t18_gen.real_run with np.linalg.inv recorded as well and model.json optional."""
    rec: dict = {"imports": [], "writes": [], "chi2": [], "solve": [], "inv": [], "fsum": [], "stepwise": None,
                 "locals": None, "in_fit": False, "model_json": None}
    o_import, o_write, o_step, o_chi2 = sc.proc_import_csv, sc.write_sas_csv, sc.stepwise_logistic, sc.chi2_sf
    o_solve, o_inv, o_fsum = np.linalg.solve, np.linalg.inv, math.fsum

    def w_import(path, guessingrows=20):
        d = o_import(path, guessingrows=guessingrows)
        rec["imports"].append((Path(path).name, d.clone()))
        return d

    def w_write(df, path, formats=None):
        rec["writes"].append((Path(path).name, df.clone()))

    def w_step(*a, **k):
        rec["in_fit"] = True
        try:
            r = o_step(*a, **k)
        finally:
            rec["in_fit"] = False
        rec["stepwise"] = r
        return r

    def w_chi2(x, df):
        r = o_chi2(x, df)
        if not rec["in_fit"]:
            rec["chi2"].append((float(x), int(df), float(r)))
        return r

    def w_solve(a, bb):
        r = o_solve(a, bb)
        if not rec["in_fit"]:
            rec["solve"].append((np.array(a, dtype=np.float64), np.array(bb, dtype=np.float64), np.array(r, dtype=np.float64)))
        return r

    def w_inv(a):
        r = o_inv(a)
        if not rec["in_fit"]:
            rec["inv"].append((np.array(a, dtype=np.float64), np.array(r, dtype=np.float64)))
        return r

    def w_fsum(xs):
        xs = [float(x) for x in xs]
        r = o_fsum(xs)
        if not rec["in_fit"]:
            rec["fsum"].append((xs, float(r)))
        return r

    def prof(frame, event, arg):
        if event == "return" and frame.f_code is train.run.__code__:
            rec["locals"] = dict(frame.f_locals)

    math.fsum = w_fsum
    np.linalg.solve, np.linalg.inv = w_solve, w_inv
    sc.proc_import_csv, sc.write_sas_csv, sc.stepwise_logistic, sc.chi2_sf = w_import, w_write, w_step, w_chi2
    if encoded:
        for k, f in b.ENCODERS.items():
            setattr(sc, k, f)
    try:
        with tempfile.TemporaryDirectory() as td, warnings.catch_warnings():
            warnings.simplefilter("ignore")
            sys.setprofile(prof)
            try:
                with contextlib.redirect_stdout(io.StringIO()):
                    train.run(ind, Path(td))
            finally:
                sys.setprofile(None)
            if (Path(td) / "model.json").exists():
                rec["model_json"] = json.loads((Path(td) / "model.json").read_text())
    finally:
        math.fsum = o_fsum
        np.linalg.solve, np.linalg.inv = o_solve, o_inv
        sc.proc_import_csv, sc.write_sas_csv, sc.stepwise_logistic, sc.chi2_sf = o_import, o_write, o_step, o_chi2
        for k, f in b.REAL.items():
            setattr(sc, k, f)
    return rec


def routine_tables(rec: dict) -> dict:
    L = rec["locals"]
    stepwise, fit_frame, y_train, ybar, n_obs = rec["stepwise"], L["fit_frame"], L["y_train"], L["ybar"], L["n_obs"]
    T = {"solve": [], "matmul": [], "matvec": [], "dot": [], "inv": [], "einsum": [], "log1p": {}, "pow2": {}}
    for a, bb, r in rec["solve"]:
        T["solve"].append((b.mw(np.atleast_2d(a)), b.vw(bb), r))
        T["dot"].append((b.vw(bb), b.vw(r), float(bb @ r)))
    for a, r in rec["inv"]:
        T["inv"].append((b.mw(np.atleast_2d(a)), r))
    for st in stepwise.steps:
        names_k = st.fit.names
        if len(names_k) - 1 == 0:
            continue
        x_k = np.column_stack([np.ones(n_obs), *[np.asarray(fit_frame.get_column(c).to_numpy(), dtype=np.float64) for c in names_k[1:]]])
        d = y_train - ybar
        T["matvec"].append((b.mw(x_k.T), b.vw(d), x_k.T @ d))
        T["matmul"].append((b.mw(x_k.T), b.mw(x_k), x_k.T @ x_k))
    final = L["final"]
    if final is not None:
        x = L["x_final"]
        T["matmul"].append((b.mw(x.T), b.mw(x), x.T @ x))  # classification_is_made
        if L["ctable_made"]:
            p = np.asarray(L["pd_train"], dtype=np.float64)
            with np.errstate(all="ignore"):
                for v in p:
                    T["log1p"][fb(-v)] = fb(np.log1p(-v))
                wv = p * (1.0 - p)
                xw = x * wv[:, None]
                mm = x.T @ xw
                vi = sc._inv_sas(mm)  # noqa: SLF001 (the port's own routine; its inner inv / solve calls are recorded above)
                q = np.einsum("ij,jk,ik->i", x, vi, x)
            T["matmul"].append((b.mw(x.T), b.mw(xw), mm))
            T["einsum"].append((b.mw(x), b.mw(vi), q))
        for idx in [0, *L["final_index"]]:
            if idx in L["left_out"]:
                continue
            bb = float(final.beta[idx])
            se = math.sqrt(float(final.cov[idx, idx]))
            T["pow2"][fb(bb / se)] = fb((bb / se) ** 2)
    for row in L["hl_table"].iter_rows():
        _, _size, o1, e1, o0, e0 = row
        for v in (o1, e1, o0, e0):
            if v is None:
                break
        else:
            for v in (float(o1) - e1, float(o0) - e0):
                T["pow2"][fb(v)] = fb(v**2)
    T["chi2"] = sorted({(fb(x_), d_, fb(r_)) for x_, d_, r_ in rec["chi2"]})
    T["fsum"] = {b.vw(xs): fb(r_) for xs, r_ in rec["fsum"]}
    for k in ("solve", "matmul", "matvec", "dot", "einsum", "inv"):
        seen, rows = set(), []
        for row in T[k]:
            key = row[:2] if k != "inv" else row[:1]
            if key not in seen:
                seen.add(key)
                rows.append(row)
        T[k] = rows
    return T


def lean_routines(T: dict) -> str:
    T2 = dict(T)
    T2["inv"] = [(a, r) for a, r in T["inv"]]
    return b.lean_routines(T2)


def scenario_dir(name: str) -> Path:
    if name == "C60":
        return ROOT / "port" / "tests" / "data" / "x27_one_class" / "C60"
    if name == "real":
        return b.sample_inputs()
    raise SystemExit(f"unknown scenario {name}")


def lean_table_any(df: pl.DataFrame) -> str:
    return b.lean_table(df)


def build(name: str, mask: int | None = None):
    ind = scenario_dir(name)
    real = real_run(ind, encoded=False)
    rec = real_run(ind, encoded=True)
    n_fmt = b.check_real_against_encoded(real, rec)
    L, sw = rec["locals"], rec["stepwise"]
    (n1, mft), (n2, mfv) = rec["imports"]
    assert (n1, n2) == ("model_features_train.csv", "model_features_validation.csv")
    T = routine_tables(rec)
    today = dt.date.today()
    order = [n for n, _ in rec["writes"]]
    writes = dict(rec["writes"])
    assert len(writes) == len(order)
    print(f"[{name}] rows {mft.height}/{mfv.height}; final {None if sw.final is None else sw.final.names}; "
          f"steps {[(s.step, s.entered, s.removed) for s in sw.steps]}; ctable_made {L['ctable_made']}; "
          f"roc_valid_created {L['roc_valid_created']}; {len(order)} files: {order}")
    print(f"[{name}] files with no row: {[n for n in order if writes[n].height == 0]}; "
          f"solve {len(T['solve'])} inv {len(T['inv'])} matmul {len(T['matmul'])} chi2 {len(T['chi2'])} fsum {len(T['fsum'])}")

    lets = (b.W + b.BI + b.OF + b.TS + b.TX + b.TD + b.FL + b.MW + b.FMT + b.DEC + b.KEYED + u.MKFIT + lean_routines(T)
            + f"let SW := {u.lean_stepwise(sw)}; "
            + f'let today : Tabular.Cell Float := Tabular.Cell.str (some "{today.isoformat()}"); '
            + f"let tT := {lean_table_any(mft)}; let tV := {lean_table_any(mfv)}; "
            + "let RUN := run_py_py_py fw fo d8 d12 pv chi2 today SW fsum inv solve matmul matvec dot einsum log1p pow2; "
            + "let R := (RUN (some tT) (some tV)).getD ([], none); ")
    parts: list[tuple[str, list[str], list[int]]] = []

    def add(term, labels, exp):
        assert len(labels) == len(exp), term
        parts.append((term, labels, [int(x) for x in exp]))

    stops = b.stop_runs(ind) if name == "real" else None
    if stops is not None:
        add("[(if (RUN (some tT) (some tV)).isSome then 1 else 0), (if (RUN none (some tV)).isNone then 1 else 0), "
            "(if (RUN (some tT) none).isNone then 1 else 0), (if (RUN none none).isNone then 1 else 0)]",
            ["completed run is some", "stop: train file absent", "stop: validation file absent", "stop: both absent"], [1] + stops)
    else:
        add("[(if (RUN (some tT) (some tV)).isSome then 1 else 0)]", ["completed run is some"], [1])
    add("[(R.1.length : Int)]", ["number of files"], [len(order)])
    add("[W (R.1.flatMap (fun (p : String × Tabular.Table Float) => ts p.1))]", ["file names in write order"],
        [w([t for n in order for t in ts(n)])])
    for k, n in enumerate(order):
        add(f"TDN (R.1.getD {k} (\"\", []))", ["run: " + s for s in b.labels_tdn(n, writes[n])], b.tdn(n, writes[n]))
    add(f"TDN (R.1.getD {len(order)} (\"\", []))", ["no pair after the last file: name", "no pair after the last file: rows"], [w(ts("")), 0])
    mj = rec["model_json"]
    if mj is None:
        add("[(if R.2.isNone then 1 else 0)]", ["model.json not written (none)"], [1])
    else:
        add("[(match R.2 with | some (i, _) => W (o i) | none => -1), "
            "(match R.2 with | some (_, cs) => W (cs.flatMap (fun (p : String × Float) => ts p.1 ++ [bi p.2])) | none => -1)]",
            ["model.json intercept", "model.json coefficients (names, order, values)"],
            [w(o(mj["intercept"])), w([t for c, v in mj["coefficients"].items() for t in ts(c) + [fb(v)]])])
    add("[(SW.steps.length : Int), (match SW.final with | some f => W (f.names.flatMap ts) | none => -1)]",
        ["stepwise: steps", "stepwise: final.names"],
        [len(sw.steps), -1 if sw.final is None else w([t for c in sw.final.names for t in ts(c)])])

    labels = [lab for _, ls, _ in parts for lab in ls]
    if mask is not None:
        for k, lab in enumerate(labels):
            if (mask >> k) & 1:
                print(k, lab)
        return
    allexp = [e for _, _, exp in parts for e in exp]
    body = ("(let P : List (List Int) := [" + ", ".join(p[0] for p in parts) + "]; let ALL := P.flatten.toArray; "
            + 'let EXP : Array Int := ("' + "".join(chr(97 + e % b.SHORT) for e in allexp)
            + '".toList.map (fun (c : Char) => ((c.toNat : Int) - 97))).toArray; '
            + f"let mask := (List.range (max ALL.size EXP.size)).foldl (fun (m : Int) (i : Nat) => if ALL.getD i 0 % {b.SHORT} == EXP.getD i (-1) "
            + "then m else m + (2 : Int) ^ i) 0; P.map W ++ [mask, (ALL.size : Int)])")
    cases = [(f"{p[1][0]} .. {p[1][-1]}" if len(p[1]) > 1 else p[1][0], "run_py_py_py", w(p[2]), {"covers": len(p[2])}) for p in parts]
    cases.append(("localisation mask (bit i: value i differs modulo %d)" % b.SHORT, "run_py_py_py", 0))
    cases.append(("number of compared values", "run_py_py_py", len(allexp)))
    s = Suite(f"x27_train_{name}")
    s.item, s.decl = "def:zz_carrier_e", "zz_carrier_e"
    s.ints(lets, body, cases, use_kit=False)
    s.notes = {"run_py_py_py": (
        f"blueprint {BLUEPRINT}; port at HEAD (fifth diff); scenario {name}: real train.run on {mft.height} training / "
        f"{mfv.height} validation rows; final {None if sw.final is None else sw.final.names}; steps "
        f"{[(st.step, st.entered, st.removed) for st in sw.steps]}; {len(order)} files compared in write order, column by "
        f"column (a file with no row = the empty table: {[n for n in order if writes[n].height == 0]}), and model.json "
        f"({'not written' if mj is None else 'written'}); formatters = injective encodings ({n_fmt} formatted cells agree with "
        "the real formatters in Python); numeric routines = tables of the real results keyed on argument digests"
        + ("; the three stops against real stopped runs" if stops is not None else ""))}
    s.write()
    (WORK / f"x27_train_{name}.in.txt").write_text(s.inputs[0]["text"])
    print(f"[{name}] input {len(s.inputs[0]['text'])} chars; {len(allexp)} values")


if __name__ == "__main__":
    if len(sys.argv) > 3 and sys.argv[1] == "--mask":
        build(sys.argv[2], mask=int(sys.argv[3]))
    else:
        for nm in (sys.argv[1:] or ["C60", "real"]):
            build(nm)
