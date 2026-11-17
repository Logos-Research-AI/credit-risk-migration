"""Fuzz of the update of 2026-11-17, port-translator-10 (not the author): the composition
def:run_py_py_py (train.run) and def:train_run_03_fit_global_rsquare, suite fz2_train_run on
def:zz_carrier_t of blueprint 5365851c-5549-44b7-9207-4bd4c422031d. Successor of
fz_train_run_gen.py (2026-11-16, old blueprint id), same method (t18_gen.py: the REAL train.run
under recorders, formatters as injective encodings, the numeric routines as tables of what the
real routines returned on that file).

  PYTHONPATH=../../port uv run --project ../../port python diffeval/units/fz2_train_run_gen.py [--explore A B]

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
import u03_gen as u03  # noqa: E402
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


def run_seed(s: int):
    """-> ('returned', rec) or ('raised', 'ExcType: message')."""
    ft, fv = frames(s)
    with tempfile.TemporaryDirectory() as td:
        ind = Path(td)
        ft.write_csv(ind / "model_features_train.csv")
        fv.write_csv(ind / "model_features_validation.csv")
        try:
            rec = t18.real_run(ind, encoded=True)
        except Exception as e:  # noqa: BLE001
            return "raised", f"{type(e).__name__}: {str(e)[:70]}"
    (_, mt), (_, mv) = rec["imports"]
    for got, want in ((mt, ft), (mv, fv)):  # what Lean generates is what the run imported
        assert got.columns == want.columns and all(t == pl.Float64 for t in got.dtypes), (s, got.schema)
        assert t18.fd(got) == t18.fd(want), s
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
    "let cell := fun (f j i : Nat) => (let u := hsh (f * 64 + j + 1) i; if i > 0 && (hsh f (500 + j)) % 12 == 0 && (u >>> 8) % 100 < 8 then (none : Option Float) "
    "else some (Float.ofNat ((u >>> 20) % (MODS.getD j 5)).toNat)); "
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
        assert t18.mw(a1) == t18.mw(i0) and t18.vw(b1) == t18.vw(u0), "recomputed i0 / u0 differ from what np.linalg.solve received"
        b_slope = st.fit.beta[1:]
        a2, b2, s2 = solves.pop(0)
        assert t18.mw(a2) == t18.mw(st.fit.cov[1:, 1:]) and t18.vw(b2) == t18.vw(b_slope)
        T["matvec"].append((t18.mw(x_k.T), t18.vw(d), u0))
        T["matmul"].append((t18.mw(x_k.T), t18.mw(x_k), g))
        T["solve"] += [(t18.mw(a1), t18.vw(b1), s1), (t18.mw(a2), t18.vw(b2), s2)]
        T["dot"] += [(t18.vw(u0), t18.vw(s1), float(u0 @ s1)), (t18.vw(b_slope), t18.vw(s2), float(b_slope @ s2))]
    assert not solves, len(solves)
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


def step03_expected(s: int, rec: dict) -> list[int]:
    L, sw = rec["locals"], rec["stepwise"]
    per = []
    for v in range(NV3):
        ws = u03.run_slice(variant(s, v, sw), L)
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
            "let S3 := fun (v : Nat) => (let o := train_run_03_fit_global_rsquare fw d12 pv chi2 { SW with steps := vr v } solve matmul matvec dot ff nobs ytr m2ll0 ybar; "
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


SEEDS_FIRST, SEEDS_LAST = 70000, 70199
BLUEPRINT = "5365851c-5549-44b7-9207-4bd4c422031d"
U_RUN, U_03 = "run_py_py_py", "train_run_03_fit_global_rsquare"
# the seeds sent to Lean (typed first-hand; the routine tables are data of each seed), chosen among
# the 200 for the classes the update asks for, smaller inputs first:
#   70055 no step (final intercept only)                 70087 no step, validation set of one class
#   70029 a quasi-complete step, then a q == 0 step      70034 the same, validation set of one class (14 rows)
#   70039 enter then remove (q == 0), one class          70002 one effect; 70011 one effect, one class
#   70000 a quasi-complete step inside, one effect left  70004 two effects, one class
SENT_CLS: dict = {}
SENT_KEPT = [70055, 70087, 70029, 70034, 70039, 70002, 70011, 70000, 70004]
GROUPS = [[70055], [70087, 70029], [70034, 70039], [70002, 70011], [70000, 70004]]
assert sorted(x for g in GROUPS for x in g) == sorted(SENT_KEPT)


def build(only: list[int] | None = None) -> None:
    suite_mod.CARRIERS["identity"] = ("def:zz_carrier_c", "zz_carrier_c")
    s = Suite("fz2_train_run" if only is None else "fz2_train_run_smoke")
    stats = {"kept": [], "rejected": {}, "raised": {}}
    cls = {"no step": 0, "final intercept only": 0, "a q == 0 step": 0, "validation of one class": 0, "a separated step": 0}
    recs = {}
    for seed in range(SEEDS_FIRST, SEEDS_LAST + 1):
        st, r = run_seed(seed)
        if st == "raised":
            stats["raised"][seed] = r
            continue
        ok, why = pre(r)
        if ok:
            stats["kept"].append(seed)
            sw = r["stepwise"]
            cls["no step"] += not sw.steps
            cls["final intercept only"] += len(sw.final.names) == 1
            cls["a q == 0 step"] += any(len(x.fit.names) == 1 for x in sw.steps)
            cls["validation of one class"] += not r["locals"]["roc_valid_created"]
            cls["a separated step"] += any(x.fit.separation is not None for x in sw.steps)
            if seed in SENT_KEPT:
                SENT_CLS[seed] = [k for k, v in (("no step", not sw.steps), ("final intercept only", len(sw.final.names) == 1),
                                                 ("q == 0 step", any(len(x.fit.names) == 1 for x in sw.steps)),
                                                 ("validation of one class", not r["locals"]["roc_valid_created"]),
                                                 ("separated step", any(x.fit.separation is not None for x in sw.steps))) if v]
        else:
            stats["rejected"][seed] = why
        if seed in (only if only is not None else SENT_KEPT):
            recs[seed] = (ok, r)
    for group in ([only] if only is not None else GROUPS):
        blocks, cases = [], []
        for seed in group:
            ok, r = recs[seed]
            assert ok, seed
            lets, body, exp, labels = lean_input(seed, r)
            assert lets.startswith(PREFIX)
            blocks.append((lets[len(PREFIX):], body))
            sw = r["stepwise"]
            what = (f"seed {seed}: {r['imports'][0][1].height}/{r['imports'][1][1].height} rows, n_obs {r['locals']['n_obs']}, "
                    f"steps {[(x.entered, x.removed, x.fit.separation) for x in sw.steps]}, final {sw.final.names[1:]}, "
                    f"roc_valid_created {r['locals']['roc_valid_created']}")
            for lab, e in zip(labels, exp, strict=True):
                s3 = lab.startswith("step 03")
                cases.append((f"{what}: {lab}", U_03 if s3 else U_RUN, e, {"fz": "kept", "covers": CH3 if s3 else 1}))
        if len(blocks) == 1:
            s.ints(PREFIX + blocks[0][0], blocks[0][1], cases, use_kit=False)
        else:
            s.ints(PREFIX + "".join(f"let r{k} : List Int := ({lt_}{bd}); " for k, (lt_, bd) in enumerate(blocks)),
                   "(" + " ++ ".join(f"r{k}" for k in range(len(blocks))) + ")", cases, use_kit=False)
    s.write()
    other = {k: v for k, v in stats["raised"].items() if "stepwise_logistic" not in v}
    assert all("cannot compare string" in v for v in other.values()), other  # an all-null default_flag is imported as String: outside the model
    ngen = SEEDS_LAST - SEEDS_FIRST + 1
    if only is None:
        note = (f"of the {ngen} seeds {len(stats['kept'])} are inside the rendered precondition ({cls}), {len(stats['rejected'])} rejected, "
                f"{len(stats['raised']) - len(other)} have no stepwise result (the real stepwise_logistic raises: the parameter does not exist), "
                f"{len(other)} import a String column (one-row validation file with a null outcome: outside the model); "
                f"sent to Lean: {SENT_KEPT} (each input carries the routine tables of its seeds, typed first-hand); classes of the sent seeds: " + str(SENT_CLS))
        (suite_mod.WORK / "fz2_train_run.fuzz.json").write_text(json.dumps({
            "fuzzer": "port-translator-10", "generator": "diffeval/units/fz2_train_run_gen.py", "blueprint": BLUEPRINT, "units": {
                U_RUN: {"seeds": f"{SEEDS_FIRST}..{SEEDS_LAST} generated; sent {SENT_KEPT}", "generated": ngen, "kept": len(SENT_KEPT),
                        "python_raises_inside_precondition": [],
                        "note": "one case = one value (number of files, model.json intercept and coefficients, one digest per exported file in call "
                                "order) of the whole train.run on one seed; feature files of 30-59 / 1-14 rows built inside Lean, small integers "
                                "as floats (ties), nulls; " + note},
                U_03: {"seeds": f"step lists 0..{NV3 - 1} of each of the seeds {SENT_KEPT}", "generated": NV3 * len(SENT_KEPT),
                       "kept": NV3 * len(SENT_KEPT), "python_raises_inside_precondition": [],
                       "note": "step lists of 0-6 steps built inside Lean from the real stepwise result of the seed: real steps in any order, with "
                               "repeats, and steps whose fit is the intercept-only fit (q == 0); fit frame, n_obs, y_train, m2ll0, ybar from step "
                               "01 on the seed's training file; expected = train.py:154-268 executed on each list; one case = digest of 50 lists"}}}, indent=1))
    print({k: len(v) for k, v in stats.items()}, cls, "raised other:", other)
    for i, inp in enumerate(s.inputs):
        print(i, len(inp["text"]), "chars")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--explore":
        explore(int(sys.argv[2]), int(sys.argv[3]))
    elif len(sys.argv) > 1 and sys.argv[1] == "--only":
        build([int(x) for x in sys.argv[2:]])
    else:
        build()
