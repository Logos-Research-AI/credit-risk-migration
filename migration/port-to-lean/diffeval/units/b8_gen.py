"""Bundle B8 differential tests: the eight step items def:predict_run_01 .. _08 and def:run_py_py
(predict.run).

  uv run python migration/diffeval/units/b8_gen.py
      -> work/b8_run (.json + .inputs.json)
  (eval_decl each input of work/b8_run.inputs.json on def:zz_carrier / zz_carrier, save the outputs
   one per line as work/b8_run.out.txt)
  uv run python migration/diffeval/compare.py migration/diffeval/work/b8_run.json migration/diffeval/work/b8_run.out.txt
  uv run python migration/diffeval/receipts.py units b8

Python side: the REAL `predict.run` is called on a temporary directory that holds `cs-test.csv`
(the header and chosen data lines of data/cs-test.csv or inputs/scenarios/edge_predict/cs-test.csv,
verbatim; or a small hand-made file), `model.json` and, with the flag, a medians CSV. Nothing of
`run` is copied here. The run is instrumented from outside:
  - `sas_compat.write_sas_csv` is replaced by a recorder: the frames Python hands to it, in call
    order, are the expected output tables of `run_py_py`;
  - a profile hook copies the local variables of `run` when it returns: they are the expected
    results of the step items (test_raw_clean, test_income_medians, test_cleaned, test_imputed,
    test_features, test_scored, test_predictions, kaggle_submission, test_predictions_full).

Lean side, one eval input per input file (the runs on the same file share the table):
  - `cs_test` = the frame `sas_compat.proc_import_csv(path, guessingrows=None)` returns, built
    inside Lean from short integer codes (a numeric cell m * 10^-e is the code m * 64 + e, built
    with `Float.ofScientific m true e`; a text cell an index into a string list; -1 a null); the
    digest of the table is compared first, so the input is the same bit for bit;
  - `input_best32` test double: `ib e` ignores what `e` evaluates to and returns the precomputed
    Float64 column keyed on `e.name`: for "MonthlyIncome" the column the real
    `sas_compat.input_best32(pl.col("MonthlyIncome"))` gives on the imported frame, for any other
    name the one of "NumberOfDependents" (name and serialization of `e` kept);
  - `intercept`, `coefficients` = the parsed model.json (floats by their bits, key order kept);
  - `medians` = `some` of the frame `pl.read_csv(medians, schema_overrides=...)` returns, or `none`;
  - the steps are chained (each step reads what the previous Lean steps produced; every
    intermediate is compared with Python's local, so a step is tested on the inputs Python had);
    step 05 and `run_py_py` are evaluated with `full` true and false (both must equal Python).
"""
from __future__ import annotations

# RETIRED 2026-11-16: this script is a record of the port before the update of 2026-11-16 and no longer
# runs: it calls fix_train_medians, medians; see t7_gen.py, t8_gen.py, t9_gen.py, t11_gen.py.
# Its recorded outputs describe the port as it was then.
import sys as _sys

_sys.exit("RETIRED 2026-11-16: " + __file__ + " calls keywords the port no longer has; see the note at its top")


import contextlib
import io
import json
import sys
import tempfile
from decimal import Decimal
from pathlib import Path

import polars as pl

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(ROOT))

import compare as cmp  # noqa: E402
import leanterm as lt  # noqa: E402
from suite import Suite  # noqa: E402

from credit_risk import predict as pr  # noqa: E402
from credit_risk import sas_compat as sc  # noqa: E402

STEP_LOCALS = [  # (local of run, unit)
    ("test_raw_clean", "predict_run_01_clean"),
    ("test_income_medians", "predict_run_02_medians"),
    ("test_cleaned", "predict_run_03_cleaned"),
    ("test_imputed", "predict_run_04_imputed"),
    ("test_features", "predict_run_05_features"),
    ("test_scored", "predict_run_06_score"),
    ("test_predictions", "predict_run_07_predictions"),
    ("kaggle_submission", "predict_run_08_outputs"),
    ("test_predictions_full", "predict_run_08_outputs"),
]
FILES = ["kaggle_submission.csv", "test_predictions.csv"]


# ---------------------------------------------------------------- the instrumented real run
def pyrun(csv_text: str, model: dict, fix: bool, medians_text: str | None) -> dict:
    rec: dict = {"files": [], "locals": None}
    o_write = sc.write_sas_csv

    def w_write(df, path, formats=None):
        rec["files"].append((Path(path).name, df))

    def prof(frame, event, arg):
        if event == "return" and frame.f_code is pr.run.__code__:
            rec["locals"] = dict(frame.f_locals)

    with tempfile.TemporaryDirectory() as d:
        dd, ind, outd = Path(d) / "data", Path(d) / "in", Path(d) / "out"
        dd.mkdir()
        ind.mkdir()
        (dd / "cs-test.csv").write_text(csv_text)
        (ind / "model.json").write_text(json.dumps(model))
        mpath = None
        if medians_text is not None:
            mpath = ind / "income_medians.csv"
            mpath.write_text(medians_text)
            rec["medians"] = pl.read_csv(mpath, schema_overrides={"age_group": pl.Int32, "median_income": pl.Float64})
        raw = sc.proc_import_csv(dd / "cs-test.csv", guessingrows=None)
        rec["raw"] = raw
        rec["mi"] = raw.select(sc.input_best32(pl.col("MonthlyIncome"))).to_series()
        rec["nd"] = raw.select(sc.input_best32(pl.col("NumberOfDependents"))).to_series()
        assert rec["mi"].dtype == pl.Float64 and rec["nd"].dtype == pl.Float64
        sc.write_sas_csv = w_write
        sys.setprofile(prof)
        try:
            with contextlib.redirect_stdout(io.StringIO()):
                pr.run(ind, outd, data_dir=dd, fix_train_medians=fix, medians=mpath if fix else None)
        finally:
            sys.setprofile(None)
            sc.write_sas_csv = o_write
    assert [f for f, _ in rec["files"]] == FILES
    return rec


def dgf(df: pl.DataFrame) -> int:
    return cmp.digest(cmp.tokens(cmp.canon_frame(df)))


def dgt(name: str, df: pl.DataFrame) -> int:
    return cmp.digest(cmp.tok_str(name) + cmp.tokens(cmp.canon_table(df)))


# ---------------------------------------------------------------- short Lean terms
def opt_floats(s: pl.Series) -> str:
    """List (Option Float): `(oF "codes")` (comma-separated; -1 = null, n = Float.ofNat n) when
    every value is a non-negative integer, else the values by their bits."""
    vals = s.to_list()
    if all(v is None or (v == int(v) and 0 <= v < 2**53 and lt.bits(v) != lt.bits(-0.0)) for v in vals):
        return '(oF "' + ",".join("-1" if v is None else str(int(v)) for v in vals) + '")'
    return "[" + ", ".join("none" if v is None else f"some {lt.lean_float(v)}" for v in vals) + "]"


# The integer codes travel as ONE comma-separated string literal (a 2400-element list literal
# does not elaborate in the time eval_decl allows); `cs` splits it back into integers.
# mkT names kinds strs codes: the table of names.length columns, row-major codes. kind 0: numeric
# cell (code -1 = null, else m * 64 + e for m * 10^-e); kind 1: text cell (code -1 = null, else an
# index into the comma-separated strs).
MK = (
    "let cs := fun (s : String) => ((s.splitOn \",\").map (fun (x : String) => (x.toInt?).getD (-1))).toArray; "
    "let oF := fun (s : String) => (cs s).toList.map (fun (v : Int) => (if v < 0 then none else some (Float.ofNat v.toNat) : Option Float)); "
    "let mkT := fun (names : List String) (kinds : List Nat) (strs : String) (codes : String) => "
    "(let C := cs codes; let S := (strs.splitOn \",\").toArray; "
    "((List.range (C.size / names.length)).map (fun (i : Nat) => (List.range names.length).map (fun (j : Nat) => "
    "let v : Int := C.getD (i * names.length + j) (-1); "
    "(names.getD j \"\", (if kinds.getD j 0 == 0 then Tabular.Cell.num (if v < 0 then none else some "
    "(Float.ofScientific (v.toNat / 64) true (v.toNat % 64))) else Tabular.Cell.str (if v < 0 then none else some "
    "(S.getD v.toNat \"\")) : Tabular.Cell Float)))) : Tabular.Table Float)); "
)


def lean_table(df: pl.DataFrame) -> str:
    """`mkT names kinds strs codes` for a frame of Float64 / String columns."""
    kinds, strs, cols = [], [], []
    for n in df.columns:
        s = df.get_column(n)
        if s.dtype == pl.String:
            kinds.append(1)
            codes = []
            for v in s.to_list():
                if v is None:
                    codes.append(-1)
                else:
                    if v not in strs:
                        strs.append(v)
                    codes.append(strs.index(v))
        else:
            assert s.dtype == pl.Float64, (n, s.dtype)
            kinds.append(0)
            codes = []
            for v in s.to_list():
                if v is None:
                    codes.append(-1)
                    continue
                assert v == v and v >= 0 and abs(v) != float("inf") and lt.bits(v) != lt.bits(-0.0), (n, v)
                sign, digits, exp = Decimal(repr(v)).as_tuple()
                m = int("".join(map(str, digits)))
                if exp > 0:
                    m, exp = m * 10 ** exp, 0
                assert -exp < 64
                assert float(f"{m}e{exp}") == v
                codes.append(m * 64 + (-exp))
        cols.append(codes)
    flat = ",".join(str(c[i]) for i in range(df.height) for c in cols)
    assert all("," not in x and '"' not in x and "\\" not in x for x in strs)
    return (f"(mkT [{', '.join(lt.lean_str(n) for n in df.columns)}] [{', '.join(map(str, kinds))}] "
            f"{lt.lean_str(','.join(strs))} \"{flat}\")")


# runS T MI ND IC CO MED fx : List Int -- the digests of one run, in the order of `cases` below
RUNS = (
    "let runS := fun (T : Tabular.Table Float) (MI ND : List (Option Float)) (IC : Float) (CO : List (String × Float)) "
    "(MED : Option (Pl.Frame Float)) (fx : Bool) => ("
    "let ib := fun (e : Pl.Expr Float) => (({ eval := fun (_ : Option (List (List Nat))) (_ : Pl.Frame Float) => "
    "Pl.Col.f64 (if e.name == some \"MonthlyIncome\" then MI else ND), name := e.name, ser := Pl.node [e.ser] }) : Pl.Expr Float); "
    "let s1 := predict_run_01_clean ib (Pl.ofTable T); "
    "let s2 := predict_run_02_medians MED s1 fx; "
    "let s3 := predict_run_03_cleaned s1; "
    "let s4 := predict_run_04_imputed s3 s2; "
    "let s5 := predict_run_05_features true s4; "
    "let s5f := predict_run_05_features false s4; "
    "let s6 := predict_run_06_score IC CO s5; "
    "let s7 := predict_run_07_predictions s6; "
    "let s8 := predict_run_08_outputs s7; "
    "let outs := fun (fl : Bool) => (run_py_py fl ib IC CO MED T fx).map (fun (p : String × Tabular.Table Float) => dg (tS p.1 ++ tA p.2)); "
    "([dg (tA T), dg (tR s1), dg (tR s2), dg (tR s3), dg (tR s4), dg (tR s5), dg (tR s5f), dg (tR s6), dg (tR s7), "
    "dg (tR s8.1), dg (tR s8.2)] ++ outs true ++ outs false : List Int)); "
)


def scenario(name: str, csv_text: str, model: dict, fix: bool, medians_text: str | None, k: int, bind):
    """-> (the lets `T<k>`, `MI<k>`, `ND<k>` of the input file, the Lean call, the cases)."""
    r = pyrun(csv_text, model, fix, medians_text)
    L = r["locals"]
    co = "[" + ", ".join(f"({lt.lean_str(k)}, {lt.lean_float(float(v))})" for k, v in model["coefficients"].items()) + "]"
    med = "none"
    if medians_text is not None:
        m = r["medians"]
        assert m.schema["age_group"] == pl.Int32 and m.schema["median_income"] == pl.Float64
        if fix:
            assert cmp.canon_frame(m) == cmp.canon_frame(L["test_income_medians"])
        med = f"(some {lt.lean_frame(m)})"
    tlets = (f"let T{k} : Tabular.Table Float := {lean_table(r['raw'])}; "
             f"let MI{k} : List (Option Float) := {opt_floats(r['mi'])}; "
             f"let ND{k} : List (Option Float) := {opt_floats(r['nd'])}; ")
    # the model and the medians frame are let-bound once per eval input (`bind` dedupes them)
    call = (f"(runS T{k} MI{k} ND{k} {lt.lean_float(float(model['intercept']))} "
            f"{bind('List (String × Float)', co)} {bind('Option (Pl.Frame Float)', med)} {lt.lean_bool(fix)})")
    tag = f"{name} fix_train_medians={fix}"
    c = lambda cid, prim, val: (f"{tag}: {cid}", prim, val)  # noqa: E731
    cases = [c("input table cs_test", "run_py_py", cmp.digest(cmp.tokens(cmp.canon_table(r["raw"]))))]
    for loc, unit in STEP_LOCALS:
        cases.append(c(loc, unit, dgf(L[loc])))
        if loc == "test_features":
            cases.append(c("test_features full=false", unit, dgf(L[loc])))
    for fl in ("true", "false"):
        cases += [c(f"{f} full={fl}", "run_py_py", dgt(f, df)) for f, df in r["files"]]
    P = L["test_predictions"]
    info = (f"[{tag}] rows={r['raw'].height} imputed rows={L['test_imputed'].height} "
            f"medians={dict(zip(L['test_income_medians'].get_column('age_group').to_list(), L['test_income_medians'].get_column('median_income').to_list()))} "
            f"null income={L['test_imputed'].get_column('monthly_income').null_count()} "
            f"null pd={P.get_column('pd_logistic').null_count()} grades={dict(sorted(P.group_by('risk_grade').len().iter_rows()))}")
    print(info)
    return tlets, call, cases


# ---------------------------------------------------------------- inputs
def pick(path: Path, n_head: int, n_total: int) -> str:
    """The header, the first n_head data lines and further lines chosen for their content (NA
    dependents, every age group, exponent notation, extreme utilization / debt ratio, incomes 0
    and huge, many dependents), n_total data lines in file order, verbatim."""
    lines = path.read_text().splitlines(keepends=True)
    head, data = lines[0], lines[1:]
    chosen = set(range(n_head))
    f = [ln.rstrip("\n").split(",") for ln in data]
    crit = [
        lambda r: r[11] == "NA",
        lambda r: "E-" in r[2] or "E-" in r[5],
        lambda r: float(r[2]) > 1000,
        lambda r: float(r[5]) > 20000,
        lambda r: r[6] == "0",
        lambda r: r[6] != "NA" and float(r[6]) > 200000,
        lambda r: r[11] != "NA" and float(r[11]) >= 6,
        lambda r: float(r[3]) < 23,
        lambda r: float(r[3]) > 95,
        lambda r: float(r[3]) < 30 and r[6] == "NA",
        lambda r: 30 <= float(r[3]) < 40 and r[6] == "NA",
        lambda r: float(r[8]) > 0 and float(r[4]) > 0 and float(r[10]) > 0,
        lambda r: 0 < float(r[2]) < 0.3 and float(r[5]) < 0.3 and r[6] != "NA" and float(r[6]) > 2500 and float(r[4]) == 0,
    ]
    k = 0
    while len(chosen) < n_total:
        pred = crit[k % len(crit)]
        k += 1
        for i in range(n_head, len(f)):
            if i not in chosen and pred(f[i]):
                chosen.add(i)
                break
        assert k < 100 * n_total
    return head + "".join(data[i] for i in sorted(chosen))


HEADER = (",SeriousDlqin2yrs,RevolvingUtilizationOfUnsecuredLines,age,NumberOfTime30-59DaysPastDueNotWorse,DebtRatio,"
          "MonthlyIncome,NumberOfOpenCreditLinesAndLoans,NumberOfTimes90DaysLate,NumberRealEstateLoansOrLines,"
          "NumberOfTime60-89DaysPastDueNotWorse,NumberOfDependents\n")

# real feature names; `debt_ratio` makes exp overflow (pd null) on the rows with a huge DebtRatio,
# `log_monthly_income` is null where the income is null (edge scenario: an age group without median)
MODEL_A = {"intercept": -1.5, "coefficients": {
    "credit_utilization_capped": 0.004, "log_monthly_income": -0.15, "total_late_payments": 0.45,
    "flag_low_income": 0.3, "age": -0.02, "debt_ratio": -0.004}}
# intercept 0.0 (the scalar-zero rule of `+`), an Int32 feature, features built with `/` and div
MODEL_B = {"intercept": 0.0, "coefficients": {
    "monthly_income": 1e-5, "income_per_dependent": -2e-5, "utilization_debt_interaction": 1e-6,
    "financial_health": -0.01, "num_dependents": 0.1, "age_category": 0.2, "total_risk_flags": 0.35,
    "log_num_credit_lines": -0.3, "credit_lines_per_person": 0.05}}
MODEL_0 = {"intercept": 0.25, "coefficients": {}}
MODEL_BIG = {"intercept": 3.0, "coefficients": {"credit_utilization": 0.5, "age_income_interaction": -0.01}}

MED_OK = "age_group,median_income\n3,6000\n1,2516\n5,5395\n2,4667\n4,6260.5\n"
# duplicated age groups (they pass the test of :72 and multiply the joined rows) and an extra column
MED_DUP = "age_group,median_income,n\n1,2516,10\n2,4667,20\n3,6000,30\n2,9999.5,40\n4,6260.5,50\n5,5395,60\n5,1,70\n5,,80\n"

SMALL = HEADER + (
    "1,,0.5,25,0,0.3,NA,4,0,0,0,NA\n"
    "2,,0.2,35,1,0.1,3000,2,0,1,0,0\n"
    "3,,1.2,45,0,0.7,2500,9,2,0,1,3\n"
    "4,,0.75,55,3,0.43,2499,0,0,0,0,1\n"
    "5,,0.3,65,0,0.6,NA,3,1,2,0,2\n"
    "6,,0,29,0,0,0,1,0,0,0,0\n"
    "7,,0.9999,30,0,5000,NA,12,0,3,0,0\n"
    "8,,0.31,40,0,0.4301,8000,7,0,1,0,NA\n"
    "9,,0.3,50,1,0.43,12000,2,0,0,2,5\n"
    "10,,2.5,60,98,1.5,1000,3,98,0,98,0\n"
    "11,,0.1,24,0,0.2,4000,5,0,0,0,1\n"
    "12,,0.1,34,0,0.2,6000,5,0,0,0,1\n"
)
ALL_NA = HEADER + "1,,0.5,25,0,0.3,NA,4,0,0,0,0\n2,,0.2,35,1,0.1,NA,2,0,1,0,1\n3,,1.2,61,0,0.7,NA,9,2,0,1,NA\n"
ONE_ROW = HEADER + "7,,0.4,41,1,0.2,5200,6,0,1,0,2\n"


def suite_run(names=None) -> Suite:
    s = Suite("b8_run")
    N_HEAD, N = 120, 200
    real = pick(ROOT / "data" / "cs-test.csv", N_HEAD, N)
    edge = pick(ROOT / "inputs" / "scenarios" / "edge_predict" / "cs-test.csv", N_HEAD, N)
    # one eval input per element of `plan`: [(file text, [(name, model, fix, medians text)])]
    plan = [
        [(real, [(f"data/cs-test[{N}] model A", MODEL_A, False, None),
                 (f"data/cs-test[{N}] model B", MODEL_B, True, MED_OK)])],
        [(edge, [(f"edge_predict[{N}] model A", MODEL_A, False, None),
                 (f"edge_predict[{N}] model B dup medians", MODEL_B, True, MED_DUP)])],
        # the hand-made files
        [(SMALL, [("small model A", MODEL_A, False, None),
                  ("small model 0 (no coefficient)", MODEL_0, False, None),
                  ("small model big", MODEL_BIG, False, None),
                  ("small medians given, flag off", MODEL_B, False, MED_OK),
                  ("small dup medians", MODEL_B, True, MED_DUP)]),
         (ALL_NA, [("all incomes NA (no median row)", MODEL_A, False, None),
                   ("all incomes NA, training medians", MODEL_A, True, MED_OK)]),
         (ONE_ROW, [("one row", MODEL_B, False, None),
                    ("one row, training medians", MODEL_A, True, MED_OK)])],
    ]
    for group in plan:
        lets, calls, cases = MK + RUNS, [], []
        bound: dict[str, str] = {}

        def bind(typ: str, term: str) -> str:
            if term not in bound:
                bound[term] = f"V{len(bound)}"
                bound[bound[term] + ":"] = f"let {bound[term]} : {typ} := {term}; "
            return bound[term]

        for k, (text, runs) in enumerate(group):
            first = True
            for name, model, fix, med in runs:
                if names is None or any(n in name for n in names):
                    tl, call, cs = scenario(name, text, model, fix, med, k, bind)
                    if first:
                        lets += tl
                        first = False
                    calls.append(call)
                    cases += cs
        if calls:
            lets += "".join(v for k_, v in bound.items() if k_.endswith(":") and k_[:-1] in bound.values())
            s.ints(lets, " ++ ".join(calls), cases, table=True)
    chain = ("real predict.run on temp files, locals captured at return; steps chained inside Lean on the Lean "
             "results of the earlier steps, each compared with the local of the real run")
    s.notes = {u: chain for _, u in STEP_LOCALS}
    s.notes["predict_run_05_features"] = chain + "; full = true and false both compared with Python"
    s.notes["run_py_py"] = ("real predict.run on temp files, frames captured at write_sas_csv; input_best32 = precomputed "
                            "Float64 columns of the real input_best32 keyed on the column name; model.json parsed; "
                            "medians = the frame pl.read_csv returns; full = true and false both compared")
    return s


if __name__ == "__main__":
    names = set(sys.argv[1:]) or None
    suite_run(names).write()
