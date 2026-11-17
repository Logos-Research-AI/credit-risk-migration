"""port-translator-9, update 2026-11-17: differential test of the train composition def:run_py_py_py
after the port changes of 2026-11-16/17 (blueprint 5365851c-5549-44b7-9207-4bd4c422031d).

Adapted from units/t18_gen.py (imported for its helpers; t18 itself is unchanged). Same method: the
REAL train.run under recorders, formatters as injective encodings, numeric routines as tables of what
the real routines returned, `fsum` keyed on the digest of its argument. What is new:
  - the files are compared as the run wrote them: the list of names in write order (a file not
    written has no pair), every table column by column; a file with a header and no row is the
    empty table (RULEBOOK section 6);
  - LogisticFit literals carry `separation`;
  - a step with q = 0 calls no solve (train.py:179-189);
  - only the composition is evaluated (the steps are their owners' units).

Scenarios (one eval input each, on def:zz_carrier_c):
  real      the T18 sample: 60 training rows / 25 validation rows of the real feature files (its
            validation outcomes are all 0 or null: a validation set of one class), and the three
            stops (a feature file absent) against real stopped runs
  twoclass  the first 40 / 14 rows of that sample with the validation outcome of rows 2 and 7 set
            to 1: a validation set of two classes
  ionly     30 / 10 rows with the training outcome permuted (first seed for which the final model
            has the intercept only)

  PYTHONPATH=../../port uv run --project ../../port python diffeval/units/u18b_gen.py [scenario ...]
      -> diffeval/work/u18b_<scenario>.json + .inputs.json
  ... u18b_gen.py --mask <scenario> <integer>   names the bits of the localisation mask
"""
from __future__ import annotations

import contextlib
import datetime as dt
import io
import json
import math
import random
import sys
from pathlib import Path

import numpy as np
import polars as pl

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))

import t18_gen as b  # noqa: E402
from suite import Suite  # noqa: E402

from credit_risk import sas_compat as sc  # noqa: E402

BLUEPRINT = "5365851c-5549-44b7-9207-4bd4c422031d"
WORK = HERE.parent / "work"
fb, w, ts, o = b.fb, b.w, b.ts, b.o


def write_pair(d: Path, tr: pl.DataFrame, va: pl.DataFrame) -> Path:
    d.mkdir(parents=True, exist_ok=True)
    tr.write_csv(d / "model_features_train.csv")
    va.write_csv(d / "model_features_validation.csv")
    return d


def try_run(ind: Path):
    try:
        return b.real_run(ind, encoded=True)
    except Exception as e:  # noqa: BLE001
        return e


def scenario_dir(name: str) -> Path:
    real = b.sample_inputs()
    if name == "real":
        return real
    tr = sc.proc_import_csv(real / "model_features_train.csv", guessingrows=None)
    va = sc.proc_import_csv(real / "model_features_validation.csv", guessingrows=None)
    d = WORK / "u18b_data" / name
    if name == "twoclass":
        va2 = va.head(14).with_columns(
            pl.when(pl.int_range(pl.len()).is_in([2, 7])).then(1.0).otherwise(pl.col("default_flag")).alias("default_flag"))
        return write_pair(d, tr.head(40), va2)
    if name == "ionly":
        base = tr.head(30)
        flags = base.get_column("default_flag").to_list()
        for seed in range(400):
            f2 = flags[:]
            random.Random(seed).shuffle(f2)
            write_pair(d, base.with_columns(pl.Series("default_flag", f2, dtype=pl.Float64)), va.head(10))
            r = try_run(d)
            if not isinstance(r, Exception) and r["stepwise"].final.names == ["Intercept"]:
                print(f"[ionly] seed {seed}: steps {[(s.step, s.entered, s.removed) for s in r['stepwise'].steps]}")
                return d
        raise SystemExit("no seed gives an intercept-only final model")
    raise SystemExit(f"unknown scenario {name}")


MKFIT = ("let mkfit := fun (names : List String) (beta : List UInt64) (cov : List (List UInt64)) (ll : UInt64) (ni : Int) (cv : Bool) "
         "(sep : Option String) => "
         "({ names := names, beta := Np.NDArray.d1 (FL beta), cov := Np.NDArray.d2 (cov.map FL), loglik := Float.ofBits ll, "
         "n_iter := ni, converged := cv, separation := sep } : LogisticFit Float); ")


def lean_fit(f: sc.LogisticFit) -> str:
    sep = "none" if f.separation is None else f"(some {b.lstr(f.separation)})"
    return (f"(mkfit [{', '.join(b.lstr(n) for n in f.names)}] {b.ul(f.beta)} {b.ull(np.atleast_2d(f.cov))} {fb(f.loglik)} "
            f"({int(f.n_iter)}) {'true' if f.converged else 'false'} {sep})")


def lean_stepwise(r: sc.StepwiseResult) -> str:
    old = b.lean_fit
    b.lean_fit = lean_fit
    try:
        return b.lean_stepwise(r)
    finally:
        b.lean_fit = old


def routine_tables(rec: dict) -> dict:
    """Argument / result pairs of the out-of-scope routines, from the captured run (t18's, with the
    steps of q = 0 skipped: train.py:179-189 `continue` before any numpy call)."""
    L = rec["locals"]
    stepwise, fit_frame, y_train, ybar, n_obs, final = rec["stepwise"], L["fit_frame"], L["y_train"], L["ybar"], L["n_obs"], L["final"]
    T = {"solve": [], "matmul": [], "matvec": [], "dot": [], "inv": [], "einsum": [], "log1p": {}, "pow2": {}}
    solves = list(rec["solve"])
    for st in stepwise.steps:
        names_k = st.fit.names
        if len(names_k) - 1 == 0:
            continue
        x_k = np.column_stack([np.ones(n_obs), *[np.asarray(fit_frame.get_column(c).to_numpy(), dtype=np.float64) for c in names_k[1:]]])
        d = y_train - ybar
        u0 = x_k.T @ d
        g = x_k.T @ x_k
        i0 = ybar * (1.0 - ybar) * g
        a1, b1, s1 = solves.pop(0)
        assert b.mw(a1) == b.mw(i0) and b.vw(b1) == b.vw(u0)
        score = u0 @ s1
        b_slope = st.fit.beta[1:]
        a2, b2, s2 = solves.pop(0)
        assert b.mw(a2) == b.mw(st.fit.cov[1:, 1:]) and b.vw(b2) == b.vw(b_slope)
        wald = b_slope @ s2
        T["matvec"].append((b.mw(x_k.T), b.vw(d), u0))
        T["matmul"].append((b.mw(x_k.T), b.mw(x_k), g))
        T["solve"] += [(b.mw(a1), b.vw(b1), s1), (b.mw(a2), b.vw(b2), s2)]
        T["dot"] += [(b.vw(u0), b.vw(s1), float(score)), (b.vw(b_slope), b.vw(s2), float(wald))]
    assert not solves, "np.linalg.solve was called outside the steps with q != 0"
    x, p = L["x_final"], np.asarray(L["pd_train"], dtype=np.float64)
    with np.errstate(all="ignore"):
        for v in p:
            T["log1p"][fb(-v)] = fb(np.log1p(-v))
        wv = p * (1.0 - p)
        xw = x * wv[:, None]
        mm = x.T @ xw
        vi = np.linalg.inv(mm)
        q = np.einsum("ij,jk,ik->i", x, vi, x)
    T["matmul"].append((b.mw(x.T), b.mw(xw), mm))
    T["inv"].append((b.mw(mm), vi))
    T["einsum"].append((b.mw(x), b.mw(vi), q))
    for idx in [0, *L["final_index"]]:
        bb = float(final.beta[idx])
        se = math.sqrt(float(final.cov[idx, idx]))
        T["pow2"][fb(bb / se)] = fb((bb / se) ** 2)
    for _, _size, o1, e1, o0, e0 in L["hl_table"].iter_rows():
        for v in (float(o1) - e1, float(o0) - e0):
            T["pow2"][fb(v)] = fb(v**2)
    T["chi2"] = sorted({(fb(x_), d_, fb(r_)) for x_, d_, r_ in rec["chi2"]})
    T["fsum"] = {b.vw(xs): fb(r_) for xs, r_ in rec["fsum"]}
    for k in ("solve", "matmul", "matvec", "dot", "einsum"):
        seen, rows = set(), []
        for row in T[k]:
            if row[:2] not in seen:
                seen.add(row[:2])
                rows.append(row)
        T[k] = rows
    return T


def old_record() -> dict:
    """The T18 record (2026-11-16, work/t18_run.json): expected digest of each `run:` case, by label."""
    p = WORK / "t18_run.json"
    if not p.exists():
        return {}
    return {c["id"].split("/", 1)[1]: c["expected"] for c in json.loads(p.read_text())["cases"] if c["primitive"] == "run_py_py_py"}


def build(name: str, mask: int | None = None):
    ind = scenario_dir(name)
    real = b.real_run(ind, encoded=False)
    rec = b.real_run(ind, encoded=True)
    n_fmt = b.check_real_against_encoded(real, rec)
    L, sw = rec["locals"], rec["stepwise"]
    (n1, mft), (n2, mfv) = rec["imports"]
    assert (n1, n2) == ("model_features_train.csv", "model_features_validation.csv")
    T = routine_tables(rec)
    today = dt.date.today()
    ms = L["model_summary"]
    if ms.height:
        assert ms.get_column("training_date").to_list()[0] == today
    order = [n for n, _ in rec["writes"]]
    writes = dict(rec["writes"])
    assert len(writes) == len(order)
    print(f"[{name}] rows {mft.height}/{mfv.height}; final {sw.final.names}; steps {[(s.step, s.entered, s.removed, s.fit.separation) for s in sw.steps]}; "
          f"roc_valid_created {L['roc_valid_created']}; {len(order)} files: {order}")
    print(f"[{name}] files with no row: {[n for n in order if writes[n].height == 0]}")

    lets = (b.W + b.BI + b.OF + b.TS + b.TX + b.TD + b.FL + b.MW + b.FMT + b.DEC + b.KEYED + MKFIT + b.lean_routines(T)
            + f"let SW := {lean_stepwise(sw)}; "
            + f'let today : Tabular.Cell Float := Tabular.Cell.str (some "{today.isoformat()}"); '
            + f"let tT := {b.lean_table(mft)}; let tV := {b.lean_table(mfv)}; "
            + "let RUN := run_py_py_py fw fo d8 d12 pv chi2 today SW fsum inv solve matmul matvec dot einsum log1p pow2; "
            + "let R := (RUN (some tT) (some tV)).getD ([], (Float.ofBits 0, [])); ")
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
    add("[bi R.2.1, W (R.2.2.flatMap (fun (p : String × Float) => ts p.1 ++ [bi p.2]))]",
        ["model.json intercept", "model.json coefficients (names, order, values)"],
        [fb(mj["intercept"]), w([t for c, v in mj["coefficients"].items() for t in ts(c) + [fb(v)]])])
    add("[(SW.steps.length : Int), (match SW.final with | some f => W (f.names.flatMap ts) | none => -1), "
        "W (SW.steps.flatMap (fun (s : StepwiseStep Float) => (match s.fit.separation with | none => [0] | some e => 1 :: ts e)))]",
        ["stepwise: steps", "stepwise: final.names", "stepwise: separation of each step"],
        [len(sw.steps), w([t for c in sw.final.names for t in ts(c)]),
         w([t for s in sw.steps for t in ([0] if s.fit.separation is None else [1] + ts(s.fit.separation))])])

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
    s = Suite(f"u18b_{name}")
    s.item, s.decl = "def:zz_carrier_c", "zz_carrier_c"
    s.ints(lets, body, cases, use_kit=False)
    s.notes = {"run_py_py_py": (
        f"blueprint {BLUEPRINT}; scenario {name}: real train.run on {mft.height} training / {mfv.height} validation rows; final "
        f"{sw.final.names}; steps {[(st.step, st.entered, st.removed) for st in sw.steps]}; roc_valid_created {L['roc_valid_created']}; "
        f"{len(order)} files compared in write order, column by column (a file with no row = the empty table: "
        f"{[n for n in order if writes[n].height == 0]}), and model.json; formatters = injective encodings ({n_fmt} formatted cells "
        "agree with the real formatters in Python); numeric routines = tables of the real results"
        + ("; the three stops against real stopped runs" if stops is not None else ""))}
    s.write()
    (WORK / f"u18b_{name}.in.txt").write_text(s.inputs[0]["text"])
    if name == "real":  # against the T18 record of the same sample
        old = old_record()
        for term, labs, exp in parts:
            lab = f"{labs[0]} .. {labs[-1]}" if len(labs) > 1 else labs[0]
            if lab.startswith("run: "):
                print(f"[real vs T18 record] {lab.split(':')[1].strip():34s} {'same' if old.get(lab) == w(exp) else ('CHANGED' if lab in old else 'not in the T18 record')}")
        new_labels = {(f"{labs[0]} .. {labs[-1]}" if len(labs) > 1 else labs[0]) for _, labs, _ in parts}
        print("[real vs T18 record] files of the T18 record with no pair now:", sorted(k for k in old if k.startswith("run: ") and k not in new_labels))


if __name__ == "__main__":
    if len(sys.argv) > 3 and sys.argv[1] == "--mask":
        build(sys.argv[2], mask=int(sys.argv[3]))
    else:
        for nm in (sys.argv[1:] or ["real", "twoclass", "ionly"]):
            with contextlib.redirect_stdout(io.StringIO()) if False else contextlib.nullcontext():
                build(nm)
