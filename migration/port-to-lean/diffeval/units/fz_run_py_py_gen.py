"""Fuzz pass 2026-11-16 (prompts/fuzz-2026-11-16.md), by port-translator-3: the composition
def:run_py_py (predict.run, predict.py:17-491), which port-translator-3 did not write.

  cd migration/port-to-lean && PYTHONPATH=../../port uv run --project ../../port python diffeval/units/fz_run_py_py_gen.py
      -> diffeval/work/fz_run_py_py.json, .inputs.json, .fuzz.json
  eval_decl each input on def:zz_carrier_p; python3 diffeval/fuzz_collect.py 3 fz_run_py_py; compare.py; fuzz_receipt.py

One seed gives, inside Lean (kit.GEN `hsh`, `gF`) and mirrored here:
  cs_test   none (file absent, 1 seed in 25) or (header with kinds, rows): 0..8 rows; the twelve
            columns in the order of the real file, or a variant (AGE upper, all upper, all lower, one
            column missing, one extra, a second age column named AGE in place of DebtRatio, reversed
            order). A cell is a text drawn from the pool of its column: a clean pool, or with a
            probability set by the seed (0, 3, 15, 40 %) a dirty one. The kind of a column is what
            proc_import_csv decides (numeric iff it has a non-empty cell and every non-empty cell is
            a number), a header-only file gets the kinds of the made-up copy (:71-75).
  medians   none (file absent), the table with no row (header-only file), or 1..6 rows of
            (age_group, median_income, overall_median_income), groups missing / repeated / 6,
            null medians, names upper-cased, an extra column `age`, reversed column order
  model     intercept and 0..12 coefficients on columns of test_features (1 seed in 25 adds a name
            that is no column), model_coefficients.csv absent in 1 seed of 25
  full      seed even
Python side: the files are WRITTEN (cs-test.csv, the medians file, model.json,
model_coefficients.csv) and the REAL predict.run is run on them; sas_compat.write_sas_csv is a
recorder (the frames in call order are the expected files); a tracer copies `test_raw` at line 82.
The generator asserts, on every seed, that the import of the written cs-test.csv is the frame the
Lean generator builds, and the same for the medians table.
Explicit parameters: input_best32 on the Lean side is "the number the text states, else missing"
(a small parser of plain decimals) with a table IBX of the texts where the real function differs;
asserted here against the real sas_compat.input_best32 on every text a String column or a BEST12.
rendering can hold. sas_best12 is a table of the real function on the numeric values of the
MonthlyIncome and NumberOfDependents pools.

Precondition def:run_py_py_precond, rendered in Python from the generated inputs and the frames of
the real run (locals of predict.run when it returns or raises):
  income_medians none / model_coefficients absent       true
  00  header names distinct, rows of the header's shape, ASCII names (always true here);
      input_best32 Float64 on text columns (true of the double)
  the check stops (ValueError "Test set scoring stopped" after line 82)   nothing more
  01  MonthlyIncome, NumberOfDependents String or Float64                 dtypes of test_raw
  02  medians table has a row; one shape; distinct ASCII names           the mirrored table
  03/04/05  age, the three late counts, the two ratios, the open-lines count Float64 in test_raw;
      medians (after the case-blind rename of :213-222, the port's own lines executed) has
      Float64 age_group, median_income, overall_median_income; no `_right` name taken;
      no NumberOfDependents value x with x + 1 = 0
  06  coefficient names distinct, each a Float64 / Int64 column of the features (list FT, checked
      against test_features of a real run)
  07, 08  follow from the above (age_name is "age" or a spelling of it that is no kept column)
"""
from __future__ import annotations

import contextlib
import io
import json
import re
import shutil
import sys
import tempfile
import textwrap
from pathlib import Path

import polars as pl

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))

import b4_gen as b4  # noqa: E402
import compare as cmp  # noqa: E402
import kit  # noqa: E402
import leanterm as lt  # noqa: E402
from suite import Suite  # noqa: E402

from credit_risk import predict as pr  # noqa: E402
from credit_risk import sas_compat as sc  # noqa: E402

ITEM, DECL = "def:zz_carrier_p", "zz_carrier_p"
U = "run_py_py"
SEED0, CH, NCH = 30000, 25, 104
FILES = ["kaggle_submission.csv", "test_predictions.csv"]
SRC = Path(pr.__file__).read_text().splitlines()
assert SRC[81].startswith("    EXPECTED = (")
assert SRC[210].strip().startswith("train_income_medians = sas_compat.proc_import_csv(income_medians)") and SRC[221].strip() == ")", (SRC[210], SRC[221])
MED_SLICE = compile(textwrap.dedent("\n".join(SRC[210:222])), "predict.py:211-222", "exec")

N0 = ["VAR1", "SeriousDlqin2yrs", "RevolvingUtilizationOfUnsecuredL", "age", "NumberOfTime30-59DaysPastDueNotW",
      "DebtRatio", "MonthlyIncome", "NumberOfOpenCreditLinesAndLoans", "NumberOfTimes90DaysLate",
      "NumberRealEstateLoansOrLines", "NumberOfTime60-89DaysPastDueNotW", "NumberOfDependents"]
AGE = ["21", "29", "30", "39.5", "40", "50", "59", "60", "65", "101", "0", "24.5"]
CNT = ["0", "0", "0", "1", "2", "3", "98"]
CNT_D = ["-1", "1.5", "", "NA"]
PC = [
    ["1"],                                                                       # 0 VAR1 (clean: the row number)
    ["", "NA", "0", "1", "NA", "0"],                                             # 1 SeriousDlqin2yrs
    ["0", "0.1", "0.2999", "0.3", "0.5", "0.75", "0.7500001", "1", "1.2", "50708"],  # 2 utilization
    AGE,                                                                         # 3 age
    CNT,                                                                         # 4 late 30-59
    ["0", "0.2", "0.3", "0.43", "0.4300001", "0.6", "0.61", "5", "3000.5"],      # 5 DebtRatio
    ["", "NA", "0", "2500", "5400", "1234567890123", "0.5", "12000", "2499.99", "na", "."],  # 6 MonthlyIncome
    ["0", "1", "2", "3", "8", "20"],                                             # 7 open credit lines
    CNT,                                                                         # 8 late 90
    ["0", "1", "2", "6"],                                                        # 9 real estate
    CNT,                                                                         # 10 late 60-89
    ["", "NA", "0", "1", "2", "3", "5", "NA"],                                   # 11 NumberOfDependents
    ["1", "2", "x"],                                                             # 12 extra
    AGE,                                                                         # 13 a second age column "AGE"
]
PD = [
    ["1", "", "x", "2"], ["2", "x", "0.5", "-1"], ["", "NA"], ["", "NA", "abc", "-5"], CNT_D, ["", "x"],
    ["-1", "abc", "-0.5"], CNT_D, CNT_D, ["", "NA"], CNT_D, ["-1", "2.5", "x"], ["", "y"], ["", "NA"],
]
PDS = [0, 0, 0, 0, 0, 0, 3, 3, 15, 40]
NR = [0, 1, 1, 2, 2, 3, 3, 4, 5, 8]
GS = [[1, 2, 3, 4, 5], [5, 4, 3, 2, 1], [1, 2, 3], [2, 4, 5], [1, 1, 2, 3, 4, 5], [1, 2, 3, 4, 5, 6], [3], [1, 2, 3, 4, 5]]
MP = [None, "0", "2500", "5400.5", "1000000", "0.1", "3000", "4200"]
OP = [None, "5000", "0", "6670.25", "5000", "5400", "1", "8000"]
KS = [0, 1, 3, 6, 12]
BS = [1, 5, 7, 11]
EC = [0.0, -0.0, 1.0, -1.0, 1e-3, 1e300, -1e300, 0.5]
OC = 4000003
# numeric columns of test_features (checked below against a real run); 41 names (prime)
FT = ["age", "monthly_income", "MonthlyIncome_missing", "num_dependents", "Dependents_missing", "age_group",
      "num_late_30_59", "num_late_60_89", "num_late_90_plus", "credit_utilization", "debt_ratio", "num_credit_lines",
      "num_real_estate_loans", "total_late_payments", "has_delinquency", "has_serious_delinquency",
      "credit_util_category", "debt_category", "income_per_dependent", "credit_lines_per_person", "age_category",
      "flag_high_utilization", "flag_very_high_utilization", "flag_high_debt_ratio", "flag_very_high_debt_ratio",
      "flag_recent_late_payments", "flag_serious_delinquency", "flag_multiple_delinquencies", "flag_low_income",
      "flag_many_dependents", "flag_few_credit_lines", "total_risk_flags", "financial_health", "log_monthly_income",
      "log_num_credit_lines", "log_total_late_payments", "age_income_interaction", "utilization_debt_interaction",
      "credit_utilization_capped", "debt_ratio_capped", "row_id"]
assert len(FT) == 41


def h(s: int, k: int) -> int:
    return kit.hsh(s, k)


# ---------------------------------------------------------------- the text parser (Lean `pf`)
def pf(t: str):
    neg = t[:1] == "-"
    b = t[1:] if neg else t
    ps = b.split(".")
    ip, fp = ps[0], (ps[1] if len(ps) > 1 else "")
    if len(ps) > 2 or (ip + fp) == "" or not all(c in "0123456789" for c in ip + fp):
        return None
    v = float(f"{int(ip + fp)}e-{len(fp)}")
    return -v if neg else v


# ---------------------------------------------------------------- generators (mirror of the Lean lets)
def cell(s: int, r: int, i: int) -> str:
    u = h(s, 3000 + 100 * r + i)
    d = (u // 7) % 100 < PDS[h(s, 2003) % 10]
    if r == 0 and not d:
        return str(i + 1)
    P = (PD if d else PC)[r]
    return P[(u // 1000) % len(P)]


def cols(s: int) -> list[tuple[int, str]]:
    hv = h(s, 2000) % 16
    base = list(range(12))
    if hv == 11:
        rs = [r for r in base if r != h(s, 2004) % 12]
    elif hv == 12:
        rs = base + [12]
    elif hv == 13:
        rs = [13 if r == 5 else r for r in base]
    elif hv == 14:
        rs = base[::-1]
    else:
        rs = base
    out = []
    for r in rs:
        nm = "extra" if r == 12 else "AGE" if r == 13 else N0[r]
        out.append((r, "AGE" if hv == 9 and r == 3 else nm.upper() if hv == 10 else nm.lower() if hv == 15 else nm))
    return out


def cs_test(s: int):
    """None, or (header [(name, is_text)], columns {name: values}, n rows)."""
    if h(s, 2002) % 25 == 0:
        return None
    n = NR[h(s, 2001) % 10]
    cl = cols(s)
    hdr, data = [], {}
    for r, name in cl:
        tx = [cell(s, r, i) for i in range(n)]
        if n == 0:
            kd = r in (1, 6, 11)
        else:
            kd = not (any(t != "" for t in tx) and all(t == "" or pf(t) is not None for t in tx))
        hdr.append((name, kd))
        data[name] = [(None if t == "" else t) for t in tx] if kd else [pf(t) for t in tx]
    return hdr, data, n, {name: [cell(s, r, i) for i in range(n)] for r, name in cl}


def medians(s: int):
    """"absent", or (names, rows of Option values, text kinds per column)."""
    mv = h(s, 2010) % 20
    if mv == 0:
        return "absent"
    nv = h(s, 2013) % 6
    names = ["age_group", "median_income", "overall_median_income"]
    if nv == 3:
        names = [x.upper() for x in names]
    gs = [] if mv == 1 else GS[h(s, 2011) % 8]
    mi = [MP[h(s, 2100 + j) % 8] for j in range(len(gs))]
    ov = OP[h(s, 2012) % 8]
    colv = [[str(g) for g in gs], mi, [ov] * len(gs)]
    if nv == 4:
        names, colv = ["age"] + names, [["1"] * len(gs)] + colv
    elif nv == 5:
        names, colv = names[::-1], colv[::-1]
    return names, colv


def coefs(s: int):
    k = KS[h(s, 2020) % 5]
    a = h(s, 2021) % len(FT)
    b = BS[h(s, 2022) % 4]
    vs = kit.gF(s + OC, k + 1, 25, 4, EC)
    co = [(FT[(a + j * b) % len(FT)], vs[j + 1]) for j in range(k)]
    if h(s, 2023) % 25 == 0:
        co.append(("nope", 1.0))
    return co, vs[0]


# ---------------------------------------------------------------- the real run
def pyrun(s: int, work: Path) -> dict:
    cs, md, (co, ic) = cs_test(s), medians(s), coefs(s)
    dd, ind, outd = work / "data", work / "in", work / "out"
    for d in (dd, ind):
        d.mkdir(parents=True)
    if cs is not None:
        hdr, _, n, texts = cs
        lines = [",".join(name for name, _ in hdr)] + [",".join(texts[name][i] for name, _ in hdr) for i in range(n)]
        (dd / "cs-test.csv").write_text("\n".join(lines) + "\n")
    medp = work / "income_medians.csv"
    if md != "absent":
        names, colv = md
        nrow = len(colv[0])
        medp.write_text("\n".join([",".join(names)] + [",".join("" if c[j] is None else c[j] for c in colv) for j in range(nrow)]) + "\n")
    (ind / "model.json").write_text(json.dumps({"intercept": ic, "coefficients": dict(co)}))
    mce = h(s, 2024) % 25 != 0
    if mce:
        (ind / "model_coefficients.csv").write_text("variable,estimate\n")
    rec: dict = {"files": [], "raw0": "unset", "locals": {}, "seed": s, "medp": medp, "mce": mce}
    code = pr.run.__code__
    o_write = sc.write_sas_csv

    def w_write(df, path, formats=None):
        rec["files"].append((Path(path).name, df))

    def local(frame, event, arg):
        if event == "line" and frame.f_lineno == 82:
            rec["raw0"] = frame.f_locals.get("test_raw")
        elif event == "return":
            rec["locals"] = dict(frame.f_locals)
        return local

    sc.write_sas_csv = w_write
    sys.settrace(lambda f, e, a: local if f.f_code is code else None)
    try:
        with contextlib.redirect_stdout(io.StringIO()):
            pr.run(ind, outd, data_dir=dd, income_medians=medp)
        rec["outcome"] = "files"
    except ValueError as ex:
        rec["outcome"] = "stop" if str(ex) == "Test set scoring stopped. Nothing is exported." else f"raises ValueError: {ex}"
    except Exception as ex:  # noqa: BLE001
        rec["outcome"] = f"raises {type(ex).__name__}: {ex}"
    finally:
        sys.settrace(None)
        sc.write_sas_csv = o_write
    if rec["outcome"] == "stop":
        assert rec["files"] == [] and not any((outd / f).exists() for f in FILES)
    elif rec["outcome"] == "files":
        assert [f for f, _ in rec["files"]] == FILES
    # ---- the mirrors are what the port imports
    if not isinstance(rec["raw0"], str):
        if cs is None:
            assert rec["raw0"] is None, s
        else:
            hdr, data, n, _ = cs
            mirror = pl.DataFrame([pl.Series(name, data[name], dtype=(pl.String if kd else pl.Float64)) for name, kd in hdr])
            assert rec["raw0"] is not None and cmp.canon_frame(mirror) == cmp.canon_frame(rec["raw0"]), (s, mirror, rec["raw0"])
    else:
        assert md == "absent" or not mce, s
    if md != "absent":
        names, colv = md
        imp = sc.proc_import_csv(medp)
        mirror = pl.DataFrame([pl.Series(nm, c if all(x is None for x in c) else [None if x is None else float(x) for x in c],
                                         dtype=(pl.String if all(x is None for x in c) else pl.Float64)) for nm, c in zip(names, colv)])
        assert cmp.canon_frame(mirror) == cmp.canon_frame(imp), (s, mirror, imp)
        rec["med_imp"] = imp
    return rec


F64_NEEDED = ["age", "NumberOfTime30-59DaysPastDueNotW", "NumberOfTime60-89DaysPastDueNotW", "NumberOfTimes90DaysLate",
              "RevolvingUtilizationOfUnsecuredL", "DebtRatio", "NumberOfOpenCreditLinesAndLoans"]
TEST_CLEANED_COLS = set(N0) | {"age_group", "MonthlyIncome_missing", "Dependents_missing"}


def precond(s: int, rec: dict) -> bool:
    md, (co, _) = medians(s), coefs(s)
    if md == "absent" or not rec["mce"]:
        return True
    # 00: true by construction (asserted)
    cs = cs_test(s)
    if cs is not None:
        names = [n for n, _ in cs[0]]
        assert len(set(names)) == len(names) and all(ord(c) < 128 for n in names for c in n)
    stopped_at_check = rec["outcome"] == "stop"
    if stopped_at_check:
        return True
    tr = rec["locals"].get("test_raw")
    assert tr is not None, (s, rec["outcome"])
    if not all(tr.schema[v] in (pl.String, pl.Float64) for v in ("MonthlyIncome", "NumberOfDependents")):
        return False
    names, colv = md
    if len(colv[0]) == 0:
        return False                                             # 02: the table has a row
    if not all(tr.schema[v] == pl.Float64 for v in F64_NEEDED):
        return False                                             # 03-05
    env = {"sas_compat": sc, "income_medians": rec["medp"], "pl": pl}
    exec(MED_SLICE, env)
    tm = env["train_income_medians"]
    if not all(c in tm.columns and tm.schema[c] == pl.Float64 for c in ("age_group", "median_income", "overall_median_income")):
        return False                                             # 04
    for c in tm.columns:
        if c in TEST_CLEANED_COLS and ((c + "_right") in TEST_CLEANED_COLS or (c + "_right") in tm.columns):
            return False
    deps = rec["locals"].get("test_imputed")
    if deps is not None and any(x is not None and x + 1 == 0 for x in deps.get_column("num_dependents").to_list()):
        return False                                             # 05
    if len({n for n, _ in co}) != len(co) or not all(n in FT for n, _ in co):
        return False                                             # 06
    return True


def file_digest(name: str, df: pl.DataFrame) -> int:
    toks = cmp.tok_str(name) + [len(df.columns)]
    for c in df.columns:
        toks += cmp.tok_str(c)
    return cmp.digest(toks + cmp.tokens(cmp.canon_table(df)))


def expected(rec: dict) -> int:
    return b4.w([0] if rec["outcome"] == "stop" else [1] + [file_digest(f, df) for f, df in rec["files"]])


# ---------------------------------------------------------------- Lean
def sl(xs) -> str:
    return "[" + ", ".join(lt.lean_str(x) for x in xs) + "]"


def ol(xs) -> str:
    return "[" + ", ".join("none" if x is None else f"some {x}" for x in xs) + "]"


def lets(ibx: dict, sbt: dict) -> str:
    return (
        b4.W + "let h := fun (s k : Nat) => (hsh s k).toNat; "
        "let pf := fun (t : String) => (let cl := t.toList; let neg := cl.head? == some '-'; let b := String.ofList (if neg then cl.drop 1 else cl); "
        "let ps := b.splitOn \".\"; let ip := ps.getD 0 \"\"; let fp := ps.getD 1 \"\"; let d := ip ++ fp; "
        "if ps.length > 2 || d.isEmpty || !(d.all Char.isDigit) then (none : Option Float) else "
        "let v := Float.ofScientific d.toNat! true fp.length; some (if neg then -v else v)); "
        f"let IBX : List (String × Option Float) := [{', '.join(f'({lt.lean_str(t)}, ' + ('none' if v is None else 'some ' + lt.lean_float(v)) + ')' for t, v in ibx.items())}]; "
        "let ib := fun (e : Pl.Expr Float) => (({ eval := fun (g : Option (List (List Nat))) (fr : Pl.Frame Float) => "
        "(match e.eval g fr with | .str v => Pl.Col.f64 (v.map (fun (o : Option String) => (match o with | none => none | some t => "
        "(match IBX.lookup t with | some r => r | none => pf t) : Option Float))) | _ => Pl.Col.f64 []), "
        "name := e.name, ser := Pl.node [e.ser] }) : Pl.Expr Float); "
        f"let SBT : List (UInt64 × String) := [{', '.join(f'({b}, {lt.lean_str(t)})' for b, t in sbt.items())}]; "
        "let sb := fun (o : Option Float) => ((match o with | none => \"!none\" | some x => (SBT.lookup x.toBits).getD \"?\") : String); "
        f"let N0 : List String := {sl(N0)}; let PC : List (List String) := [{', '.join(sl(p) for p in PC)}]; "
        f"let PD : List (List String) := [{', '.join(sl(p) for p in PD)}]; "
        f"let pd := fun (s : Nat) => ({PDS} : List Nat).getD (h s 2003 % 10) 0; "
        "let cell := fun (s r i : Nat) => let u := h s (3000 + 100 * r + i); let d := decide ((u / 7) % 100 < pd s); "
        "if r == 0 && !d then toString (i + 1) else let P := (if d then PD else PC).getD r []; P.getD ((u / 1000) % P.length) \"\"; "
        "let cols := fun (s : Nat) => let hv := h s 2000 % 16; let base := List.range 12; "
        "let rs : List Nat := if hv == 11 then base.filter (fun (r : Nat) => r != h s 2004 % 12) else if hv == 12 then base ++ [12] "
        "else if hv == 13 then base.map (fun (r : Nat) => if r == 5 then 13 else r) else if hv == 14 then base.reverse else base; "
        "rs.map (fun (r : Nat) => (r, (let nm := if r == 12 then \"extra\" else if r == 13 then \"AGE\" else N0.getD r \"\"; "
        "if hv == 9 && r == 3 then \"AGE\" else if hv == 10 then nm.toUpper else if hv == 15 then nm.toLower else nm))); "
        "let CS := fun (s : Nat) => if h s 2002 % 25 == 0 then (none : Option (List (String × Bool) × Tabular.Table Float)) else "
        f"let n := ({NR} : List Nat).getD (h s 2001 % 10) 0; let cl := cols s; "
        "let kd := fun (r : Nat) => let tx := (List.range n).map (cell s r); if n == 0 then (r == 1 || r == 6 || r == 11) else "
        "!(tx.any (fun (t : String) => t != \"\") && tx.all (fun (t : String) => t == \"\" || (pf t).isSome)); "
        "some (cl.map (fun (c : Nat × String) => (c.2, kd c.1)), (List.range n).map (fun (i : Nat) => cl.map (fun (c : Nat × String) => "
        "(c.2, (let t := cell s c.1 i; if kd c.1 then Tabular.Cell.str (if t == \"\" then none else some t) else Tabular.Cell.num (pf t) : Tabular.Cell Float))))); "
        f"let MP : List (Option Float) := {ol(MP)}; let OP : List (Option Float) := {ol(OP)}; "
        "let MD := fun (s : Nat) => let mv := h s 2010 % 20; if mv == 0 then (none : Option (Tabular.Table Float)) else "
        f"let gs : List Nat := if mv == 1 then [] else ({GS} : List (List Nat)).getD (h s 2011 % 8) []; "
        "let mi := (List.range gs.length).map (fun (j : Nat) => MP.getD (h s (2100 + j) % 8) none); let ov := OP.getD (h s 2012 % 8) none; let nv := h s 2013 % 6; "
        "let cn := fun (o : Option Float) (an : Bool) => (if an then Tabular.Cell.str none else Tabular.Cell.num o : Tabular.Cell Float); "
        "let nm := fun (t : String) => if nv == 3 then t.toUpper else t; "
        "some ((List.range gs.length).map (fun (j : Nat) => let r : Tabular.Row Float := [(nm \"age_group\", Tabular.Cell.num (some (gs.getD j 0).toFloat)), "
        "(nm \"median_income\", cn (mi.getD j none) (mi.all Option.isNone)), (nm \"overall_median_income\", cn ov ov.isNone)]; "
        "if nv == 4 then (\"age\", Tabular.Cell.num (some 1.0)) :: r else if nv == 5 then r.reverse else r)); "
        f"let FT : List String := {sl(FT)}; let EC : List (Option Float) := [{', '.join('some ' + lt.lean_float(x) for x in EC)}]; "
        f"let CO := fun (s : Nat) => let k := ({KS} : List Nat).getD (h s 2020 % 5) 0; let a := h s 2021 % {len(FT)}; let b := ({BS} : List Nat).getD (h s 2022 % 4) 1; "
        f"let vs := gF (s + {OC}) (k + 1) 25 4 EC; "
        f"((List.range k).map (fun (j : Nat) => (FT.getD ((a + j * b) % {len(FT)}) \"\", (vs.getD (j + 1) none).getD 0.0)) ++ (if h s 2023 % 25 == 0 then [(\"nope\", 1.0)] else []), (vs.getD 0 none).getD 0.0); "
        "let tL := fun (ns : List String) => ns.length.toUInt64 :: ns.flatMap tS; "
        "let E := fun (s : Nat) => W (match run_py_py (α := Float) (s % 2 == 0) ib (CO s).2 (CO s).1 sb (h s 2024 % 25 != 0) (CS s) (MD s) with | none => [0] | some fs => "
        "1 :: fs.map (fun (f : String × List String × Tabular.Table Float) => dg (tS f.1 ++ tL f.2.1 ++ tA f.2.2))); "
    )


def main() -> None:
    base = Path(tempfile.mkdtemp(prefix="fz_pred_"))
    # ---- the doubles, checked against the real functions
    texts = sorted({t for p in PC + PD for t in p if t != ""} | {str(i) for i in range(1, 10)})
    nums6_11 = sorted({pf(t) for r in (6, 11) for t in PC[r] + PD[r] if t != "" and pf(t) is not None})
    sbt = {lt.bits(v): sc.sas_best12(v) for v in nums6_11}
    texts = sorted(set(texts) | set(sbt.values()))
    real = pl.DataFrame({"s": texts}, schema={"s": pl.String}).select(sc.input_best32(pl.col("s"))).to_series().to_list()
    assert all(t == t.strip(" ") and len(t) <= 32 for t in texts)
    ibx = {t: v for t, v in zip(texts, real) if not ((v is None and pf(t) is None) or (v is not None and pf(t) is not None and lt.bits(v) == lt.bits(pf(t))))}
    for t in texts:  # the import's rule on our texts is the parser's
        assert (re.match(sc._NUM_RE, t) is not None) == (pf(t) is not None) or t in sbt.values(), t
        assert pf(t) is None or pf(t) == float(t), t
    print("IBX (texts where input_best32 is not the plain parse):", ibx, "| sas_best12 table:", sbt)
    kept, rej, raises, dropped, outcomes = {}, {}, [], [], {}
    ft_checked = False
    for s in range(SEED0, SEED0 + CH * NCH):
        rec = pyrun(s, base / str(s))
        ok = precond(s, rec)
        ran = not rec["outcome"].startswith("raises")
        key = ("kept " if ok else "rejected ") + (rec["outcome"] if ran else "raises")
        if ran and rec["outcome"] == "files" and rec["files"][0][1].height == 0:
            key += " (no row)"
        outcomes[key] = outcomes.get(key, 0) + 1
        if ran and rec["outcome"] == "files" and not ft_checked:
            tf = rec["locals"]["test_features"]
            assert all(n in tf.columns and tf.schema[n] in (pl.Float64, pl.Int64, pl.Int32) for n in FT if n != "row_id"), [(n, tf.schema.get(n)) for n in FT]
            ft_checked = True
        if ok and ran:
            kept[s] = expected(rec)
        elif ok:
            raises.append(s)
            print("PYTHON RAISES INSIDE THE PRECONDITION", s, rec["outcome"][:200])
        elif ran:
            rej[s] = expected(rec)
        else:
            dropped.append(s)
        shutil.rmtree(base / str(s), ignore_errors=True)
    shutil.rmtree(base, ignore_errors=True)
    print(outcomes)
    st = Suite("fz_run_py_py")
    st.item, st.decl = ITEM, DECL
    L = lets(ibx, sbt)
    notk = sorted(set(rej) | set(dropped) | set(raises))
    per = 26  # blocks per eval input
    for k0 in range(0, NCH, per):
        blocks = range(k0, min(NCH, k0 + per))
        lo, hi = SEED0 + CH * blocks[0], SEED0 + CH * (blocks[-1] + 1)
        ex = [x for x in notk if lo <= x < hi]
        cases = []
        for i in blocks:
            r = range(SEED0 + CH * i, SEED0 + CH * i + CH)
            k_ = [x for x in r if x in kept]
            cases.append((f"kept seeds of {r[0]}..{r[-1]}", U, b4.w([kept[x] for x in k_]), {"fz": "kept", "covers": len(k_)}))
        rj = [x for x in ex if x in rej]
        cases += [(f"rejected seed {x}", U, rej[x], {"fz": "rejected"}) for x in rj]
        body = (f"(let X : List Nat := {ex}; let RJ : List Nat := {rj}; (List.range' {blocks[0]} {len(blocks)}).map (fun (i : Nat) => "
                f"W (((List.range' ({SEED0} + {CH} * i) {CH}).filter (fun (s : Nat) => !(X.contains s))).map E)) ++ RJ.map E)")
        st.ints(L, body, cases, gen=True, table=True)
    st.notes = {U: "fuzz 2026-11-16"}
    st.write()
    fuzz = {"fuzzer": "port-translator-3", "generator": "diffeval/units/fz_run_py_py_gen.py", "units": {U: {
        "seeds": f"{SEED0}..{SEED0 + CH * NCH - 1}", "generated": CH * NCH, "kept": len(kept),
        "python_raises_inside_precondition": raises,
        "note": f"generated files, real predict.run; outcomes {outcomes}; rejected and Python raises (dropped): {len(dropped)}; "
                f"kept cases digest a block of {CH} seeds, each rejected input is one case"
                "; the 3 differing blocks are seeds 30930, 31316, 31393: last bit of exp (recorded limit, RULEBOOK 6), "
                "shown by experiments/fz_run_py_py_exp_last_bit.py"}}}
    (HERE.parent / "work" / "fz_run_py_py.fuzz.json").write_text(json.dumps(fuzz, indent=1))
    for i, inp in enumerate(st.inputs):
        print(i, len(inp["text"]), "chars")


if __name__ == "__main__":
    main()
