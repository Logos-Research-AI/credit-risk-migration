"""The classification table on a fit with an observation of leverage 1 or near it (experiment X21).

    cd port && uv run python tests/test_leverage_one.py        (or: uv run pytest tests)

SAS makes no one-step adjustment for an observation whose leverage is within about 1e-8 of 1: its
cross-validated probability is its predicted probability (adjusted at 1 - h = 1.489e-8, kept at 8.56e-9
and below). tests/data/sas_x21_leverage.json: the designed fits of
migration/legacy-to-port/experiments/x21_leverage_one.py (rows, MODEL order, SAS's estimates and its
Classification table); tests/data/x21_r3_s03: the training feature file and SAS's
printed_classification.csv of the raw input R3 (judge/runs/x21_r3_s03), where row id 276 has leverage
1 within 1e-13 and the sign of 1 - h depends on the order the probabilities are summed in.
"""

from __future__ import annotations

import contextlib
import io
import json
import sys
import warnings
from pathlib import Path
from typing import Any

import numpy as np
import polars as pl

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from credit_risk import sas_compat  # noqa: E402

DATA = HERE / "data"
CASES: list[dict[str, Any]] = json.loads((DATA / "sas_x21_leverage.json").read_text())
COUNTS = ["CorrectEvents", "CorrectNonevents", "IncorrectEvents", "IncorrectNonevents"]
# train.py's MODEL statement order (train.sas:74-103)
CANDIDATES = (
    "credit_utilization_capped debt_ratio_capped num_late_30_59 num_late_60_89 num_late_90_plus "
    "total_late_payments has_delinquency has_serious_delinquency age monthly_income log_monthly_income "
    "num_credit_lines num_real_estate_loans log_num_credit_lines num_dependents income_per_dependent "
    "credit_lines_per_person flag_high_utilization flag_very_high_utilization flag_high_debt_ratio "
    "flag_very_high_debt_ratio flag_recent_late_payments flag_serious_delinquency "
    "flag_multiple_delinquencies flag_low_income flag_many_dependents flag_few_credit_lines total_risk_flags "
    "credit_util_category debt_category age_category financial_health age_income_interaction "
    "utilization_debt_interaction MonthlyIncome_missing Dependents_missing"
).split()


def rows_of(t: pl.DataFrame) -> list[tuple[Any, ...]]:
    return [
        (round(float(r[0]), 3), *(int(v) for v in r[1:])) for r in t.select("ProbLevel", *COUNTS).iter_rows()
    ]


def leverage(x: np.ndarray, p: np.ndarray) -> np.ndarray:
    w = p * (1.0 - p)
    return w * np.einsum("ij,jk,ik->i", x, np.linalg.inv(x.T @ (x * w[:, None])), x)


def test_designed_fits_are_sas() -> None:
    """The 18 fits with a Classification table: five with an effect that is 1 on one observation alone
    (h printed 1) and thirteen with 1 - h from about 1e-4 down to 1e-16; the table from SAS's estimates
    is SAS's, row for row."""
    n = near = 0
    for case in CASES:
        if not case["classification"]:
            continue
        arr = np.array(case["rows"], dtype=float)
        y = arr[:, 0]
        x = np.column_stack(
            [np.ones(len(arr)), *[arr[:, 1 + case["columns"].index(c)] for c in case["model"]]]
        )
        p = sas_compat._expit(x @ np.array(case["estimates"]))
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            got = rows_of(sas_compat.classification_table(y, x, pd=p))
            near += bool(np.any(1.0 - leverage(x, p) <= 1e-8))
        want = [tuple(r) for r in case["classification"]]
        assert got == want, (case["case"], [(a, b) for a, b in zip(got, want, strict=False) if a != b][:3])
        n += 1
    assert n == 18, n
    print(f"  {n} fits: SAS's table; {near} with an observation whose 1 - h is 1e-8 or less")


def test_raw_input_r3_both_orders() -> None:
    """R3 through train.py's selection: final model age, flag_recent_late_payments,
    utilization_debt_interaction; SAS's 51 rows whichever order the probabilities are summed in
    (the pipeline's, 1 - h = -3.2e-14 on row id 276; x @ beta, 5.9e-15 apart, 1 - h = +5.4e-15)."""
    df = sas_compat.proc_import_csv(DATA / "x21_r3_s03" / "model_features_train.csv", guessingrows=None)
    ff = df.filter(pl.all_horizontal(pl.col(*CANDIDATES, "default_flag").is_not_null()))
    with contextlib.redirect_stdout(io.StringIO()):
        fin = sas_compat.stepwise_logistic(ff, "default_flag", CANDIDATES, 0.05, 0.05).final
    assert fin is not None
    assert fin.names == ["Intercept", "utilization_debt_interaction", "age", "flag_recent_late_payments"]
    y = ff["default_flag"].to_numpy().astype(np.float64)
    x = np.column_stack([np.ones(ff.height), *[ff[c].to_numpy().astype(np.float64) for c in fin.names[1:]]])
    eta = pl.lit(float(fin.beta[0]), pl.Float64)  # train.py's pd_logistic: the effects in MODEL order
    for c in [c for c in CANDIDATES if c in fin.names]:
        eta = eta + float(fin.beta[fin.names.index(c)]) * pl.col(c)
    p_pipeline = ff.select(1 / (1 + (-eta).exp())).to_series().to_numpy()
    p_entry = sas_compat._expit(x @ fin.beta)
    sas = pl.read_csv(DATA / "x21_r3_s03" / "printed_classification.csv", infer_schema=False)
    want = [
        (round(float(r[0]), 3), *(int(v) for v in r[1:]))
        for r in sas.select("ProbLevel", *COUNTS).iter_rows()
    ]
    i = int(ff["row_id"].to_list().index(276))
    for tag, p in (("pipeline", p_pipeline), ("x @ beta", p_entry)):
        h = leverage(x, p)
        assert abs(1.0 - h[i]) < 1e-12, (tag, 1.0 - h[i])
        got = rows_of(sas_compat.classification_table(y, x, pd=p))
        assert got == want, (tag, sum(a != b for a, b in zip(got, want, strict=False)), len(got), len(want))
        print(f"  {tag}: 1 - h of row id 276 = {1.0 - h[i]:.2e}; {len(got)} rows as SAS")


if __name__ == "__main__":
    for t in (test_designed_fits_are_sas, test_raw_input_r3_both_orders):
        print(t.__name__)
        t()
    print("ALL OK")
