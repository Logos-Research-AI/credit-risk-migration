"""A fit with a variable is SAS's iteration stopped where SAS stops it (`sas_compat._fit_as_sas`).

    cd port && uv run python tests/test_fit_as_sas.py        (or: uv run pytest tests)

SAS's side is migration/legacy-to-port/experiments/x17_sas_iteration_histories.json: for every step
of PROC LOGISTIC as train.sas calls it, with ITPRINT, the ridge of each iteration, -2 Log L after
each iteration and the estimates of the last one, 15 digits. The cases used here are the reference
feature file (19 steps, 37 ridged iterations) and "sub50000_2", 50,000 of its rows (25 steps, 88
ridged iterations, ridges up to 104.8576), the case that tells the ridge rule from its neighbours.

tests/data/sas_fit_cases.json holds single steps of the reviewer's ITPRINT runs of 2026-11-17 (SAS
logs under out/review_fit/sas, git-ignored): the model's columns, the outcome, and SAS's history
(ridge per iteration, how the step ended, the last -2 Log L and estimates). They cover what X17
does not: a first ridge of 1e-4, ridges below 0.0064 and below 1e-4, ridged iterations on
separated steps, ridges up to 419.4304.
"""

from __future__ import annotations

import contextlib
import io
import json
import random
import re
import sys
from pathlib import Path
from typing import Any

import numpy as np
import polars as pl

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from credit_risk import sas_compat  # noqa: E402

ROOT = HERE.parents[1]
SAS = json.loads((ROOT / "migration/legacy-to-port/experiments/x17_sas_iteration_histories.json").read_text())
REFERENCE = ROOT / "judge" / "reference"
_train = (HERE.parent / "credit_risk" / "train.py").read_text()
_start = _train.index("candidates = [")
CANDIDATES = re.findall(r'"([A-Za-z_0-9]+)"', _train[_start : _train.index("]", _start)])


def features(case: str) -> pl.DataFrame:
    df = pl.read_csv(REFERENCE / "model_features_train.csv", infer_schema_length=None)
    if case == "real":
        return df
    n, seed = (int(v) for v in case[3:].split("_"))  # x17_ridging_run.py: the same rows
    rows = sorted(random.Random(1000 * seed + n).sample(range(len(df)), n))
    assert (case, sum(rows)) == ("sub50000_2", 2625731170), "another sampler than the experiment's"
    return df[rows]


def column(df: pl.DataFrame, name: str) -> np.ndarray:
    return (
        df[next(c for c in df.columns if c[:32] == name)].to_numpy().astype(float)
    )  # SAS names: 32 characters


def check_case(case: str) -> None:
    df = features(case)
    y = df["default_flag"].to_numpy().astype(float)
    worst = 0.0
    ridged = 0
    for step in SAS[case]:
        names = ["Intercept", *step["variables"]]
        x = np.column_stack([np.ones(len(y)), *[column(df, v) for v in step["variables"]]])
        fit = sas_compat._fit_as_sas(x, y, names)
        assert fit is not None and fit.converged and fit.separation is None, (case, step["step"])
        assert fit.n_iter == len(step["ridge"]), (case, step["step"], fit.n_iter, len(step["ridge"]))
        m2 = step["neg2loglike"][-1]
        assert abs(-2.0 * fit.loglik - m2) <= 1e-10 * m2, (case, step["step"])
        sas_b = np.array(step["estimates"])
        diff = float(np.abs(fit.beta - sas_b).max())
        assert np.allclose(fit.beta, sas_b, rtol=1e-9, atol=1e-11), (case, step["step"], diff)
        worst = max(worst, diff)
        ridged += sum(r > 0 for r in step["ridge"])
    print(
        f"  {case}: {len(SAS[case])} steps stop at SAS's iteration with SAS's estimates (largest difference"
    )
    print(f"  {worst:.1e}); SAS ridged {ridged} of their iterations")


def test_reference_data_steps_are_sas() -> None:
    check_case("real")


def test_subset_with_large_ridges_is_sas() -> None:
    check_case("sub50000_2")


CASES = json.loads((HERE / "data" / "sas_fit_cases.json").read_text())


def check_step(case: dict[str, Any]) -> None:
    y = np.array(case["y"], dtype=float)
    x = np.column_stack([np.ones(len(y)), *[np.array(case["columns"][v]) for v in case["variables"]]])
    with np.errstate(over="ignore"):
        fit = sas_compat._fit_as_sas(x, y, ["Intercept", *case["variables"]])
    where = (case["case"], case["step"])
    assert fit is not None, where
    assert (fit.separation, fit.n_iter) == (case["separation"], len(case["ridge"])), (
        where,
        fit.separation,
        fit.n_iter,
    )
    assert fit.converged == (case["separation"] is None), where
    # a separated step's estimates grow without bound and its systems are badly conditioned: the
    # two sides agree to 2e-6 relative at worst (the floor on the ladder moves them by 1.9%)
    assert np.allclose(fit.beta, np.array(case["estimates"]), rtol=1e-5, atol=1e-9), (where, fit.beta)
    assert abs(-2.0 * fit.loglik - case["neg2loglike"]) <= 1e-6 * case["neg2loglike"], where


def test_single_steps_are_sas() -> None:
    """Each step ends as in SAS: same iteration, same kind, same estimates."""
    for case in CASES:
        check_step(case)
    print(f"  {len(CASES)} steps of {len({c['case'] for c in CASES})} runs end as in SAS")


def test_ridge_ladder_starts_at_1e_4_and_has_no_floor() -> None:
    """What the cases must contain for the ridge rule to be pinned: a fit whose first ridge is 1e-4
    (a start further up the ladder, or a ladder that cannot come down below 0.0064, would ridge
    more), a ridge below 1e-4 right after one of 1e-4 (no floor at the start of the ladder), and
    ridged iterations on separated steps."""
    first = [next(r for r in c["ridge"] if r > 0) for c in CASES if any(c["ridge"])]
    assert first.count(1e-4) >= 2 and min(first) == 1e-4, sorted(first)
    floor = next(c for c in CASES if 2.5e-5 in c["ridge"])
    k = floor["ridge"].index(2.5e-5)
    assert floor["ridge"][k - 1] == 1e-4 and floor["separation"] == "complete"
    assert any(0 < r < 0.0064 for c in CASES for r in c["ridge"])
    ridged_separated = [c for c in CASES if c["separation"] and any(c["ridge"])]
    assert {c["separation"] for c in ridged_separated} == {"complete", "quasicomplete"}
    smallest = min(r for c in CASES for r in c["ridge"] if r)
    print(f"  first ridges {sorted(set(first))}; smallest ridge {smallest:g};")
    print(f"  {len(ridged_separated)} separated steps with ridged iterations")


def test_a_step_that_keeps_the_log_likelihood_is_taken() -> None:
    """The port's own choice, not measured in SAS (docstring of `_fit_as_sas`): a step that leaves
    the log likelihood exactly equal is taken without a ridge. Here the variable's score is exactly
    zero at the start, so the first step is zero and the fit has converged at iteration 1.
    This does not tell `<` from `<=` in the test that calls for a ridge: on a zero step the first
    ridge gives the same zero step and is accepted, and an exact tie on a step that is not zero
    could not be built. The two readings differ only there."""
    y = np.array([0.0, 1.0, 0.0, 1.0])
    x = np.column_stack([np.ones(4), np.array([1.0, 1.0, -1.0, -1.0])])
    fit = sas_compat._fit_as_sas(x, y, ["Intercept", "x"])
    assert fit is not None and fit.converged and fit.n_iter == 1 and fit.beta.tolist() == [0.0, 0.0], fit
    print("  a zero step is taken: converged at iteration 1")


def test_reference_data_selection_is_the_reference() -> None:
    """The whole selection on the reference feature file: every chi-square of the step summary is
    the reference listing's to the 4 decimals printed (with the fully converged estimates the port
    had before, 11 of the 19 were not, by up to 0.0245)."""
    df = pl.read_csv(REFERENCE / "model_features_train.csv", infer_schema_length=None)
    with contextlib.redirect_stdout(io.StringIO()):
        res = sas_compat.stepwise_logistic(df, "default_flag", CANDIDATES, 0.05, 0.05)
    ref = pl.read_csv(REFERENCE / "stepwise_summary.csv", infer_schema_length=0).to_dicts()
    assert len(res.steps) == len(ref)
    for s, r in zip(res.steps, ref, strict=True):
        assert (s.entered or "")[:20] == (r["EffectEntered"] or "") and (s.removed or "")[:20] == (
            r["EffectRemoved"] or ""
        )
        v, printed = (s.score_chisq, r["ScoreChiSq"]) if s.entered else (s.wald_chisq, r["WaldChiSq"])
        assert v is not None and f"{v:.4f}" == printed, (s.step, v, printed)
    print(f"  reference data: the {len(ref)} printed chi-squares equal the reference listing")


if __name__ == "__main__":
    for t in (
        test_reference_data_steps_are_sas,
        test_subset_with_large_ridges_is_sas,
        test_single_steps_are_sas,
        test_ridge_ladder_starts_at_1e_4_and_has_no_floor,
        test_a_step_that_keeps_the_log_likelihood_is_taken,
        test_reference_data_selection_is_the_reference,
    ):
        print(t.__name__)
        t()
    print("ALL OK")
