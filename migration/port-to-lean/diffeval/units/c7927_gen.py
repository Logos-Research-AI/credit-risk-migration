"""Re-translation after commit 7927af7 (plain `<` / `<=` -> sas_compat.lt / le): differential tests
of the six re-translated step items

  def:fe_run_02_income_medians, def:fe_run_03_cleaned, def:fe_run_05_features,
  def:predict_run_02_medians, def:predict_run_03_cleaned, def:predict_run_05_features.

  uv run python migration/diffeval/units/c7927_gen.py [fe] [pred]
      -> work/c7927_fe, work/c7927_pred (.json + .inputs.json)
  (eval_decl each input on def:zz_carrier_f / zz_carrier_f, save the outputs one per line as
   work/c7927_<suite>.out.txt)
  uv run python migration/diffeval/compare.py migration/diffeval/work/c7927_<suite>.json migration/diffeval/work/c7927_<suite>.out.txt

Adapted from units/b7_gen.py and units/b8_gen.py (their helpers are imported, not copied). Python
side: the REAL `feature_engineering.run` / `predict.run`, instrumented from outside as there (a
profile hook copies the locals of `run` at return). Lean side: the steps 01..05 are chained
(01 and 04 are accepted items that did not change); every intermediate is compared with Python's
local, so each of the six units is tested on the inputs Python had. Steps 06+ and the `run` items
are not evaluated here (cleared by other re-translations).

Scenarios:
  real-data slices as in b7 / b8 (slice250 of data/cs-training.csv; 200 lines of data/cs-test.csv
  and of the edge_predict file, fix_train_medians False and True);
  hand-made imported frames (proc_import_csv replaced by a function returning the frame, as in b7)
  that reach a missing value in every comparison the commit changed:
    thresholds  text MonthlyIncome / NumberOfDependents through the REAL input_best32: null and NaN
                age, utilization, debt ratio, credit lines; values exactly at 30/40/50/60,
                25/35/65 (age), 30/50/75 (credit_utilization), 30/43/60 (debt_ratio), 2500
                (monthly_income), 2 (num_credit_lines) and next to them; an age group without any
                income (null monthly_income after the imputation)
    nanincome   numeric MonthlyIncome / NumberOfDependents with `sas_compat.input_best32` replaced by
                the identity on BOTH sides (it is an explicit parameter of step 01; the real one
                turns NaN into null, so a NaN monthly_income is not reachable through it): NaN
                monthly_income, directly and through a NaN median
"""
from __future__ import annotations

import contextlib
import io
import json
import math
import sys
import tempfile
from pathlib import Path

import polars as pl

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(ROOT))

import b7_gen as b7  # noqa: E402
import b8_gen as b8  # noqa: E402
import compare as cmp  # noqa: E402
import leanterm as lt  # noqa: E402
from suite import Suite  # noqa: E402

from credit_risk import predict as pr  # noqa: E402
from credit_risk import sas_compat as sc  # noqa: E402

CARRIER = ("def:zz_carrier_f", "zz_carrier_f")
nan = float("nan")
dgf = b7.dgf
IBID = "let IBID := fun (e : Pl.Expr Float) => e; "

# ---------------------------------------------------------------- hand-made imported frames
#  VAR1  dlq  util     age   n30  debt     income  nopen n90  nre  n60  deps
THRESH = [
    (1,   0,   0.3,     30,   0,   0.3,     2500,   2,    0,   0,   0,   0),      # exactly 30 / 30 / 2500 / 2
    (2,   0,   0.5,     40,   0,   0.43,    2499,   3,    0,   0,   0,   1),      # 50 / 43
    (3,   1,   0.75,    50,   1,   0.6,     "NA",   1,    0,   0,   0,   2),      # 75 / 60; group 4 has no income
    (4,   0,   0.2,     60,   0,   0.2,     2501,   0,    0,   0,   0,   3),
    (5,   0,   None,    None, 0,   None,    "NA",   None, 0,   0,   0,   "NA"),   # nulls; income imputed from group 1
    (6,   0,   nan,     nan,  0,   nan,     3000,   nan,  0,   0,   0,   0),      # NaN everywhere
    (7,   0,   0.1,     25,   0,   0.1,     "NA",   4,    0,   0,   0,   "NA"),
    (8,   0,   0.9,     35,   2,   0.9,     7000,   5,    1,   0,   0,   0),
    (9,   0,   0.1,     65,   0,   0.1,     9000,   6,    0,   0,   0,   0),
    (10,  0,   math.nextafter(0.3, 0), 24, 0, math.nextafter(0.3, 0), 1000, 2, 0, 0, 0, 0),   # just below 30
    (11,  0,   math.nextafter(0.3, 1), 29, 0, math.nextafter(0.3, 1), 2000, 7, 0, 0, 0, 0),   # just above 30
    (12,  0,   math.nextafter(0.5, 0), 34, 0, math.nextafter(0.43, 0), 4000, 2, 0, 0, 0, 1),
    (13,  0,   math.nextafter(0.75, 0), 39, 0, math.nextafter(0.6, 0), 4100, 3, 0, 0, 0, 1),
    (14,  0,   math.nextafter(0.75, 1), 49, 0, math.nextafter(0.6, 1), 5000, 9, 0, 0, 0, 1),
    (15,  1,   2.5,     59,   3,   50,      "NA",   12,   2,   1,   1,   0),      # group 4 again: null monthly_income
    (16,  0,   0.4,     64,   0,   0.5,     6000,   2,    0,   0,   0,   2),
    (17,  0,   0.4,     None, 0,   0.5,     1500,   None, 0,   0,   0,   0),      # null age WITH an income: enters the median of group 1
    (18,  0,   None,    nan,  0,   None,    "NA",   2,    0,   0,   0,   0),      # NaN age, income NA: imputed from group 5
    (19,  0,   0.0,     29.999999999999996, 0, 0.0, 0, 2.0000000000000004, 0, 0, 0, 0),
    (20,  0,   1.0,     math.nextafter(60, 61), 0, 1.0, 2500, 1.9999999999999998, 0, 0, 0, 0),
]
THRESH_SPLIT = [1, 3, 5, 6, 10, 15, 17, 20]
#  numeric income / dependents, input_best32 = identity: NaN reaches monthly_income
NANINC = [
    (1,   0,   0.3,     45,   0,   0.3,     nan,    2,    0,   0,   0,   0),      # group 3: one income, NaN -> median NaN
    (2,   0,   0.5,     41,   0,   0.43,    None,   3,    0,   0,   0,   1),      # imputed with the NaN median
    (3,   1,   0.75,    33,   1,   0.6,     nan,    1,    0,   0,   0,   2),      # group 2: [NaN, 1000, 2000] -> 2000
    (4,   0,   0.2,     31,   0,   0.2,     1000,   0,    0,   0,   0,   3),
    (5,   0,   0.2,     32,   0,   0.2,     2000,   0,    0,   0,   0,   0),
    (6,   0,   0.2,     38,   0,   0.2,     None,   0,    0,   0,   0,   None),
    (7,   0,   None,    None, 0,   None,    2500.5, None, 0,   0,   0,   0),      # group 1 (null age): [2500.5, NaN] -> NaN
    (8,   0,   nan,     22,   0,   nan,     nan,    nan,  0,   0,   0,   0),
    (9,   0,   0.1,     None, 0,   0.1,     None,   2,    0,   0,   0,   1),
    (10,  0,   0.1,     70,   0,   0.1,     2499.9999999999995, 2, 0, 0, 0, 1),
    (11,  0,   0.1,     nan,  0,   0.1,     2500.0000000000005, 3, 0, 0, 0, 1),
    (12,  0,   0.1,     55,   0,   0.1,     None,   3,    0,   0,   0,   0.5),    # group 4: no income -> null monthly_income
]
NANINC_SPLIT = [2, 3, 7, 8, 12]


# ================================================================ feature_engineering
FE_BODY = (
    "let s1 := fe_run_01_clean IBX (Pl.ofTable T); "
    "let s2 := fe_run_02_income_medians s1; "
    "let s3 := fe_run_03_cleaned s1; "
    "let s4 := fe_run_04_imputed s3 s2; "
    "let s5 := fe_run_05_features true s4; "
    "let s5f := fe_run_05_features false s4; "
    "[dg (tA T), dg (tR s1), dg (tR s2), dg (tR s3), dg (tR s4), dg (tR s5), dg (tR s5f)]"
)
FE_STEPS = [("credit_raw_clean", "fe_run_01_clean (chain)"), ("income_medians", "fe_run_02_income_medians"),
            ("credit_cleaned", "fe_run_03_cleaned"), ("credit_imputed", "fe_run_04_imputed (chain)")]


@contextlib.contextmanager
def identity_best32(on: bool):
    o = sc.input_best32
    if on:
        sc.input_best32 = lambda e: e
    try:
        yield
    finally:
        sc.input_best32 = o


def fe_scenario(s: Suite, name: str, split_ids: list, *, csv_text=None, frame=None, ident=False):
    split_text = "row_id\n" + "".join(("" if v is None else str(v)) + "\n" for v in split_ids)
    with identity_best32(ident):
        L = b7.pyrun(split_text, csv_text=csv_text, frame=frame)["locals"]
    raw = L["credit_raw"]
    assert raw.columns == b7.COLS
    lets = b7.MK + IBID + f"let IBX := {'IBID' if ident else 'IB'}; " + b7.lean_table("T", raw)
    c = lambda cid, prim, val: (f"{name}: {cid}", prim, val)  # noqa: E731
    cases = [c("input table cs_training (the imported frame)", "harness input", cmp.digest(cmp.tokens(cmp.canon_table(raw))))]
    cases += [c(k, u, dgf(L[k])) for k, u in FE_STEPS]
    cases += [c("credit_features full=true", "fe_run_05_features", dgf(L["credit_features"])),
              c("credit_features full=false", "fe_run_05_features", dgf(L["credit_features"]))]
    s.ints(lets, FE_BODY, cases, table=True)
    cf, ci, cc = L["credit_features"], L["credit_imputed"], L["credit_cleaned"]
    print(f"[fe {name}] rows={raw.height} medians={L['income_medians'].rows()}\n"
          f"   null/NaN age={cc['age'].null_count()}/{cc['age'].is_nan().sum()} "
          f"credit_utilization={ci['credit_utilization'].null_count()}/{ci['credit_utilization'].is_nan().sum()} "
          f"debt_ratio={ci['debt_ratio'].null_count()}/{ci['debt_ratio'].is_nan().sum()} "
          f"monthly_income={ci['monthly_income'].null_count()}/{ci['monthly_income'].is_nan().sum()} "
          f"num_credit_lines={ci['num_credit_lines'].null_count()}/{ci['num_credit_lines'].is_nan().sum()}")
    if raw.height <= 30:
        with pl.Config(tbl_rows=40, tbl_cols=30, tbl_width_chars=250):
            print(cf.select("row_id", "age", "age_group", "age_category", "credit_utilization", "credit_util_category",
                            "debt_ratio", "debt_category", "monthly_income", "flag_low_income", "num_credit_lines",
                            "flag_few_credit_lines"))
    return L


def suite_fe() -> Suite:
    s = Suite("c7927_fe")
    s.item, s.decl = CARRIER
    rows = sorted(set(list(range(1, 21)) + list(range(2551, 2779)) + b7.long_income_rows(2)))
    fe_scenario(s, "slice250", b7.real_split(rows), csv_text=b7.slice_text(rows))
    fe_scenario(s, "edges (b7)", b7.EDGES_SPLIT, frame=b7.hand(b7.EDGES))
    fe_scenario(s, "thresholds", THRESH_SPLIT, frame=b7.hand(THRESH))
    fe_scenario(s, "nanincome", NANINC_SPLIT, frame=b7.hand(NANINC, mi_text=False, nd_text=False), ident=True)
    return s


# ================================================================ predict
PR_STEPS = [("test_raw_clean", "predict_run_01_clean (chain)"), ("test_income_medians", "predict_run_02_medians"),
            ("test_cleaned", "predict_run_03_cleaned"), ("test_imputed", "predict_run_04_imputed (chain)")]
# runS T MI ND MED fx : the digests of one run (b8.RUNS cut after step 05)
RUNS5 = (
    "let runS := fun (T : Tabular.Table Float) (MI ND : List (Option Float)) "
    "(MED : Option (Pl.Frame Float)) (fx : Bool) => ("
    "let ib := fun (e : Pl.Expr Float) => (({ eval := fun (_ : Option (List (List Nat))) (_ : Pl.Frame Float) => "
    "Pl.Col.f64 (if e.name == some \"MonthlyIncome\" then MI else ND), name := e.name, ser := Pl.node [e.ser] }) : Pl.Expr Float); "
    "let s1 := predict_run_01_clean ib (Pl.ofTable T); "
    "let s2 := predict_run_02_medians MED s1 fx; "
    "let s3 := predict_run_03_cleaned s1; "
    "let s4 := predict_run_04_imputed s3 s2; "
    "let s5 := predict_run_05_features true s4; "
    "let s5f := predict_run_05_features false s4; "
    "([dg (tA T), dg (tR s1), dg (tR s2), dg (tR s3), dg (tR s4), dg (tR s5), dg (tR s5f)] : List Int)); "
)
MODEL = b8.MODEL_0  # the model is read after step 05; no coefficient, so every frame scores


def pr_pyrun(fix: bool, medians_text, *, csv_text=None, frame=None, ident=False) -> dict:
    rec: dict = {}
    o_write, o_import = sc.write_sas_csv, sc.proc_import_csv

    def prof(fr, event, arg):
        if event == "return" and fr.f_code is pr.run.__code__:
            rec["locals"] = dict(fr.f_locals)

    with tempfile.TemporaryDirectory() as d, identity_best32(ident):
        dd, ind, outd = Path(d) / "data", Path(d) / "in", Path(d) / "out"
        dd.mkdir()
        ind.mkdir()
        (ind / "model.json").write_text(json.dumps(MODEL))
        mpath = None
        if medians_text is not None:
            mpath = ind / "income_medians.csv"
            mpath.write_text(medians_text)
            rec["medians"] = pl.read_csv(mpath, schema_overrides={"age_group": pl.Int32, "median_income": pl.Float64})
        if csv_text is not None:
            (dd / "cs-test.csv").write_text(csv_text)
            raw = sc.proc_import_csv(dd / "cs-test.csv", guessingrows=None)
        else:
            raw = frame
            sc.proc_import_csv = lambda path, guessingrows=20: frame
        rec["raw"] = raw
        rec["mi"] = raw.select(sc.input_best32(pl.col("MonthlyIncome"))).to_series()
        rec["nd"] = raw.select(sc.input_best32(pl.col("NumberOfDependents"))).to_series()
        assert rec["mi"].dtype == pl.Float64 and rec["nd"].dtype == pl.Float64
        sc.write_sas_csv = lambda df, path, formats=None: None
        sys.setprofile(prof)
        try:
            with contextlib.redirect_stdout(io.StringIO()):
                pr.run(ind, outd, data_dir=dd, fix_train_medians=fix, medians=mpath if fix else None)
        finally:
            sys.setprofile(None)
            sc.write_sas_csv, sc.proc_import_csv = o_write, o_import
    return rec


def opt_floats(s_: pl.Series) -> str:
    return "[" + ", ".join("none" if v is None else f"some {lt.lean_float(v)}" for v in s_.to_list()) + "]"


def pr_group(s: Suite, text_or_frame, runs: list, *, ident=False):
    """One eval input: the runs (name, fix, medians text) on one imported frame."""
    is_csv = isinstance(text_or_frame, str)
    lets, calls, cases, first = "", [], [], True
    meds: dict[str, str] = {}
    for name, fix, med_text in runs:
        r = pr_pyrun(fix, med_text, **({"csv_text": text_or_frame} if is_csv else {"frame": text_or_frame}), ident=ident)
        L = r["locals"]
        if first:
            if is_csv:  # b8 encoding (codes in one string)
                lets = (b8.MK + RUNS5 + f"let T : Tabular.Table Float := {b8.lean_table(r['raw'])}; "
                        f"let MI : List (Option Float) := {b8.opt_floats(r['mi'])}; "
                        f"let ND : List (Option Float) := {b8.opt_floats(r['nd'])}; ")
            else:       # b7 encoding (handles NaN and any float by its bits)
                lets = (b7.MK + RUNS5 + b7.lean_table("T", r["raw"])
                        + f"let MI : List (Option Float) := {opt_floats(r['mi'])}; "
                        f"let ND : List (Option Float) := {opt_floats(r['nd'])}; ")
            first = False
        med = "none"
        if med_text is not None:
            m = r["medians"]
            if fix:
                assert cmp.canon_frame(m) == cmp.canon_frame(L["test_income_medians"])
            if med_text not in meds:
                meds[med_text] = f"M{len(meds)}"
                lets += f"let {meds[med_text]} : Option (Pl.Frame Float) := (some {lt.lean_frame(m)}); "
            med = meds[med_text]
        calls.append(f"(runS T MI ND {med} {lt.lean_bool(fix)})")
        tag = f"{name} fix_train_medians={fix}"
        c = lambda cid, prim, val: (f"{tag}: {cid}", prim, val)  # noqa: E731
        cases.append(c("input table cs_test", "harness input", cmp.digest(cmp.tokens(cmp.canon_table(r["raw"])))))
        cases += [c(k, u, dgf(L[k])) for k, u in PR_STEPS]
        cases += [c("test_features full=true", "predict_run_05_features", dgf(L["test_features"])),
                  c("test_features full=false", "predict_run_05_features", dgf(L["test_features"]))]
        ti, tf = L["test_imputed"], L["test_features"]
        print(f"[pred {tag}] rows={r['raw'].height} medians={L['test_income_medians'].rows()}\n"
              f"   null/NaN age={ti['age'].null_count()}/{ti['age'].is_nan().sum()} "
              f"credit_utilization={ti['credit_utilization'].null_count()}/{ti['credit_utilization'].is_nan().sum()} "
              f"debt_ratio={ti['debt_ratio'].null_count()}/{ti['debt_ratio'].is_nan().sum()} "
              f"monthly_income={ti['monthly_income'].null_count()}/{ti['monthly_income'].is_nan().sum()} "
              f"num_credit_lines={ti['num_credit_lines'].null_count()}/{ti['num_credit_lines'].is_nan().sum()}")
        if r["raw"].height <= 30:
            with pl.Config(tbl_rows=40, tbl_cols=30, tbl_width_chars=250):
                print(tf.select("row_id", "age", "age_group", "age_category", "credit_utilization", "credit_util_category",
                                "debt_ratio", "debt_category", "monthly_income", "flag_low_income", "num_credit_lines",
                                "flag_few_credit_lines"))
    s.ints(lets, " ++ ".join(calls), cases, table=True)


def suite_pred() -> Suite:
    s = Suite("c7927_pred")
    s.item, s.decl = CARRIER
    N_HEAD, N = 120, 200
    real = b8.pick(ROOT / "data" / "cs-test.csv", N_HEAD, N)
    edge = b8.pick(ROOT / "inputs" / "scenarios" / "edge_predict" / "cs-test.csv", N_HEAD, N)
    pr_group(s, real, [(f"data/cs-test[{N}]", False, None), (f"data/cs-test[{N}] training medians", True, b8.MED_OK)])
    pr_group(s, edge, [(f"edge_predict[{N}]", False, None), (f"edge_predict[{N}] dup medians", True, b8.MED_DUP)])
    pr_group(s, b7.hand(THRESH), [("thresholds", False, None), ("thresholds training medians", True, b8.MED_OK),
                                  ("thresholds dup medians", True, b8.MED_DUP)])
    pr_group(s, b7.hand(NANINC, mi_text=False, nd_text=False),
             [("nanincome", False, None), ("nanincome training medians", True, b8.MED_OK)], ident=True)
    return s


if __name__ == "__main__":
    want = set(sys.argv[1:]) or {"fe", "pred"}
    if "fe" in want:
        suite_fe().write()
    if "pred" in want:
        suite_pred().write()
