"""Update after verification, task T2: differential test of def:fe_run_00_input_check
(credit_risk/feature_engineering.py:43-128, the input check of feature_engineering.run).

  cd migration/port-to-lean && PYTHONPATH=../../port uv run --project ../../port python diffeval/units/t2_gen.py
      -> diffeval/work/t2_check (.json + .inputs.json)
  (eval_decl each input of work/t2_check.inputs.json on def:zz_carrier_f / zz_carrier_f, save
   the outputs one per line as work/t2_check.out.txt)
  ... python diffeval/compare.py diffeval/work/t2_check.json diffeval/work/t2_check.out.txt

Python side, never a re-implementation:
  real   the REAL feature_engineering.run on the scenario's cs-training.csv, with
         sas_compat.proc_import_csv wrapped to record the imported frame, write_sas_csv replaced by
         a recorder of the file names and a profile hook that copies the locals of `run` when it returns or raises: the
         four counters, whether it raised ValueError, and `credit_raw` after the check;
  slice  lines 43-128 read from the file at run time (verbatim, dedented) and executed with the
         module's globals on a given `credit_raw`. On the whole imported frame its counters, stop
         and frame are asserted equal to the real run's. It is then run on a sub-frame of the
         imported frame (the Lean input has to be typed into an eval_decl call): the first rows,
         every row the port marks bad, every row with a repeated or missing id, a row without a
         known income; on every single row of the sub-frame; and on every pair (row j, row i).
         Hand-made frames (values the CSV import cannot produce) go through the slice only.

Lean side: one eval input per group of scenarios. Each scenario gives
  [digest of the input frame, stop, digest of the returned frame] ++ stop of every single row
  ++ stop of every pair (j, i).
The digest of the input frame is compared with the digest of the Python sub-frame first, so the
inputs are the same bit for bit. `input_best32` is the test double IB: a lookup table from the
text (blanks already stripped by the unit) to the value the REAL sas_compat.input_best32 returns
for it, generated here from the port as it stands today.
"""
from __future__ import annotations

import contextlib
import io
import sys
import tempfile
import textwrap
from pathlib import Path

import polars as pl

HERE = Path(__file__).resolve().parent
KIT_DIR = HERE.parent
ROOT = HERE.parents[1]          # migration/port-to-lean
REPO = HERE.parents[3]
sys.path.insert(0, str(KIT_DIR))

import suite as suite_mod  # noqa: E402

suite_mod.CARRIERS["identity"] = ("def:zz_carrier_f", "zz_carrier_f")

import compare as cmp  # noqa: E402
import leanterm as lt  # noqa: E402
from suite import Suite  # noqa: E402

from credit_risk import feature_engineering as fe  # noqa: E402
from credit_risk import sas_compat as sc  # noqa: E402

UNIT = "fe_run_00_input_check"
A, B = 43, 128
SCEN = REPO / "judge" / "scenarios"
nan, inf = float("nan"), float("inf")
COUNTERS = ("columns_ok", "bad_rows", "duplicate_ids", "known_incomes")
N0 = ["VAR1", "SeriousDlqin2yrs", "RevolvingUtilizationOfUnsecuredL", "age", "NumberOfTime30-59DaysPastDueNotW",
      "DebtRatio", "MonthlyIncome", "NumberOfOpenCreditLinesAndLoans", "NumberOfTimes90DaysLate",
      "NumberRealEstateLoansOrLines", "NumberOfTime60-89DaysPastDueNotW", "NumberOfDependents"]


# ---------------------------------------------------------------- running the code of the package
def slice_code():
    src = "".join(Path(fe.__file__).read_text().splitlines(keepends=True)[A - 1:B])
    assert src.lstrip().startswith("EXPECTED = (") and src.rstrip().endswith(
        'raise ValueError("Feature engineering stopped. Nothing is exported.")'), "line numbers moved"
    return compile(textwrap.dedent(src), f"feature_engineering.py:{A}-{B}", "exec")


CODE = slice_code()


def run_slice(credit_raw):
    ns = dict(vars(fe))
    ns["credit_raw"] = credit_raw
    stopped = False
    with contextlib.redirect_stdout(io.StringIO()):
        try:
            exec(CODE, ns)
        except ValueError as e:
            assert str(e) == "Feature engineering stopped. Nothing is exported.", e
            stopped = True
    return {"stop": stopped, "counters": tuple(int(ns[c]) for c in COUNTERS), "credit_raw": ns["credit_raw"],
            "input_check": ns.get("input_check")}


def real_run(csv: Path | None):
    rec: dict = {"imported": None, "locals": None}
    o_write, o_import = sc.write_sas_csv, sc.proc_import_csv

    def w_import(path, guessingrows=20):
        df = o_import(path, guessingrows=guessingrows)
        rec["imported"] = df
        return df

    def prof(fr, event, arg):
        if event == "return" and fr.f_code is fe.run.__code__:
            rec["locals"] = dict(fr.f_locals)

    stopped = False
    with tempfile.TemporaryDirectory() as d:
        ind, outd = Path(d) / "in", Path(d) / "out"
        ind.mkdir()
        if csv is not None:
            (ind / "cs-training.csv").write_bytes(csv.read_bytes())
        written: list[str] = []
        sc.proc_import_csv, sc.write_sas_csv = w_import, (lambda df, path, formats=None: written.append(Path(path).name))
        sys.setprofile(prof)
        try:
            with contextlib.redirect_stdout(io.StringIO()):
                fe.run(ind, outd, split_ids=ROOT / "inputs" / "split_ids.csv")
        except ValueError as e:
            assert str(e) == "Feature engineering stopped. Nothing is exported.", e
            stopped = True
        finally:
            sys.setprofile(None)
            sc.write_sas_csv, sc.proc_import_csv = o_write, o_import
        assert list(outd.iterdir()) == []
        files = written
    lo = rec["locals"]
    return {"stop": stopped, "counters": tuple(int(lo[c]) for c in COUNTERS), "credit_raw": lo["credit_raw"],
            "imported": rec["imported"], "files": files}


def same_frame(a, b) -> bool:
    if a is None or b is None:
        return a is None and b is None
    return cmp.canon_frame(a) == cmp.canon_frame(b)


# ---------------------------------------------------------------- Lean terms
def flit(x: float) -> str:
    if x != x or x in (inf, -inf):
        return lt.lean_float(x)
    r = repr(x)
    if r.endswith(".0") and abs(x) < 2 ** 53 and not (x == 0 and r.startswith("-")):
        r = r[:-2]
    return r if not r.startswith("-") else f"({r})"


def col_term(s: pl.Series) -> str:
    vals = s.to_list()
    if s.dtype == pl.String:
        if None in vals:
            return "R [" + ", ".join("none" if v is None else f"some {lt.lean_str(v)}" for v in vals) + "]"
        return "S [" + ", ".join(lt.lean_str(v) for v in vals) + "]"
    assert s.dtype == pl.Float64, s.dtype
    if None in vals:
        return "G [" + ", ".join("none" if v is None else f"o {flit(v)}" for v in vals) + "]"
    return "F [" + ", ".join(flit(v) for v in vals) + "]"


def frame_term(df: pl.DataFrame) -> str:
    names = "N0" if df.columns == N0 else "[" + ", ".join(lt.lean_str(n) for n in df.columns) + "]"
    return f"(mk {names} [" + ", ".join(col_term(df.get_column(n)) for n in df.columns) + "])"


def best32_keys(df: pl.DataFrame) -> set[str]:
    """Every text the unit can hand to input_best32: the cells of the String columns, blanks stripped."""
    keys: set[str] = set()
    for n in df.columns:
        if df.schema[n] == pl.String:
            keys |= {v.strip(" ") for v in df.get_column(n).to_list() if v is not None}
    return keys


def best32_table(keys: set[str]) -> str:
    ks = sorted(keys)
    vals = pl.DataFrame({"t": ks}, schema={"t": pl.String}).select(sc.input_best32(pl.col("t"))).to_series().to_list()
    return "[" + ", ".join(f"({lt.lean_str(k)}, {'none' if v is None else 'some ' + (flit(v) if v == int(v) and abs(v) < 2 ** 53 and v == v else lt.lean_float(v))})"
                           for k, v in zip(ks, vals, strict=True)) + "]"


def lets(table: str) -> str:
    return (
        "let o := fun (x : Float) => (some x : Option Float); "
        "let F := fun (v : List Float) => (Pl.Col.f64 (v.map some) : Pl.Col Float); "
        "let G := fun (v : List (Option Float)) => (Pl.Col.f64 v : Pl.Col Float); "
        "let S := fun (v : List String) => (Pl.Col.str (v.map some) : Pl.Col Float); "
        "let R := fun (v : List (Option String)) => (Pl.Col.str v : Pl.Col Float); "
        "let N0 : List String := [" + ", ".join(lt.lean_str(n) for n in N0) + "]; "
        "let mk := fun (ns : List String) (cs : List (Pl.Col Float)) => (List.zip ns cs : Pl.Frame Float); "
        f"let T : List (String × Option Float) := {table}; "
        "let IB := fun (e : Pl.Expr Float) => ({ e with eval := fun (g : Option (List (List Nat))) (fr : Pl.Frame Float) => "
        "(match e.eval g fr with | .str v => Pl.Col.f64 (v.map (fun (q : Option String) => "
        "(match q with | some s => (T.lookup s).join | none => none : Option Float))) | c => c) } : Pl.Expr Float); "
        f"let U := fun (fr : Option (Pl.Frame Float)) => {UNIT} (α := Float) IB fr; "
        "let b := fun (x : Bool) => (if x then 1 else 0 : Int); "
        "let one := fun (f : Pl.Frame Float) (j : Nat) => [dg (tR f), b (U (some f)).1, dg (tR (U (some f)).2)] ++ "
        "(List.range f.height).map (fun (i : Nat) => b (U (some (f.takeRows [i]))).1) ++ "
        "(List.range f.height).map (fun (i : Nat) => b (U (some (f.takeRows [j, i]))).1); "
    )


def dgf(df) -> int:
    return cmp.digest(cmp.tokens(cmp.canon_frame(df)))


def cases_of(name: str, sub: pl.DataFrame, j: int, note: str = ""):
    """The Lean term and the expected integers of one scenario (all from run_slice)."""
    r = run_slice(sub)
    extra = {"note": note} if note else {}
    out = [(f"{name}/input", UNIT, dgf(sub), extra), (f"{name}/stop", UNIT, int(r["stop"]), extra),
           (f"{name}/frame", UNIT, dgf(r["credit_raw"]), extra)]
    for i in range(sub.height):
        out.append((f"{name}/row{i}", UNIT, int(run_slice(sub[[i]])["stop"]), extra))
    for i in range(sub.height):
        out.append((f"{name}/pair{j}_{i}", UNIT, int(run_slice(sub[[j, i]])["stop"]), extra))
    return f"one {frame_term(sub)} {j}", out, r


def pick_rows(imp: pl.DataFrame, ic: pl.DataFrame, head: int = 3, cap: int = 9) -> tuple[list[int], int]:
    """Rows of the sub-frame (file order) and the position in it of a good row with a known income."""
    bad = ic.get_column("bad_row").to_list()
    known = ic.get_column("known_income").to_list()
    ids = ic.get_column("VAR1").to_list()
    seen: dict = {}
    rep: list[int] = []
    for i, v in enumerate(ids):
        if v is None:
            rep.append(i)
        elif v in seen:
            rep += [seen[v], i]
        else:
            seen[v] = i
    rows = set(range(min(head, imp.height)))
    rows |= {i for i, x in enumerate(bad) if x == 1}
    rows |= set(rep)
    unknown = [i for i, k in enumerate(known) if k == 0 and bad[i] == 0]
    rows |= set(unknown[:1])
    dep = [i for i, v in enumerate(imp.get_column(imp.columns[-1]).to_list()) if v in (None, "NA")]
    rows |= set(dep[:1])
    rows_l = sorted(rows)[:cap]
    good = [k for k, i in enumerate(rows_l) if bad[i] == 0 and known[i] == 1]
    return rows_l, (good[0] if good else 0)


# ---------------------------------------------------------------- scenarios
def file_scenarios() -> list[tuple[str, Path]]:
    out = [("real", REPO / "legacy" / "data" / "cs-training.csv")]
    for grp, pat in (("fix2", "train_*"), ("fix2", "good"), ("fix2", "valid_unusual"), ("fix_G34", "train_*"),
                     ("fix_Q27_textid", "train_text_id"), ("fix_round5", "train_*")):
        for d in sorted((SCEN / grp).glob(pat)):
            out.append((f"{grp}/{d.name}", d / "cs-training.csv"))
    out.append(("fix_Q27", SCEN / "fix_Q27" / "cs-training.csv"))
    return out


def hand_frames() -> list[tuple[str, pl.DataFrame, str]]:
    f = pl.Float64
    base = {n: [1.0, 2.0, 3.0, 4.0] if n == "VAR1" else [0.0, 1.0, 0.0, 1.0] if n == "SeriousDlqin2yrs" else [5.0, 6.0, 7.0, 8.0]
            for n in N0}

    def fr(over: dict, names: dict | None = None, drop: tuple = (), add: dict | None = None) -> pl.DataFrame:
        cols = {**base, **over}
        df = pl.DataFrame({n: pl.Series(n, cols[n], dtype=(pl.String if any(isinstance(x, str) for x in cols[n]) else f))
                           for n in N0 if n not in drop})
        if add:
            df = df.with_columns([pl.Series(k, v) for k, v in add.items()])
        return df.rename(names or {})

    t33 = "1" * 33
    out = [
        ("ids_float_edges", fr({"VAR1": [0.0, -0.0, nan, nan]}), "-0.0 / 0.0 and two NaN ids"),
        ("ids_null", fr({"VAR1": [1.0, None, None, 2.0]}), "null ids"),
        ("ids_text", fr({"VAR1": ["7", "07", "7 ", " 7"]}), "text ids compared exactly"),
        ("ids_text_bad", fr({"VAR1": ["7", "x", None, "7"]}), ""),
        ("outcome_edges", fr({"SeriousDlqin2yrs": [-0.0, nan, 2.0, None]}), ""),
        ("outcome_text", fr({"SeriousDlqin2yrs": [" 1 ", "1.0", "true", "\t1"]}), ""),
        ("counts_edges", fr({"NumberOfTimes90DaysLate": [-0.0, 2.5, -1.0, inf],
                             "NumberOfOpenCreditLinesAndLoans": [nan, None, 1e300, 0.9999999999999999],
                             "NumberOfTime30-59DaysPastDueNotW": [-0.5, 0.5, -inf, 3.0]}), "NaN, inf, signed zero in the count columns"),
        ("counts_text", fr({"NumberOfTime60-89DaysPastDueNotW": ["2", "2.0", "2.5", "-0"],
                            "NumberOfTimes90DaysLate": ["1e2", "1E400", "", " 3"]}), ""),
        ("income_text", fr({"MonthlyIncome": [" NA ", "na", ".", ""]}), "no value stated"),
        ("income_text2", fr({"MonthlyIncome": ["abc", "-1", "-0", "1e3"]}), ""),
        ("income_text3", fr({"MonthlyIncome": [None, t33, " " + "1" * 32 + " ", "\tNA"]}), "33 characters; a tab is not stripped"),
        ("income_float", fr({"MonthlyIncome": [None, -0.0, -1e-300, nan]}), ""),
        ("income_float2", fr({"MonthlyIncome": [0.0, inf, -inf, 12.5]}), ""),
        ("dependents_text", fr({"NumberOfDependents": ["NA", "n a", "2.5", "Na"]}), ""),
        ("dependents_text2", fr({"NumberOfDependents": [None, "-1", " . ", "3"]}), ""),
        ("dependents_float", fr({"NumberOfDependents": [None, 2.5, -1.0, nan]}), ""),
        ("required_null", fr({"age": [None, 1.0, 1.0, 1.0], "DebtRatio": [1.0, None, 1.0, 1.0],
                              "RevolvingUtilizationOfUnsecuredL": [1.0, 1.0, None, 1.0],
                              "NumberRealEstateLoansOrLines": [1.0, 1.0, 1.0, None]}), ""),
        ("required_text", fr({"age": ["4 5", "45", " 45", "4" * 32], "DebtRatio": ["0x10", "+.5", "5.", "."]}), ""),
        ("names_case", fr({}, names={"age": "AGE", "MonthlyIncome": "monthlyincome", "VAR1": "var1",
                                     "NumberOfTime30-59DaysPastDueNotW": "NUMBEROFTIME30-59DAYSPASTDUENOTW"}), "case-blind names"),
        ("names_11", fr({}, drop=("age",)), "a missing column"),
        ("names_13", fr({}, add={"extra": [1.0, 2.0, 3.0, 4.0]}), "an extra column"),
        ("names_12_wrong", fr({}, drop=("DebtRatio",), add={"Other": [1.0, 2.0, 3.0, 4.0]}), "twelve columns, one of them not expected"),
        ("names_12_wrong_income", fr({}, drop=("MonthlyIncome",), add={"MonthlyIncome_": ["1", "2", "3", "4"]}), ""),
        ("zero_rows", fr({}).clear(), "twelve columns and no row"),
        ("zero_rows_text", fr({"MonthlyIncome": ["NA", "1", "2", "3"]}).clear(), ""),
        ("one_row", fr({})[[0]], ""),
        # asked by the reviewer (port-translator-4): NaN / inf alone in a count column of an otherwise valid frame
        ("counts_nan_only", fr({"NumberOfTimes90DaysLate": [nan, 1.0, 5.0, 6.0]}), "NaN in a count column: not a bad row"),
        ("counts_inf_only", fr({"NumberOfTimes90DaysLate": [inf, 1.0, 5.0, 6.0]}), "inf in a count column: not a bad row"),
        ("counts_neginf_only", fr({"NumberOfTimes90DaysLate": [-inf, 1.0, 5.0, 6.0]}), "-inf in a count column"),
    ]
    return out


def main() -> None:
    s = Suite("t2_check")
    groups: list[tuple[list[str], list[tuple], set[str]]] = [([], [], set())]
    notes: list[str] = []

    def add(term: str, cases: list[tuple], keys: set[str]):
        g = groups[-1]
        if sum(len(t) for t in g[0]) + len(term) > 7000 and g[0]:
            groups.append(([], [], set()))
            g = groups[-1]
        g[0].append(term)
        g[1].extend(cases)
        g[2].update(keys)

    print(f"{'scenario':42s} stop  columns_ok bad_rows duplicate_ids known_incomes  files   sub-frame")
    for name, csv in file_scenarios():
        real = real_run(csv)
        imp = real["imported"]
        whole = run_slice(imp)
        assert whole["stop"] == real["stop"] and whole["counters"] == real["counters"], (name, whole["counters"], real["counters"])
        assert same_frame(whole["credit_raw"], real["credit_raw"]), name
        assert (real["files"] == []) == real["stop"], (name, real["files"])
        rows, j = pick_rows(imp, whole["input_check"], head=(30 if name == "real" else 3), cap=(40 if name == "real" else 9))
        sub = imp[rows]
        term, cases, r = cases_of(name, sub, j)
        # the sub-frame keeps what makes the file stop or pass
        assert r["stop"] == real["stop"], (name, r["counters"], real["counters"])
        assert r["counters"][0] == real["counters"][0], name
        assert r["counters"][1] == min(real["counters"][1], sub.height) or real["counters"][1] > 9, name
        assert (r["counters"][1] != 0) == (real["counters"][1] != 0), name
        assert (r["counters"][2] != 0) == (real["counters"][2] != 0), name
        print(f"{name:42s} {int(real['stop'])}     " + " ".join(f"{c:>10d}" for c in real["counters"])
              + f"  {len(real['files'])}  rows {rows[:12]}{'...' if len(rows) > 12 else ''} j={j} sub counters {r['counters']}")
        add(term, cases, best32_keys(sub.rename({n: n for n in sub.columns})))
    for name, df, note in hand_frames():
        term, cases, r = cases_of("hand/" + name, df, 0, note)
        print(f"{'hand/' + name:42s} {int(r['stop'])}     " + " ".join(f"{c:>10d}" for c in r["counters"]))
        add(term, cases, best32_keys(df))
    # the import raised (credit_raw is None) and the table with no row (Pl.ofTable [] = [])
    none_real = real_run(None)
    none_slice = run_slice(None)
    assert none_real["stop"] and none_slice["stop"] and none_real["counters"] == none_slice["counters"] == (0, 1, 1, 0)
    assert none_real["files"] == []
    print(f"{'absent file (real run)':42s} 1     " + " ".join(f"{c:>10d}" for c in none_real["counters"]))
    for g in groups:
        s.ints(lets(best32_table(g[2])), " ++ ".join(g[0]), g[1])
    s.ints(lets("[]"), "[b (U none).1, ((U none).2.length : Int), b (U (some [])).1, ((U (some [])).2.length : Int)]",
           [("none/stop", UNIT, 1, {"note": "credit_raw is None (real run without the file, and the slice)"}),
            ("none/frame_width", UNIT, 0, {"note": "no frame in Python; the Lean returns []"}),
            ("empty/stop", UNIT, 1, {"note": "Pl.ofTable [] = []: no column; a header-only file stops in Python (zero_rows)"}),
            ("empty/frame_width", UNIT, 0, {"note": "as documented"})])
    s.notes = {UNIT: "real run on legacy/data and 30 scenario files (counters and stop asserted equal to the slice); "
                     "Lean on sub-frames, single rows and pairs; hand-made edge frames through the slice"}
    s.write()


if __name__ == "__main__":
    main()
