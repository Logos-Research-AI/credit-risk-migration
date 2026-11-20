"""Fidelity pass 2026-11-20 (third attempt), label train-a: REAL DATA for def:train_run_01_fit_frame,
def:train_run_02_stepwise_summary and def:train_run_04_score_train.

  cd migration/port-to-lean && PYTHONPATH=../../port uv run --project ../../port python diffeval/units/fz10c_train_a_real.py [--rerun]

Real inputs: work/fz10_trainb_real/model_features_train.csv, the feature file the port (HEAD 4a757fb) wrote from
legacy/data (diffeval/units/fz10_trainb_real_gen.py: fe.run(legacy/data, ..., split_ids=inputs/split_ids.csv)),
imported as train.py does (sas_compat.proc_import_csv, guessingrows=None); the REAL stepwise result:
sas_compat.stepwise_logistic(fit_frame, "default_flag", candidates, 0.05, 0.05) on the full real fit frame
(--rerun computes it, minutes; cached in work/fz10c_ta_real.pkl).
The eval input carries the real StepwiseResult (every step: step, entered, removed, df, number_in_model,
score/wald/p as exact floats; the step fits are not read by the three units and are a dummy; final and
intercept_only exact: names, beta, cov, loglik, n_iter, converged, separation) and WINDOWS of real rows (the full
105,000-row frame does not fit an eval input): rows chosen to cover the first rows, rows where a candidate or
default_flag is null (fit_mask false) if any, and the rows of the largest |eta| of the real final model.
Per window w: step 01 on (real stepwise, window) and step 04 on (step 01's candidates and fit_mask, real final,
window); step 02 once on (real stepwise, real final) with the injective stand-in formatters of
fz10c_train_a_gen.py. Expected values: the train.py segments executed (fz10c_train_a_gen.run01/run02/run04).
The Lean returns the list of case indices whose digest differs ([] = all equal).
"""
from __future__ import annotations

import json
import pickle
import sys
import time
from pathlib import Path

import numpy as np
import polars as pl

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))

import compare as cmp  # noqa: E402
import fz10c_train_a_gen as g  # noqa: E402
import kit  # noqa: E402

from credit_risk import sas_compat as sc  # noqa: E402

W = HERE.parent / "work"
FEAT = W / "fz10_trainb_real" / "model_features_train.csv"
PKL = W / "fz10c_ta_real.pkl"


def lf(x):
    return g.lf(float(x))


def lfc(x):
    """compact element of a typed `List Float` literal: an exact decimal, else Float.ofBits"""
    x = float(x)
    d = g.lean_float_decimal(x) if x == x and abs(x) != float("inf") and x != 0.0 else None
    if x == 0.0:
        return "-0.0" if str(x).startswith("-") else "0.0"
    if d is not None:
        return d if "." in d else d + ".0"
    return f"Float.ofBits {g.fb(x)}"


def lfl(xs):
    return "([" + ", ".join(lfc(x) for x in xs) + "] : List Float)"


def lean_fit(f):
    if f is None:
        return "none"
    beta = np.asarray(f.beta, dtype=np.float64)
    cov = np.asarray(f.cov, dtype=np.float64)
    assert beta.ndim == 1 and cov.ndim == 2
    b = lfl(beta.tolist())
    c = "(" + "[" + ", ".join("[" + ", ".join(lfc(x) for x in r) + "]" for r in cov.tolist()) + "] : List (List Float))"
    sep = "none" if f.separation is None else f"some {json.dumps(f.separation)}"
    return (f"some ({{ names := {g.ls(list(f.names))}, beta := Np.NDArray.d1 {b}, cov := Np.NDArray.d2 {c}, "
            f"loglik := {lf(f.loglik)}, n_iter := {int(f.n_iter)}, converged := {'true' if f.converged else 'false'}, "
            f"separation := {sep} }} : LogisticFit Float)")


def lopt(x):
    return "none" if x is None else f"(some {lf(x)})"


def lstr(x):
    return "none" if x is None else f"(some {json.dumps(x, ensure_ascii=False)})"


MKS = ("let mkS := fun (a : Int) (en rm : Option String) (d n : Int) (s w : Option Float) (p : Float) => "
       "({ step := a, entered := en, removed := rm, df := d, number_in_model := n, score_chisq := s, wald_chisq := w, "
       "p_value := p, fit := dum } : StepwiseStep Float); ")


def lean_steps(sw):
    out = []
    for st in sw.steps:
        out.append(f"mkS {int(st.step)} {lstr(st.entered)} {lstr(st.removed)} ({int(st.df)}) ({int(st.number_in_model)}) "
                   f"{lopt(st.score_chisq)} {lopt(st.wald_chisq)} {lf(st.p_value)}")
    return "[" + ", ".join(out) + "]"


def lean_data(df):
    """NM (column names) and D (one list of floats per column, every window's rows concatenated); all real columns
    are Float64 without null (asserted)."""
    for n in df.columns:
        assert df.schema[n] == pl.Float64 and df.get_column(n).null_count() == 0, n
    nm = g.ls(df.columns)
    d = "(" + "[" + ", ".join("[" + ", ".join(lfc(x) for x in df.get_column(n).to_list()) + "]" for n in df.columns) + "] : List (List Float))"
    return (f"let NM : List String := {nm}; let D : List (List Float) := {d}; "
            "let win := fun (rs : List Nat) => ((NM.zip D).map (fun (p : String × List Float) => "
            "(p.1, Pl.Col.f64 (rs.map (fun (i : Nat) => some (p.2.getD i 0.0))))) : Pl.Frame Float); ")


def lean_frame(df):
    cols = []
    for n in df.columns:
        s = df.get_column(n)
        k = g.cmp.canon_series(s)["kind"]
        if k == "f64":
            vals = s.to_list()
            if any(x is None for x in vals):
                v = "[" + ", ".join("none" if x is None else f"(some {lf(x)})" for x in vals) + "]"
            else:
                v = "(" + lfl(vals) + ".map some)"
            cols.append(f"({json.dumps(n)}, Pl.Col.f64 {v})")
        elif k == "int":
            v = "[" + ", ".join("none" if x is None else f"(some ({int(x)} : Int))" for x in s.to_list()) + "]"
            cols.append(f"({json.dumps(n)}, Pl.Col.int {v})")
        else:
            raise ValueError(f"column {n}: kind {k}")
    return "[" + ", ".join(cols) + "]"


def main():
    t0 = time.time()
    full = sc.proc_import_csv(FEAT, guessingrows=None)
    print("import", full.shape, round(time.time() - t0, 1), "s", "dtypes", set(map(str, full.dtypes)))
    if "--rerun" in sys.argv or not PKL.exists():
        ns = {"pl": pl, "np": np, "math": __import__("math"), "model_features_train": full}
        holder = {}

        def real_sw(*a, **k):
            holder["sw"] = sc.stepwise_logistic(*a, **k)
            return holder["sw"]
        import types
        ns["sas_compat"] = types.SimpleNamespace(stepwise_logistic=real_sw)
        exec(g.CODE01, ns)
        PKL.write_bytes(pickle.dumps(holder["sw"]))
        print("stepwise done", round(time.time() - t0, 1), "s")
    sw = pickle.loads(PKL.read_bytes())
    print("steps", len(sw.steps), "final", None if sw.final is None else sw.final.names)
    # windows
    cand_null = full.select(pl.any_horizontal(pl.col(*g.CANDS, "default_flag").is_null()).alias("m")).to_series()
    null_rows = [i for i, b in enumerate(cand_null.to_list()) if b]
    ns_full = g.run04(g.CANDS, [True] * full.height, sw.final, full)
    e = full.select((-ns_full["eta_train"]).alias("e")).to_series().to_numpy()
    order = np.argsort(np.abs(e))
    big = sorted(order[-3:].tolist())
    small = sorted(order[:2].tolist())
    windows = [list(range(0, 5)), big, small]
    if null_rows:
        windows.append(null_rows[:5])
    print("null rows", len(null_rows), "windows", windows)
    # expected
    cases, exp = [], []
    lean_cases = []
    allrows = [r for w in windows for r in w]
    data = lean_data(full[allrows])
    off = 0
    for k, rows in enumerate(windows):
        df = full[rows]
        local = list(range(off, off + len(rows)))
        off += len(rows)
        n1 = g.run01(sw, df)
        toks1 = (g.p_tT(n1["candidates"]) + g.p_tB([bool(b) for b in n1["fit_mask"].tolist()]) + g.p_frame(n1["fit_frame"])
                 + g.p_fit(n1["final"]) + g.p_fit(n1["intercept_only"]) + g.p_tI([n1["n_obs"]])
                 + g.p_tF(n1["y_train"].tolist()) + [g.fb(n1["ybar"])] + ([g.fb(n1["m2ll0"])] if sw.intercept_only is not None else []))
        pre1 = g.pre01(sw, df, n1)
        n4 = g.run04(n1["candidates"], n1["fit_mask"].tolist(), sw.final, df)
        pre4 = g.pre04_static(n1["candidates"], n1["fit_mask"].tolist(), sw.final, df) and g.pre04_exp(n4, df)
        toks4 = (g.p_tT(n4["final_names"]) + g.p_tT(n4["final_effects"]) + g.p_tI(n4["final_index"]) + g.p_tI(n4["left_out"])
                 + g.p_tF([n4["intercept"]]) + [len(n4["coefficients"])]
                 + [t for kk, v in n4["coefficients"].items() for t in cmp.tok_str(kk) + [g.fb(v)]]
                 + g.p_frame(n4["logit_scored_train"]) + g.p_frame(n4["fit_scored"]))
        cases += [{"case": f"w{k}.01", "rows": rows, "kept": pre1}, {"case": f"w{k}.04", "rows": rows, "kept": pre4}]
        exp += [cmp.digest(toks1), cmp.digest(toks4)]
        lean_cases.append(f"(let f : Pl.Frame Float := win {g.ln(local)}; "
                          "match train_run_01_fit_frame (α := Float) SW f with | (c, mk, ff, fin, io, nobs, ytr, m0, yb) => "
                          "[dg (tT (c.map some) ++ tB (mk.map some) ++ tR ff ++ tFit fin ++ tFit io ++ tI [some nobs] ++ tF (ytr.map some) "
                          "++ [yb.toBits] ++ (if io.isSome then [m0.toBits] else [])), "
                          "(match train_run_04_score_train (α := Float) c mk SW.final f with | (nm, ef, ix, lo, ic, co, lst, fsc) => "
                          "dg (tT (nm.map some) ++ tT (ef.map some) ++ tI (ix.map some) ++ tI (lo.map some) ++ tF [ic] ++ "
                          "(co.length.toUInt64 :: co.flatMap (fun (p : String × Float) => tS p.1 ++ [p.2.toBits])) ++ tR lst ++ tR fsc) : Int)])")
    r2 = g.run02(sw, sw.final)
    toks2 = [0] if r2 is None else [1] + cmp.tok_str(r2[0]) + cmp.tokens(cmp.canon_table(r2[1]))
    cases.append({"case": "real.02", "kept": True})
    exp.append(cmp.digest(toks2))
    lean_cases.append("[dg (match train_run_02_stepwise_summary fw pv SW SW.final with | none => [0] | some p => 1 :: tS p.1 ++ tA p.2 : List UInt64)]")
    lets = (g.LETS02.split("let E1")[0]  # fw, pv
            + g.TOK
            + 'let dum : LogisticFit Float := { names := ["Intercept"], beta := Np.NDArray.d1 [], cov := Np.NDArray.d2 [], loglik := 0.0, n_iter := 0, converged := true }; '
            + MKS + data
            + f"let SW : StepwiseResult Float := {{ steps := {lean_steps(sw)}, final := {lean_fit(sw.final)}, intercept_only := {lean_fit(sw.intercept_only)} }}; ")
    body = (f"let G : List Int := {' ++ '.join(lean_cases)}; let E : List Int := {g.ln(exp)}; "
            "((List.range E.length).filter (fun (j : Nat) => G.getD j 0 != E.getD j 0)).map (fun (j : Nat) => (j : Int)))")
    text = "(" + kit.KIT + lets + body
    (W / "fz10c_ta_real.inputs.json").write_text(json.dumps([{"item": g.CARRIER[0], "decl": g.CARRIER[1], "inputs": [text]}],
                                                            ensure_ascii=False))
    (W / "fz10c_ta_real.json").write_text(json.dumps({"suite": "fz10c_ta_real", "generator": "diffeval/units/fz10c_train_a_real.py",
                                                      "blueprint": g.BLUEPRINT, "cases": cases, "expected": exp,
                                                      "expected_output": [], "windows": windows,
                                                      "steps": len(sw.steps), "final_names": None if sw.final is None else sw.final.names,
                                                      "left_out_full": ns_full["left_out"]}))
    print("cases", [(c["case"], c["kept"]) for c in cases], "input chars", len(text))


if __name__ == "__main__":
    main()
