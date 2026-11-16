"""Review of T4 by port-translator-6 (2026-11-16): independent probes of
  def:fe_run_02b_medians_all   credit_risk/feature_engineering.py:179-186
  def:fe_run_04_imputed        credit_risk/feature_engineering.py:208-229
on hand-made inputs inside their preconditions. The Python side executes the source lines of the
package verbatim (read from the file at run time); the Lean side is evaluated through
def:zz_carrier_f; one digest per input frame and per result.

  cd migration/port-to-lean
  PYTHONPATH=../../port uv run --project ../../port python experiments/rev_t4_probe.py
      -> diffeval/work/rev_t4.json, rev_t4.inputs.json
"""
from __future__ import annotations

import struct
import sys
import textwrap
from pathlib import Path

import polars as pl

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "diffeval"))

import compare as cmp  # noqa: E402
from suite import Suite  # noqa: E402

from credit_risk import feature_engineering as fe  # noqa: E402

nan, inf = float("nan"), float("inf")
NULL, NAN = -9, -8


def run_lines(a: int, b: int, must: str, env: dict) -> dict:
    lines = Path(fe.__file__).read_text().splitlines(keepends=True)
    src = "".join(lines[a - 1:b])
    assert must in src, (a, b, must)
    ns = dict(vars(fe))
    ns.update(env)
    exec(compile(textwrap.dedent(src), f"{fe.__file__}:{a}-{b}", "exec"), ns)  # noqa: S102
    return ns


def py02b(im: pl.DataFrame, crc: pl.DataFrame) -> pl.DataFrame:
    return run_lines(179, 186, "income_medians_all = age_groups.join(", {"income_medians": im, "credit_raw_clean": crc})["income_medians_all"]


def py04(cc: pl.DataFrame, ima: pl.DataFrame) -> pl.DataFrame:
    return run_lines(208, 229, "credit_imputed = credit_cleaned.join(", {"credit_cleaned": cc, "income_medians_all": ima})["credit_imputed"]


def dgf(df: pl.DataFrame) -> int:
    return cmp.digest(cmp.tokens(cmp.canon_frame(df)))


# ---------------------------------------------------------------- columns as short codes
def zf(v):  # Float64 from integer codes
    return [None if k == NULL else nan if k == NAN else float(k) for k in v]


def bits(x) -> int:
    return struct.unpack("<Q", struct.pack("<d", float(x)))[0]


CODEC = (
    "let Z := fun (v : List Int) => (Pl.Col.f64 (v.map (fun (k : Int) => if k == -9 then none else if k == -8 then some (0.0 / 0.0) else some (Float.ofInt k))) : Pl.Col Float); "
    "let B := fun (v : List Nat) => (Pl.Col.f64 (v.map (fun (b : Nat) => if b == 1 then none else some (Float.ofBits b.toUInt64))) : Pl.Col Float); "
    "let I := fun (v : List Int) => (Pl.Col.int (v.map (fun (k : Int) => if k == -9 then none else some k)) : Pl.Col Float); "
)


class Fr:
    """A frame given once, as polars columns and as the Lean term."""

    def __init__(self, cols: list[tuple]):
        self.data, self.schema, terms = {}, {}, []
        for name, kind, v in cols:
            if kind == "Z":
                self.data[name], self.schema[name] = zf(v), pl.Float64
                terms.append(f'("{name}", Z [{",".join(map(str, v))}])')
            elif kind == "B":
                self.data[name], self.schema[name] = v, pl.Float64
                terms.append(f'("{name}", B [{",".join("1" if x is None else str(bits(x)) for x in v)}])')
            elif kind in ("I32", "I64"):
                self.data[name], self.schema[name] = [None if k == NULL else k for k in v], pl.Int32 if kind == "I32" else pl.Int64
                terms.append(f'("{name}", I [{",".join(map(str, v))}])')
            elif kind == "S":
                self.data[name], self.schema[name] = v, pl.String
                terms.append(f'("{name}", Pl.Col.str [{",".join("none" if x is None else f"some {chr(34)}{x}{chr(34)}" for x in v)}])')
        self.df = pl.DataFrame(self.data, schema=self.schema)
        self.term = "[" + ", ".join(terms) + "]"


def build() -> Suite:
    s = Suite("rev_t4")
    s.item, s.decl = "def:zz_carrier_f", "zz_carrier_f"
    lets, body, cases = CODEC, [], []

    def frame(name: str, fr: Fr):
        nonlocal lets
        lets += f"let {name} : Pl.Frame Float := {fr.term}; "
        body.append(f"dg (tR {name})")
        cases.append((f"input {name}", "input", dgf(fr.df)))

    def case(cid: str, unit: str, term: str, expected: pl.DataFrame):
        body.append(f"dg (tR ({term}))")
        cases.append((cid, unit, dgf(expected)))
        print(cid, expected.schema, expected.rows())

    # ---------------- fe_run_02b_medians_all
    im1 = Fr([("age_group", "I32", [2, 1]), ("median_income", "Z", [5, 6])])
    im2 = Fr([("age_group", "I32", []), ("median_income", "Z", [])])
    im3 = Fr([("age_group", "I32", [1, 1, NULL, 7, 5]), ("median_income", "Z", [1, 2, 9, 3, NAN])])
    im4 = Fr([("overall_median_income", "S", ["x"]), ("age_group", "I64", [3]), ("n", "I64", [4])])
    c1 = Fr([("MonthlyIncome", "Z", [3, 1, NULL, 2])])
    c2 = Fr([("MonthlyIncome", "Z", [NULL, NULL])])
    c3 = Fr([("x", "Z", [0, 0]), ("MonthlyIncome", "B", [1016.85, 7098.24])])
    c4 = Fr([("MonthlyIncome", "B", [1.0, nan, None, 2.0, nan])])
    c5 = Fr([("MonthlyIncome", "B", [-inf, inf])])
    c6 = Fr([("MonthlyIncome", "Z", [])])
    for n, f in (("im1", im1), ("im2", im2), ("im3", im3), ("im4", im4), ("c1", c1), ("c2", c2), ("c3", c3), ("c4", c4),
                 ("c5", c5), ("c6", c6)):
        frame(n, f)
    for a, b in (("im1", "c1"), ("im2", "c2"), ("im3", "c3"), ("im4", "c3"), ("im1", "c4"), ("im3", "c5"), ("im2", "c6"),
                 ("im1", "c6")):
        case(f"02b {a} {b}", "fe_run_02b_medians_all", f"fe_run_02b_medians_all {a} {b}",
             py02b(locals()[a].df, locals()[b].df))

    # ---------------- fe_run_04_imputed
    #  rows:      0    1    2    3    4     5     6    7     8
    grp = [1, 2, 3, 6, NULL, 2, 4, 5, 1]
    miss = [1, 1, 1, 1, 1, 0, NULL, 0, 1]
    base = [("VAR1", "Z", [1, 2, 3, 4, 5, 6, 7, 8, NULL]), ("SeriousDlqin2yrs", "Z", [0, 1, 0, NULL, 0, 1, 0, 0, 1]),
            ("age", "Z", [25, 35, 45, 99, NULL, 36, 55, NAN, 22]),
            ("RevolvingUtilizationOfUnsecuredL", "B", [0.5, -0.0, None, nan, inf, 0.766126609, 1e-320, 2.0, -1.5]),
            ("NumberOfTime30-59DaysPastDueNotW", "Z", [0, 1, 2, NULL, 0, 0, 0, 0, 98]),
            ("DebtRatio", "B", [0.802982129, 5710.0, None, nan, -inf, 0.43, 1.7976931348623157e308, 0.0, 0.01]),
            ("NumberOfOpenCreditLinesAndLoans", "Z", [13, 4, 0, NULL, 1, 2, 3, 4, 5]),
            ("NumberOfTimes90DaysLate", "Z", [0, 0, 1, NULL, 0, 0, 0, 0, 98]),
            ("NumberRealEstateLoansOrLines", "Z", [6, 0, 0, NULL, 0, 0, 0, 1, 2]),
            ("NumberOfTime60-89DaysPastDueNotW", "Z", [0, 0, 0, NULL, 0, 0, 0, 0, 98]),
            ("MonthlyIncome", "Z", [NULL, NULL, NULL, NULL, NULL, 7000, 1234, NAN, 777]),
            ("NumberOfDependents", "Z", [2, 0, 0, 1, 0, 3, 0, 0, 0]),
            ("age_group", "I32", grp), ("MonthlyIncome_missing", "I64", miss),
            ("Dependents_missing", "I64", [0, 1, 0, 0, NULL, 0, 0, 0, 1])]
    cc = Fr(base)
    # the same frame with a column of its own called median_income (the right one becomes median_income_right)
    cc2 = Fr(base + [("median_income", "Z", [50, NULL, 51, 52, 53, 54, 55, 56, NULL])])
    ma = Fr([("age_group", "I32", [1, 2, 3, 4, 5]), ("median_income", "Z", [5400, NULL, NAN, 6000, 7000]),
             ("overall_median_income", "Z", [5000, 5000, 5000, 5000, 5000])])
    mb = Fr([("age_group", "I32", [1, 2, 3, 4, 5]), ("median_income", "Z", [NULL, NULL, NULL, NULL, NULL]),
             ("overall_median_income", "Z", [NULL, NULL, NULL, NULL, NULL])])
    # duplicate keys, a null key, a different order of rows and of columns, an extra column
    mc = Fr([("overall_median_income", "Z", [1, 2, 3, 4]), ("extra", "S", ["a", "b", None, "d"]),
             ("median_income", "Z", [10, NULL, 30, 40]), ("age_group", "I64", [2, 2, NULL, 1])])
    md = Fr([("age_group", "I32", []), ("median_income", "Z", []), ("overall_median_income", "Z", [])])
    for n, f in (("cc", cc), ("cc2", cc2), ("ma", ma), ("mb", mb), ("mc", mc), ("md", md)):
        frame(n, f)
    for a, b in (("cc", "ma"), ("cc", "mb"), ("cc", "mc"), ("cc", "md"), ("cc2", "ma")):
        case(f"04 {a} {b}", "fe_run_04_imputed", f"fe_run_04_imputed {a} {b}", py04(locals()[a].df, locals()[b].df))

    s.ints(lets, "[" + ", ".join(body) + "]", cases)
    s.write()
    return s


if __name__ == "__main__":
    build()
