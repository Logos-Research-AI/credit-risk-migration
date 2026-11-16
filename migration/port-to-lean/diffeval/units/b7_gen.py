"""Bundle B7 differential tests: feature_engineering.run (def:run) and its six step items
def:fe_run_01_clean .. def:fe_run_06_split.

  uv run python migration/diffeval/units/b7_gen.py [scenario ...]
      -> work/b7_run (.json + .inputs.json)
  (eval_decl each input of work/b7_run.inputs.json on def:zz_carrier / zz_carrier, save work/b7_run.out.txt)
  uv run python migration/diffeval/compare.py migration/diffeval/work/b7_run.json migration/diffeval/work/b7_run.out.txt
  uv run python migration/diffeval/receipts.py units b7

Python side: the REAL `feature_engineering.run` is called; nothing of `run` is copied here. It is
instrumented from outside:
  - `sas_compat.write_sas_csv` is replaced by a recorder: the frames Python hands to it, in call
    order, are the expected output tables of `run`;
  - a profile hook copies the local variables of `run` when it returns: they are the expected
    results of the step items (credit_raw_clean, income_medians, credit_cleaned, credit_imputed,
    credit_features, credit_train, credit_validation) and the imported frame `credit_raw`;
  - slice scenarios: a temporary data directory holds a `cs-training.csv` made of the header and
    chosen data lines of data/cs-training.csv, verbatim; the import is the real
    `sas_compat.proc_import_csv`; the split file is inputs/split_ids.csv restricted to the row ids
    of the slice (same order);
  - hand-made scenarios: `sas_compat.proc_import_csv` is replaced by a function returning the
    hand-made frame (the import is out of scope: the Lean takes the imported frame as a table;
    a NaN or a null row id cannot be produced through a CSV file); the split file is a real CSV.

Lean side, one eval input per scenario. The input table is built inside Lean from short integer
codes (a numeric cell is m * 32 + e + 1 for the decimal m * 10^-e, 0 for null; a text cell is 0
for null, 1 for "NA", n + 2 for the decimal text of n; other values are listed as bit patterns);
the first two cases of each scenario compare that table and the split table with what Python had.
`input_best32` is the test double IB: on a String column null / "NA" -> null and a digit string
-> its value; on a Float64 column the identity, except that a non-finite value becomes null. It
is not trusted: the first step case compares `fe_run_01_clean IB credit_raw` with Python's
`credit_raw_clean`, which holds the columns the real `sas_compat.input_best32` returned.
The steps are chained (each step reads what the previous Lean steps produced; every intermediate
is compared with Python's) and `run` is evaluated on the two tables for full = true / false and
export_train_medians = false / true. Python cannot choose `full` (thread pool): both values are
compared with the same Python result.
"""
from __future__ import annotations

# RETIRED 2026-11-16: this script is a record of the port before the update of 2026-11-16 and no longer
# runs: it calls fix_income_truncation, export_train_medians; see t2_gen.py, t3_gen.py, t4_gen.py, t5t9_gen.py, t6_gen.py.
# Its recorded outputs describe the port as it was then.
import sys as _sys

_sys.exit("RETIRED 2026-11-16: " + __file__ + " calls keywords the port no longer has; see the note at its top")


import contextlib
import io
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

from credit_risk import feature_engineering as fe  # noqa: E402
from credit_risk import sas_compat as sc  # noqa: E402

nan, inf = float("nan"), float("inf")
COLS = ["VAR1", "SeriousDlqin2yrs", "RevolvingUtilizationOfUnsecuredL", "age", "NumberOfTime30-59DaysPastDueNotW",
        "DebtRatio", "MonthlyIncome", "NumberOfOpenCreditLinesAndLoans", "NumberOfTimes90DaysLate",
        "NumberRealEstateLoansOrLines", "NumberOfTime60-89DaysPastDueNotW", "NumberOfDependents"]
STEPS = [("credit_raw_clean", "fe_run_01_clean"), ("income_medians", "fe_run_02_income_medians"),
         ("credit_cleaned", "fe_run_03_cleaned"), ("credit_imputed", "fe_run_04_imputed")]


# ---------------------------------------------------------------- the instrumented real run
def pyrun(split_text: str, *, csv_text: str | None = None, frame: pl.DataFrame | None = None,
          fix: bool = False, export: bool = False) -> dict:
    rec: dict = {"files": [], "locals": None}
    o_write, o_import = sc.write_sas_csv, sc.proc_import_csv

    def w_write(df, path, formats=None):
        rec["files"].append((Path(path).name, df))

    def prof(fr, event, arg):
        if event == "return" and fr.f_code is fe.run.__code__:
            rec["locals"] = dict(fr.f_locals)

    with tempfile.TemporaryDirectory() as d:
        ind, outd = Path(d) / "in", Path(d) / "out"
        ind.mkdir()
        if csv_text is not None:
            (ind / "cs-training.csv").write_text(csv_text)
        else:
            sc.proc_import_csv = lambda path, guessingrows=20: frame
        (ind / "split.csv").write_text(split_text)
        sc.write_sas_csv = w_write
        sys.setprofile(prof)
        try:
            with contextlib.redirect_stdout(io.StringIO()):
                fe.run(ind, outd, split_ids=ind / "split.csv", fix_income_truncation=fix, export_train_medians=export)
        finally:
            sys.setprofile(None)
            sc.write_sas_csv, sc.proc_import_csv = o_write, o_import
    return rec


def dgf(df) -> int:
    return cmp.digest(cmp.tokens(cmp.canon_frame(df)))


def dgt(name, df) -> int:
    return cmp.digest(cmp.tok_str(name) + cmp.tokens(cmp.canon_table(df)))


# ---------------------------------------------------------------- tables as short Lean terms
MK = (
    "let num := fun (c : Nat) => (Tabular.Cell.num (if c = 0 then none else some (Float.ofScientific ((c - 1) / 32) true ((c - 1) % 32))) : Tabular.Cell Float); "
    'let txt := fun (c : Nat) => (Tabular.Cell.str (if c = 0 then none else if c = 1 then some "NA" else some (toString (c - 2))) : Tabular.Cell Float); '
    "let mkT := fun (K : List (String × Bool)) (O : List (Nat × Float)) (D : Array Nat) => (((List.range (D.size / K.length)).map (fun (i : Nat) => "
    '(List.range K.length).map (fun (j : Nat) => let k := K.getD j ("", false); let ix := i * K.length + j; '
    "(k.1, (match O.lookup ix with | some x => Tabular.Cell.num (some x) | none => (if k.2 then txt (D.getD ix 0) else num (D.getD ix 0))))))) : Tabular.Table Float); "
    'let mkS := fun (L : List Nat) => ((L.map (fun (c : Nat) => [("row_id", (Tabular.Cell.num (if c = 0 then none else some (Float.ofNat (c - 1))) : Tabular.Cell Float))])) : Tabular.Table Float); '
    # the test double of sas_compat.input_best32 (checked by the fe_run_01_clean case)
    "let IB := fun (e : Pl.Expr Float) => ({ e with eval := fun (g : Option (List (List Nat))) (fr : Pl.Frame Float) => "
    '(match e.eval g fr with | .str v => Pl.Col.f64 (v.map (fun (o : Option String) => (match o with | some s => (if s == "NA" then none else s.toNat?.map Float.ofNat) | none => none))) '
    "| c => Pl.Col.f64 (c.asF64.map (fun (o : Option Float) => o.bind (fun (x : Float) => if x.isFinite then some x else none)))) } : Pl.Expr Float); "
)


def num_code(v: float) -> int | None:
    """m * 32 + e + 1 with float(f'{m}e-{e}') == v bit for bit; None when v needs a bit pattern."""
    if v != v or v in (inf, -inf) or v < 0 or (v == 0 and cmp.fbits(v) != 0):
        return None
    sign, digits, exp = Decimal(repr(v)).as_tuple()
    m = int("".join(map(str, digits)))
    if exp > 0:
        m, exp = m * 10 ** exp, 0
    e = -exp
    if e >= 32 or cmp.fbits(float(f"{m}e-{e}")) != cmp.fbits(v):
        return None
    return m * 32 + e + 1


def lean_table(name: str, df: pl.DataFrame) -> str:
    kinds, codes, over = [], [], []
    w = len(df.columns)
    for n in df.columns:
        assert df.schema[n] in (pl.Float64, pl.String), (n, df.schema[n])
        kinds.append(df.schema[n] == pl.String)
    for i, row in enumerate(df.iter_rows()):
        for j, v in enumerate(row):
            if v is None:
                codes.append(0)
            elif kinds[j]:
                if v == "NA":
                    codes.append(1)
                else:
                    assert v.isdigit() and str(int(v)) == v, v
                    codes.append(int(v) + 2)
            else:
                c = num_code(v)
                if c is None:
                    over.append((i * w + j, v))
                    codes.append(0)
                else:
                    codes.append(c)
    K = ", ".join(f"({lt.lean_str(n)}, {'true' if k else 'false'})" for n, k in zip(df.columns, kinds, strict=True))
    O = ", ".join(f"({ix}, {lt.lean_float(v)})" for ix, v in over)
    return f"let {name} := mkT [{K}] [{O}] #[{', '.join(map(str, codes))}]; "


def lean_split(name: str, ids: list) -> str:
    return f"let {name} := mkS [" + ", ".join("0" if v is None else str(int(v) + 1) for v in ids) + "]; "


BODY = (
    "let f0 := Pl.ofTable T; "
    "let s1 := fe_run_01_clean IB f0; "
    "let s2 := fe_run_02_income_medians s1; "
    "let s3 := fe_run_03_cleaned s1; "
    "let s4 := fe_run_04_imputed s3 s2; "
    "let s5 := fe_run_05_features true s4; "
    "let s5f := fe_run_05_features false s4; "
    "let s6 := fe_run_06_split S s5; "
    "let rr := fun (full ex : Bool) => (run full IB T S FIX ex).map (fun (p : String × Tabular.Table Float) => dg (tS p.1 ++ tA p.2)); "
    "[dg (tA T), dg (tA S), dg (tR s1), dg (tR s2), dg (tR s3), dg (tR s4), dg (tR s5), dg (tR s5f), dg (tR s6.1), dg (tR s6.2)] "
    "++ rr true false ++ rr false false ++ rr true true ++ rr false true"
)


def scenario(s: Suite, name: str, split_ids: list, *, csv_text: str | None = None, frame: pl.DataFrame | None = None,
             fix: bool = False, note: str = ""):
    split_text = "row_id\n" + "".join(("" if v is None else str(v)) + "\n" for v in split_ids)  # an empty line is a null id
    r0 = pyrun(split_text, csv_text=csv_text, frame=frame, fix=fix, export=False)
    r1 = pyrun(split_text, csv_text=csv_text, frame=frame, fix=fix, export=True)
    L = r0["locals"]
    raw = L["credit_raw"]
    assert raw.columns == COLS
    train_ids = L["train_ids"]
    assert train_ids.dtype == pl.Float64 and train_ids.to_list() == [None if v is None else float(v) for v in split_ids]
    split_df = pl.DataFrame({"row_id": train_ids})
    for k in ("credit_raw_clean", "income_medians", "credit_cleaned", "credit_imputed", "credit_features",
              "credit_train", "credit_validation"):
        assert dgf(L[k]) == dgf(r1["locals"][k])  # export_train_medians changes no step
    assert [f for f, _ in r0["files"]] == ["model_features_train.csv", "model_features_validation.csv"]
    assert [f for f, _ in r1["files"]] == ["income_medians.csv", "model_features_train.csv", "model_features_validation.csv"]
    lets = MK + lean_table("T", raw) + lean_split("S", split_ids) + f"let FIX := {'true' if fix else 'false'}; "
    c = lambda cid, prim, val: (f"{name}: {cid}", prim, val)  # noqa: E731
    cases = [c("input table cs_training (the imported frame)", "run", cmp.digest(cmp.tokens(cmp.canon_table(raw)))),
             c("input table split_ids", "run", cmp.digest(cmp.tokens(cmp.canon_table(split_df))))]
    cases += [c(k, u, dgf(L[k])) for k, u in STEPS]
    cases += [c("credit_features full=true", "fe_run_05_features", dgf(L["credit_features"])),
              c("credit_features full=false", "fe_run_05_features", dgf(L["credit_features"])),
              c("credit_train", "fe_run_06_split", dgf(L["credit_train"])),
              c("credit_validation", "fe_run_06_split", dgf(L["credit_validation"]))]
    for r, ex in ((r0, False), (r1, True)):
        for full in (True, False):
            cases += [c(f"{f} full={full} export_train_medians={ex} fix_income_truncation={fix}", "run", dgt(f, df))
                      for f, df in r["files"]]
    s.ints(lets, BODY, cases, table=True)
    cf = L["credit_features"]
    print(f"[{name}] rows={raw.height} MonthlyIncome={raw.schema['MonthlyIncome']} NumberOfDependents={raw.schema['NumberOfDependents']} "
          f"medians={L['income_medians'].sort('age_group').rows()} train={L['credit_train'].height} valid={L['credit_validation'].height} "
          f"null monthly_income={cf['monthly_income'].null_count()} nonfinite clpp={(~cf['credit_lines_per_person'].is_finite()).sum()} {note}")
    return L


# ---------------------------------------------------------------- slices of data/cs-training.csv
def slice_text(rows: list[int]) -> str:
    lines = (ROOT / "data" / "cs-training.csv").read_text().splitlines(keepends=True)
    return lines[0] + "".join(lines[r] for r in rows)  # data line r has row id r


def real_split(rows: list[int]) -> list[int]:
    ids = pl.read_csv(ROOT / "inputs" / "split_ids.csv", infer_schema=False).get_column("row_id").cast(pl.Int64).to_list()
    keep = set(rows)
    return [i for i in ids if i in keep]


def long_income_rows(k: int) -> list[int]:
    """The first k data lines whose MonthlyIncome has 6 or more characters (cut to 5 by the default import)."""
    raw = pl.read_csv(ROOT / "data" / "cs-training.csv", infer_schema=False)
    return raw.with_row_index("i", offset=1).filter(pl.col("MonthlyIncome").str.len_chars() >= 6).get_column("i").head(k).to_list()


# ---------------------------------------------------------------- hand-made frames
def hand(rows: list[tuple], mi_text: bool = True, nd_text: bool = True) -> pl.DataFrame:
    """rows: (VAR1, dlq, util, age, n30, debt, income, nopen, n90, nre, n60, deps) in file order."""
    cols = list(zip(*rows, strict=True))
    data = {}
    for n, v in zip(COLS, cols, strict=True):
        text = (n == "MonthlyIncome" and mi_text) or (n == "NumberOfDependents" and nd_text)
        data[n] = pl.Series(n, [None if x is None else (str(x) if text else float(x)) for x in v],
                            dtype=pl.String if text else pl.Float64)
    return pl.DataFrame(data)


#         VAR1  dlq  util      age   n30  debt      income  nopen n90  nre  n60  deps
EDGES = [
    (1,    1,   0.5,      25,   0,   0.2,      "NA",   4,    0,   1,   0,   1),     # the only row under 30: no income -> no median for group 1
    (2,    0,   0.0,      35,   1,   0.43,     3000,   2,    0,   0,   0,   0),     # utilization 0; debt_ratio 43 exactly; 2 credit lines
    (3,    0,   0.75,     38,   0,   0.6,      5000,   3,    0,   0,   2,   3),     # thresholds 75 / 60; 3 dependents
    (4,    1,   507.08,   39,   2,   5710,     "NA",   9,    1,   2,   0,   "NA"),  # large utilization; income imputed (even group: 0.5*(b-a)+a)
    (5,    0,   0.3,      None, 0,   0.3,      2499,   1,    0,   0,   0,   2),     # null age -> group 5 / category 5
    (6,    0,   nan,      nan,  0,   nan,      0,      0,    0,   0,   0,   0),     # NaN age, utilization, debt ratio; income 0
    (7,    None, None,    45,   None, None,    2500,   None, None, None, None, "NA"),  # nulls: all three late counts null
    (8,    0,   1.0,      45,   None, 0.2999,  7000,   5,    0,   1,   1,   5),     # one late count null
    (9,    1,   0.2999,   55,   3,   0.4301,   "NA",   30,   2,   0,   1,   0),     # fh reaches 0
    (None, 0,   0.1,      61,   0,   0.1,      9000,   7,    0,   0,   0,   1),     # null row id: in neither output
    (11,   0,   0.9,      64,   0,   0.05,     9000,   7,    0,   0,   0,   1),     # row id not in the split
    (12,   0,   0.9,      65,   0,   0.05,     9000,   7,    0,   0,   0,   2),     # tie in the median group
    (13,   0,   0.4,      24,   0,   0.1,      "NA",   6,    0,   0,   0,   0),     # second row of group 1 without income
    (14,   0,   1e-5,     50,   0,   1e-5,     11111,  6,    0,   0,   0,   0),     # one-row group
]
EDGES_SPLIT = [3, 1, 99, None, 4, 6, 7, 9, 12, 14, 3]
# NumberOfDependents numeric (the import typed it numeric): -1 gives a zero divisor (OUTSIDE the
# precondition of fe_run_05_features / run), NaN and inf go through the real input_best32 (-> null)
NUMERIC = [
    (1,    1,   0.5,      25,   0,   0.2,      4000,   4,    0,   1,   0,   -1),
    (2,    0,   0.2,      35,   1,   0.5,      3000,   0,    0,   0,   0,   -1),
    (3,    0,   0.9,      38,   0,   0.6,      nan,    3,    0,   0,   2,   nan),
    (4,    1,   2.0,      39,   2,   0.1,      inf,    9,    1,   2,   0,   inf),
    (5,    0,   0.3,      70,   0,   0.3,      None,   1,    0,   0,   0,   None),
    (6,    0,   0.3,      29,   0,   0.3,      2500.5, 1,    0,   0,   0,   0.5),
    (7,    0,   0.3,      30,   0,   0.3,      1e6,    1,    0,   0,   0,   -2),
]
ONE = [(7, 0, 0.0, 30, 0, 0.0, 0, 0, 0, 0, 0, 0)]
NOINC = [(1, 0, 0.1, 22, 0, 0.1, "NA", 1, 0, 0, 0, "NA"), (2, 1, 0.9, 62, 1, 0.9, "NA", 2, 1, 0, 0, 2)]


def suite_run(names=None) -> Suite:
    s = Suite("b7_run")
    want = lambda n: names is None or n in names  # noqa: E731
    if want("slice250"):
        # the first 20 data lines (they decide the import types, as in the full file), 228 further
        # lines, and the first two lines whose income has 6 digits (cut to 5 characters by the import)
        rows = list(range(1, 21)) + list(range(2551, 2779)) + long_income_rows(2)
        rows = sorted(set(rows))
        L = scenario(s, "slice250", real_split(rows), csv_text=slice_text(rows))
        cf = L["credit_features"]
        print("   age groups", sorted(set(cf["age_group"].to_list())), "age categories", sorted(set(cf["age_category"].to_list())),
              "income NA", cf["MonthlyIncome_missing"].sum(), "dependents NA", cf["Dependents_missing"].sum(),
              "util 0:", (cf["credit_utilization"] == 0).sum(), "util>200:", (cf["credit_utilization"] > 200).sum(),
              "risk flags", sorted(set(cf["total_risk_flags"].to_list())), "fh", sorted(set(cf["financial_health"].to_list())))
    if want("fixtrunc"):
        rows = sorted(set(list(range(1, 21)) + long_income_rows(4)))
        scenario(s, "fixtrunc_default", real_split(rows), csv_text=slice_text(rows), fix=False)
        scenario(s, "fixtrunc_fixed", real_split(rows), csv_text=slice_text(rows), fix=True)
    if want("edges"):
        scenario(s, "edges", EDGES_SPLIT, frame=hand(EDGES))
    if want("numeric"):
        scenario(s, "numeric_dependents", [1, 3, 5, 7], frame=hand(NUMERIC, mi_text=False, nd_text=False),
                 note="(rows 1, 2: num_dependents = -1, zero divisor, outside the precondition)")
    if want("one"):
        scenario(s, "one_row", [7], frame=hand(ONE))
        scenario(s, "one_row_unselected", [8], frame=hand(ONE, mi_text=False, nd_text=False))
    if want("noinc"):
        scenario(s, "no_income", [2], frame=hand(NOINC))
    chain = ("real feature_engineering.run; steps chained inside Lean on the Lean results of the earlier steps, each compared "
             "with the locals of the real run")
    ib = ("input_best32 = test double IB (String: NA / null -> null, digits -> value; Float64: identity, non-finite -> null), "
          "checked against the real input_best32 by the credit_raw_clean cases")
    s.notes = {
        "fe_run_01_clean": chain + "; " + ib,
        "fe_run_02_income_medians": chain,
        "fe_run_03_cleaned": chain,
        "fe_run_04_imputed": chain,
        "fe_run_05_features": chain + "; full = true and false both compared with the one Python result; scenario "
                              "numeric_dependents has num_dependents = -1 (zero divisor, outside the precondition): "
                              "Python gives inf / NaN there",
        "fe_run_06_split": chain,
        "run": "real run, frames captured at write_sas_csv (values as bits, names, order, file order); slices of "
               "data/cs-training.csv through the real proc_import_csv (guessingrows=20; fixtrunc_fixed: "
               "fix_income_truncation=True, guessingrows=None), hand-made frames by replacing proc_import_csv; "
               "full x export_train_medians = 4 runs per scenario; " + ib,
    }
    return s


if __name__ == "__main__":
    suite_run(set(sys.argv[1:]) or None).write()
