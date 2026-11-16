"""T8 edges (hand-made inputs, NOT scenarios of the plan): the case-blind rename of step 02 and the
join of step 04 on medians tables a real feature-engineering run does not write (key not first,
repeated and absent keys, clashing names, NaN / -0.0 / null keys).

  cd migration/port-to-lean && PYTHONPATH=../../port uv run --project ../../port python diffeval/units/t8_edges_gen.py
      -> diffeval/work/t8_edges.json (+ .inputs.json); eval on def:zz_carrier_p; compare as t8_gen.

Python side: the source lines of predict.py themselves (:211-222 and :247-271, cut out of the file
by line number and executed; `sas_compat.proc_import_csv` replaced by a function returning the
frame). test_cleaned is the local of a real predict.run on a three-line test file.
"""
from __future__ import annotations

import sys
import tempfile
import textwrap
import types
from pathlib import Path

import polars as pl

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))

import compare as cmp  # noqa: E402
import leanterm as lt  # noqa: E402
import t8_gen as t8  # noqa: E402
from suite import Suite  # noqa: E402

from credit_risk import predict as pr  # noqa: E402
from credit_risk import sas_compat as sc  # noqa: E402

SRC = Path(pr.__file__).read_text().splitlines()
nan = float("nan")


def cut(a: int, b: int) -> str:
    return textwrap.dedent("\n".join(SRC[a - 1:b]))


assert SRC[210].strip().startswith("train_income_medians = sas_compat.proc_import_csv(income_medians)")
assert SRC[246].strip().startswith("test_imputed = test_cleaned.join(") and SRC[270].strip() == ")"


def step02(frame: pl.DataFrame) -> pl.DataFrame:
    fake = types.SimpleNamespace(proc_import_csv=lambda p: frame)
    env = {"sas_compat": fake, "pl": pl, "income_medians": None}
    exec(cut(211, 222), env)
    return env["train_income_medians"]


def step04(test_cleaned: pl.DataFrame, med: pl.DataFrame) -> pl.DataFrame:
    env = {"sas_compat": sc, "pl": pl, "test_cleaned": test_cleaned, "train_income_medians": med}
    exec(cut(247, 271), env)
    return env["test_imputed"]


def main():
    s = Suite("t8_edges")
    base = Path(tempfile.mkdtemp(prefix="t8e_"))
    real_train = t8.REPO / "legacy" / "data" / "cs-training.csv"
    out, _ = t8.stages_before(real_train, base / "before", None)
    hm = (t8.REPO / "legacy" / "data" / "cs-test.csv").read_text().splitlines(keepends=True)[0] + (
        "1,,0.5,25,0,0.3,NA,4,0,0,0,NA\n2,,0.2,35,1,0.1,NA,2,0,1,0,1\n3,,1.2,61,0,0.7,5000,9,2,0,1,2\n4,,1.2,45,0,0.7,NA,9,2,0,1,2\n")
    tc = t8.pyrun(hm, out, base / "run")["locals"]["test_cleaned"]
    f = lambda cols, rows: pl.DataFrame({c: [r[i] for r in rows] for i, c in enumerate(cols)}, schema={c: pl.Float64 for c in cols})  # noqa: E731
    rows = [(1.0, 10.0, 99.0), (2.0, None, 99.0)]
    lets, cases = lt.lean_frame_let("TC", tc), []
    for k, cols in enumerate((["AGE_GROUP", "Median_Income", "OVERALL_MEDIAN_INCOME"], ["Age_Group", "age_group", "m"],
                              ["age_group", "AGE_GROUP", "median_income"], ["AGE_GROUP", "aGE_GROUP", "age_group"],
                              ["x", "Overall_Median_Income", "median_income"])):
        df = f(cols, rows)
        exp = step02(df)
        print("rename", cols, "->", exp.columns)
        cases.append((f"step 02 rename {cols}", "predict_run_02_medians", f"tR (predict_run_02_medians {lt.lean_table(df)})", cmp.canon_frame(exp)))
    meds = {
        "key not first, repeated key 1, no key 2, clash age": pl.DataFrame(
            {"median_income": [10.0, None, 12.0, 50.0], "age": [7.0, 8.0, 9.0, 6.0], "age_group": [1.0, 1.0, 3.0, 5.0],
             "overall_median_income": [33.0, 34.0, 35.0, None]}),
        "keys NaN, -0.0, null, 2.5, 3": pl.DataFrame(
            {"age_group": [nan, -0.0, None, 2.5, 3.0], "median_income": [1.0, 2.0, 3.0, 4.0, nan], "overall_median_income": [9.0] * 5}),
        "all medians null": pl.DataFrame(
            {"age_group": [1.0, 2.0, 3.0, 4.0, 5.0], "median_income": pl.Series([None] * 5, dtype=pl.Float64), "overall_median_income": [5400.0] * 5}),
        "left names on the right (VAR1, MonthlyIncome)": pl.DataFrame(
            {"VAR1": [0.5, 0.25], "age_group": [5.0, 1.0], "MonthlyIncome": [1.0, 2.0], "median_income": [70.0, None], "overall_median_income": [None, 80.0]}),
    }
    for k, (name, m) in enumerate(meds.items()):
        exp = step04(tc, m)
        print("join", name, exp.rows())
        lets += lt.lean_frame_let(f"M{k}", m)
        cases.append((f"step 04 {name}", "predict_run_04_imputed", f"tR (predict_run_04_imputed TC M{k})", cmp.canon_frame(exp)))
    exp = step04(tc.clear(), meds["all medians null"])
    lets += lt.lean_frame_let("TC0", tc.clear())
    cases.append(("step 04 left frame with no row", "predict_run_04_imputed", "tR (predict_run_04_imputed TC0 M2)", cmp.canon_frame(exp)))
    s.digest(lets, cases, gen=False, table=True)
    for inp in s.inputs:
        inp["item"], inp["decl"] = t8.CARRIER
    s.notes = {"predict_run_02_medians": "hand-made column names; Python = lines 211-222 of predict.py executed",
               "predict_run_04_imputed": "hand-made medians frames; Python = lines 247-271 of predict.py executed on the test_cleaned of a real run"}
    s.write()


if __name__ == "__main__":
    main()
