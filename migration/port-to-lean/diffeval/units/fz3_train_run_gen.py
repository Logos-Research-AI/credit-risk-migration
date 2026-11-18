"""Fuzz of the update of 2026-11-17, port-translator-10 (not the author): the composition
def:run_py_py_py (train.run) and def:train_run_03_fit_global_rsquare, suite fz3_train_run on
def:zz_carrier_t of blueprint 5365851c-5549-44b7-9207-4bd4c422031d. Successor of
fz_train_run_gen.py (2026-11-16, old blueprint id), same method (t18_gen.py: the REAL train.run
under recorders, formatters as injective encodings, the numeric routines as tables of what the
real routines returned on that file).

  PYTHONPATH=../../port uv run --project ../../port python diffeval/units/fz3_train_run_gen.py [--explore A B]

Changes for the port as it stands: the list of exported files varies (a file not written has no
pair; a header-only file is the empty table), so the compared values are the number of files,
model.json and one digest per file in call order; LogisticFit carries `separation`; a step with
q == 0 makes no solve (routine tables follow train.py:177-190); the generator reaches on purpose
intercept-only final models, stepwise results with no step or with a q == 0 step, and validation
sets of one class (default_flag of the validation file all 0.0 when hsh(s, 605) % 4 == 0; files of
1 or 2 rows are often of one class anyway).

Files of seed s (42 columns, the header of the real feature file, all Float64), built inside Lean
and mirrored here (the script asserts that the frames the real run imported are the mirrored ones):
  rows: training 30 + hsh(s, 603) % 30, validation [1, 2, 5, 9, 14][hsh(s, 604) % 5]
  cell (file seed f = s for training, s + 2^20 for validation; column j; row i), u = hsh(f*64+j+1, i):
    null when i > 0, the column is a null column (hsh(f, 500+j) % 12 == 0) and (u >> 8) % 100 < 8,
    else float((u >> 20) % m), m = 2 for the flag_ / has_ / _missing columns and 5 otherwise
  default_flag: 0.0 in the validation file when hsh(s, 605) % 4 == 0; else null when
    hsh(f, 800+i) % 25 == 0, else 1.0 when va + vb + hsh(f+7, 700+i) % 7 >= 5 + hsh(s, 602) % 3,
    else 0.0; va, vb = the cells (null as 0) of candidate columns CAND[hsh(s, 600) % 36], CAND[hsh(s, 601) % 36]
Step 03 (def:train_run_03_fit_global_rsquare), 250 step lists per seed, built inside Lean from the
real stepwise result: list v has hsh(s*1000+v, 0) % 7 steps; step j is the real step number
hsh(s*1000+v, j+1) % (number of real steps + 1), or, for the last value, a step whose fit is the
intercept-only fit (q == 0). The routine tables of the real run cover every such list (each step's
statistics depend on that step alone). Expected: train.py:154-268 executed on each list
(u03_gen.run_slice). One case = the digest of 50 lists.
Precondition of the composition (def:run_py_py_py_precond) as the Python function `pre`, on the
locals of the real run: okT of both tables -> both frames have a row, 42 distinct names, every
column Float64 (asserted of the import); n_obs != 0; final / intercept_only present; step 03, for
the steps with q != 0: exp(-lr/n_obs), exp(-m2ll0/n_obs) finite and 1 - exp(-m2ll0/n_obs) != 0;
step 04: exp(-eta) finite on every row -> pd_logistic != 0.0 wherever not null; step 06: cov[idx,
idx] >= 0, sqrt != 0, the three exp finite; column presence and dtypes by construction.
NOT rendered: the preconditions of the library units reached through steps 05, 07, 08, 13, 14
(association_table, hosmer_lemeshow, classification_table, roc_association, merge_one_to_one): a
seed on which the real run returns is taken as inside them. The step 03 precondition on a
generated list is that of its real steps (rendered above) and nothing for a q == 0 step.
"""
from __future__ import annotations

import dataclasses
import datetime as dt
import json
import math
import sys
import tempfile
import time
from pathlib import Path

import numpy as np
import polars as pl

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))

import kit  # noqa: E402
import suite as suite_mod  # noqa: E402
import t18_gen as t18  # noqa: E402
from credit_risk import train as _train  # noqa: E402,F401
from suite import Suite  # noqa: E402

from credit_risk import sas_compat as sc  # noqa: E402

NAMES = ("row_id,default_flag,age,monthly_income,MonthlyIncome_missing,num_dependents,Dependents_missing,age_group,num_late_30_59,"
         "num_late_60_89,num_late_90_plus,credit_utilization,debt_ratio,num_credit_lines,num_real_estate_loans,total_late_payments,"
         "has_delinquency,has_serious_delinquency,credit_util_category,debt_category,income_per_dependent,credit_lines_per_person,"
         "age_category,flag_high_utilization,flag_very_high_utilization,flag_high_debt_ratio,flag_very_high_debt_ratio,"
         "flag_recent_late_payments,flag_serious_delinquency,flag_multiple_delinquencies,flag_low_income,flag_many_dependents,"
         "flag_few_credit_lines,total_risk_flags,financial_health,log_monthly_income,log_num_credit_lines,log_total_late_payments,"
         "age_income_interaction,utilization_debt_interaction,credit_utilization_capped,debt_ratio_capped").split(",")
NOTC = {"row_id", "default_flag", "age_group", "credit_utilization", "debt_ratio", "log_total_late_payments"}
CANDJ = [j for j, n in enumerate(NAMES) if n not in NOTC]  # indexes of the 36 candidates, in file order
MODS = [2 if (n.startswith(("flag_", "has_")) or n.endswith("_missing")) else 5 for n in NAMES]
NV = [1, 2, 5, 9, 14]
OFFV = 1 << 20
assert len(NAMES) == 42 and len(CANDJ) == 36


def cell(f: int, j: int, i: int):
    sd = f % OFFV
    if kit.hsh(sd, 606) % 3 == 0 and j == CANDJ[kit.hsh(sd, 610) % 36]:
        j = CANDJ[kit.hsh(sd, 611) % 36]  # a duplicated column: a singular information matrix when both enter
    return cell0(f, j, i)


def cell0(f: int, j: int, i: int):
    u = kit.hsh(f * 64 + j + 1, i)
    if i > 0 and kit.hsh(f, 500 + j) % 12 == 0 and (u >> 8) % 100 < 8:
        return None
    return float((u >> 20) % MODS[j])


def flag(s: int, f: int, i: int):
    if f != s and kit.hsh(s, 605) % 4 == 0:
        return 0.0
    if kit.hsh(f, 800 + i) % 25 == 0:
        return None
    a, b = CANDJ[kit.hsh(s, 600) % 36], CANDJ[kit.hsh(s, 601) % 36]
    va, vb = cell(f, a, i) or 0.0, cell(f, b, i) or 0.0
    return 1.0 if int(va) + int(vb) + kit.hsh(f + 7, 700 + i) % 7 >= 5 + kit.hsh(s, 602) % 3 else 0.0


def frame(s: int, f: int, n: int) -> pl.DataFrame:
    return pl.DataFrame({nm: pl.Series([flag(s, f, i) if j == 1 else cell(f, j, i) for i in range(n)], dtype=pl.Float64)
                         for j, nm in enumerate(NAMES)})


def frames(s: int):
    return frame(s, s, 30 + kit.hsh(s, 603) % 30), frame(s, s + OFFV, NV[kit.hsh(s, 604) % 5])


WALD_TOL = 1.5e-16
MUT_KINDS = ["zero diagonal", "1e-17", "tol", "nextafter(tol, 1)", "nextafter(tol, 0)"]


def mutate(s: int, sw):
    """The parameter `stepwise` is not translated, so the generator may hand both sides a stepwise result the real
    fit did not give: in a third of the seeds one step that is neither the final nor the intercept-only fit gets the
    covariance of its first slope (MODEL order) set to a value at the edges of global_wald: 0 (left out, NaN Wald),
    1e-17, the tolerance 1.5e-16 and one ulp either side (pivot of the first slope = its diagonal)."""
    if kit.hsh(s, 620) % 3 != 0:
        return sw
    elig = [k for k, st in enumerate(sw.steps) if st.fit is not sw.final and st.fit is not sw.intercept_only and len(st.fit.names) > 1]
    if not elig:
        return sw
    k = elig[kit.hsh(s, 621) % len(elig)]
    kind = kit.hsh(s, 622) % 5
    st = sw.steps[k]
    cand = [n for n, _ in zip(CAND_NAMES, range(99))]
    first = min(st.fit.names[1:], key=cand.index)
    i = st.fit.names.index(first)
    cov = np.array(st.fit.cov, dtype=np.float64)
    cov[i, i] = [0.0, 1e-17, WALD_TOL, np.nextafter(WALD_TOL, 1.0), np.nextafter(WALD_TOL, 0.0)][kind]
    steps = list(sw.steps)
    steps[k] = dataclasses.replace(st, fit=dataclasses.replace(st.fit, cov=cov))
    MUTATED[s] = (k, MUT_KINDS[kind], first)
    return sc.StepwiseResult(steps, sw.final, sw.intercept_only)


MUTATED: dict = {}
import ast as _ast
import re as _re
_src = (Path(sys.modules["credit_risk.train"].__file__ if "credit_risk.train" in sys.modules else __import__("credit_risk.train").train.__file__)).read_text()
CAND_NAMES = _ast.literal_eval(_re.search(r"candidates = (\[.*?\])", _src, _re.S).group(1))  # train.py:55-95, the MODEL order


def run_seed(s: int):
    """-> ('returned', rec) or ('raised', 'ExcType: message')."""
    ft, fv = frames(s)
    orig = sc.stepwise_logistic
    sc.stepwise_logistic = lambda *a, **k: mutate(s, orig(*a, **k))
    with tempfile.TemporaryDirectory() as td:
        ind = Path(td)
        ft.write_csv(ind / "model_features_train.csv")
        fv.write_csv(ind / "model_features_validation.csv")
        try:
            rec = t18.real_run(ind, encoded=True)
        except Exception as e:  # noqa: BLE001
            return "raised", f"{type(e).__name__}: {str(e)[:70]}"
        finally:
            sc.stepwise_logistic = orig
    (_, mt), (_, mv) = rec["imports"]
    for got, want in ((mt, ft), (mv, fv)):  # what Lean generates is what the run imported
        assert got.columns == want.columns and all(t == pl.Float64 for t in got.dtypes), (s, got.schema)
        assert t18.fd(got) == t18.fd(want), s
    assert rec["locals"]["candidates"] == CAND_NAMES
    return "returned", rec


def pre(rec: dict) -> tuple[bool, str]:
    L, sw = rec["locals"], rec["stepwise"]
    if sw.final is None or sw.intercept_only is None:
        return False, "no final model"
    n = L["fit_frame"].height
    if n == 0:
        return False, "n_obs = 0"
    m2ll0 = L["m2ll0"]
    try:
        for st in sw.steps:
            if len(st.fit.names) - 1 == 0:
                continue
            if not math.isfinite(math.exp(-(m2ll0 - (-2.0) * st.fit.loglik) / n)):
                return False, "step 03 exp not finite"
        e0 = math.exp(-m2ll0 / n)
        if any(len(st.fit.names) > 1 for st in sw.steps) and (not math.isfinite(e0) or 1.0 - e0 == 0.0):
            return False, "step 03 exp(-m2ll0/n)"
        for idx in [0, *L["final_index"]]:
            b, cv = float(sw.final.beta[idx]), float(sw.final.cov[idx, idx])
            if cv < 0 or math.sqrt(cv) == 0.0:
                return False, "step 06 se"
            se = math.sqrt(cv)
            if idx != 0 and not all(math.isfinite(math.exp(a)) for a in (b, b - sc.Z975 * se, b + sc.Z975 * se)):
                return False, "step 06 exp"
    except (OverflowError, ValueError):
        return False, "exp overflow"
    pdl = L["logit_scored_train"].get_column("pd_logistic").to_list()
    if any(v is not None and v == 0.0 for v in pdl):
        return False, "step 04 exp(-eta) overflow"
    # step 15 precondition as narrowed on 2026-11-17 (revision 5fcb0b4a): an exported ROC frame with rows has a ROCModel label that is not null
    for fr, on in ((L["roc_train"], True), (L["roc_valid"], bool(L["roc_valid_created"]))):
        lab = fr.get_column("ROCModel").to_list()
        if on and lab and all(v is None for v in lab):
            return False, "step 15 ROCModel labels all null"
    return True, ""


LGEN = (
    "let NAMES : List String := " + json.dumps(NAMES) + "; "
    "let MODS : List UInt64 := NAMES.map (fun (n : String) => if n.startsWith \"flag_\" || n.startsWith \"has_\" || n.endsWith \"_missing\" then 2 else 5); "
    "let CANDJ : List Nat := (List.range 42).filter (fun (j : Nat) => !([0, 1, 7, 11, 12, 37] : List Nat).contains j); "
    "let cell0 := fun (f j i : Nat) => (let u := hsh (f * 64 + j + 1) i; if i > 0 && (hsh f (500 + j)) % 12 == 0 && (u >>> 8) % 100 < 8 then (none : Option Float) "
    "else some (Float.ofNat ((u >>> 20) % (MODS.getD j 5)).toNat)); "
    "let cell := fun (f j i : Nat) => (let sd := f % 1048576; if (hsh sd 606) % 3 == 0 && j == CANDJ.getD ((hsh sd 610) % 36).toNat 0 then "
    "cell0 f (CANDJ.getD ((hsh sd 611) % 36).toNat 0) i else cell0 f j i); "
    "let cz := fun (f j i : Nat) => (match cell f j i with | none => 0 | some v => v.toUInt64.toNat : Nat); "
    "let flg := fun (s f i : Nat) => (if f != s && (hsh s 605) % 4 == 0 then some 0.0 else if (hsh f (800 + i)) % 25 == 0 then (none : Option Float) else "
    "let a := CANDJ.getD ((hsh s 600) % 36).toNat 0; let b := CANDJ.getD ((hsh s 601) % 36).toNat 0; "
    "some (if cz f a i + cz f b i + ((hsh (f + 7) (700 + i)) % 7).toNat >= 5 + ((hsh s 602) % 3).toNat then 1.0 else 0.0)); "
    "let gT := fun (s f n : Nat) => ((List.range n).map (fun (i : Nat) => (List.range 42).map (fun (j : Nat) => "
    "(NAMES.getD j \"\", Tabular.Cell.num (if j == 1 then flg s f i else cell f j i)))) : Tabular.Table Float); "
)
HSH = ("let hsh := fun (s i : Nat) => let z : UInt64 := s.toUInt64 * 0x9E3779B97F4A7C15 + i.toUInt64 * 0xD1B54A32D192ED03 + 1; "
       "let z := (z ^^^ (z >>> 30)) * 0xBF58476D1CE4E5B9; let z := (z ^^^ (z >>> 27)) * 0x94D049BB133111EB; z ^^^ (z >>> 31); ")
assert [j for j, n in enumerate(NAMES) if n in NOTC] == [0, 1, 7, 11, 12, 37]


def routine_tables(rec: dict) -> dict:
    """t18_gen.routine_tables for the port as it stands: a step with q == 0 makes no solve
    (train.py:177-190); the rest is t18's (the same numpy expressions as train.py and sas_compat)."""
    L = rec["locals"]
    stepwise, fit_frame, y_train, ybar, n_obs, final = rec["stepwise"], L["fit_frame"], L["y_train"], L["ybar"], L["n_obs"], L["final"]
    T = {"solve": [], "matmul": [], "matvec": [], "dot": [], "inv": [], "einsum": [], "log1p": {}, "pow2": {}}
    # train.py as at 524cd28: step 03 calls np.linalg.solve for the score and inside sas_compat.global_wald
    # (pivots, chi-square); dot is float(b @ r) of every recorded solve (score, c @ ..., bk @ ...)
    T["solve"] = [(t18.mw(a), t18.vw(b), r) for a, b, r in rec["solve"]]
    T["dot"] = [(t18.vw(b), t18.vw(r), float(np.asarray(b, dtype=np.float64) @ np.asarray(r, dtype=np.float64))) for a, b, r in rec["solve"]]
    for st in stepwise.steps:
        names_k = st.fit.names
        if len(names_k) - 1 == 0:
            continue
        x_k = np.column_stack([np.ones(n_obs), *[np.asarray(fit_frame.get_column(c).to_numpy(), dtype=np.float64) for c in names_k[1:]]])
        d = y_train - ybar
        u0 = x_k.T @ d
        g = x_k.T @ x_k
        T["matvec"].append((t18.mw(x_k.T), t18.vw(d), u0))
        T["matmul"].append((t18.mw(x_k.T), t18.mw(x_k), g))
    x, p = L["x_final"], np.asarray(L["pd_train"], dtype=np.float64)
    with np.errstate(all="ignore"):
        for v in p:
            T["log1p"][t18.fb(-v)] = t18.fb(np.log1p(-v))
        wv = p * (1.0 - p)
        xw = x * wv[:, None]
        mm = x.T @ xw
        vi = np.linalg.inv(mm)
        q = np.einsum("ij,jk,ik->i", x, vi, x)
    T["matmul"].append((t18.mw(x.T), t18.mw(xw), mm))
    T["inv"].append((t18.mw(mm), vi))
    T["einsum"].append((t18.mw(x), t18.mw(vi), q))
    for idx in [0, *L["final_index"]]:
        b = float(final.beta[idx])
        se = math.sqrt(float(final.cov[idx, idx]))
        T["pow2"][t18.fb(b / se)] = t18.fb((b / se) ** 2)
    for _, _size, o1, e1, o0, e0 in L["hl_table"].iter_rows():
        for v in (float(o1) - e1, float(o0) - e0):
            T["pow2"][t18.fb(v)] = t18.fb(v**2)
    T["chi2"] = sorted({(t18.fb(x), d, t18.fb(r)) for x, d, r in rec["chi2"]})
    T["fsum"] = {t18.vw(xs): t18.fb(r) for xs, r in rec["fsum"]}
    for k in ("solve", "matmul", "matvec", "dot", "einsum"):
        seen, rows = set(), []
        for row in T[k]:
            if row[:2] not in seen:
                seen.add(row[:2])
                rows.append(row)
        T[k] = rows
    return T


def lean_fit(f: sc.LogisticFit) -> str:
    sep = "none" if f.separation is None else f"(some {t18.lstr(f.separation)})"
    return (f"(mkfit [{', '.join(t18.lstr(n) for n in f.names)}] {t18.ul(f.beta)} {t18.ull(np.atleast_2d(f.cov))} {t18.fb(f.loglik)} "
            f"({int(f.n_iter)}) {'true' if f.converged else 'false'} {sep})")


t18.lean_fit = lean_fit  # t18.lean_stepwise writes its fits through this
MKFIT = ("let mkfit := fun (names : List String) (beta : List UInt64) (cov : List (List UInt64)) (ll : UInt64) (ni : Int) (cv : Bool) (sep : Option String) => "
         "({ names := names, beta := Np.NDArray.d1 (FL beta), cov := Np.NDArray.d2 (cov.map FL), loglik := Float.ofBits ll, "
         "n_iter := ni, converged := cv, separation := sep } : LogisticFit Float); ")
NV3, CH3 = 250, 50  # step lists per seed for step 03, lists per case


def zstep(k: int, io):
    return sc.StepwiseStep(step=k, entered=None, removed="zz", df=1, number_in_model=0, score_chisq=None, wald_chisq=1.5, p_value=0.5, fit=io)


def variant(s: int, v: int, sw):
    n = len(sw.steps)
    out = []
    for j in range(kit.hsh(s * 1000 + v, 0) % 7):
        r = kit.hsh(s * 1000 + v, j + 1) % (n + 1)
        out.append(sw.steps[r] if r < n else zstep(j + 1, sw.intercept_only))
    return sc.StepwiseResult(out, sw.final, sw.intercept_only)


def run_slice3(stepwise, L):
    """train.py:162-283 (as at 524cd28) executed on a stepwise result: u03.run_slice with global_wald and candidates."""
    import textwrap
    import types
    src = Path(sys.modules["credit_risk.train"].__file__).read_text().splitlines()
    assert src[161].strip() == 'fs_step: list[str] = ["0"]' and "printed_rsquare.csv" in src[282]
    code = textwrap.dedent("\n".join(src[161:283]))
    writes: list = []
    proxy = types.SimpleNamespace(
        sas_d12_3=t18.ENCODERS["sas_d12_3"], fmt_wd=t18.ENCODERS["fmt_wd"], sas_pvalue=t18.ENCODERS["sas_pvalue"],
        chi2_sf=sc.chi2_sf, global_wald=sc.global_wald, write_sas_csv=lambda df, path, formats=None: writes.append((Path(path).name, df.clone())))
    ns = {"sas_compat": proxy, "np": np, "pl": pl, "math": math, "stepwise": stepwise, "output_dir": Path("out"),
          "m2ll0": L["m2ll0"], "n_obs": L["n_obs"], "fit_frame": L["fit_frame"], "y_train": L["y_train"], "ybar": L["ybar"],
          "candidates": L["candidates"]}
    exec(compile(code, "train.py:162-283", "exec"), ns)  # noqa: S102
    return writes


def step03_expected(s: int, rec: dict) -> list[int]:
    L, sw = rec["locals"], rec["stepwise"]
    per = []
    for v in range(NV3):
        ws = run_slice3(variant(s, v, sw), L)
        per.append(t18.w([len(ws)] + [x for n, df in ws for x in t18.tdn(n, df)]))
    return [t18.w(per[c * CH3:(c + 1) * CH3]) for c in range(NV3 // CH3)]


def lean_step03(s: int) -> str:
    return ("let (_c, _m, ff, _f, _i, nobs, ytr, m2ll0, ybar) := train_run_01_fit_frame (α := Float) SW (Pl.ofTable tT); "
            "let IO := SW.intercept_only.getD (mkfit [] [] [] 0 0 true none); "
            'let Z := fun (k : Int) => ({ step := k, entered := none, removed := some "zz", df := 1, number_in_model := 0, '
            f"score_chisq := none, wald_chisq := some (Float.ofBits {t18.fb(1.5)}), p_value := Float.ofBits {t18.fb(0.5)}, fit := IO }} : StepwiseStep Float); "
            "let nS := SW.steps.length; "
            f"let vr := fun (v : Nat) => (List.range ((hsh ({s} * 1000 + v) 0) % 7).toNat).map (fun (j : Nat) => "
            f"let r := ((hsh ({s} * 1000 + v) (j + 1)) % (nS + 1).toUInt64).toNat; if r < nS then SW.steps.getD r (Z 0) else Z ((j : Int) + 1)); "
            "let S3 := fun (v : Nat) => (let o := train_run_03_fit_global_rsquare fw d12 pv chi2 { SW with steps := vr v } solve matmul matvec dot ff nobs ytr m2ll0 ybar _c; "
            "W ((o.length : Int) :: o.flatMap TDN)); "
            f"let R3 := (List.range {NV3 // CH3}).map (fun (c : Nat) => W ((List.range {CH3}).map (fun (i : Nat) => S3 (c * {CH3} + i)))); ")


PREFIX = t18.W + t18.BI + t18.TS + t18.TX + t18.TD + t18.FL + t18.MW + t18.FMT + t18.KEYED + MKFIT + HSH + LGEN


def lean_input(s: int, rec: dict):
    L, sw = rec["locals"], rec["stepwise"]
    T = routine_tables(rec)
    td_ = L["model_summary"].get_column("training_date").to_list()  # no row when the validation set has one class
    today = td_[0] if td_ else dt.date.today()
    order = [n for n, _ in rec["writes"]]
    writes = dict(rec["writes"])
    assert len(order) == len(writes)
    nt, nv = rec["imports"][0][1].height, rec["imports"][1][1].height
    lets = (PREFIX
            + t18.lean_routines(T) + f"let SW := {t18.lean_stepwise(sw)}; "
            + f'let today : Tabular.Cell Float := Tabular.Cell.str (some "{today.isoformat()}"); '
            + f"let tT := gT {s} {s} {nt}; let tV := gT {s} {s + OFFV} {nv}; "
            + "let RUN := run_py_py_py fw fo d8 d12 pv chi2 today SW fsum inv solve matmul matvec dot einsum log1p pow2; "
            + "let R := (RUN (some tT) (some tV)).getD ([], (Float.ofBits 0, [])); " + lean_step03(s))
    body = ("(R3 ++ [(R.1.length : Int), bi R.2.1, W (R.2.2.flatMap (fun (p : String × Float) => ts p.1 ++ [bi p.2]))] ++ "
            "R.1.map (fun (p : String × Tabular.Table Float) => W (TDN p)))")
    mj = rec["model_json"]
    exp = step03_expected(s, rec)
    exp += [len(order), t18.fb(mj["intercept"]), t18.w([t for c, b in mj["coefficients"].items() for t in t18.ts(c) + [t18.fb(b)]])]
    exp += [t18.w(t18.tdn(n, writes[n])) for n in order]
    labels = [f"step 03 on step lists {c * CH3}..{c * CH3 + CH3 - 1}" for c in range(NV3 // CH3)]
    return lets, body, exp, labels + ["number of files", "model.json intercept", "model.json coefficients"] + order


def explore(a: int, b: int) -> None:
    for s in range(a, b):
        t0 = time.time()
        st, r = run_seed(s)
        if st == "raised":
            print(s, "RAISED", r)
            continue
        ok, why = pre(r)
        sw, L = r["stepwise"], r["locals"]
        lets, body, _, _ = lean_input(s, r)
        text = lets + body
        print(s, "kept" if ok else f"rejected({why})", f"rows {r['imports'][0][1].height}/{r['imports'][1][1].height} n_obs {L['n_obs']}",
              f"steps {[(x.entered or '-' + x.removed, len(x.fit.names) - 1, x.fit.separation) for x in sw.steps]}", f"final {sw.final.names[1:]}",
              f"files {len(r['writes'])} roc_valid {L['roc_valid_created']}", f"{len(text) - len(PREFIX)} chars", f"{time.time() - t0:.1f}s")


SEEDS_FIRST, SEEDS_LAST = 80000, 80699
BLUEPRINT = "5365851c-5549-44b7-9207-4bd4c422031d"
U_RUN, U_03 = "run_py_py_py", "train_run_03_fit_global_rsquare"
MAXSENT, CALL_CHARS = 30, 24000


def tags(s: int, r: dict) -> list[str]:
    L, sw = r["locals"], r["stepwise"]
    t = []
    t += ["no step"] if not sw.steps else []
    t += ["final intercept only"] if len(sw.final.names) == 1 else []
    t += ["q == 0 step"] if any(len(x.fit.names) == 1 for x in sw.steps) else []
    t += ["validation of one class"] if not L["roc_valid_created"] else []
    t += ["separated step"] if any(x.fit.separation is not None for x in sw.steps) else []
    t += ["HL partition < 3 groups"] if L["hl_table"].height < 3 else []
    if len(sw.final.names) > 1:
        t += [f"effect, HL groups {min(L['hl_table'].height, 4)}{'+' if L['hl_table'].height >= 4 else ''}"]
    if s in MUTATED:
        t += ["global_wald edge: " + MUTATED[s][1]]
    return t


def build(only: list[int] | None = None) -> None:
    suite_mod.CARRIERS["identity"] = ("def:zz_carrier_c", "zz_carrier_c")
    s = Suite("fz3_train_run" if only is None else "fz3_train_run_smoke")
    stats = {"kept": [], "rejected": {}, "raised": {}}
    tagcount: dict = {}
    cand = []  # (chars, seed, tags)
    recs = {}
    for seed in range(SEEDS_FIRST, SEEDS_LAST + 1):
        if only is not None and seed not in only:
            continue
        MUTATED.pop(seed, None)
        st, r = run_seed(seed)
        if st == "raised":
            stats["raised"][seed] = r
            continue
        ok, why = pre(r)
        if not ok:
            stats["rejected"][seed] = why
            continue
        stats["kept"].append(seed)
        tg = tags(seed, r)
        for k in tg:
            tagcount[k] = tagcount.get(k, 0) + 1
        lets, body, _, _ = lean_input(seed, r)
        cand.append((len(lets) - len(PREFIX) + len(body), seed, tg))
        recs[seed] = r
    cand.sort()
    if only is not None:
        chosen = [c[1] for c in cand]
    else:
        chosen = []
        for k in sorted(tagcount, key=lambda k: tagcount[k]):  # rarest class first, the smallest inputs of it, 3 of each
            have = sum(1 for sd in chosen if k in tags(sd, recs[sd]))
            for size, seed, tg in cand:
                if have >= 3 or len(chosen) >= MAXSENT:
                    break
                if k in tg and seed not in chosen:
                    chosen.append(seed)
                    have += 1
        for size, seed, tg in cand:
            if len(chosen) < MAXSENT and seed not in chosen and size < 9000:
                chosen.append(seed)
    sizes = {c[1]: c[0] for c in cand}
    chosen.sort(key=lambda x: sizes[x])
    groups, cur, tot = [], [], len(PREFIX)
    for seed in chosen:  # greedy, smallest first, a call up to CALL_CHARS
        if cur and tot + sizes[seed] > CALL_CHARS:
            groups.append(cur)
            cur, tot = [], len(PREFIX)
        cur.append(seed)
        tot += sizes[seed]
    if cur:
        groups.append(cur)
    sent_tags = {}
    for group in groups:
        blocks, cases = [], []
        for seed in group:
            r = recs[seed]
            lets, body, exp, labels = lean_input(seed, r)
            assert lets.startswith(PREFIX)
            blocks.append((lets[len(PREFIX):], body))
            sw = r["stepwise"]
            sent_tags[seed] = tags(seed, r)
            what = (f"seed {seed}: {r['imports'][0][1].height}/{r['imports'][1][1].height} rows, n_obs {r['locals']['n_obs']}, "
                    f"steps {[(x.entered, x.removed, x.fit.separation) for x in sw.steps]}, final {sw.final.names[1:]}, "
                    f"roc_valid_created {r['locals']['roc_valid_created']}, {sent_tags[seed]}")
            for lab, e in zip(labels, exp, strict=True):
                s3 = lab.startswith("step 03")
                cases.append((f"{what}: {lab}", U_03 if s3 else U_RUN, e, {"fz": "kept", "covers": CH3 if s3 else 1}))
        if len(blocks) == 1:
            s.ints(PREFIX + blocks[0][0], blocks[0][1], cases, use_kit=False)
        else:
            s.ints(PREFIX + "".join(f"let r{k} : List Int := ({lt_}{bd}); " for k, (lt_, bd) in enumerate(blocks)),
                   "(" + " ++ ".join(f"r{k}" for k in range(len(blocks))) + ")", cases, use_kit=False)
    s.write()
    ngen = (SEEDS_LAST - SEEDS_FIRST + 1) if only is None else len(only)
    nraised_other = {k: v for k, v in stats["raised"].items() if "stepwise_logistic" not in v}
    nvals = sum(1 for c in s.cases if c.get("unit", U_RUN) == U_RUN) if hasattr(s, "cases") else 0
    note = (f"of the {ngen} seeds {len(stats['kept'])} are inside the rendered precondition, {len(stats['rejected'])} rejected ({sorted(set(stats['rejected'].values()))}), "
            f"{len(stats['raised']) - len(nraised_other)} raise in the real stepwise_logistic (the parameter does not exist), {len(nraised_other)} import a String column; "
            f"classes among the kept seeds: {tagcount}; sent to Lean: {len(chosen)} seeds in {len(groups)} calls: {chosen}; classes of the sent seeds: {sent_tags}")
    if only is None:
        (suite_mod.WORK / "fz3_train_run.fuzz.json").write_text(json.dumps({
            "fuzzer": "port-translator", "generator": "diffeval/units/fz3_train_run_gen.py", "blueprint": BLUEPRINT, "units": {
                U_RUN: {"seeds": f"{SEEDS_FIRST}..{SEEDS_LAST} generated; sent {chosen}", "generated": ngen, "kept": len(chosen),
                        "python_raises_inside_precondition": [], "note": note},
                U_03: {"seeds": f"step lists 0..{NV3 - 1} of each sent seed", "generated": NV3 * len(chosen), "kept": NV3 * len(chosen),
                       "python_raises_inside_precondition": [], "note": "step lists of the real and mutated steps of the seed, in any order, with q == 0 steps"}}}, indent=1))
    print(note[:1500])
    for i, inp in enumerate(s.inputs):
        print(i, len(inp["text"]), "chars")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--explore":
        explore(int(sys.argv[2]), int(sys.argv[3]))
    elif len(sys.argv) > 1 and sys.argv[1] == "--only":
        build([int(x) for x in sys.argv[2:]])
    else:
        build()
