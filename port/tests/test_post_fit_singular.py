"""A step whose X'X is singular (a variable a linear combination of the others): the step tables as SAS.

    cd port && uv run python tests/test_post_fit_singular.py        (or: uv run pytest tests)

Experiment X28 (migration/legacy-to-port/experiments/x28_post_fit_singular.py) on X22 B
(tests/data/x22_B: num_late_90_plus = 2 * flag_recent_late_payments; SAS run judge/runs/x22_B, MODEL
num_late_90_plus age flag_recent_late_payments, no selection; its step tables copied there as
sas_printed_global_tests.csv, sas_printed_fit_statistics.csv, sas_printed_rsquare.csv). train.py is run with
the selection replaced by one step that enters the design's three variables. SAS leaves the dependent flag
out of the tests and the parameter count: Likelihood Ratio, Score and Wald with DF 2, AIC and SC with three
parameters. Before X28 the port raised LinAlgError in the score test.
"""

from __future__ import annotations

import contextlib
import csv
import io
import sys
import tempfile
import warnings
from pathlib import Path
from typing import Any

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from credit_risk import sas_compat, train  # noqa: E402

DATA = HERE / "data" / "x22_B"
COLS = ["num_late_90_plus", "age", "flag_recent_late_payments"]
TABLES = {  # file -> the columns SAS writes without a selection (no Step, no RowId in the global tests)
    "printed_global_tests": ["Test", "ChiSq", "DF", "ProbChiSq"],
    "printed_fit_statistics": ["RowId", "Criterion", "InterceptOnly", "InterceptAndCovariates"],
    "printed_rsquare": ["Label1", "cValue1", "nValue1", "Label2", "cValue2", "nValue2"],
}


def _rows(path: Path, cols: list[str]) -> list[list[str]]:
    with path.open() as fh:
        # the port's step 0 (-2 Log L of the intercept-only model) has no row in a run without selection
        return [[r.get(c, "") for c in cols] for r in csv.DictReader(fh) if r.get("Step") != "0"]


def _same(sas: str, port: str) -> bool:
    """Equal cells; a number to the decimals SAS prints (the D12.3 InterceptOnly column of a run without
    selection prints 168.322 where the port's step table holds more digits)."""
    if sas == port:
        return True
    try:
        d = len(sas.split(".")[1]) if "." in sas else 0
        return abs(float(sas) - float(port)) <= 0.5 * 10.0**-d
    except ValueError:
        return False


def one_step(df: Any, response: str, candidates: Any, *_a: Any) -> sas_compat.StepwiseResult:
    used = df.select([response, *candidates]).drop_nulls()
    y = used.get_column(response).to_numpy().astype(np.float64)
    x = np.column_stack([np.ones(len(y)), *[used.get_column(c).to_numpy().astype(np.float64) for c in COLS]])
    fit = sas_compat._fit_as_sas(x, y, ["Intercept", *COLS])
    assert fit is not None
    io_fit = sas_compat.fit_logistic(x[:, :1], y, ["Intercept"])
    step = sas_compat.StepwiseStep(1, COLS[-1], None, 1, len(COLS), 0.0, None, 0.0, fit)
    return sas_compat.StepwiseResult([step], fit, io_fit)


def test_singular_step_is_sas() -> None:
    real = sas_compat.stepwise_logistic
    sas_compat.stepwise_logistic = one_step  # type: ignore[assignment]
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp)
        try:
            with contextlib.redirect_stdout(io.StringIO()), warnings.catch_warnings():
                warnings.simplefilter("ignore")
                train.run(DATA, out)
        finally:
            sas_compat.stepwise_logistic = real  # type: ignore[assignment]
        for t, cols in TABLES.items():
            want = _rows(DATA / f"sas_{t}.csv", cols)
            got = _rows(out / f"{t}.csv", cols)
            assert len(want) == len(got), (t, want, got)
            for w, g in zip(want, got, strict=True):
                assert all(_same(a, b) for a, b in zip(w, g, strict=True)), (t, w, g)
        tests = {r[0]: r[2] for r in _rows(out / "printed_global_tests.csv", TABLES["printed_global_tests"])}
        assert tests == {"Likelihood Ratio": "2", "Score": "2", "Wald": "2"}, tests
    print("  X22 B: global tests, fit statistics and R-square as SAS")


if __name__ == "__main__":
    test_singular_step_is_sas()
    print("ALL OK")
