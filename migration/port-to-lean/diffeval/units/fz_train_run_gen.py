"""Fuzz pass 2026-11-16, port-translator-10: the composition def:run_py_py_py (train.run) on
generated small feature files (suite fz_train_run, carrier def:zz_carrier_t). Not my unit (T18 is
port-translator-9's); the method is theirs (units/t18_gen.py, imported here): the REAL train.run
under recorders, formatters as injective encodings, the numeric routines (stepwise result, solve,
matmul, matvec, dot, inv, einsum, log1p, pow2, chi2, fsum) as tables of what the real routines
returned on that file.

  PYTHONPATH=../../port uv run --project ../../port python diffeval/units/fz_train_run_gen.py [--explore A B]

One case = one seed = one eval input (the tables of the routines are data of the case; they cannot
be generated inside Lean). The two feature files ARE generated inside Lean from the seed and
mirrored here (cell / flag below); this script writes the mirrored frames as CSV, runs the real
train.run on them and asserts that the frames it imported are the mirrored ones bit for bit.

Files of seed s (42 columns, the header of the real feature file, all Float64):
  rows: training 30 + hsh(s, 603) % 30, validation [1, 2, 5, 9, 14][hsh(s, 604) % 5]
  cell (file seed f = s for training, s + 2^20 for validation; column j; row i), u = hsh(f*64+j+1, i):
    null when i > 0, the column is a null column (hsh(f, 500+j) % 12 == 0) and (u >> 8) % 100 < 8
    (row 0 has no null: a column of nulls only is imported as String, outside the model),
    else float((u >> 20) % m), m = 2 for the flag_ / has_ / _missing columns and 5 otherwise
    (small integers as floats: ties in every column and in pd_logistic)
  default_flag: null when hsh(f, 800+i) % 25 == 0, else 1.0 when
    va + vb + hsh(f+7, 700+i) % 7 >= 5 + hsh(s, 602) % 3, else 0.0; va, vb = the cells (null as 0)
    of two candidate columns a = CAND[hsh(s, 600) % 36], b = CAND[hsh(s, 601) % 36]
Precondition (def:run_py_py_py_precond) as a Python function `pre`, on the locals of the real run:
  okT of both tables -> both frames have a row, 42 distinct names, every column Float64 (asserted
    of the import); final_effects != [] -> len(final.names) > 1; n_obs != 0 -> fit_frame.height > 0;
  stepwise.final / intercept_only present -> not None; step 03: exp(-lr/n_obs), exp(-m2ll0/n_obs)
    finite and 1 - exp(-m2ll0/n_obs) != 0 -> the same expressions; step 04: exp(-eta) finite on
    every row -> pd_logistic != 0.0 wherever it is not null (exp overflow gives exactly 0.0);
    step 06: cov[idx, idx] >= 0, sqrt != 0, the three exp finite -> the same expressions;
  the column-presence / dtype clauses of the steps hold by construction of the files.
  NOT rendered: the preconditions of the library units reached through steps 05, 07, 08, 13, 14
  (association_table, hosmer_lemeshow, classification_table, roc_association, merge_one_to_one):
  a seed on which the real run returns is taken as inside them.
"""
from __future__ import annotations

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
    if len(sw.final.names) <= 1:
        return False, "final_effects = []"
    m2ll0 = L["m2ll0"]
    try:
        for st in sw.steps:
            if not math.isfinite(math.exp(-(m2ll0 - (-2.0) * st.fit.loglik) / n)):
                return False, "step 03 exp not finite"
        e0 = math.exp(-m2ll0 / n)
        if not math.isfinite(e0) or 1.0 - e0 == 0.0:
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
    return True, ""


LGEN = (
    "let NAMES : List String := " + json.dumps(NAMES) + "; "
    "let MODS : List UInt64 := NAMES.map (fun (n : String) => if n.startsWith \"flag_\" || n.startsWith \"has_\" || n.endsWith \"_missing\" then 2 else 5); "
    "let CANDJ : List Nat := (List.range 42).filter (fun (j : Nat) => !([0, 1, 7, 11, 12, 37] : List Nat).contains j); "
    "let cell := fun (f j i : Nat) => (let u := hsh (f * 64 + j + 1) i; if i > 0 && (hsh f (500 + j)) % 12 == 0 && (u >>> 8) % 100 < 8 then (none : Option Float) "
    "else some (Float.ofNat ((u >>> 20) % (MODS.getD j 5)).toNat)); "
    "let cz := fun (f j i : Nat) => (match cell f j i with | none => 0 | some v => v.toUInt64.toNat : Nat); "
    "let flg := fun (s f i : Nat) => (if (hsh f (800 + i)) % 25 == 0 then (none : Option Float) else "
    "let a := CANDJ.getD ((hsh s 600) % 36).toNat 0; let b := CANDJ.getD ((hsh s 601) % 36).toNat 0; "
    "some (if cz f a i + cz f b i + ((hsh (f + 7) (700 + i)) % 7).toNat >= 5 + ((hsh s 602) % 3).toNat then 1.0 else 0.0)); "
    "let gT := fun (s f n : Nat) => ((List.range n).map (fun (i : Nat) => (List.range 42).map (fun (j : Nat) => "
    "(NAMES.getD j \"\", Tabular.Cell.num (if j == 1 then flg s f i else cell f j i)))) : Tabular.Table Float); "
)
HSH = ("let hsh := fun (s i : Nat) => let z : UInt64 := s.toUInt64 * 0x9E3779B97F4A7C15 + i.toUInt64 * 0xD1B54A32D192ED03 + 1; "
       "let z := (z ^^^ (z >>> 30)) * 0xBF58476D1CE4E5B9; let z := (z ^^^ (z >>> 27)) * 0x94D049BB133111EB; z ^^^ (z >>> 31); ")
assert [j for j, n in enumerate(NAMES) if n in NOTC] == [0, 1, 7, 11, 12, 37]


PREFIX = t18.W + t18.BI + t18.TS + t18.TX + t18.TD + t18.FL + t18.MW + t18.FMT + t18.KEYED + t18.MKFIT + HSH + LGEN


def lean_input(s: int, rec: dict):
    L, sw = rec["locals"], rec["stepwise"]
    T = t18.routine_tables(rec)
    today = L["model_summary"].get_column("training_date").to_list()[0]
    order = [n for n, _ in rec["writes"]]
    writes = dict(rec["writes"])
    assert len(order) == len(writes) == 18
    nt, nv = rec["imports"][0][1].height, rec["imports"][1][1].height
    lets = (PREFIX
            + t18.lean_routines(T) + f"let SW := {t18.lean_stepwise(sw)}; "
            + f'let today : Tabular.Cell Float := Tabular.Cell.str (some "{today.isoformat()}"); '
            + f"let tT := gT {s} {s} {nt}; let tV := gT {s} {s + OFFV} {nv}; "
            + "let RUN := run_py_py_py fw fo d8 d12 pv chi2 today SW fsum inv solve matmul matvec dot einsum log1p pow2; "
            + "let R := (RUN (some tT) (some tV)).getD ([], (Float.ofBits 0, [])); ")
    body = ("([(R.1.length : Int), bi R.2.1, W (R.2.2.flatMap (fun (p : String × Float) => ts p.1 ++ [bi p.2]))] ++ "
            "R.1.map (fun (p : String × Tabular.Table Float) => W (TDN p)))")
    mj = rec["model_json"]
    exp = [18, t18.fb(mj["intercept"]), t18.w([t for c, b in mj["coefficients"].items() for t in t18.ts(c) + [t18.fb(b)]])]
    exp += [t18.w(t18.tdn(n, writes[n])) for n in order]
    return lets, body, exp, ["number of files", "model.json intercept", "model.json coefficients"] + order


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
              f"steps {[(x.entered, x.removed) for x in sw.steps]}", f"final {sw.final.names[1:]}", f"{len(text)} chars", f"{time.time() - t0:.1f}s")


SEEDS_FIRST, SEEDS_LAST = 60000, 60039
# the seeds sent to Lean (one eval input each, typed first-hand): chosen among the 40 for variety of
# the stepwise path and of the validation file, smaller inputs first
SENT_KEPT = [60008, 60031, 60017, 60037, 60007, 60010]
SENT_REJECTED = [60009, 60004]
# eval inputs: the seeds of a group share the fixed prefix (digests, formatters, generator); each seed
# is a parenthesised block with its own tables. A group of one seed is the plain form.
GROUPS = [[60008], [60031, 60017, 60009], [60037, 60007], [60010, 60004]]
assert sorted(x for g in GROUPS for x in g) == sorted(SENT_KEPT + SENT_REJECTED)


def build(only: list[int] | None = None) -> None:
    suite_mod.CARRIERS["identity"] = ("def:zz_carrier_t", "zz_carrier_t")
    s = Suite("fz_train_run" if only is None else "fz_train_run_smoke")
    stats = {"kept": [], "rejected": {}, "raised": {}}
    recs = {}
    for seed in range(SEEDS_FIRST, SEEDS_LAST + 1):
        st, r = run_seed(seed)
        if st == "raised":
            stats["raised"][seed] = r
            continue
        ok, why = pre(r)
        if ok:
            stats["kept"].append(seed)
        else:
            stats["rejected"][seed] = why
        recs[seed] = (ok, r)
    for group in ([only] if only is not None else GROUPS):
        blocks, cases = [], []
        for seed in group:
            ok, r = recs[seed]
            assert ok == (seed in SENT_KEPT) or only is not None, seed
            lets, body, exp, labels = lean_input(seed, r)
            assert lets.startswith(PREFIX)
            blocks.append((lets[len(PREFIX):], body))
            sw = r["stepwise"]
            what = (f"seed {seed}: {r['imports'][0][1].height}/{r['imports'][1][1].height} rows, n_obs {r['locals']['n_obs']}, "
                    f"steps {[(x.entered, x.removed) for x in sw.steps]}, final {sw.final.names[1:]}")
            cases += [(f"{what}: {lab}", "run_py_py_py", e, {"fz": "kept" if ok else "rejected", "covers": 1})
                      for lab, e in zip(labels, exp, strict=True)]
        if len(blocks) == 1:
            s.ints(PREFIX + blocks[0][0], blocks[0][1], cases, use_kit=False)
        else:
            s.ints(PREFIX + "".join(f"let r{k} : List Int := ({lt_}{bd}); " for k, (lt_, bd) in enumerate(blocks)),
                   "(" + " ++ ".join(f"r{k}" for k in range(len(blocks))) + ")", cases, use_kit=False)
    s.write()
    assert all("stepwise_logistic" in v for v in stats["raised"].values()), stats["raised"]
    if only is None:
        (suite_mod.WORK / "fz_train_run.fuzz.json").write_text(json.dumps({
            "fuzzer": "port-translator-10", "generator": "diffeval/units/fz_train_run_gen.py", "units": {"run_py_py_py": {
                "seeds": f"{SEEDS_FIRST}..{SEEDS_LAST} generated; sent to Lean: kept {SENT_KEPT}, rejected {SENT_REJECTED}",
                "generated": SEEDS_LAST - SEEDS_FIRST + 1, "kept": len(SENT_KEPT),
                "python_raises_inside_precondition": [],
                "note": (f"one case = one value (number of files, model.json, one digest per exported table) of the whole train.run on one "
                         f"seed; files of 30-59 / 1-14 rows, small integers as floats (ties), nulls in some columns and in default_flag; "
                         f"of the 40 seeds {len(stats['kept'])} are inside the rendered precondition, {len(stats['rejected'])} return with "
                         f"an intercept-only final model (rejected by `final_effects != []`), {len(stats['raised'])} have no stepwise "
                         f"result (the real stepwise_logistic raises 'did not converge': the parameter does not exist, no input to "
                         f"send); only {len(SENT_KEPT)} + {len(SENT_REJECTED)} seeds were sent: each input is 8,000-13,000 characters of "
                         f"routine tables typed first-hand")}}}, indent=1))
    print({k: (len(v), sorted(v)) for k, v in stats.items()})
    for i, inp in enumerate(s.inputs):
        print(i, len(inp["text"]), "chars")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--explore":
        explore(int(sys.argv[2]), int(sys.argv[3]))
    elif len(sys.argv) > 1 and sys.argv[1] == "--only":
        build([int(x) for x in sys.argv[2:]])
    else:
        build()
