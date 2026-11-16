"""Update after verification, task T4: differential tests of
  def:fe_run_02b_medians_all   credit_risk/feature_engineering.py:179-186
  def:fe_run_04_imputed        credit_risk/feature_engineering.py:208-229

  cd migration/port-to-lean
  PYTHONPATH=../../port uv run --project ../../port python diffeval/units/t4_gen.py   -> diffeval/work/t4_units.*
  (eval_decl each input of work/t4_units.inputs.json on def:zz_carrier_f / zz_carrier_f, one output per
   line in work/t4_units.out.txt)
  PYTHONPATH=../../port uv run --project ../../port python diffeval/compare.py diffeval/work/t4_units.json diffeval/work/t4_units.out.txt

Each unit is evaluated DIRECTLY on its inputs (no chaining: other step items may be cleared).

Python side: the code of the package only, never a re-implementation.
  real   the REAL feature_engineering.run under a line tracer that copies the locals of `run` when
         it reaches the first line of a slice and when it has left its last line: the inputs and
         the result of the slice in that run. Runs: legacy/data/cs-training.csv (the file of
         judge/scenarios/edge_predict is byte-identical: asserted), judge/scenarios/fix_Q1,
         fix_Q14, fix2/train_no_known_income (the run stops at :128, before both slices: asserted)
         and the header with the first 40 data lines of the real file.
  slice  the source lines of the slice, read from the file at run time and executed verbatim with
         the module's globals (`run_slice`): (1) on the inputs of a real run restricted to what
         has to be typed into an eval_decl call; the result is asserted equal to the real run's
         (the whole frame, or the same rows of it); (2) on hand-made frames the upstream code of
         `run` cannot produce.
  What a restriction is: 02b reads one column of credit_raw_clean (MonthlyIncome), so the Lean
  input is that column alone; 04 works row by row on credit_cleaned, so the Lean input is a choice
  of rows of the real credit_cleaned with the real income_medians_all.
  NOT evaluated in Lean: 02b on the full real file and on the full fix_Q14 (the overall median
  needs the 150,000 / 3000 values of MonthlyIncome; an eval_decl input is typed by hand and echoed
  back). Instead: the real run on the header and the first 300 data lines of fix_Q14 (the age
  group 40-49 still has no known income) and on the first 40 of the real file.

Lean side: frames are built from short codes (FZ: non-negative whole numbers as Float64, -1 null;
FB: float bits, 1 null; IZ: integers, -9 null); the first digests of every call are those of the
input frames, compared with the Python frames, so the inputs are the same bit for bit.
"""
from __future__ import annotations

import contextlib
import io
import math
import sys
import tempfile
import textwrap
from pathlib import Path

import polars as pl

HERE = Path(__file__).resolve().parent
KIT_DIR = HERE.parents[1]            # migration/port-to-lean
REPO = HERE.parents[3]
sys.path.insert(0, str(HERE.parent))

import suite as suite_mod  # noqa: E402

suite_mod.CARRIERS["identity"] = ("def:zz_carrier_f", "zz_carrier_f")  # the carrier of the group

import compare as cmp  # noqa: E402
import leanterm as lt  # noqa: E402
from suite import Suite  # noqa: E402

from credit_risk import feature_engineering as fe  # noqa: E402

nan, inf = float("nan"), float("inf")
SCEN = REPO / "judge" / "scenarios"
REAL = REPO / "legacy" / "data"
SPLIT = KIT_DIR / "inputs" / "split_ids.csv"
SLICES = {"s02b": (179, 186, 'age_groups = pl.DataFrame({"age_group": [1, 2, 3, 4, 5]}'),
          "s04": (208, 229, "pl.coalesce(pl.col(\"median_income\"), pl.col(\"overall_median_income\"))")}
U02B, U04 = "fe_run_02b_medians_all", "fe_run_04_imputed"


# ---------------------------------------------------------------- running the code of the package
def slice_source(key: str) -> str:
    a, b, must = SLICES[key]
    src = "".join(Path(fe.__file__).read_text().splitlines(keepends=True)[a - 1:b])
    assert must in src, (key, "the slice does not hold the expected line: line numbers moved?")
    return textwrap.dedent(src)


def run_slice(key: str, env: dict) -> dict:
    a, b, _ = SLICES[key]
    ns = dict(vars(fe))
    ns.update(env)
    exec(compile(slice_source(key), f"{fe.__file__}:{a}-{b}", "exec"), ns)  # noqa: S102
    return ns


def traced(data_dir: Path) -> tuple[dict, str]:
    """The real feature_engineering.run on data_dir; locals of `run` at the slice boundaries."""
    snap: dict = {}

    def local(frame, event, arg):
        if event in ("line", "return"):
            for k, (a, b, _) in SLICES.items():
                if (k, "in") not in snap and event == "line" and frame.f_lineno >= a:
                    snap[k, "in"] = dict(frame.f_locals)
                if (k, "in") in snap and (k, "out") not in snap and (event == "return" or frame.f_lineno > b):
                    snap[k, "out"] = dict(frame.f_locals)
        return local

    def glob(frame, event, arg):
        return local if frame.f_code is fe.run.__code__ else None

    end = "completed"
    with tempfile.TemporaryDirectory() as out, contextlib.redirect_stdout(io.StringIO()):
        sys.settrace(glob)
        try:
            fe.run(data_dir, Path(out), split_ids=SPLIT)
        except Exception as ex:  # noqa: BLE001
            end = f"{type(ex).__name__}: {str(ex)[:70]}"
        finally:
            sys.settrace(None)
    return snap, end


def same(a: pl.DataFrame, b: pl.DataFrame) -> bool:
    return cmp.canon_frame(a) == cmp.canon_frame(b)


def dgf(df: pl.DataFrame) -> int:
    return cmp.digest(cmp.tokens(cmp.canon_frame(df)))


# ---------------------------------------------------------------- frames as short Lean terms
ENC = (
    "let FZ := fun (v : List Int) => (Pl.Col.f64 (v.map (fun (k : Int) => if k < 0 then none else some (Float.ofNat k.toNat))) : Pl.Col Float); "
    "let FB := fun (v : List Nat) => (Pl.Col.f64 (v.map (fun (b : Nat) => if b == 1 then none else some (Float.ofBits b.toUInt64))) : Pl.Col Float); "
    "let IZ := fun (v : List Int) => (Pl.Col.int (v.map (fun (k : Int) => if k == -9 then none else some k)) : Pl.Col Float); "
)
M2 = (
    "let m2 := fun (im rc : Pl.Frame Float) => [dg (tR im), dg (tR rc), dg (tR (fe_run_02b_medians_all im rc))]; ")
S4 = (
    "let s4 := fun (cc ia : Pl.Frame Float) => [dg (tR cc), dg (tR ia), dg (tR (fe_run_04_imputed cc ia))]; "
)


def _ints(vals) -> str:
    return "[" + ", ".join(str(v) if v >= 0 else f"({v})" for v in vals) + "]"


def enc_col(s: pl.Series) -> str:
    v = s.to_list()
    if s.dtype == pl.Float64:
        if all(x is None or (x == x and abs(x) != inf and x == int(x) and 0 <= x < 2**53 and math.copysign(1, x) > 0)
               for x in v):
            return "(FZ " + _ints([-1 if x is None else int(x) for x in v]) + ")"
        assert all(x is None or cmp.fbits(x) != 1 for x in v)
        return "(FB " + _ints([1 if x is None else cmp.fbits(x) for x in v]) + ")"
    if s.dtype.is_integer():
        assert all(x != -9 for x in v if x is not None)
        return "(IZ " + _ints([-9 if x is None else x for x in v]) + ")"
    return lt.lean_col(s)


def enc_frame(df: pl.DataFrame) -> str:
    return "(let f_ : Pl.Frame Float := [" + ", ".join(f"({lt.lean_str(n)}, {enc_col(df[n])})" for n in df.columns) + "]; f_)"


class Group:
    """One eval input: calls, each returning the digests of its inputs and of its result."""

    def __init__(self, lets: str):
        self.lets, self.calls, self.cases = lets, [], []

    def add02b(self, cid: str, im: pl.DataFrame, rc: pl.DataFrame, expected: pl.DataFrame):
        self.calls.append(f"m2 {enc_frame(im)} {enc_frame(rc)}")
        self.cases += [(f"{cid} / input income_medians", U02B + " (input)", dgf(im)),
                       (f"{cid} / input credit_raw_clean", U02B + " (input)", dgf(rc)),
                       (f"{cid} / income_medians_all", U02B, dgf(expected))]

    def add04(self, cid: str, cc: pl.DataFrame, ia: pl.DataFrame, expected: pl.DataFrame):
        self.calls.append(f"s4 {enc_frame(cc)} {enc_frame(ia)}")
        self.cases += [(f"{cid} / input credit_cleaned", U04 + " (input)", dgf(cc)),
                       (f"{cid} / input income_medians_all", U04 + " (input)", dgf(ia)),
                       (f"{cid} / credit_imputed", U04, dgf(expected))]

    def flush(self, s: Suite, limit: int = 4200):
        """One eval input per chunk of calls of at most `limit` characters (each input is typed by hand)."""
        chunk, cases, size = [], [], 0
        for i, call in enumerate(self.calls):
            if chunk and size + len(call) > limit:
                s.ints(ENC + self.lets, " ++ ".join(chunk), cases, table=False)
                chunk, cases, size = [], [], 0
            chunk.append(call)
            cases += self.cases[3 * i:3 * i + 3]
            size += len(call)
        if chunk:
            s.ints(ENC + self.lets, " ++ ".join(chunk), cases, table=False)
        self.calls, self.cases = [], []


# ---------------------------------------------------------------- cases
def case02b(g: Group, cid: str, im: pl.DataFrame, rc: pl.DataFrame, real_out: pl.DataFrame | None):
    """The slice on (income_medians, the MonthlyIncome column); asserted equal to the real run's result."""
    ns = run_slice("s02b", {"income_medians": im, "credit_raw_clean": rc})
    out = ns["income_medians_all"]
    if real_out is not None:
        assert same(out, real_out), cid
    g.add02b(cid, im, rc, out)
    return out


def case04(g: Group, cid: str, cc: pl.DataFrame, ia: pl.DataFrame, real_rows: pl.DataFrame | None):
    ns = run_slice("s04", {"credit_cleaned": cc, "income_medians_all": ia})
    out = ns["credit_imputed"]
    if real_rows is not None:
        assert same(out, real_rows), cid
    g.add04(cid, cc, ia, out)
    return out


def pick_rows(cc: pl.DataFrame, per: int) -> list[int]:
    """Row numbers of credit_cleaned: for each age group, the first `per` rows with a missing
    income and the first `per` with a known one (frame order)."""
    idx = []
    for grp in (1, 2, 3, 4, 5):
        for miss in (1, 0):
            rows = [i for i, (a, m) in enumerate(zip(cc["age_group"].to_list(), cc["MonthlyIncome_missing"].to_list()))
                    if a == grp and m == miss][:per]
            idx += rows
    return sorted(idx)


def f64(vals) -> pl.Series:
    return pl.Series("x", [None if v is None else float(v) for v in vals], dtype=pl.Float64)


def i32(vals) -> pl.Series:
    return pl.Series("x", vals, dtype=pl.Int32)


def medians(groups, vals, **extra) -> pl.DataFrame:
    return pl.DataFrame({"age_group": i32(groups), "median_income": f64(vals), **extra})


def cleaned(rows: list[tuple]) -> pl.DataFrame:
    """A hand-made credit_cleaned: (age_group, MonthlyIncome, MonthlyIncome_missing) per row; the
    other twelve columns carry values that tell the columns apart."""
    n = len(rows)
    k = [float(i + 1) for i in range(n)]
    return pl.DataFrame({
        "VAR1": k, "SeriousDlqin2yrs": [float(i % 2) for i in range(n)],
        "RevolvingUtilizationOfUnsecuredL": f64([0.766126609, None, nan, 0.1, -0.0, 1e300, 2.5][:n] + [0.5] * max(0, n - 7)),
        "age": [20.0 + 7 * i for i in range(n)],
        "NumberOfTime30-59DaysPastDueNotW": [x + 10 for x in k], "DebtRatio": f64([0.802982129, 0.07, None, nan, inf, 3.0, 0.29][:n] + [1.5] * max(0, n - 7)),
        "NumberOfOpenCreditLinesAndLoans": [x + 20 for x in k], "NumberOfTimes90DaysLate": [x + 30 for x in k],
        "NumberRealEstateLoansOrLines": [x + 40 for x in k], "NumberOfTime60-89DaysPastDueNotW": [x + 50 for x in k],
        "MonthlyIncome": f64([r[1] for r in rows]), "NumberOfDependents": [x + 60 for x in k],
        "age_group": i32([r[0] for r in rows]),
        "MonthlyIncome_missing": pl.Series([r[2] for r in rows], dtype=pl.Int64),
        "Dependents_missing": pl.Series([i % 2 for i in range(n)], dtype=pl.Int64),
    })


def build() -> Suite:
    s = Suite("t4_units")
    report = []
    assert (REAL / "cs-training.csv").read_bytes() == (SCEN / "edge_predict" / "cs-training.csv").read_bytes()

    # the first 40 data lines of the real file, verbatim
    tmp = Path(tempfile.mkdtemp(prefix="t4_"))
    with (REAL / "cs-training.csv").open() as fh:
        (tmp / "cs-training.csv").write_text("".join(next(fh) for _ in range(41)))

    tmp14 = Path(tempfile.mkdtemp(prefix="t4_"))
    with (SCEN / "fix_Q14" / "cs-training.csv").open() as fh:
        (tmp14 / "cs-training.csv").write_text("".join(next(fh) for _ in range(301)))

    runs = [("real cs-training.csv (= edge_predict/cs-training.csv)", REAL), ("fix_Q1", SCEN / "fix_Q1"),
            ("fix_Q14", SCEN / "fix_Q14"), ("fix2/train_no_known_income", SCEN / "fix2" / "train_no_known_income"),
            ("real, first 40 rows", tmp), ("fix_Q14, first 300 rows", tmp14)]
    g02, g04 = Group(M2), Group(S4)
    for name, d in runs:
        snap, end = traced(d)
        reached = sorted({k for k, _ in snap})
        report.append(f"{name}: run {end}; slices reached: {reached}")
        if not reached:
            assert name == "fix2/train_no_known_income" and end.startswith("ValueError"), (name, end)
            continue
        i2, o2, i4, o4 = snap["s02b", "in"], snap["s02b", "out"], snap["s04", "in"], snap["s04", "out"]
        rc_full, im, ima = i2["credit_raw_clean"], i2["income_medians"], o2["income_medians_all"]
        cc, ci = i4["credit_cleaned"], o4["credit_imputed"]
        assert same(i4["income_medians_all"], ima)
        # the slices on the full frames ARE what the real run did
        assert same(run_slice("s02b", {"income_medians": im, "credit_raw_clean": rc_full})["income_medians_all"], ima)
        assert same(run_slice("s04", {"credit_cleaned": cc, "income_medians_all": ima})["credit_imputed"], ci)
        report.append(f"   rows {rc_full.height}; income_medians {im.rows()}; income_medians_all {ima.rows()}")
        # 02b: the MonthlyIncome column alone
        rc = rc_full.select("MonthlyIncome")
        if rc.height <= 300:
            case02b(g02, f"real run, {name} ({rc.height} rows, column MonthlyIncome)", im, rc, ima)
        else:
            report.append(f"   02b NOT evaluated in Lean on this run: {rc.height} values of MonthlyIncome cannot be typed into a call")
        # 04: all rows, or a choice of rows of credit_cleaned
        if "first" in name:
            report.append("   04 not taken from this truncated run (the full run of the same file is used)")
        elif cc.height <= 2:
            case04(g04, f"real run, {name} (all {cc.height} rows)", cc, ima, ci)
        else:
            idx = pick_rows(cc, 1)
            sub, exp = cc[idx], ci[idx]
            miss = sub.filter(pl.col("MonthlyIncome_missing") == 1).height
            case04(g04, f"real run, {name} (rows {idx[0] + 1}..{idx[-1] + 1}: {len(idx)} of {cc.height}, {miss} with a missing income)",
                   sub, ima, exp)
            report.append(f"   04 rows chosen (0-based): {idx}")

    # ---- hand-made inputs, the slice's source lines executed verbatim
    e_i = medians([], [])
    mi = lambda vals: pl.DataFrame({"MonthlyIncome": f64(vals)})  # noqa: E731
    hand02 = [
        ("no known income: income_medians without a row, every MonthlyIncome null", e_i, mi([None, None, None])),
        ("credit_raw_clean without a row", e_i, mi([])),
        ("one known income", medians([2], [5000.0]), mi([None, 5000.0])),
        ("even count, interpolated: 1016.85 and 7098.24", medians([1, 5], [1016.85, 7098.24]), mi([7098.24, None, 1016.85])),
        ("even count, equal middle values", medians([3], [2500.0]), mi([2500.0, 1.0, 2500.0, 9e9])),
        ("a NaN income is a value, the greatest", medians([4, 1], [nan, 2.0]), mi([nan, 1.0, 3.0, None])),
        ("NaN in the middle", medians([4], [nan]), mi([nan, 1.0, nan])),
        ("infinite incomes of both signs", medians([1], [0.5]), mi([inf, -inf])),
        ("groups in order 5, 3, 1; groups 2 and 4 absent", medians([5, 3, 1], [50.5, 30.25, 10.125]), mi([10.125, 30.25, 50.5, 0.1, 0.2])),
        ("income_medians with two rows for group 2 and a null key", medians([2, None, 2, 9], [1.0, 2.0, 3.0, 4.0]), mi([4.0, 1.0])),
        ("income_medians with a third column and its own overall_median_income (replaced in place)",
         medians([1, 4], [1.5, None], overall_median_income=["a", "b"], extra=f64([7.0, 8.0])), mi([0.3, 0.1, 0.2])),
        ("Int64 key in income_medians", pl.DataFrame({"age_group": pl.Series([3, 5], dtype=pl.Int64), "median_income": f64([3.0, 5.0])}),
         mi([3.0, 5.0, 4.0, None, 4.5])),
    ]
    for cid, im, rc in hand02:
        out = case02b(g02, "hand: " + cid, im, rc, None)
        report.append(f"   02b hand [{cid}] -> {out.rows()}")

    full_ia = pl.DataFrame({"age_group": i32([1, 2, 3, 4, 5]), "median_income": f64([3000.0, None, 5400.5, nan, None]),
                            "overall_median_income": f64([4100.25] * 5)})
    rows7 = [(1, None, 1), (2, None, 1), (3, 100.0, 0), (4, None, 1), (5, 700.0, 0), (2, 250.0, 1), (5, None, 0)]
    hand04 = [
        ("group medians present, null (overall used), NaN (kept); flag 1 with an income; flag 0 with a null income",
         cleaned(rows7), full_ia),
        ("no known income: both medians null on every row",
         cleaned(rows7[:4]), pl.DataFrame({"age_group": i32([1, 2, 3, 4, 5]), "median_income": f64([None] * 5),
                                           "overall_median_income": f64([None] * 5)})),
        ("age groups of credit_cleaned absent from income_medians_all (7) : null income",
         cleaned([(7, None, 1), (1, None, 1), (7, 5.0, 0)]), full_ia.head(1)),
        ("income_medians_all without a row", cleaned(rows7[:3]), full_ia.clear()),
        ("two rows of income_medians_all for group 2: the left row is repeated",
         cleaned(rows7[:3]), pl.DataFrame({"age_group": i32([2, 3, 2]), "median_income": f64([None, 1.0, 9.0]),
                                           "overall_median_income": f64([4.0, 4.0, nan])})),
        ("flag values other than 0 and 1 (2, null)",
         cleaned([(1, 10.0, 2), (1, None, None), (2, None, 1)]), full_ia),
    ]
    for cid, cc, ia in hand04:
        out = case04(g04, "hand: " + cid, cc, ia, None)
        report.append(f"   04 hand [{cid}] -> monthly_income {out['monthly_income'].to_list()} ({out.height} rows)")

    g02.flush(s)
    g04.flush(s)
    s.notes = {
        U02B: "evaluated directly on (income_medians, the MonthlyIncome column of credit_raw_clean); real = the locals of the real "
              "feature_engineering.run at the slice boundaries (line tracer): fix_Q1, the first 300 rows of fix_Q14, the first 40 rows of "
              "the real file; the full real file (150,000 values) and the full fix_Q14 (3000) are too long for a typed call: not "
              "evaluated in Lean; hand = the "
              "slice's source lines executed verbatim",
        U04: "evaluated directly on (credit_cleaned, income_medians_all); real = the locals of the real feature_engineering.run "
             "at the slice boundaries: all rows of fix_Q1; a choice of rows (per age group one with and one without an income) of the full "
             "real run and of the full fix_Q14, with the run's own "
             "income_medians_all (slice on those rows asserted equal to the same rows of the real result); hand = the slice's "
             "source lines executed verbatim",
    }
    s.write()
    (suite_mod.WORK / "t4_units.report.txt").write_text("\n".join(report) + "\n")
    print("\n".join(report))
    return s


if __name__ == "__main__":
    build()
