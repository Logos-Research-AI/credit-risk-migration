"""A singular information matrix: the fit leaves a parameter out as SAS does (singular-information.md).

    cd port && uv run python tests/test_singular_information.py        (or: uv run pytest tests)

tests/data/sas_singular_cases.json: the 40 designed cases of experiment x19 (their rows, the order of
the MODEL statement, whether the run was stepwise) with SAS's results from ITPRINT, DETAILS and COVB:
for each fit how it ended, at which iteration, the last estimates, each parameter's DF, standard
error and Wald chi-square, the global tests; for the stepwise runs the step summary; the warnings.
"""

from __future__ import annotations

import contextlib
import io
import json
import math
import sys
import tempfile
from pathlib import Path
from typing import Any

import numpy as np
import polars as pl

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from credit_risk import sas_compat, train  # noqa: E402

CASES: list[dict[str, Any]] = json.loads((HERE / "data" / "sas_singular_cases.json").read_text())
SINGULAR = "WARNING: The information matrix is singular and thus the convergence is questionable."


def xy(case: dict[str, Any], variables: list[str]) -> tuple[np.ndarray, np.ndarray]:
    arr = np.array(case["rows"], dtype=float)
    cols = [arr[:, 1 + case["columns"].index(v)] for v in variables]
    return np.column_stack([np.ones(len(arr)), *cols]), arr[:, 0]


def kind(status: str) -> str | None:
    return "complete" if "Complete" in status else "quasicomplete" if "Quasi" in status else None


def test_every_fit_is_sas() -> None:
    """The 44 fits: the stop and its iteration, the last estimates, which parameters have DF 0
    (variance exactly 0 in the port's covariance), and the standard errors of the others."""
    n = left = 0
    for case in CASES:
        for st in case["steps"]:
            x, y = xy(case, st["variables"])
            fit = sas_compat._fit_as_sas(x, y, ["Intercept", *st["variables"]])
            where = (case["case"], st["step"])
            assert fit is not None, where
            assert (fit.separation, fit.n_iter) == (kind(st["status"]), st["n_iter"]), (
                where,
                fit.separation,
                fit.n_iter,
            )
            assert np.allclose(fit.beta, st["estimates"], rtol=1e-6, atol=1e-9), (where, fit.beta)
            out = sas_compat._left_out(fit)
            assert out == [p["variable"] for p in st["parameters"] if p["df"] == 0], (where, out)
            for i, p in enumerate(st["parameters"]):
                if p["df"] and p["stderr"] is not None:
                    assert abs(math.sqrt(fit.cov[i, i]) - p["stderr"]) <= 1e-5 * p["stderr"], (
                        where,
                        p["variable"],
                    )
            n += 1
            left += bool(out)
    print(f"  {n} fits end as in SAS; {left} of them with a parameter left out at the last iteration")


def test_the_cases_pin_the_tolerance_and_the_limit() -> None:
    """What the cases hold: the two sides of the 1e-9 tolerance (G8 series: the second column off
    collinearity by 2.3e-5 is left out, by 2.7e-5 it is kept), unchanged when the first or the second
    column is multiplied by 1000 (H1, G8e: a tolerance relative to the largest diagonal element
    fails there); which of two collinear columns goes (the later in the MODEL order, G7a and G7b);
    the limit 36.7368 beyond which a weight is 0 (G4a below it, G4b above, and mirrored)."""
    by = {c["case"]: c for c in CASES}

    def left_out(name: str) -> list[str]:
        return [p["variable"] for p in by[name]["steps"][0]["parameters"] if p["df"] == 0]

    assert left_out("G8m_near_2.3e-05") == ["x2"] and left_out("G8m_near_2.7e-05") == []
    assert (
        left_out("H1_x1_times_1000_near_2.3e-05") == ["x2"]
        and left_out("H1_x1_times_1000_near_2.7e-05") == []
    )
    assert left_out("G8e_near_1e-7_x2_times_1000") == ["x2"]
    assert left_out("G7a_collinear_after_x1_x2") == ["x2"] and left_out("G7b_collinear_after_x2_x1") == ["x1"]
    for name in (
        "G4a_n202_k5_below",
        "G4b_n283_k7_above",
        "G9d_mirror_n202_k5_below",
        "G9e_mirror_n283_k7_above",
    ):
        assert name in by
    print("  tolerance bracketed (2.3e-5 out, 2.7e-5 kept; the same with a column scaled);")
    print("  the order and the limit cases are present")


def test_stepwise_runs_are_sas() -> None:
    """The 14 stepwise runs: SAS's steps; a variable whose parameter was left out at the last
    iteration is removed at the next step with DF 0 and no Wald test, also beside a variable whose
    own test keeps it (J5: `a` with a Wald chi-square of 42.37 stays, x1 goes); one left out on the
    way only is removed by its ordinary test (Wald 4.4e-13, DF 1); and the port prints SAS's warning
    on the same runs as SAS."""
    n = zero_df = 0
    for case in CASES:
        if not case["stepwise"]:
            continue
        arr = np.array(case["rows"], dtype=float)
        df = pl.DataFrame({"y": arr[:, 0], **{v: arr[:, 1 + i] for i, v in enumerate(case["columns"])}})
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            res = sas_compat.stepwise_logistic(df, "y", case["model"], 0.05, 0.05)
        assert len(res.steps) == len(case["summary"]), (case["case"], len(res.steps))
        for s, r in zip(res.steps, case["summary"], strict=True):
            where = (case["case"], s.step)
            assert (s.entered or "", s.removed or "", s.df) == (r["entered"], r["removed"], r["df"]), where
            if r["entered"]:
                assert s.score_chisq is not None and abs(s.score_chisq - r["score"]) <= 1e-6 * r["score"], (
                    where
                )
            elif r["df"] == 0:
                assert s.wald_chisq is not None and math.isnan(s.wald_chisq) and math.isnan(s.p_value), where
                zero_df += 1
            else:
                assert s.wald_chisq is not None and abs(s.wald_chisq - r["wald"]) <= 1e-6 * max(
                    r["wald"], 1e-6
                ), where
        assert (SINGULAR in buf.getvalue()) == any(w.startswith(SINGULAR) for w in case["warnings"]), case[
            "case"
        ]
        n += 1
    j5 = next(c for c in CASES if c["case"] == "J5_regular_then_flag")
    assert [(r["removed"], r["df"]) for r in j5["summary"]][-1] == ("x1", 0)
    assert zero_df >= 8
    print(f"  {n} stepwise runs: steps, DF and tests as SAS; {zero_df} removals with DF 0; warning as SAS")


def test_train_writes_sas_cells() -> None:
    """The 14 stepwise runs through `train.run`, each designed variable in a column of the feature
    file (a -> age, x1 -> flag_very_high_utilization, z -> flag_low_income, every other candidate 0,
    which the entry test skips as aliased with the intercept; the MODEL order a, x1, z is kept).
    stepwise_summary.csv: a removal of a parameter left out at the last iteration is
    `step,,effect,0,n,_,,` (DF 0, empty Wald chi-square and probability). printed_global_tests.csv:
    SAS's chi-square and DF of every test of every step with a variable; the Wald test of a step with
    a parameter left out has an empty chi-square and probability and DF = the variables not left out
    (J5 step 2: `2,Wald,,1,`; G2 step 1: `1,Wald,,0,`)."""
    header = (HERE.parents[1] / "judge" / "reference" / "model_features_train.csv").open().readline()
    column = {"a": "age", "x1": "flag_very_high_utilization", "z": "flag_low_income"}
    n = empty = 0
    for case in CASES:
        if not case["stepwise"]:
            continue
        arr = np.array(case["rows"], dtype=float)
        cols = {h: np.zeros(len(arr)) for h in header.strip().split(",")}
        cols["row_id"] = np.arange(1.0, len(arr) + 1.0)
        cols["default_flag"] = arr[:, 0]
        for i, v in enumerate(case["columns"]):
            cols[column[v]] = arr[:, 1 + i]
        with tempfile.TemporaryDirectory() as tmp:
            d = Path(tmp)
            pl.DataFrame(cols).write_csv(d / "model_features_train.csv")
            pl.DataFrame(cols).write_csv(d / "model_features_validation.csv")
            with contextlib.redirect_stdout(io.StringIO()):
                train.run(d, d / "out")
            summary = pl.read_csv(d / "out" / "stepwise_summary.csv", infer_schema_length=0).fill_null("")
            tests = pl.read_csv(d / "out" / "printed_global_tests.csv", infer_schema_length=0).fill_null("")
        assert summary.height == len(case["summary"]), case["case"]
        for row, r in zip(summary.iter_rows(named=True), case["summary"], strict=True):
            where = (case["case"], r["step"])
            assert row["DF"] == str(r["df"]), (where, row)
            if r["df"] == 0:
                assert (row["ScoreChiSq"], row["WaldChiSq"], row["ProbChiSq"]) == ("_", "", ""), (where, row)
                empty += 1
            elif r["removed"]:
                assert row["WaldChiSq"] == sas_compat.fmt_wd(r["wald"], 10, 4), (where, row)
            else:
                assert row["ScoreChiSq"] == sas_compat.fmt_wd(r["score"], 10, 4), (where, row)
        got = {(int(t["Step"]), t["Test"]): t for t in tests.iter_rows(named=True)}
        for st in case["steps"]:
            for g in st["global_tests"]:
                t = got[(st["step"], g["test"])]
                where = (case["case"], st["step"], g["test"])
                assert t["DF"] == str(g["df"]), (where, t)
                if g["chisq"] is None:
                    assert (t["ChiSq"], t["ProbChiSq"]) == ("", ""), (where, t)
                    empty += 1
                else:
                    assert t["ChiSq"] == sas_compat.fmt_wd(g["chisq"], 10, 4), (where, t)
        n += 1
    print(f"  {n} stepwise runs through train.run: summary and global tests as SAS; {empty} empty-cell rows")


if __name__ == "__main__":
    for t in (
        test_every_fit_is_sas,
        test_the_cases_pin_the_tolerance_and_the_limit,
        test_stepwise_runs_are_sas,
        test_train_writes_sas_cells,
    ):
        print(t.__name__)
        t()
    print("ALL OK")
