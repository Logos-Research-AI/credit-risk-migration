"""A final model with a parameter left out of a singular information matrix (variance exactly 0), as SAS.

    cd port && uv run python tests/test_left_out_final.py        (or: uv run pytest tests)

Experiment X22 (migration/legacy-to-port/experiments/x22_left_out_final.py): train.sas with its MODEL
statement fixed to the design's variables and no selection, on the staged feature files of
tests/data/x22_<design> (SAS's outputs copied there as sas_*.csv, the list of files it wrote in
sas_files.txt). The selection path is not known to reach such a final model, so train.py is run with
the selection replaced by the design's fit.
  A  X21 S1: one event, the flag 1 on it alone; left out at the last iteration (weight 0), complete
     separation.
  B  num_late_90_plus = 2 * the flag: the flag is a linear combination, left out from the start; converged.
  C  three events, one flagged alone: left out at the last iteration (weight 0); converged.
SAS: the left-out parameter is printed with DF 0, Estimate 0 and empty cells and has no odds ratio; OUTPUT and
PROC PLM predict with 0 for it, and Hosmer-Lemeshow uses those probabilities; the Association table is of the
last iteration's estimates, the left-out value included; no Classification table in A and C, one in B.
"""

from __future__ import annotations

import contextlib
import csv
import io
import json
import sys
import tempfile
import warnings
from pathlib import Path
from typing import Any

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from credit_risk import sas_compat, train  # noqa: E402

DATA = HERE / "data"
DESIGNS = {
    "A": ["age", "flag_recent_late_payments"],
    "B": ["num_late_90_plus", "age", "flag_recent_late_payments"],
    "C": ["age", "flag_recent_late_payments"],
}
TABLES = [
    "model_coefficients",
    "printed_odds_ratios",
    "printed_association",
    "printed_hl_partition",
    "printed_hosmer_lemeshow",
    "printed_classification",
]
# depend on the selection (SAS ran without one): not compared
SELECTION = {
    "stepwise_summary.csv",
    "printed_fit_statistics.csv",
    "printed_global_tests.csv",
    "printed_rsquare.csv",
}
TRAIN_FILES = {
    "risk_scores_train.csv",
    "risk_scores_validation.csv",
    "final_model_output.csv",
    "model_summary.csv",
    "model_coefficients.csv",
    "printed_association.csv",
    "printed_odds_ratios.csv",
    "printed_hl_partition.csv",
    "printed_hosmer_lemeshow.csv",
    "printed_classification.csv",
    "printed_roc_train.csv",
    "printed_roc_validation.csv",
    "printed_confusion_train.csv",
    "printed_confusion_validation.csv",
}


def run_design(name: str, out: Path) -> sas_compat.LogisticFit:
    cols = DESIGNS[name]
    fits: list[sas_compat.LogisticFit] = []

    def fixed(df: Any, response: str, candidates: Any, *_a: Any) -> sas_compat.StepwiseResult:
        used = df.select([response, *candidates]).drop_nulls()
        y = used.get_column(response).to_numpy().astype(np.float64)
        x = np.column_stack(
            [np.ones(len(y)), *[used.get_column(c).to_numpy().astype(np.float64) for c in cols]]
        )
        fit = sas_compat._fit_as_sas(x, y, ["Intercept", *cols])
        assert fit is not None
        fits.append(fit)
        return sas_compat.StepwiseResult([], fit, sas_compat.fit_logistic(x[:, :1], y, ["Intercept"]))

    real = sas_compat.stepwise_logistic
    sas_compat.stepwise_logistic = fixed  # type: ignore[assignment]
    try:
        with contextlib.redirect_stdout(io.StringIO()), warnings.catch_warnings():
            warnings.simplefilter("ignore")
            train.run(DATA / f"x22_{name}", out)
    finally:
        sas_compat.stepwise_logistic = real  # type: ignore[assignment]
    return fits[0]


def column(path: Path, name: str) -> list[str]:
    with path.open() as fh:
        return [r[name] for r in csv.DictReader(fh)]


def test_designs_are_sas() -> None:
    for name in DESIGNS:
        d = DATA / f"x22_{name}"
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            fit = run_design(name, out)
            # the fit leaves the flag out at its last iteration (variance exactly 0)
            assert sas_compat._left_out(fit) == ["flag_recent_late_payments"], (
                name,
                sas_compat._left_out(fit),
            )
            sas_files = set((d / "sas_files.txt").read_text().split()) & TRAIN_FILES
            port_files = {p.name for p in out.iterdir()} & TRAIN_FILES
            assert port_files == sas_files, (name, sas_files ^ port_files)
            for t in TABLES:
                if not (d / f"sas_{t}.csv").exists():
                    continue
                want = (d / f"sas_{t}.csv").read_text().splitlines()
                got = (out / f"{t}.csv").read_text().splitlines()
                if name == "A" and t == "model_coefficients":
                    # age has no information there: its estimate is a rounding residue on both sides
                    # (SAS 2.19E-15, the port's iteration -1.1E-15); the other cells are compared
                    i = [ln.split(",")[0] for ln in want].index("age")
                    assert abs(float(got[i].split(",")[2])) < 1e-14, got[i]
                    want = [ln for k, ln in enumerate(want) if k != i]
                    got = [ln for k, ln in enumerate(got) if k != i]
                assert got == want, (name, t, [(a, b) for a, b in zip(got, want, strict=False) if a != b][:3])
            assert (
                "flag_recent_late_pay,0,0,,,,MLE" in (out / "model_coefficients.csv").read_text().splitlines()
            )
            # OUTPUT and PROC PLM: 0 for the left-out parameter (pd_logistic as SAS's, to its 8 digits)
            for part in ("train", "validation"):
                a = np.array(column(out / f"risk_scores_{part}.csv", "pd_logistic"), dtype=float)
                b = np.array(column(d / f"sas_risk_scores_{part}.csv", "pd_logistic"), dtype=float)
                assert np.allclose(a, b, rtol=1e-7, atol=0.0), (name, part, np.max(np.abs(a / b - 1)))
            model = json.loads((out / "model.json").read_text())
            assert model["coefficients"]["flag_recent_late_payments"] == 0.0, model
            print(
                f"  {name}: {len(sas_files)} train files as SAS; classification table: "
                f"{'printed_classification.csv' in port_files}"
            )


if __name__ == "__main__":
    test_designs_are_sas()
    print("ALL OK")
