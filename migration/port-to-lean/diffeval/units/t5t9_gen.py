"""Update after the verification round (2026-11-16), tasks T5 and T9: differential tests of
  def:fe_run_05_features        credit_risk/feature_engineering.py:234-336
  def:predict_run_05_features   credit_risk/predict.py:277-372
against what the PORT produced in real runs.

  cd migration/port-to-lean
  PYTHONPATH=../../port uv run --project ../../port python diffeval/units/t5t9_gen.py
      -> diffeval/work/t5t9_fe, t5t9_pr (.json + .inputs.json)
  (eval_decl each input of work/t5t9_fe.inputs.json on def:zz_carrier_f / zz_carrier_f and of
   work/t5t9_pr.inputs.json on def:zz_carrier_p / zz_carrier_p; save the outputs one per line as
   work/t5t9_<suite>.out.txt)
  PYTHONPATH=../../port uv run --project ../../port python diffeval/compare.py diffeval/work/t5t9_<suite>.json diffeval/work/t5t9_<suite>.out.txt

Python side (the code of the package, never a re-implementation):
  real   the REAL feature_engineering.run / predict.run on the files of the scenario; a profile hook
         copies the locals of `run` when it returns: `credit_imputed` / `test_imputed` are the input
         of the slice and `credit_features` / `test_features` its result in the real run (neither
         name is rebound after the slice).
  slice  the source lines of the slice, read from the file at run time (verbatim, dedented) and
         executed with the module's globals (`run_slice`). Used (1) on the whole input of the real
         run: the result is asserted equal to the real result, frame for frame; (2) on the chosen
         rows of the real input restricted to the nine columns the slice reads: the result is
         asserted equal to the same rows of the real result, column for column (the slice works
         row by row and reads only those nine columns); (3) on hand-made rows that the code before
         the slice cannot produce (NaN, infinities, a negative zero, num_dependents below zero).

Lean side. The input must be typed into an eval_decl call, so only chosen rows of a real run are
evaluated (all rows when the run has few). The rows are chosen so that every combination of the
branches the slice takes in the run is present (see `signature`), plus the rows holding the
smallest and the largest value of every input column, plus a seeded sample. The frame is built in
Lean from integer codes (see `code`); the digest of the Lean frame is compared with the digest of
the Python frame first, so the inputs are the same bit for bit. The unit is evaluated with
full = true and full = false (Python cannot choose the reduction shape: both are compared with
the one Python result); one digest for each whole result and one for each column of it.
"""
from __future__ import annotations

import contextlib
import io
import json
import math
import random
import struct
import sys
import textwrap
from pathlib import Path

import polars as pl

HERE = Path(__file__).resolve().parent
KITDIR = HERE.parents[1]                      # migration/port-to-lean
REPO = HERE.parents[3]
sys.path.insert(0, str(HERE.parent))

import suite as suite_mod  # noqa: E402
import compare as cmp  # noqa: E402
from suite import Suite  # noqa: E402

from credit_risk import feature_engineering as fe  # noqa: E402
from credit_risk import predict as pr  # noqa: E402

nan, inf = float("nan"), float("inf")
WORK = HERE.parent / "work" / "t5t9"
SCEN = REPO / "judge" / "scenarios"
DATA = REPO / "legacy" / "data"
SPLIT = KITDIR / "inputs" / "split_ids.csv"
READ = ["age", "monthly_income", "num_dependents", "num_late_30_59", "num_late_60_89", "num_late_90_plus",
        "credit_utilization", "debt_ratio", "num_credit_lines"]
DECIMAL = {"credit_utilization", "debt_ratio"}  # the two columns computed as `raw * 100` by step 04
SLICES = {
    "fe": (fe, 234, 336, "credit_imputed", "credit_features", "fe_run_05_features", ("def:zz_carrier_f", "zz_carrier_f")),
    "pr": (pr, 277, 372, "test_imputed", "test_features", "predict_run_05_features", ("def:zz_carrier_p", "zz_carrier_p")),
}
MUST = ['pl.col("flag_very_high_utilization")', '.then(pl.col("age") * sas_compat.sas_log(pl.col("monthly_income")))',
        'utilization_debt_interaction=pl.col("credit_utilization") * pl.col("debt_ratio")']


# ---------------------------------------------------------------- running the code of the package
def slice_source(key: str) -> str:
    mod, a, b = SLICES[key][:3]
    lines = Path(mod.__file__).read_text().splitlines(keepends=True)
    src = "".join(lines[a - 1:b])
    for m in MUST:
        assert m in src, (key, m, "the slice does not hold the changed line: line numbers moved?")
    # the slice is exactly the statements between the step before and the step after
    assert lines[a - 2].lstrip().startswith("#") and lines[b].strip() == "", (key, lines[a - 2], lines[b])
    return textwrap.dedent(src)


def run_slice(key: str, frame: pl.DataFrame) -> pl.DataFrame:
    mod, a, b, vin, vout = SLICES[key][:5]
    ns = dict(vars(mod))
    ns[vin] = frame
    exec(compile(slice_source(key), f"{mod.__file__}:{a}-{b}", "exec"), ns)  # noqa: S102
    return ns[vout]


def _profiled(code, call) -> tuple[dict | None, str]:
    rec: dict = {"locals": None}

    def prof(fr, event, arg):
        if event == "return" and fr.f_code is code:
            rec["locals"] = dict(fr.f_locals)

    out = io.StringIO()
    err = ""
    sys.setprofile(prof)
    try:
        with contextlib.redirect_stdout(out):
            call()
    except Exception as e:  # noqa: BLE001  a stopped run raises ValueError; the locals are still copied
        err = f"{type(e).__name__}: {e}"
    finally:
        sys.setprofile(None)
    return rec["locals"], err


def real_fe(name: str, data_dir: Path) -> tuple[dict, str]:
    out = WORK / name
    out.mkdir(parents=True, exist_ok=True)
    return _profiled(fe.run.__code__, lambda: fe.run(data_dir, out, split_ids=SPLIT))


def real_pr(name: str, data_dir: Path, input_dir: Path, medians: Path) -> tuple[dict, str]:
    out = WORK / name / "predict"
    out.mkdir(parents=True, exist_ok=True)
    return _profiled(pr.run.__code__, lambda: pr.run(input_dir, out, data_dir=data_dir, income_medians=medians))


def same(a: pl.DataFrame, b: pl.DataFrame) -> bool:
    return cmp.canon_frame(a) == cmp.canon_frame(b)


def dgf(df: pl.DataFrame) -> int:
    return cmp.digest(cmp.tokens(cmp.canon_frame(df)))


def dgc(df: pl.DataFrame, n: str) -> int:
    return cmp.digest(cmp.tok_str(n) + cmp.tokens(cmp.canon_series(df.get_column(n))))


# ---------------------------------------------------------------- choosing rows of a real run
SIG = ["credit_util_category", "debt_category", "age_category", "has_delinquency", "has_serious_delinquency",
       "flag_high_utilization", "flag_very_high_utilization", "flag_high_debt_ratio", "flag_very_high_debt_ratio",
       "flag_recent_late_payments", "flag_serious_delinquency", "flag_multiple_delinquencies", "flag_low_income",
       "flag_many_dependents", "flag_few_credit_lines", "total_risk_flags", "financial_health"]


def signature(res: pl.DataFrame) -> pl.DataFrame:
    """One row per row of the result: the branch each expression of the slice took."""
    return res.select(
        *[pl.col(c) for c in SIG],
        inc_null=pl.col("monthly_income").is_null(),
        inc_pos=(pl.col("monthly_income") > 0).fill_null(False),
        inc1_pos=(pl.col("monthly_income") + 1 > 0).fill_null(False),
        dep_pos=(pl.col("num_dependents") > 0).fill_null(False),
        util_capped=(pl.col("credit_utilization") > 200).fill_null(False),
        debt_capped=(pl.col("debt_ratio") > 500).fill_null(False),
        late_null=pl.col("log_total_late_payments").is_null(),
        lines_null=pl.col("log_num_credit_lines").is_null(),
    )


def choose(inp: pl.DataFrame, res: pl.DataFrame, n_sig: int, n_rand: int, seed: int) -> tuple[list[int], dict]:
    h = inp.height
    sig = signature(res).with_row_index("i")
    first = sig.group_by([c for c in sig.columns if c != "i"], maintain_order=True).agg(pl.col("i").first(), n=pl.len())
    by_freq = first.sort("n", descending=True, maintain_order=True)
    rows: list[int] = []
    # the smallest and the largest value of every input column (first row holding it)
    for c in READ:
        s = inp.get_column(c)
        for v in (s.min(), s.max()):
            if v is not None:
                rows.append(int(inp.with_row_index("i").filter(pl.col(c) == v).get_column("i")[0]))
        if s.null_count():
            rows.append(int(inp.with_row_index("i").filter(pl.col(c).is_null()).get_column("i")[0]))
    # every value each branch column takes in the run (first row holding it)
    for c in sig.columns:
        if c != "i":
            rows += sig.group_by(c, maintain_order=True).agg(pl.col("i").first()).get_column("i").to_list()
    # the rarest signatures first (the common ones are also met by the sample)
    rare = by_freq.get_column("i").to_list()[::-1]
    rows += rare[:n_sig]
    rng = random.Random(seed)
    rows += rng.sample(range(h), min(n_rand, h))
    rows = sorted(set(rows))
    covered = sig.filter(pl.col("i").is_in(rows)).select([c for c in sig.columns if c != "i"]).unique().height
    return rows, {"rows": h, "signatures": first.height, "signatures_covered": covered, "chosen": len(rows)}


# ---------------------------------------------------------------- frames as short Lean terms
def fbits(x: float) -> int:
    return struct.unpack("<Q", struct.pack("<d", float(x)))[0]


def _dec(v: float) -> tuple[int, int] | None:
    """(m, e) with float(f'{m}e-{e}') == v bit for bit, m >= 0, e < 32; None when there is none."""
    if v != v or v in (inf, -inf) or v < 0 or (v == 0 and fbits(v) != 0):
        return None
    from decimal import Decimal

    _, digits, exp = Decimal(repr(v)).as_tuple()
    m = int("".join(map(str, digits)))
    if exp > 0:
        m, exp = m * 10 ** exp, 0
    e = -exp
    if e >= 32 or fbits(float(f"{m}e-{e}")) != fbits(v):
        return None
    return m, e


def gcode(v: float | None, times100: bool) -> int:
    """General code. 0: null. 4 * (m * 32 + e) + 1: the decimal m * 10^-e times 100.0 (the way step
    04 computes the two percentage columns). 4 * (m * 32 + e) + 2: the decimal m * 10^-e.
    4 * bits + 3: the bit pattern."""
    if v is None:
        return 0
    if times100 and v == v and abs(v) != inf:
        for d in range(1, 18):
            c = float(f"{v / 100:.{d}g}")
            if fbits(c * 100.0) == fbits(v):
                me = _dec(c)
                if me is not None and me[0] < 2 ** 60:
                    return 4 * (me[0] * 32 + me[1]) + 1
                break
    me = _dec(v)
    if me is not None and me[0] < 2 ** 60:  # a longer decimal is shorter as its bit pattern
        return 4 * (me[0] * 32 + me[1]) + 2
    return 4 * fbits(v) + 3


def code(v: float | None, col: str) -> int:
    """Percentage columns: the general code. Other columns: 2 * n + 1 for a whole number n >= 0,
    else 2 * (general code)."""
    if col in DECIMAL:
        return gcode(v, True)
    if v is not None and v == v and 0 <= v < 2 ** 40 and v == int(v) and fbits(v) != fbits(-0.0):
        return 2 * int(v) + 1
    return 2 * gcode(v, False)


CODEC = (
    "let G := fun (c : Nat) => (if c == 0 then none else (let q := c / 4; if c % 4 == 1 then some (Float.ofScientific (q / 32) true (q % 32) * 100.0) "
    "else if c % 4 == 2 then some (Float.ofScientific (q / 32) true (q % 32)) else some (Float.ofBits q.toUInt64)) : Option Float); "
    "let W := fun (c : Nat) => (if c % 2 == 1 then some (Float.ofNat (c / 2)) else G (c / 2) : Option Float); "
    "let mkF := fun (D : Array Nat) => (let n := D.size / 9; let cl := fun (j : Nat) (g : Nat → Option Float) => "
    "Pl.Col.f64 ((List.range n).map (fun (i : Nat) => g (D.getD (i * 9 + j) 0))); "
    '([("age", cl 0 W), ("monthly_income", cl 1 W), ("num_dependents", cl 2 W), ("num_late_30_59", cl 3 W), '
    '("num_late_60_89", cl 4 W), ("num_late_90_plus", cl 5 W), ("credit_utilization", cl 6 G), ("debt_ratio", cl 7 G), '
    '("num_credit_lines", cl 8 W)] : Pl.Frame Float)); '
)


def lean_rows(df: pl.DataFrame) -> str:
    assert df.columns == READ and all(df.schema[c] == pl.Float64 for c in READ), df.schema
    return ",".join(str(code(v, c)) for row in df.iter_rows() for v, c in zip(row, READ, strict=True))


class Group:
    """The frames of one eval_decl input: `ev #[codes]` for each, results concatenated."""

    def __init__(self, s: Suite, key: str):
        self.s, self.key, self.terms, self.cases = s, key, [], []

    def add(self, label: str, inp9: pl.DataFrame, expected: pl.DataFrame, **extra):
        unit = SLICES[self.key][5]
        got = run_slice(self.key, inp9)
        assert same(got, expected), (label, "the slice on the chosen rows differs from the real result on those rows")
        self.terms.append(f"ev #[{lean_rows(inp9)}]")
        tag = f"{label} ({inp9.height} rows)"
        self.cases += [(f"{tag}: input frame", unit, dgf(inp9), extra), (f"{tag}: result full=true", unit, dgf(expected), extra),
                       (f"{tag}: result full=false", unit, dgf(expected), extra)]
        self.cases += [(f"{tag}: column {n}", unit, dgc(expected, n), extra) for n in expected.columns]

    def flush(self):
        if not self.terms:
            return
        unit = SLICES[self.key][5]
        lets = CODEC + (f"let ev := fun (D : Array Nat) => (let f := mkF D; let o := {unit} true f; let o2 := {unit} false f; "
                        "[dg (tR f), dg (tR o), dg (tR o2)] ++ o.map (fun (p : String × Pl.Col Float) => dg (tS p.1 ++ tC p.2)) : List Int); ")
        self.s.ints(lets, " ++ ".join(self.terms), self.cases)
        self.terms, self.cases = [], []


# ---------------------------------------------------------------- hand-made rows (slice only)
#   age    income  deps  l30   l60   l90   util    debt    lines
EDGES = [
    (40.0, 5000.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0),            # fix_Q7 row
    (25.0, 0.0, 0.0, 0.0, 0.0, 0.0, 100.0, 100.0, 0.0),           # income 0: the otherwise branch, log(1) = 0
    (25.0, -0.0, 0.0, 0.0, 0.0, 0.0, 100.0, 100.0, 0.0),          # -0.0 is not above 0
    (25.0, -1.0, 0.0, 0.0, 0.0, 0.0, 30.0, 30.0, 2.0),            # income -1: income + 1 = 0, log_monthly_income null
    (25.0, -0.5, 1.0, 0.0, 0.0, 0.0, 50.0, 43.0, 3.0),            # income + 1 = 0.5 > 0
    (25.0, -2.0, 2.0, 0.0, 0.0, 0.0, 75.0, 60.0, 1.0),
    (None, None, 3.0, None, None, None, None, None, None),        # nulls
    (nan, nan, 0.0, nan, 0.0, 0.0, nan, nan, nan),                # NaN: above 0 in the polars order
    (35.0, None, 0.0, 1.0, None, 2.0, 200.0, 500.0, 2.0),         # null income: else branch; caps exactly
    (50.0, inf, 4.0, 0.0, 1.0, 0.0, inf, 0.0, inf),               # inf * 0.0 = NaN product
    (65.0, 2500.0, 0.5, 3.0, 0.0, 0.0, -inf, -inf, 5.0),
    (64.0, 2499.0, 0.0, 0.0, 0.0, 3.0, 1e200, 1e200, 4.0),        # product overflows to inf
    (24.0, 1e-320, 0.0, 0.0, 0.0, 0.0, 1e-200, 1e-200, 2.0),      # subnormal income, product underflows to 0
    (0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 75.00000000000001, 43.00000000000001, 2.0000000000000004),
    (-1.0, 0.5, -2.0, -1.0, -1.0, -1.0, -5.0, -5.0, -1.0),        # negative counts; num_dependents + 1 = -1
    (34.0, 2500.0000000000005, 3.0, 2.0, 1.0, 0.0, 100.0, 60.0, 2.0),
    (49.0, 7000.0, 2.0, 1.0, 1.0, 1.0, 100.00000000000001, 60.00000000000001, 30.0),
    (nan, 3000.0, 0.0, 0.0, 0.0, 0.0, 10.0, 10.0, 10.0),          # NaN age with an income
    (45.0, nan, 0.0, 0.0, 0.0, 0.0, 10.0, 10.0, 10.0),            # NaN income with an age
    (None, 3000.0, 0.0, 0.0, 0.0, 0.0, 10.0, 10.0, 10.0),         # null age with an income
]


def edges_frame() -> pl.DataFrame:
    return pl.DataFrame(EDGES, schema={c: pl.Float64 for c in READ}, orient="row")


# ---------------------------------------------------------------- scenarios
def real_case(g: Group, key: str, label: str, L: dict | None, err: str, n_sig: int, n_rand: int, seed: int, report: list):
    vin, vout = SLICES[key][3:5]
    if L is None or vin not in L or vout not in L:
        report.append({"scenario": label, "unit": SLICES[key][5], "reached": False, "error": err})
        print(f"[{label}] the run did not reach the slice: {err}")
        return
    inp, res = L[vin], L[vout]
    assert same(run_slice(key, inp), res), (label, "the slice on the whole real input differs from the real result")
    created = [c for c in res.columns if c not in inp.columns]
    assert res.columns == inp.columns + created and same(res.select(inp.columns), inp), label
    assert all(inp.schema[c] == pl.Float64 for c in READ), (label, inp.schema)
    if inp.height:
        rows, info = choose(inp, res, n_sig, n_rand, seed)
    else:
        rows, info = [], {"rows": 0, "signatures": 0, "signatures_covered": 0, "chosen": 0}
    inp9 = inp.select(READ)[rows] if rows else inp.select(READ).clear()
    exp = res.select(READ + created)[rows] if rows else res.select(READ + created).clear()
    zero_div = inp9.filter(pl.col("num_dependents") + 1 == 0).height
    info.update({"scenario": label, "unit": SLICES[key][5], "reached": True, "error": err, "created_columns": len(created),
                 "rows_with_zero_divisor": inp.filter(pl.col("num_dependents") + 1 == 0).height,
                 "null_income": inp.get_column("monthly_income").null_count(),
                 "income_not_above_0": inp.filter(pl.col("monthly_income") <= 0).height})
    report.append(info)
    print(f"[{label}] {info}")
    assert zero_div == 0, label
    g.add(label, inp9, exp)


def build(only: set[str] | None = None) -> None:
    want = lambda n: only is None or n in only  # noqa: E731
    report: list = []
    real = WORK / "real"          # the real runs of feature engineering and train (see the module docstring of the run log)
    if want("fe"):
        s = Suite("t5t9_fe")
        s.item, s.decl = SLICES["fe"][6]
        g = Group(s, "fe")
        L, err = real_fe("real_fe", DATA)
        real_case(g, "fe", "real cs-training.csv", L, err, 60, 30, 5, report)
        g.flush()
        for label, d, ns, nr in (("fix_Q7", SCEN / "fix_Q7", 10, 10), ("fix_Q9", SCEN / "fix_Q9", 10, 10),
                                 ("fix_G34/income_zero", SCEN / "fix_G34" / "income_zero", 10, 6)):
            L, err = real_fe(label.replace("/", "_") + "_fe", d)
            real_case(g, "fe", label, L, err, ns, nr, 7, report)
        e = edges_frame()
        g.add("hand-made rows (slice)", e, run_slice("fe", e))
        z = e.clear()
        g.add("hand-made frame with no row (slice)", z, run_slice("fe", z))
        g.flush()
        s.notes = {"fe_run_05_features": NOTE}
        s.write()
    if want("pr"):
        s = Suite("t5t9_pr")
        s.item, s.decl = SLICES["pr"][6]
        g = Group(s, "pr")
        L, err = real_pr("real_pr", DATA, real, real / "income_medians.csv")
        real_case(g, "pr", "real cs-test.csv", L, err, 60, 30, 9, report)
        g.flush()
        # fix2/q14_negative_real is named by the plan: the port stops in the input check on it (both
        # files), so the slice is not reached; it stays in the list so that the report records it.
        # fix_G34/income_zero (a test file with incomes of 0) is evaluated in its place.
        for label, d, ns, nr in (("fix_Q7", SCEN / "fix_Q7", 10, 10), ("fix_Q9", SCEN / "fix_Q9", 10, 10),
                                 ("fix2/q14_negative_real", SCEN / "fix2" / "q14_negative_real", 10, 6),
                                 ("fix_G34/income_zero", SCEN / "fix_G34" / "income_zero", 10, 6)):
            nm = label.replace("/", "_")
            # the medians of the scenario's own training file (a real feature-engineering run on it);
            # the model files of the real run (the slice is before the scoring)
            _, ferr = real_fe(nm + "_pr", d)
            med = WORK / (nm + "_pr") / "income_medians.csv"
            if not med.exists():
                print(f"[{label}] feature engineering wrote no income_medians.csv ({ferr}): medians of the real run used")
                med = real / "income_medians.csv"
            L, err = real_pr(nm + "_pr", d, real, med)
            real_case(g, "pr", label, L, err, ns, nr, 11, report)
        e = edges_frame()
        g.add("hand-made rows (slice)", e, run_slice("pr", e))
        g.flush()
        s.notes = {"predict_run_05_features": NOTE}
        s.write()
    (WORK / "report.json").write_text(json.dumps(report, indent=1))


NOTE = ("real run, locals of `run` copied at return; the slice (source lines executed verbatim) equals the real result on the "
        "whole input; Lean evaluated on chosen rows (every value of every branch column, the rarest branch combinations, the "
        "extremes of each input column, a seeded sample; all rows of a small run), input frame compared first; full = true and false; "
        "hand-made rows with NaN, infinities, -0.0 and nulls through the slice")

if __name__ == "__main__":
    build(set(sys.argv[1:]) or None)
