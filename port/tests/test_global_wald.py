"""The Wald test of the global null hypothesis as SAS prints it (global-wald-rule.md).

    cd port && uv run python tests/test_global_wald.py        (or: uv run pytest tests)

tests/data/sas_global_wald_cases.json: the 17 runs of experiment X20 (seed 6's step-7 model fitted
alone with columns rescaled), SAS's estimates, covariance (COVB) and global Wald test of each. The
interaction's pivot runs from 6.3e-25 to 6.3e-15: SAS leaves it out of the chi-square up to 1e-16 (T1)
and keeps it from 2e-16 (T2), whatever the other slopes' scale (B1 to B5) or the intercept's variance
(S1); the DF is 7 in every run.
The second test runs `train.run` on seed 6's feature file (judge/runs/gen_s06, SAS's run of the
generated input) and compares printed_global_tests.csv with SAS's, cell by cell.
"""

from __future__ import annotations

import contextlib
import io
import json
import sys
import tempfile
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from credit_risk import sas_compat, train  # noqa: E402

RUNS = json.loads((HERE / "data" / "sas_global_wald_cases.json").read_text())["runs"]
SEED6 = HERE.parents[1] / "judge" / "runs" / "gen_s06"


def test_x20_runs_are_sas() -> None:
    """Each run's chi-square from SAS's own estimates and covariance, and its DF of 7. A tolerance
    relative to the largest slope variance fails A4 (left out by SAS at 5.2e-15 of it) or B4 and B5;
    one relative to the slope's own variance (about 0.99 in every run) fails A0 to A4 or A5."""
    left = 0
    for run, r in RUNS.items():
        names = ["Intercept", *r["names"][1:]]
        fit = sas_compat.LogisticFit(names, np.array(r["beta"]), np.array(r["cov"]), 0.0, 1, True)
        chisq, df = sas_compat.global_wald(fit, names[1:])
        assert abs(chisq - r["wald"]) <= 1e-8 * r["wald"], (run, chisq, r["wald"])
        assert df == r["df"] == 7, (run, df)
        left += abs(chisq - 406.4827) < 1e-3
    assert left == 11, left
    print(f"  {len(RUNS)} runs: chi-square and DF as SAS; the interaction left out in {left}")


def test_seed6_global_tests_are_sas() -> None:
    """train.run on seed 6: every cell of printed_global_tests.csv equals SAS's, step 7's Wald test
    included (`7,Wald,406.4827,7,<.0001`; the port printed 407.3550 before)."""
    assert (SEED6 / "model_features_train.csv").exists(), f"{SEED6} is needed (SAS's run of seed 6)"
    with tempfile.TemporaryDirectory() as tmp:
        with contextlib.redirect_stdout(io.StringIO()):
            train.run(SEED6, Path(tmp))
        got = (Path(tmp) / "printed_global_tests.csv").read_text().splitlines()
    sas = (SEED6 / "printed_global_tests.csv").read_text().splitlines()
    assert "7,Wald,406.4827,7,<.0001" in sas
    assert got == sas, [(g, s) for g, s in zip(got, sas, strict=False) if g != s][:3]
    print(f"  seed 6: {len(got) - 1} global test rows equal SAS's")


if __name__ == "__main__":
    for t in (test_x20_runs_are_sas, test_seed6_global_tests_are_sas):
        print(t.__name__)
        t()
    print("ALL OK")
