"""A fit with a variable is SAS's iteration stopped where SAS stops it (`sas_compat._fit_as_sas`).

    cd port && uv run python tests/test_fit_as_sas.py        (or: uv run pytest tests)

SAS's side is migration/legacy-to-port/experiments/x17_sas_iteration_histories.json: for every step
of PROC LOGISTIC as train.sas calls it, with ITPRINT, the ridge of each iteration, -2 Log L after
each iteration and the estimates of the last one, 15 digits. The cases used here are the reference
feature file (19 steps, 37 ridged iterations) and "sub50000_2", 50,000 of its rows (25 steps, 88
ridged iterations, ridges up to 104.8576), the case that tells the ridge rule from its neighbours.
"""

from __future__ import annotations

import contextlib
import io
import json
import random
import re
import sys
from pathlib import Path

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
        test_reference_data_selection_is_the_reference,
    ):
        print(t.__name__)
        t()
    print("ALL OK")
