"""Review of T8 by port-translator-9 (hand-made inputs the suites t8 / t8_edges do not hold).

  cd migration/port-to-lean && PYTHONPATH=../../port uv run --project ../../port python diffeval/units/rv_t8_gen.py
      -> diffeval/work/rv_t8.json (+ .inputs.json); eval on def:zz_carrier_p; compare with compare.py.

Python side: the source lines of predict.py (:192-206, :247-271) cut out by line number and executed
on hand-made frames with the real sas_compat. Lean side: the same frames as literals; the doubles of
input_best32 / sas_best12 are tables of the real functions' values on these inputs.
Step 04: a left frame with its OWN median_income column next to the right one; null / 0 / unmatched
left keys; null MonthlyIncome_missing; NaN, -0.0, inf operands; right key repeated, -0.0, not first;
a right frame with no row. Step 01: a numeric MonthlyIncome with NaN / inf / null / a 13-digit
value next to a text NumberOfDependents (and the reverse); a frame that already has
MonthlyIncome_num / NumberOfDependents_num; a frame with no row.
"""
from __future__ import annotations

import sys
from pathlib import Path

import polars as pl

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))

import compare as cmp  # noqa: E402
import leanterm as lt  # noqa: E402
import t8_edges_gen as e8  # noqa: E402
import t8_gen as t8  # noqa: E402
from suite import Suite  # noqa: E402

from credit_risk import sas_compat as sc  # noqa: E402

nan, inf = float("nan"), float("inf")
assert e8.SRC[191].strip().startswith("def input_best32(v: str)") and e8.SRC[205].strip() == ")"


def step01(test_raw: pl.DataFrame) -> pl.DataFrame:
    env = {"sas_compat": sc, "pl": pl, "test_raw": test_raw}
    exec(e8.cut(192, 206), env)
    return env["test_raw_clean"]


def doubles(frames: list[pl.DataFrame]) -> str:
    """ib / sb as tables of the real functions on every value these frames hold."""
    sb, ib = {}, {}
    for fr in frames:
        for c in ("MonthlyIncome", "NumberOfDependents"):
            s = fr[c]
            if s.dtype == pl.String:
                texts = [x for x in s.to_list() if x is not None]
            else:
                texts = []
                for x in s.to_list():
                    if x is not None:
                        sb[lt.bits(float(x))] = sc.sas_best12(float(x))
                        texts.append(sb[lt.bits(float(x))])
            if texts:
                vals = pl.DataFrame({"v": texts}).select(sc.input_best32(pl.col("v")))["v"].to_list()
                ib.update(zip(texts, vals))
    ibt = "[" + ", ".join(f"({lt.lean_str(k)}, {'none' if v is None else 'some ' + lt.lean_float(v)})" for k, v in ib.items()) + "]"
    sbt = "[" + ", ".join(f"({k}, {lt.lean_str(v)})" for k, v in sb.items()) + "]"
    return f"let ib := mkIb {ibt}; let sb := mkSb {sbt}; "


def main():
    s = Suite("rv_t8")
    F, I = pl.Float64, pl.Int64
    left = pl.DataFrame(
        {
            "VAR1": [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0],
            "median_income": [111.0, None, 113.0, 114.0, None, 116.0, nan],   # the left frame's own column
            "age": [25.0, None, 61.0, nan, 45.0, 30.0, 0.0],
            "age_group": [1, None, 0, 7, 3, 1, 0],
            "MonthlyIncome": [nan, 5.0, -0.0, None, 7.0, inf, 9.0],
            "MonthlyIncome_missing": [1, None, 0, 1, 1, 0, 1],
            "NumberOfDependents": [0.0, 1.0, None, 2.0, 3.0, 4.0, 5.0],
            "Dependents_missing": [0, 0, 1, 0, 0, 0, None],
            "NumberOfTime30-59DaysPastDueNotW": [0.0, 1.0, 2.0, 98.0, None, 0.0, 1.0],
            "NumberOfTime60-89DaysPastDueNotW": [0.0] * 7,
            "NumberOfTimes90DaysLate": [1.0] * 7,
            "RevolvingUtilizationOfUnsecuredL": [0.07, 0.29, nan, inf, None, -0.0, 1.1],
            "DebtRatio": [0.57, 1e306, 1e307, -inf, 0.0035, None, 4.35],
            "NumberOfOpenCreditLinesAndLoans": [1.0] * 7,
            "NumberRealEstateLoansOrLines": ["a", None, "c", "d", "e", "f", "g"],
        },
        schema_overrides={"age_group": pl.Int32, "MonthlyIncome_missing": I, "Dependents_missing": I},
    )
    left2 = left.drop("median_income")
    rights = {
        "right repeats key 1, has -0.0, key last": pl.DataFrame(
            {"overall_median_income": [50.0, None, 52.0, 53.0], "median_income": [None, 21.0, 22.0, None],
             "age_group": [1.0, 1.0, -0.0, 3.0]}, schema={"overall_median_income": F, "median_income": F, "age_group": F}),
        "right with no row": pl.DataFrame(
            {"age_group": [], "median_income": [], "overall_median_income": []},
            schema={"age_group": F, "median_income": F, "overall_median_income": F}),
        "right key null / NaN / inf, extra text column": pl.DataFrame(
            {"age_group": [None, nan, inf, 7.0, 0.0], "t": ["p", None, "r", "s", "u"], "median_income": [1.0, 2.0, 3.0, nan, None],
             "overall_median_income": [None, None, None, None, -0.0]},
            schema={"age_group": F, "t": pl.String, "median_income": F, "overall_median_income": F}),
    }
    lets = t8.MK + lt.lean_frame_let("L1", left) + lt.lean_frame_let("L2", left2)
    cases = []
    for k, (name, m) in enumerate(rights.items()):
        lets += lt.lean_frame_let(f"R{k}", m)
        for ln, lf in (("L1 (own median_income)", left), ("L2", left2)):
            exp = e8.step04(lf, m)
            print("step 04", ln, "|", name, exp.select("row_id", "monthly_income", "credit_utilization", "debt_ratio").rows())
            cases.append((f"step 04 {ln} | {name}", "predict_run_04_imputed",
                          f"tR (predict_run_04_imputed {ln[:2]} R{k})", cmp.canon_frame(exp)))
    # ---- step 01
    raws = {
        "numeric MonthlyIncome, text NumberOfDependents": pl.DataFrame(
            {"VAR1": [1.0, 2.0, 3.0, 4.0, 5.0, 6.0], "MonthlyIncome": [1234567890123.0, None, nan, inf, -0.0, 0.1],
             "z": ["a", "b", None, "d", "e", "f"], "NumberOfDependents": ["NA", "2", None, " 3 ", "1e2", "x"]},
            schema={"VAR1": F, "MonthlyIncome": F, "z": pl.String, "NumberOfDependents": pl.String}),
        "text MonthlyIncome, numeric NumberOfDependents, frame has the _num names": pl.DataFrame(
            {"NumberOfDependents_num": [9.0, 8.0, 7.0], "NumberOfDependents": [None, 20.0, 1e-7], "MonthlyIncome_num": ["k", "l", "m"],
             "MonthlyIncome": ["5400", ".", "-"], "VAR1": [1.0, 2.0, 3.0]},
            schema={"NumberOfDependents_num": F, "NumberOfDependents": F, "MonthlyIncome_num": pl.String, "MonthlyIncome": pl.String, "VAR1": F}),
    }
    raws["both numeric, no row"] = pl.DataFrame(
        {"MonthlyIncome": [], "VAR1": [], "NumberOfDependents": []}, schema={"MonthlyIncome": F, "VAR1": F, "NumberOfDependents": F})
    raws["both text, no row"] = pl.DataFrame(
        {"MonthlyIncome": [], "VAR1": [], "NumberOfDependents": []}, schema={"MonthlyIncome": pl.String, "VAR1": F, "NumberOfDependents": pl.String})
    lets += doubles(list(raws.values()))
    for k, (name, fr) in enumerate(raws.items()):
        exp = step01(fr)
        print("step 01", name, exp.schema, exp.rows())
        lets += lt.lean_frame_let(f"T{k}", fr)
        cases.append((f"step 01 {name}", "predict_run_01_clean", f"tR (predict_run_01_clean ib sb T{k})", cmp.canon_frame(exp)))
    s.digest(lets, cases, gen=False, table=True)
    for inp in s.inputs:
        inp["item"], inp["decl"] = t8.CARRIER
    s.notes = {"predict_run_04_imputed": "review of T8: hand-made left / right frames; Python = lines 247-271 executed",
               "predict_run_01_clean": "review of T8: hand-made test_raw frames; Python = lines 192-206 executed with the real sas_compat"}
    s.write()
    for inp in s.inputs:
        print(len(inp["text"]), "characters of input")


if __name__ == "__main__":
    main()
