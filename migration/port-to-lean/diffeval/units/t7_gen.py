"""T7 differential test: def:predict_run_00_input_check (predict.py:82-182) against the REAL
`predict.run` on the test files of judge/scenarios (update-after-verification.md section 3, T7).

  cd migration/port-to-lean
  PYTHONPATH=../../port uv run --project ../../port python diffeval/units/t7_gen.py
      -> diffeval/work/t7_check.json, t7_check.inputs.json
  eval_decl each input on def:zz_carrier_p / zz_carrier_p; outputs one per line in
  diffeval/work/t7_check.out.txt; then
  PYTHONPATH=../../port uv run --project ../../port python diffeval/compare.py diffeval/work/t7_check.json diffeval/work/t7_check.out.txt

Python side. Nothing of `run` is copied. The real `predict.run` is called with `data_dir` = the
scenario folder, an existing (empty) medians file and an existing (empty) model_coefficients.csv,
so that the run reaches the input check. A trace function reads the locals of `run`:
  line 82  (`EXPECTED = (`)                : test_raw as lines 42-79 left it (None or a frame)
  line 176 (`if test_raw is None or ...`)  : columns_ok, bad_rows, duplicate_ids, test_raw, age_name, raw
  line 177 (the first print of the stop)   : the run stopped
The counters are also read from the ERROR line the run prints, and must agree with the locals.
What the run does after line 182 (it fails on the empty medians file) is not looked at.

Lean side, a few eval inputs, each holding one base frame (column codes) and the scenarios as
differences from it:
  - `cs_test` = `some (header, rows)`: header = (name, is String) of the frame at line 82, rows =
    its rows; `none` when that frame is None. The digest of
    `predict_run_00_input_check_frame cs_test` is compared with the frame at line 82 first, so the
    input is the same bit for bit (and the frame helper is tested, zero-row frames included).
  - `input_best32` test double IB: a String column is mapped value by value through a table from
    the stripped text to what the real `sas_compat.input_best32` returns for it (built from every
    String column of `raw` in the input's scenarios); a text not in the table gives null. The
    strip / len_chars / to_uppercase helpers are also compared directly with polars (case group
    `helpers`).
  - per scenario 7 integers: digest of the input frame, columns_ok, bad_rows, duplicate_ids
    (from `predict_run_00_input_check_checked`), stop (0/1), digest of the returned frame, digest
    of age_name (from `predict_run_00_input_check`).
When the import fails (test_raw None) Python has no frame: the expected frame is the empty frame
the unit documents, expected age_name "age".
"""
from __future__ import annotations

import contextlib
import io
import re
import sys
import tempfile
from decimal import Decimal
from pathlib import Path

import polars as pl

HERE = Path(__file__).resolve().parent
KIT_DIR = HERE.parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(KIT_DIR))

import compare as cmp  # noqa: E402
import leanterm as lt  # noqa: E402
from suite import Suite  # noqa: E402

from credit_risk import predict as pr  # noqa: E402
from credit_risk import sas_compat as sc  # noqa: E402

SCEN = ROOT / "judge" / "scenarios"
UNIT = "predict_run_00_input_check"
L_CHECK, L_TEST, L_STOP = 82, 176, 177
_src = Path(pr.__file__).read_text().splitlines()
assert _src[L_CHECK - 1].startswith("    EXPECTED = ("), _src[L_CHECK - 1]
assert _src[L_TEST - 1].startswith("    if test_raw is None or columns_ok != 1"), _src[L_TEST - 1]
assert _src[L_STOP - 1].strip() == "print(", _src[L_STOP - 1]

NUM_COLS = ["VAR1", "SeriousDlqin2yrs", "age", "MonthlyIncome", "NumberOfDependents",
            "RevolvingUtilizationOfUnsecuredL", "DebtRatio", "NumberOfTime30-59DaysPastDueNotW",
            "NumberOfTime60-89DaysPastDueNotW", "NumberOfTimes90DaysLate",
            "NumberOfOpenCreditLinesAndLoans", "NumberRealEstateLoansOrLines"]


# ---------------------------------------------------------------- the traced real run
def pyrun(data_dir: Path) -> dict:
    rec: dict = {"stopped": False}
    code = pr.run.__code__

    def local(frame, event, arg):
        if event == "line":
            ln = frame.f_lineno
            loc = frame.f_locals
            if ln == L_CHECK:
                rec["raw0"] = loc.get("test_raw")
            elif ln == L_TEST:
                for k in ("columns_ok", "bad_rows", "duplicate_ids", "test_raw", "age_name"):
                    rec[k] = loc[k]
                rec["raw"] = loc.get("raw")
            elif ln == L_STOP:
                rec["stopped"] = True
        return local

    def glob(frame, event, arg):
        return local if frame.f_code is code else None

    with tempfile.TemporaryDirectory() as d:
        ind, outd = Path(d) / "in", Path(d) / "out"
        ind.mkdir()
        (ind / "model_coefficients.csv").write_text("")
        med = ind / "income_medians.csv"
        med.write_text("")
        buf = io.StringIO()
        sys.settrace(glob)
        try:
            with contextlib.redirect_stdout(buf):
                pr.run(ind, outd, data_dir=data_dir, income_medians=med)
        except Exception as ex:  # the stop (ValueError) or, after the check, the empty medians file
            rec["exc"] = f"{type(ex).__name__}: {ex}"
        finally:
            sys.settrace(None)
        rec["written"] = sorted(p.name for p in outd.iterdir()) if outd.exists() else []
    rec["out"] = buf.getvalue()
    assert "columns_ok" in rec, "the run did not reach line 176"
    m = re.search(r"columns_ok=(-?\d+) bad_rows=(-?\d+) duplicate_ids=(-?\d+)\.", rec["out"])
    if rec["stopped"]:
        assert m and tuple(map(int, m.groups())) == (rec["columns_ok"], rec["bad_rows"], rec["duplicate_ids"]), rec["out"]
        assert rec["exc"] == "ValueError: Test set scoring stopped. Nothing is exported." and rec["written"] == []
    else:
        assert m is None
    if rec["raw0"] is not None:  # the precondition of the unit holds on this input
        r0 = rec["raw0"]
        assert len(set(r0.columns)) == len(r0.columns) and all(n.isascii() for n in r0.columns), r0.columns
        assert all(dt in (pl.String, pl.Float64) for dt in r0.dtypes), r0.schema
    stop = rec["test_raw"] is None or rec["columns_ok"] != 1 or rec["bad_rows"] != 0 or rec["duplicate_ids"] != 0
    assert stop == rec["stopped"]
    return rec


# ---------------------------------------------------------------- encoding
class Enc:
    """Codes of one eval input: text cells index S, numeric cells are m * 64 + e (m * 10^-e) or
    -(2 + k) for the bit pattern X[k]; -1 is a null."""

    def __init__(self):
        self.S: list[str] = []
        self.si: dict[str, int] = {}
        self.X: list[int] = []
        self.xi: dict[int, int] = {}
        self.N: list[str] = []

    def n(self, v: str) -> int:
        if v not in self.N:
            self.N.append(v)
        return self.N.index(v)

    def s(self, v: str | None) -> int:
        if v is None:
            return -1
        if v not in self.si:
            self.si[v] = len(self.S)
            self.S.append(v)
        return self.si[v]

    def f(self, v: float | None) -> int:
        if v is None:
            return -1
        b = cmp.fbits(v)
        if v == v and v not in (float("inf"), float("-inf")) and v >= 0 and b != cmp.fbits(-0.0):
            _, digits, exp = Decimal(repr(v)).as_tuple()
            m = int("".join(map(str, digits)))
            if exp > 0:
                m, exp = m * 10 ** exp, 0
            e = -exp
            if e < 64 and m < 2 ** 63 and cmp.fbits(float(f"{m}e-{e}")) == b:
                return m * 64 + e
        if b not in self.xi:
            self.xi[b] = len(self.X)
            self.X.append(b)
        return -(2 + self.xi[b])

    def col(self, s: pl.Series) -> tuple[bool, list[int]]:
        if s.dtype == pl.String:
            return True, [self.s(v) for v in s.to_list()]
        assert s.dtype == pl.Float64, s.dtype  # what proc_import_csv produces (G4)
        return False, [self.f(v) for v in s.to_list()]


def codes(xs: list[int]) -> str:
    return 'cs "' + ",".join(map(str, xs)) + '"'


LETS_HEAD = (
    'let cs := fun (s : String) => (if s == "" then (#[] : Array Int) else ((s.splitOn ",").map (fun (x : String) => (x.toInt?).getD (-1))).toArray); '
)
LETS_TAIL = (
    "let P := fun (b : Nat) => B.getD b #[]; let E : Array Int := #[]; "
    "let hd := fun (ix : String) (ks : String) => (((cs ix).toList.zip ks.toList).map (fun (p : Int × Char) => (N.getD p.1.toNat \"\", p.2 == '1')) : List (String × Bool)); "
    "let pc := fun (b : Nat) (ov : List (Nat × Int)) => ov.foldl (fun (a : Array Int) (p : Nat × Int) => a.set! p.1 p.2) (B.getD b #[]); "
    "let num := fun (c : Int) => (if c == -1 then none else if c < -1 then some (Float.ofBits (X.getD (-c - 2).toNat 0)) else some (Float.ofScientific (c.toNat / 64) true (c.toNat % 64)) : Option Float); "
    'let cell := fun (k : Bool) (c : Int) => (if k then Tabular.Cell.str (if c < 0 then none else some (S.getD c.toNat "")) else Tabular.Cell.num (num c) : Tabular.Cell Float); '
    "let mkC := fun (H : List (String × Bool)) (cols : List (Array Int)) => ((H, (List.range ((cols.headD #[]).size)).map (fun (i : Nat) => (H.zip cols).map (fun (p : (String × Bool) × Array Int) => (p.1.1, cell p.1.2 (p.2.getD i (-1)))))) : List (String × Bool) × Tabular.Table Float); "
    'let IBT : List (String × Option Float) := (IK.toList.zip IV.toList).map (fun (p : Int × Int) => (S.getD p.1.toNat "", num p.2)); '
    "let IB := fun (e : Pl.Expr Float) => ({ eval := fun (g : Option (List (List Nat))) (fr : Pl.Frame Float) => (match e.eval g fr with | .str v => Pl.Col.f64 (v.map (fun (o : Option String) => o.bind (fun (s : String) => (IBT.lookup s).getD none))) | _ => Pl.Col.f64 []), name := e.name, ser := Pl.node [e.ser] } : Pl.Expr Float); "
    f"let ev := fun (C : Option (List (String × Bool) × Tabular.Table Float)) => (let u := {UNIT} IB C; "
    f"(match C with | none => [0, 0, 0, 0] | some c => (let fr := {UNIT}_frame c; let r := {UNIT}_checked IB fr; [dg (tR fr), r.1, r.2.1, r.2.2.1])) "
    "++ [(if u.1 then 1 else 0), dg (tR u.2.1), dg (tS u.2.2)] : List Int); "
)


def dgf(df: pl.DataFrame) -> int:
    return cmp.digest(cmp.tokens(cmp.canon_frame(df)))


def build_input(s: Suite, group: list[tuple[str, dict]]):
    """One eval input for the scenarios of `group` = [(name, rec)]."""
    enc = Enc()
    frames = [(n, r) for n, r in group if r["raw0"] is not None]
    base = max((r["raw0"] for _, r in frames), key=lambda df: df.height * df.width, default=pl.DataFrame())
    bcols = [enc.col(base.get_column(c)) for c in base.columns]
    terms, cases = [], []
    ib: dict[str, float | None] = {}
    for name, r in group:
        raw0 = r["raw0"]
        if raw0 is None:
            terms.append("ev none")
            exp = [0, 0, 0, 0, 1, dgf(pl.DataFrame()), cmp.digest(cmp.tok_str("age"))]
            assert r["stopped"] and r["test_raw"] is None and r["age_name"] == "age"
        else:
            H, K, cols = [], [], []
            for c in raw0.columns:
                k, v = enc.col(raw0.get_column(c))
                H.append(str(enc.n(c)))
                K.append("1" if k else "0")
                best = None
                for bi, (bk, bv) in enumerate(bcols):
                    if bk == k and len(bv) == len(v):
                        ov = [(i, x) for i, (x, y) in enumerate(zip(v, bv, strict=True)) if x != y]
                        if best is None or len(ov) < len(best[1]):
                            best = (bi, ov)
                if not v:
                    cols.append("E")
                elif best is not None and not best[1]:
                    cols.append(f"P {best[0]}")
                elif best is not None and len(best[1]) <= 12:
                    cols.append(f"pc {best[0]} [" + ", ".join(f"({i}, {x})" for i, x in best[1]) + "]")
                else:
                    cols.append(codes(v))
            terms.append(f"ev (some (mkC (hd \"{','.join(H)}\" \"{''.join(K)}\") [{', '.join(cols)}]))")
            exp = [dgf(raw0), r["columns_ok"], r["bad_rows"], r["duplicate_ids"], int(r["stopped"]),
                   dgf(r["test_raw"]), cmp.digest(cmp.tok_str(r["age_name"]))]
            raw = r["raw"]
            for c in NUM_COLS:
                if raw.schema[c] == pl.String:
                    text = pl.col(c).str.strip_chars(" ")
                    got = raw.select(k=text, v=sc.input_best32(text))
                    assert got.schema["v"] == pl.Float64 and got.height == raw.height
                    for kk, vv in got.iter_rows():
                        if kk is not None:
                            assert kk not in ib or cmp.fbits(ib[kk] or 0.0) == cmp.fbits(vv or 0.0) and (ib[kk] is None) == (vv is None)
                            ib[kk] = vv
        for lab, e in zip(("input frame", "columns_ok", "bad_rows", "duplicate_ids", "stop", "test_raw", "age_name"), exp, strict=True):
            note = {"note": "import failed: Python has no frame; the unit returns the empty frame"} if raw0 is None and lab == "test_raw" else {}
            cases.append((f"{name}: {lab}", UNIT, int(e), note))
    ik = [enc.s(k) for k in ib]
    iv = [enc.f(v) for v in ib.values()]
    lets = (LETS_HEAD
            + "let X : Array UInt64 := #[" + ", ".join(map(str, enc.X)) + "]; "
            + "let N : Array String := #[" + ", ".join(lt.lean_str(x) for x in enc.N) + "]; "
            + "let S : Array String := #[" + ", ".join(lt.lean_str(x) for x in enc.S) + "]; "
            + "let B : Array (Array Int) := #[" + ", ".join(codes(v) for _, v in bcols) + "]; "
            + f"let IK := {codes(ik)}; let IV := {codes(iv)}; "
            + LETS_TAIL)
    s.ints(lets, "(" + " ++ ".join(terms) + ")", cases)


# ---------------------------------------------------------------- scenarios
def scenario_dirs() -> list[tuple[str, Path]]:
    out: list[tuple[str, Path]] = []
    for fam, pat in (("fix_Q27_emptytest", "*"), ("fix_Q27_emptytest_badheader", "*"), ("fix_Q27_column_order", "*"),
                     ("fix_round5", "test_*"), ("fix2", "test_*"), ("fix_G34", "test_*"), ("fix_Q27_textid", "test_*")):
        for d in sorted((SCEN / fam).glob(pat)):
            if d.is_dir() and (d / "cs-test.csv").exists():
                out.append((f"{fam}/{d.name}", d))
    out.append(("fix_Q27_test", SCEN / "fix_Q27_test"))
    out.append(("fix_Q27", SCEN / "fix_Q27"))
    return out


HDR = ",SeriousDlqin2yrs,RevolvingUtilizationOfUnsecuredLines,age,NumberOfTime30-59DaysPastDueNotWorse,DebtRatio,MonthlyIncome,NumberOfOpenCreditLinesAndLoans,NumberOfTimes90DaysLate,NumberRealEstateLoansOrLines,NumberOfTime60-89DaysPastDueNotWorse,NumberOfDependents"
# hand-made files (not in the plan): sites of the unit the scenario files do not reach
HAND = {
    # text id with blanks, long text, texts that are no number; outcome stated in several spellings;
    # income / dependents text with blanks, ".", "na", negative, fraction; a count with exponent
    "hand/text_cells": HDR + "\n" + "\n".join([
        "1,,0.5,40,0,0.1,5000,4,0,0,0,0",
        " 2 ,1,0.5,40,0,0.1, 5000 ,4,0,0,0, 2 ",
        "x3,0,0.5,40,0,0.1,NA,4,0,0,0,NA",
        "4,2,0.5,40,0,0.1,na,4,0,0,0,na",
        "5, na ,0.5,40,0,0.1,.,4,0,0,0,.",
        "6,.,0.5,40,0,0.1,-1,4,0,0,0,1.5",
        "7,1.0,0.5,40,0,0.1,abc,4,0,0,0,abc",
        "00000000000000000000000000000000008,,0.5,40,0,0.1,12,4,0,0,0,-0",
        "9,x,0.5,40,0,0.1,1e3,4,0,0,0,2e0",
        "1e1,,0.5,40,0,0.1,-0,1e1,0,0,0,3",
        "11,,0.5,40,0,0.1,1e400,4,0,0,0,1e400",
        "2,,0.5,40,0,0.1,0.5,4,0,0,0,0",
    ]) + "\n",
    # numeric columns with values the check rejects or accepts at the edge
    "hand/numeric_edges": HDR + "\n" + "\n".join([
        "1,0,0.5,40,0,0.1,5000,4,0,0,0,0",
        "2,1,-0.5,0,1,0,0,0,0,-3,0,0",
        "3,0,0.5,40,1.5,0.1,5000,4,0,0,0,0",
        "4,0,0.5,40,0,0.1,5000,-1,0,0,0,0",
        "5,0,0.5,40,0,0.1,5000,4,-0.5,0,0,0",
        "6,0,0.5,40,0,0.1,5000,4,0,0,1e400,0",
        "7,0,0.5,40,0,0.1,-0.0,4,0,0,-0.0,7",
        "8,0,,40,0,0.1,5000,4,0,0,0,0",
        "9,0,0.5,40,0,,5000,4,0,0,0,0",
        "10,0,0.5,40,0,0.1,5000,4,0,,0,0",
        "10.0,0,0.5,40,0,0.1,5000,4,0,0,,0",
        ",0,0.5,40,0,0.1,5000,4,0,0,0,0",
        "13,0.5,0.5,40,0,0.1,,4,0,0,0,",
    ]) + "\n",
    # names in other cases; two names that differ only in case (the later one is not read)
    "hand/case_names": ",SERIOUSDLQIN2YRS,revolvingutilizationofunsecuredlines,AgE,NumberOfTime30-59DaysPastDueNotWorse,debtratio,MONTHLYINCOME,NumberOfOpenCreditLinesAndLoans,NumberOfTimes90DaysLate,NumberRealEstateLoansOrLines,NumberOfTime60-89DaysPastDueNotWorse,numberofdependents\n1,,0.5,40,0,0.1,5000,4,0,0,0,0\n2,,0.5,41,0,0.1,NA,4,0,0,0,NA\n",
    "hand/case_duplicate": HDR + ",AGE\n1,,0.5,40,0,0.1,5000,4,0,0,0,0,41\n2,,0.5,41,0,0.1,NA,4,0,0,0,NA,42\n",
    "hand/case_duplicate_first": ",SeriousDlqin2yrs,RevolvingUtilizationOfUnsecuredLines,AGE,NumberOfTime30-59DaysPastDueNotWorse,DebtRatio,MonthlyIncome,NumberOfOpenCreditLinesAndLoans,NumberOfTimes90DaysLate,NumberRealEstateLoansOrLines,NumberOfTime60-89DaysPastDueNotWorse,age\n1,,0.5,40,0,0.1,5000,4,0,0,0,0\n",
    "hand/var_named": "VAR1,SeriousDlqin2yrs,RevolvingUtilizationOfUnsecuredLines,age,NumberOfTime30-59DaysPastDueNotWorse,DebtRatio,MonthlyIncome,NumberOfOpenCreditLinesAndLoans,NumberOfTimes90DaysLate,NumberRealEstateLoansOrLines,NumberOfTime60-89DaysPastDueNotWorse,NumberOfDependents\n1,,0.5,40,0,0.1,5000,4,0,0,0,0\n",
    "hand/no_expected_name": "a,b,c\n1,2,3\n4,5,6\n",
    "hand/no_expected_name_only": "a,b,c\n",
    "hand/one_row": HDR + "\n1,,0.5,40,0,0.1,5000,4,0,0,0,0\n",
    "hand/one_bad_row": HDR + "\n,,0.5,40,0,0.1,5000,4,0,0,0,0\n",
    "hand/empty_file": "",
}


def main():
    recs: list[tuple[str, dict]] = []
    for name, d in scenario_dirs():
        recs.append((name, pyrun(d)))
    with tempfile.TemporaryDirectory() as t:
        recs.append(("hand/absent_file", pyrun(Path(t))))
        for name, text in HAND.items():
            d = Path(t) / name.replace("/", "_")
            d.mkdir()
            (d / "cs-test.csv").write_bytes(text.encode())
            recs.append((name, pyrun(d)))
    for name, r in recs:
        raw0 = r["raw0"]
        shape = None if raw0 is None else raw0.shape
        print(f"{name:55} raw0={shape} columns_ok={r['columns_ok']} bad_rows={r['bad_rows']} duplicate_ids={r['duplicate_ids']} "
              f"stop={int(r['stopped'])} age_name={r['age_name']!r}")
    s = Suite("t7_check")
    s.item, s.decl, s.carrier = "def:zz_carrier_p", "zz_carrier_p", "identity"
    n_groups = 2
    size = -(-len(recs) // n_groups)
    for k in range(0, len(recs), size):
        build_input(s, recs[k:k + size])

    # the string helpers against polars, directly
    t = pl.DataFrame({"t": ["  12 ", "\t12", " NA ", "", None, "na", ". ", " a b ", "   ", "x" * 33, " " + "1" * 32 + " ", " 12", " é ", "\U0001f600x", " 5\t "]})
    a = pl.DataFrame({"t": ["  12 ", " Na ", "", None, "na", ". ", " a b ", "AbC-xyz_09", "{z}`a@[Z"]})
    lets = lt.lean_frame_let("f", t) + lt.lean_frame_let("a", a) + 'let c := Pl.col (α := Float) "t"; '
    st = f"({UNIT}_strMap {UNIT}_strip c)"
    s.digest(lets, [
        ("helpers: strip_chars(' ')", UNIT, f"tR (f.select [(\"s\", {st})])", cmp.canon_frame(t.select(s=pl.col("t").str.strip_chars(" ")))),
        ("helpers: len_chars", UNIT, f"tR (f.select [(\"n\", {UNIT}_lenChars c), (\"m\", {UNIT}_lenChars {st})])",
         cmp.canon_frame(t.select(n=pl.col("t").str.len_chars(), m=pl.col("t").str.strip_chars(" ").str.len_chars()))),
        ("helpers: len_chars <= 32", UNIT, f"tR (f.select [(\"n\", ({UNIT}_lenChars {st}).le (Pl.litI 32))])",
         cmp.canon_frame(t.select(n=pl.col("t").str.strip_chars(" ").str.len_chars() <= 32))),
        ("helpers: to_uppercase (ASCII)", UNIT, f"tR (a.select [(\"u\", {UNIT}_strMap String.toUpper c)])",
         cmp.canon_frame(a.select(u=pl.col("t").str.to_uppercase()))),
        ("helpers: stated chain", UNIT,
         f"tR (a.select [(\"u\", (({UNIT}_strMap String.toUpper ({UNIT}_strMap {UNIT}_strip (c.fillNull (Pl.litS \"\")))).isInS [\"\", \".\", \"NA\"]).not)])",
         cmp.canon_frame(a.select(u=~pl.col("t").fill_null("").str.strip_chars(" ").str.to_uppercase().is_in(["", ".", "NA"])))),
    ], gen=False, table=False)
    s.notes = {UNIT: "real predict.run traced at lines 82 / 176 / 177 on the test files of judge/scenarios named by T7 "
                     "(fix_Q27_emptytest, fix_Q27_emptytest_badheader, fix_Q27_column_order, fix_round5/test_*, fix2/test_*, "
                     "fix_G34/test_*, fix_Q27_test) plus fix_Q27, fix_Q27_textid/test_* and hand-made files; input_best32 = "
                     "table from stripped text to the real input_best32 result; all three eval inputs run first-hand by the "
                     "translator (2026-11-16), outputs taken from the tool results (a helper agent's earlier run gave the same integers)"}
    s.write()


if __name__ == "__main__":
    main()
