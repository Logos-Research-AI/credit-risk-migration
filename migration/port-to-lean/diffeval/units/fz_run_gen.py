"""Fuzz pass 2026-11-16 (prompts/fuzz-2026-11-16.md): def:run (feature_engineering.run,
credit_risk/feature_engineering.py:19-380) with def:run_precond, fuzzed by port-translator-8
(did not write it: T6).

  cd migration/port-to-lean && PYTHONPATH=../../port uv run --project ../../port python diffeval/units/fz_run_gen.py [calls] [seeds per call] [suite]
      -> diffeval/work/fz_run.{json,inputs.json,fuzz.json}
  eval_decl each input on def:zz_carrier_f (one input per call); python3 diffeval/fuzz_collect.py 8 fz_run;
  compare.py; fuzz_receipt.py fz_run

One case = one seed s. Both sides build from s (kit.hsh / gF / gI, every value drawn from a pool) a
cs-training frame of n = 1, 2, 3, 4, 5, 6, 8 or 12 rows with the twelve columns in file order, and a
list of split ids. Modes q = hsh(s, 99) % 16:
  0, 11-15  a valid frame
  1         a repeated row id (row ir takes the id of row 0)          -> duplicate_ids
  2         a missing row id on row ir                                -> bad_rows and duplicate_ids
  3-7       a valid frame with ONE cell (row ir, column jc) replaced by an edge: a Float64 column takes
            a value of HE (empty, 1e400 = inf, -1e400, -0.0, 0.5, -1, 2.5, 1e300, 5e-324, one ulp under
            1, 2, an odd integer above 2^52), a text column a text of SX ("abc", "-1", "1.5", 33
            digits, a non-ASCII text, "1e400", "Na", " . ", "2.5", "N A")
  8         column jc holds text: whole numbers 0..3 as text and one missing spelling
  9         names: one name in capitals / in lower case / replaced by "x", a column removed, a
            thirteenth column, every name in capitals                 -> columns_ok (or a run that completes)
  10        no known income (MonthlyIncome text: missing spellings and empty cells) -> known_incomes
A valid frame: ids 1..n; outcome 0 / 1; age, the two ratios and the counts from pools holding every
threshold of the steps and one ulp beside some (EA, EU, ED, EL, EC); MonthlyIncome and
NumberOfDependents each numeric or text (1 in 2): numeric from EI / EP (empty cells, 0, -0.0, 2500 and
its neighbours, a 13-digit income that BEST12. changes, 1e-5, ...), text from SI / SD (numbers with
blanks, signs, exponents, leading zeros, "NA", ".", empty) with one cell forced to a missing spelling
("NA", "na", ".", " ") so that the file keeps the column as text.
Split ids: each of 1..n+2 with probability 1/2; when none, the id 1, or (1 in 4) no id at all.

Python: the frame is written as cs-training.csv (empty cell for null, repr for a number, 1e400 for
inf) and the ids as a split file, and the REAL feature_engineering.run runs on the two files
(sas_compat.write_sas_csv replaced by a recorder; proc_import_csv wrapped to record what it returns).
A seed is used only if the imported frame IS the generated frame, names, dtypes and bits (the file
cannot hold: a numeric column with no value, which is imported as text; a text column whose cells are
all numbers): the others are counted as "the file cannot hold the frame". "Feature engineering
stopped" is the expected `none`. Also, once each: no file (`none`) and a file with a header and no
data row (`some []`).
Lean: `run full IB SB (some (Pl.toTable (mk s))) (split s)` with full = (s even); Python has no
`full`. One integer per seed: the digest of [digest of the input table, digest of the split table,
0 for `none` or the number of files and the digest of every (file name, table)]. The four columns
that hold a logarithm (log_monthly_income, log_num_credit_lines, log_total_late_payments,
age_income_interaction) are left out of that digest (the last bit of log is outside the model,
RULEBOOK 6); the last case of each call folds those columns of every seed without their low 20 bits
("covers" 0).
IB (input_best32) and SB (sas_best12) are lookup tables made from the real sas_compat functions over
every text and number the pools can hold (raw and stripped of blanks, and the BEST12. texts); each
run's texts and numbers are asserted to be in them.
Precondition (def:run_precond), rendered in Python (`precond`):
  table clauses (same shape in every row, distinct names): hold by construction (Pl.toTable of a frame);
  def:fe_run_00_input_check_precond: every column Float64 or String, ASCII names, names distinct after
    the case-blind renaming, ASCII text in MonthlyIncome / NumberOfDependents (the non-ASCII edge text
    is rejected by this clause), input_best32 Float64 of the frame's height (true of IB);
  when the check does not stop (`stopped` taken from the Python run): the step preconditions reduce,
    on a frame the check accepted, to: the ten computing columns are Float64 (a text column there
    always holds a cell that is no number, so the check stops: asserted), num_dependents + 1 != 0
    (asserted on the dependents the check lets through), and split_ids has at least one row (a run
    that completes with no split id is sent as "rejected").
"""
from __future__ import annotations

import contextlib
import io
import json
import sys
import tempfile
from pathlib import Path

import polars as pl

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import compare as cmp  # noqa: E402
import kit  # noqa: E402
import leanterm as lt  # noqa: E402
import suite as suite_mod  # noqa: E402

suite_mod.CARRIERS["identity"] = ("def:zz_carrier_f", "zz_carrier_f")
from suite import Suite  # noqa: E402

from credit_risk import feature_engineering as fe  # noqa: E402
from credit_risk import sas_compat as sc  # noqa: E402

UNIT = "run"
inf = float("inf")
N0 = ["VAR1", "SeriousDlqin2yrs", "RevolvingUtilizationOfUnsecuredL", "age", "NumberOfTime30-59DaysPastDueNotW",
      "DebtRatio", "MonthlyIncome", "NumberOfOpenCreditLinesAndLoans", "NumberOfTimes90DaysLate",
      "NumberRealEstateLoansOrLines", "NumberOfTime60-89DaysPastDueNotW", "NumberOfDependents"]
FILES = ["income_medians.csv", "model_features_train.csv", "model_features_validation.csv"]
LOGS = ["log_monthly_income", "log_num_credit_lines", "log_total_late_payments", "age_income_interaction"]
ROWS = [1, 2, 3, 4, 5, 6, 8, 12]
EO = [0.0, 1.0]
EU = [0.0, 0.3, 0.29999999999999993, 0.5, 0.75, 0.7500000000000001, 1.0, 1.0000000000000002, 2.0, 2.5, 1e-300]
EA = [29.0, 30.0, 39.0, 40.0, 49.0, 50.0, 59.0, 60.0, 24.0, 25.0, 34.0, 35.0, 64.0, 65.0, 0.0, 21.5,
      29.999999999999996, 1e300, -3.0]
EL = [0.0, 0.0, 0.0, 0.0, 1.0, 2.0, 3.0, 98.0]
ED = [0.0, 0.3, 0.43, 0.6, 0.42999999999999994, 0.6000000000000001, 5.0, 5.000000000000001, 0.25, 329664.0]
EC = [0.0, 1.0, 2.0, 3.0, 4.0, 10.0]
EI = [None, None, 0.0, 2500.0, 2499.99, 2500.01, 5000.0, 1234567890123.0, 0.1, 1e-5, 12345.678901234, 1.0, -0.0, 7000.0]
EP = [None, 0.0, 0.0, 1.0, 2.0, 3.0, 4.0, 20.0]
HE = [None, inf, -inf, -0.0, 0.5, -1.0, 2.5, 1e300, 5e-324, 0.9999999999999999, 2.0, 4503599627370497.0]
PS = [EO, EU, EA, EL, ED, EI, EC, EL, EC, EL, EP]     # the pool of column j is PS[j - 1]
SN = ["NA", "na", ".", " "]
SI = [None, "NA", ".", "5000", "07", "7.0", "1e3", "+7", " 3 ", "0", "2499.99", "1234567890123", "1E2", "-0"]
SD = [None, "NA", "0", "1", "2", "3", " 2 ", "2.0", "+1", "04"]
SX = ["abc", "-1", "1.5", "1" * 33, "ñ", "1e400", "Na", " . ", "2.5", "N A"]


def h(s, i, m):
    return kit.hsh(s, i) % m


def pk(L, seed, n, pn):
    return [None if o is None else L[o] for o in kit.gI(seed, n, pn, len(L), 0)]


def put(v, i, x):
    if i < len(v):
        v[i] = x
    return v


def mk(s: int) -> pl.DataFrame:
    q, n = h(s, 99, 16), ROWS[h(s, 98, 8)]
    jc, ir, k = h(s, 301, 12), h(s, 302, n), kit.hsh(s, 303)

    def na(i):
        return SN[h(s, i, 4)]

    def col(j):
        if j == 0:
            v = [float(i + 1) for i in range(n)]
            return pl.Series(put(v, ir, 1.0) if q == 1 else put(v, ir, None) if q == 2 else v, dtype=pl.Float64)
        if j == 6 and q == 10:
            return pl.Series(pk(SN, s * 16 + 6, n, 30), dtype=pl.String)
        if j in (6, 11) and h(s, 200 + j, 2) == 0:
            return pl.Series(put(pk(SI if j == 6 else SD, s * 16 + j, n, 0), h(s, 310 + j, n), na(320 + j)), dtype=pl.String)
        if q == 8 and j == jc:
            return pl.Series(put([str(o) for o in kit.gI(s * 16 + j, n, 0, 4, 0)], ir, na(306)), dtype=pl.String)
        return pl.Series(kit.gF(s * 16 + j, n, 100, 0, PS[j - 1]), dtype=pl.Float64)

    def ed(c: pl.Series) -> pl.Series:
        v = c.to_list()
        return pl.Series(put(v, ir, HE[k % len(HE)] if c.dtype == pl.Float64 else SX[k % len(SX)]), dtype=c.dtype)

    cols = [(N0[j], ed(col(j)) if 3 <= q <= 7 and j == jc else col(j)) for j in range(12)]
    nv = h(s, 304, 6)
    if q == 9:
        if nv == 3:
            del cols[jc]
        elif nv == 4:
            cols.append(("extra", col(1)))
        else:
            cols = [((nm.upper() if nv == 5 or (j == jc and nv == 0) else nm.lower() if j == jc and nv == 1
                      else "x" if j == jc and nv == 2 else nm), c) for j, (nm, c) in enumerate(cols)]
    return pl.DataFrame([c.alias(nm) for nm, c in cols])


def split(s: int) -> list[float]:
    n = ROWS[h(s, 98, 8)]
    v = [float(i + 1) for i in range(n + 2) if h(s, 400 + i, 2) == 0]
    return v if v else ([] if h(s, 399, 4) == 0 else [1.0])


# ---------------------------------------------------------------- Lean
def fl(x: float) -> str:
    if x == inf:
        return "(1/0)"
    if x == -inf:
        return "(-1/0)"
    if x == 5e-324:
        return "Float.ofBits 1"
    r = repr(x)
    if r.endswith(".0") and not r.startswith("-"):
        r = r[:-2]
    return f"({r})" if r.startswith("-") else r


def fls(v) -> str:
    """a pool as List (Option Float): leading nulls, then `P [...]`"""
    k = 0
    while v[k] is None:
        k += 1
    assert None not in v[k:]
    return "none :: " * k + "P [" + ", ".join(fl(x) for x in v[k:]) + "]"


def sls(v) -> str:
    k = 1 if v[0] is None else 0
    return "none :: " * k + "[" + ", ".join(lt.lean_str(x) for x in v[k:]) + "].map some"


def tables() -> tuple[str, set[str], dict[int, str]]:
    nums = [x for x in EI + EP + HE if x is not None]
    b12: dict[int, str] = {}
    order: list[float] = []
    for x in nums:
        if cmp.fbits(x) not in b12:
            b12[cmp.fbits(x)] = sc.sas_best12(x)
            order.append(x)
    raw = {x for x in SN + SI + SD + SX + ["0", "1", "2", "3"] if x is not None}
    keys = sorted(raw | {x.strip(" ") for x in raw} | set(b12.values()))
    vals = pl.DataFrame({"t": keys}, schema={"t": pl.String}).select(sc.input_best32(pl.col("t"))).to_series().to_list()
    T = "[" + ", ".join(f"({lt.lean_str(t)}, {fl(v)})" for t, v in zip(keys, vals, strict=True) if v is not None) + "]"
    text = (
        f"let BF : List Float := [{', '.join(fl(x) for x in order)}]; "
        f"let BT : List String := [{', '.join(lt.lean_str(b12[cmp.fbits(x)]) for x in order)}]; "
        'let SB := fun (q : Option Float) => (match q with | some x => ((BF.zip BT).find? (fun (p : Float × String) => p.1.toBits == x.toBits)).elim "?" (fun (p : Float × String) => p.2) | none => "." : String); '
        f"let T : List (String × Float) := {T}; "
        "let IB := fun (e : Pl.Expr Float) => ({ e with eval := fun (g : Option (List (List Nat))) (fr : Pl.Frame Float) => "
        "(match e.eval g fr with | .str v => Pl.Col.f64 (v.map (fun (q : Option String) => q.bind (fun (s : String) => T.lookup s))) | c => c) } : Pl.Expr Float); "
    )
    return text, set(keys), b12


TAB, KEYS, B12 = tables()
# the part of kit.KIT this suite uses (digest, string, cell and table tokens), to keep the input short
MINI = "".join("let " + x + "; " for x in kit.KIT.strip().removeprefix("let ").removesuffix(";").split("; let ")
               if x.split(" ")[0] in ("mx", "dg", "tS", "tX", "tA"))
assert MINI.count("let ") == 6, MINI

LETS = (
    "let P := fun (v : List Float) => v.map some; "
    f"let N0 := [{', '.join(lt.lean_str(x) for x in N0)}]; "
    f"let EL := {fls(EL)}; let EC := {fls(EC)}; "
    f"let PS : List (List (Option Float)) := [{fls(EO)}, {fls(EU)}, {fls(EA)}, EL, {fls(ED)}, {fls(EI)}, EC, EL, EC, EL, {fls(EP)}]; "
    f"let HE : List (Option Float) := {fls(HE)}; "
    f"let SN : List (Option String) := {sls(SN)}; let SI : List (Option String) := {sls(SI)}; "
    f"let SD : List (Option String) := {sls(SD)}; let SX : List (Option String) := {sls(SX)}; "
    f"let LOGS := [{', '.join(lt.lean_str(x) for x in LOGS)}]; "
    "let h := fun (s i m : Nat) => ((hsh s i) % m.toUInt64).toNat; "
    "let pk := fun (L : List (Option String)) (s n : Nat) (pn : UInt64) => (gI s n pn L.length.toUInt64 0).map "
    "(fun (o : Option Int) => (match o with | some i => L.getD i.toNat none | none => none : Option String)); "
    "let nn := fun (s : Nat) => [1, 2, 3, 4, 5, 6, 8, 12].getD (h s 98 8) 1; "
    "let mk := fun (s : Nat) => let q := h s 99 16; let n := nn s; let jc := h s 301 12; let ir := h s 302 n; let k := (hsh s 303).toNat; "
    "let na := fun (i : Nat) => SN.getD (h s i 4) none; "
    "let col := fun (j : Nat) => ("
    "if j == 0 then (let v := (List.range n).map (fun (i : Nat) => some (Float.ofNat (i + 1))); "
    "Pl.Col.f64 (if q == 1 then v.set ir (some 1.0) else if q == 2 then v.set ir none else v)) "
    "else if j == 6 && q == 10 then Pl.Col.str (pk SN (s * 16 + 6) n 30) "
    "else if (j == 6 || j == 11) && h s (200 + j) 2 == 0 then Pl.Col.str ((pk (if j == 6 then SI else SD) (s * 16 + j) n 0).set (h s (310 + j) n) (na (320 + j))) "
    "else if q == 8 && j == jc then Pl.Col.str (((gI (s * 16 + j) n 0 4 0).map (fun (o : Option Int) => o.map toString)).set ir (na 306)) "
    "else Pl.Col.f64 (gF (s * 16 + j) n 100 0 (PS.getD (j - 1) [])) : Pl.Col Float); "
    "let ed := fun (c : Pl.Col Float) => (match c with | .f64 v => Pl.Col.f64 (v.set ir (HE.getD (k % HE.length) none)) "
    "| .str v => Pl.Col.str (v.set ir (SX.getD (k % SX.length) none)) | c => c : Pl.Col Float); "
    "let fr : Pl.Frame Float := (List.range 12).map (fun (j : Nat) => (N0.getD j \"\", if 3 ≤ q && q ≤ 7 && j == jc then ed (col j) else col j)); "
    "let nv := h s 304 6; "
    "(if q != 9 then fr else if nv == 3 then fr.eraseIdx jc else if nv == 4 then fr ++ [(\"extra\", col 1)] else "
    "(List.range 12).map (fun (j : Nat) => let p := fr.getD j (\"\", Pl.Col.f64 []); "
    "((if nv == 5 || (j == jc && nv == 0) then p.1.toUpper else if j == jc && nv == 1 then p.1.toLower else if j == jc && nv == 2 then \"x\" else p.1), p.2)) : Pl.Frame Float); "
    "let sp := fun (s : Nat) => (let v := (List.range (nn s + 2)).filter (fun (i : Nat) => h s (400 + i) 2 == 0); "
    "(if v.isEmpty then (if h s 399 4 == 0 then [] else [0]) else v).map (fun (i : Nat) => [(\"row_id\", Tabular.Cell.num (some (Float.ofNat (i + 1))))]) : Tabular.Table Float); "
    "let u := fun (i : Int) => i.toNat.toUInt64; "
    "let DL := fun (t : Tabular.Table Float) => (t.map (fun (r : Tabular.Row Float) => r.filter (fun (p : String × Tabular.Cell Float) => !(LOGS.contains p.1))) : Tabular.Table Float); "
    "let LG := fun (t : Tabular.Table Float) => t.flatMap (fun (r : Tabular.Row Float) => LOGS.map (fun (c : String) => "
    "(match r.lookup c with | some (.num (some x)) => if x.isNaN then 1 else ((x.toBits >>> 20).toNat : Int) + 2 | some (.num none) => 0 | _ => -1 : Int))); "
    "let W := fun (t : List Int) => t.foldl (fun (a x : Int) => (a * 1099511628211 + x + 7) % 18446744073709551616) 14695981039346656037; "
    "let rn := fun (t : Option (Tabular.Table Float)) (s : Tabular.Table Float) (full : Bool) => (match run (α := Float) full IB SB t s with "
    "| none => ([0], []) | some fs => (fs.length.toUInt64 :: fs.map (fun (p : String × Tabular.Table Float) => u (dg (tS p.1 ++ tA (DL p.2)))), fs.flatMap (fun (p : String × Tabular.Table Float) => LG p.2)) : List UInt64 × List Int); "
    "let one := fun (s : Nat) => let t := Pl.toTable (mk s); let r := rn (some t) (sp s) (s % 2 == 0); (dg ([u (dg (tA t)), u (dg (tA (sp s)))] ++ r.1), r.2); "
)


# ---------------------------------------------------------------- Python
def csv_text(df: pl.DataFrame) -> str:
    def cell(x):
        if x is None:
            return ""
        if isinstance(x, str):
            assert "," not in x and '"' not in x and "\n" not in x
            return x
        return "1e400" if x == inf else "-1e400" if x == -inf else repr(x)
    return ",".join(df.columns) + "\n" + "".join(",".join(cell(x) for x in r) + "\n" for r in df.rows())


def bits(df: pl.DataFrame):
    return [(n, str(df.schema[n]), [x if x is None or isinstance(x, str) else cmp.fbits(x) for x in df.get_column(n).to_list()])
            for n in df.columns]


def pyrun(csv: str | None, split_text: str, want: pl.DataFrame | None) -> dict:
    rec: dict = {"files": [], "imported": None, "held": True, "raised": None, "stop": False}
    o_write, o_import = sc.write_sas_csv, sc.proc_import_csv

    def w_import(path, guessingrows=20):
        df = o_import(path, guessingrows=guessingrows)
        rec["imported"] = df
        if want is not None and bits(df) != bits(want):
            rec["held"] = False
            raise KeyboardInterrupt  # not caught by the run: leave it at once
        return df

    with tempfile.TemporaryDirectory() as d:
        ind, outd = Path(d) / "in", Path(d) / "out"
        ind.mkdir()
        outd.mkdir()
        if csv is not None:
            (ind / "cs-training.csv").write_text(csv, encoding="utf-8")
        (ind / "split.csv").write_text(split_text)
        sc.proc_import_csv = w_import
        sc.write_sas_csv = lambda df, path, formats=None: rec["files"].append((Path(path).name, df))
        try:
            with contextlib.redirect_stdout(io.StringIO()):
                fe.run(ind, outd, split_ids=ind / "split.csv")
        except KeyboardInterrupt:
            if rec["held"]:
                raise
        except ValueError as e:
            if str(e) == "Feature engineering stopped. Nothing is exported.":
                rec["stop"] = True
                assert rec["files"] == [] and list(outd.iterdir()) == []
            else:
                rec["raised"] = f"{type(e).__name__}: {str(e)[:150]}"
        except Exception as e:  # noqa: BLE001
            rec["raised"] = f"{type(e).__name__}: {str(e)[:150]}"
        finally:
            sc.write_sas_csv, sc.proc_import_csv = o_write, o_import
    if rec["held"] and rec["raised"] is None and not rec["stop"]:
        assert [f for f, _ in rec["files"]] == FILES
    return rec


def check_precond(df: pl.DataFrame) -> bool:
    names = df.columns
    if len(set(names)) != len(names) or not all(t in (pl.Float64, pl.String) for t in df.dtypes):
        return False
    if not all(nm.isascii() for nm in names):
        return False
    by_upper = {c.upper(): c for c in N0}
    ren = [by_upper.get(nm.upper(), nm) for nm in names]
    if len(set(ren)) != len(ren):
        return False
    for nm, r in zip(names, ren, strict=True):
        if r in ("MonthlyIncome", "NumberOfDependents") and df.schema[nm] == pl.String:
            if not all(v.isascii() for v in df.get_column(nm).to_list() if v is not None):
                return False
    return True


def precond(df: pl.DataFrame, stopped: bool, sp: list[float]) -> bool:
    if not check_precond(df):
        return False
    if stopped:
        return True
    ren = {c.upper(): c for c in N0}
    ten = [n for n in df.columns if ren[n.upper()] not in ("MonthlyIncome", "NumberOfDependents")]
    assert all(df.schema[n] == pl.Float64 for n in ten), "a text column among the ten and the check did not stop"
    return len(sp) > 0


def texts_used(df: pl.DataFrame) -> set[str]:
    out: set[str] = set()
    for n in df.columns:
        vals = [v for v in df.get_column(n).to_list() if v is not None]
        if df.schema[n] == pl.String:
            out |= set(vals) | {v.strip(" ") for v in vals}
        elif n.upper() in ("MONTHLYINCOME", "NUMBEROFDEPENDENTS"):
            for v in vals:
                assert cmp.fbits(v) in B12, v
    return out


def dgt(name: str, df: pl.DataFrame) -> int:
    return cmp.digest(cmp.tok_str(name) + cmp.tokens(cmp.canon_table(df.drop([c for c in LOGS if c in df.columns]))))


def logtokens(df: pl.DataFrame) -> list[int]:
    out = []
    for r in df.iter_rows(named=True):
        for c in LOGS:
            if c not in r:
                out.append(-1)
            else:
                x = r[c]
                out.append(0 if x is None else 1 if x != x else (cmp.fbits(x) >> 20) + 2)
    return out


def wfold(t) -> int:
    a = 14695981039346656037
    for x in t:
        a = (a * 1099511628211 + x + 7) % 18446744073709551616
    return a


def table_digest(df: pl.DataFrame) -> int:
    return cmp.digest(cmp.tokens(cmp.canon_table(df)))


def main() -> None:
    calls = int(sys.argv[1]) if len(sys.argv) > 1 else 6
    per = int(sys.argv[2]) if len(sys.argv) > 2 else 450
    name = sys.argv[3] if len(sys.argv) > 3 else "fz_run"
    base0 = 80000
    s = Suite(name, generator="port-to-lean/diffeval/units/fz_run_gen.py")
    st = {"generated": 0, "kept": 0, "rejected_sent": 0, "not_held": 0, "dropped": 0, "raises_inside": [], "stop": 0,
          "completed": 0, "modes": {}, "kept_modes": {}, "stops_by": {}, "rej_why": {}}
    for c in range(calls):
        base = base0 + c * per
        bad, cases, logs = [], [], []
        for seed in range(base, base + per):
            st["generated"] += 1
            df, sp = mk(seed), split(seed)
            q = h(seed, 99, 16)
            r = pyrun(csv_text(df), "row_id\n" + "".join(f"{int(i)}\n" for i in sp), df)
            if not r["held"]:
                st["not_held"] += 1
                bad.append(seed)
                continue
            ok = precond(df, r["stop"], sp) if r["raised"] is None else check_precond(df) and len(sp) > 0
            if r["raised"] is not None:
                if ok:
                    st["raises_inside"].append((seed, r["raised"]))
                else:
                    st["dropped"] += 1
                bad.append(seed)
                continue
            assert texts_used(df) <= KEYS, texts_used(df) - KEYS
            sp_df = pl.DataFrame({"row_id": sp}, schema={"row_id": pl.Float64})
            res = [0] if r["stop"] else [len(r["files"])] + [dgt(f, x) for f, x in r["files"]]
            if ok:
                for _, x in r["files"]:
                    logs += logtokens(x)
            st["kept" if ok else "rejected_sent"] += 1
            st["stop" if r["stop"] else "completed"] += 1
            st["modes"][q] = st["modes"].get(q, 0) + 1
            if not ok:
                why = "non-ASCII text in MonthlyIncome / NumberOfDependents" if not check_precond(df) else "no split id"
                st["rej_why"][why] = st["rej_why"].get(why, 0) + 1
            what = "none" if r["stop"] else f"{r['files'][1][1].height} train / {r['files'][2][1].height} validation rows"
            cases.append((f"seed {seed} (mode {q}, {df.height} rows): {what}", UNIT,
                          cmp.digest([table_digest(df), table_digest(sp_df)] + res), {"fz": "kept" if ok else "rejected"},
                          ok))
        off = [b - base for b in bad]
        rej = [int(cs[0].split()[1]) - base for cs in cases if not cs[4]]
        lets = (TAB + LETS + f"let BAD : List Nat := {off}; let REJ : List Nat := {rej}; "
                f"let R := (((List.range {per}).filter (fun (i : Nat) => !(BAD.contains i))).map (fun (i : Nat) => (i, one ({base} + i)))); ")
        body = "R.map (fun (p : Nat × Int × List Int) => p.2.1) ++ [W ((R.filter (fun (p : Nat × Int × List Int) => !(REJ.contains p.1))).flatMap (fun (p : Nat × Int × List Int) => p.2.2))]"
        allc = [cs[:4] for cs in cases] + [(f"seeds {base}..{base + per - 1}: the four log columns of the kept runs without their low 20 bits",
                                             UNIT, wfold(logs), {"fz": "kept", "covers": 0})]
        s.ints(MINI + lets, body, allc, gen=True, use_kit=False)
    # no file; a file with a header and no data row
    absent = pyrun(None, "row_id\n1\n", None)
    header = pyrun(",".join(N0) + "\n", "row_id\n1\n", None)
    assert absent["stop"] and absent["imported"] is None and header["stop"] and header["imported"].height == 0
    one = (lambda t: "(dg (rn " + t + " (sp 0) true).1 : Int)")
    s.ints(MINI + TAB + LETS, "[" + one("none") + ", " + one("(some [])") + "]",
           [("no file: none", UNIT, cmp.digest([0]), {"fz": "kept"}),
            ("a header and no data row: none", UNIT, cmp.digest([0]), {"fz": "kept"})], gen=True, use_kit=False)
    st["generated"] += 2
    st["kept"] += 2
    s.write()
    note = (f"one case = one seed: a cs-training frame of 1-12 rows written as a file and a split file, the real run; modes "
            f"(0, 11-15 valid; 1 repeated id; 2 missing id; 3-7 one edge cell; 8 a text column; 9 names; 10 no known income) sent: "
            f"{dict(sorted(st['modes'].items()))}; runs that complete: {st['completed']}, stop: {st['stop']}; not used: {st['not_held']} "
            f"frames the file cannot hold; rejected by the precondition and sent: {st['rej_why']}; rejected and Python raises: "
            f"{st['dropped']}; full = (seed even); the four log columns compared without their low 20 bits; plus no file and a "
            f"header-only file")
    (HERE.parent / "work" / f"{name}.fuzz.json").write_text(json.dumps({
        "fuzzer": "port-translator-8", "generator": "diffeval/units/fz_run_gen.py",
        "units": {UNIT: {"seeds": f"{base0}..{base0 + calls * per - 1}, no file, header only", "generated": st["generated"],
                         "kept": st["kept"], "python_raises_inside_precondition": st["raises_inside"], "note": note}}}, indent=1))
    print(st)
    print([len(i["text"]) for i in s.inputs])


if __name__ == "__main__":
    main()
