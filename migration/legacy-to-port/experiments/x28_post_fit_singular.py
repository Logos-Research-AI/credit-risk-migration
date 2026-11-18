"""X28: the numpy linear algebra train.py runs after the fit, on a singular matrix (task of 2026-11-18).

The calls after the fit on the train path (port at 41608e6), and whether each can raise LinAlgError:
  1. train.py:229, global score test: np.linalg.solve(i0, u0), i0 = ybar (1 - ybar) X'X of the step's model.
     Raises when X'X is singular, that is when a variable of the step is a linear combination of the others.
  2. sas_compat.global_wald (:849, :853): np.linalg.solve on the slopes kept, each with a pivot above 1.5e-16, so
     the matrix solved is never singular; with no slope kept the 0 x 0 solve returns [] (numpy 2.5.4). Returns
     before any solve when a parameter is left out (`_left_out`).
  3. sas_compat.classification_table -> _inv_sas(X'WX) (:1558), and classification_is_made -> _kept(X'X):
     `_kept` solves on the parameters already kept (pivots above 1e-9 of their diagonal), `_inv_sas` inverts
     the kept block only. Cannot raise; with every weight 0 nothing is kept and nothing is inverted.
  (Inside the selection, before train.py's tables: _entry_score_chisq :1009, :1015 solve X'WX at the step's
  estimates with p (1 - p) weights, outside `_fit_as_sas`'s try. A matrix singular through the weights there
  has a parameter left out at the step's last iteration, which the selection removes before any entry test.)

So only (1) can raise, and only on a model with a linear combination among its columns. The selection does not
enter such a column on the inputs searched: the entry test leaves out a candidate whose relative residual
information is below 1e-8, and over 7,599 selections (x28_search.py: random outcomes on 15 known training parts
and on 60- to 5,000-row slices of the reference features, among them outcomes driven by the late-payment
columns, which hold two exact relations, total_late_payments = the three counts and has_serious_delinquency =
flag_serious_delinquency; 25,552 steps, 2 selections stopped by the fit, not by linear algebra) the 10,603 entry
tests of an exactly dependent candidate gave at most 2.9e-13, and no call (1) to (3) raised. The test is not
exact: on models the selection did not reach (x28_alias_probe.py: 24,874 fits of random models with a dependent
candidate, condition numbers up to 3e31), 11 of 37,863 dependent candidates passed it (ratio up to 3.4e-8), so a
step with a singular X'X is not excluded by construction.

A forced design reaches it: X22 B (MODEL num_late_90_plus age flag_recent_late_payments, num_late_90_plus =
2 * flag; SAS run judge/runs/x22_B of 2026-11-18, no selection). The port raises there
(`numpy.linalg.LinAlgError: Singular matrix` at train.py:229) once the fit is a step of the selection. SAS
leaves the flag out of the tests as it does of the estimates ("set to 0, since the variables are a linear
combination"): printed_global_tests.csv `Likelihood Ratio,59.2895,2`, `Score,50.3215,2`, `Wald,34.2078,2`;
printed_fit_statistics.csv AIC 113.032 = -2 Log L 107.032 + 2 * 3 and SC 121.395 = 107.032 + 3 ln 120 (three
parameters, not four). Where the flag is left out through the weights (A, C), SAS counts it: DF 2 for the
likelihood ratio and score tests, AIC = -2 Log L + 2 * 3 with two variables, the Wald test empty with DF 1.

The fix proposed (x28_post_fit_singular.patch; not applied, this task measures and proposes): in train.py's step loop,
the variables left out of X'X itself (`_kept`) count in no DF and no parameter count, the score test solves with
`_solve_sas`, and global_wald takes those variables as `dependent` (left out of its slopes, not emptying the
test). On a model with no linear combination `_kept` keeps every column and `_solve_sas` is np.linalg.solve,
so every judged output is unchanged. Not settled: which of two collinear variables SAS leaves out on a step
of the selection (the port's `_kept` goes in the step's order, entry order; X22 B is in MODEL order).

usage (from port/):  uv run python ../migration/legacy-to-port/experiments/x28_post_fit_singular.py <port dir>
runs train.py of <port dir> (the port as it is, or a copy with the patch applied) on the staged X22 inputs with
the selection replaced by one step that enters the design's variables, and compares the three step tables with
SAS's x22 files. Results, the port at 41608e6: B stops with LinAlgError, A and C as SAS. With the patch: A, B
and C as SAS (every cell of the three tables).
"""

from __future__ import annotations

import contextlib
import csv
import importlib
import io
import sys
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
STAGED = ROOT / "out" / "x22" / "staged"
OUT = ROOT / "out" / "x28"
TABLES = {  # file -> the columns SAS writes without a selection (no Step, no RowId in the global tests)
    "printed_global_tests.csv": ["Test", "ChiSq", "DF", "ProbChiSq"],
    "printed_fit_statistics.csv": ["RowId", "Criterion", "InterceptOnly", "InterceptAndCovariates"],
    "printed_rsquare.csv": ["Label1", "cValue1", "nValue1", "Label2", "cValue2", "nValue2"],
}


def _rows(path: Path, cols: list[str], drop_step0: bool) -> list[list[str]]:
    with path.open() as fh:
        rows = list(csv.DictReader(fh))
    if drop_step0:
        rows = [r for r in rows if r.get("Step") != "0"]
    return [[r.get(c, "") for c in cols] for r in rows]


def _same(sas: str, port: str) -> bool:
    """Equal cells; a number to the decimals SAS prints (D12.3 InterceptOnly prints 12.172 in SAS's CSV of a run
    without selection, 12.171929 in the port's)."""
    if sas == port:
        return True
    try:
        d = len(sas.split(".")[1]) if "." in sas else 0
        return abs(float(sas) - float(port)) <= 0.5 * 10.0**-d
    except ValueError:
        return False


def main(port_dir: str) -> int:
    sys.path.insert(0, port_dir)
    sys.path.insert(0, str(HERE))
    import numpy as np

    x22 = importlib.import_module("x22_left_out_final")
    from credit_risk import sas_compat, train

    assert Path(sas_compat.__file__).resolve().is_relative_to(Path(port_dir).resolve()), sas_compat.__file__
    x22.make()
    bad = 0
    for name, (cols, _rows_) in x22.designs().items():
        out = OUT / Path(port_dir).resolve().name / name
        out.mkdir(parents=True, exist_ok=True)
        for p in out.iterdir():
            p.unlink()
        real = sas_compat.stepwise_logistic

        def one_step(df: Any, response: str, candidates: Any, *a: Any, _cols: list[str] = cols) -> Any:
            used = df.select([response, *candidates]).drop_nulls()
            y = used.get_column(response).to_numpy().astype(np.float64)
            x = np.column_stack([np.ones(len(y)), *[used.get_column(c).to_numpy().astype(np.float64) for c in _cols]])
            fit = sas_compat._fit_as_sas(x, y, ["Intercept", *_cols])
            io_fit = sas_compat.fit_logistic(x[:, :1], y, ["Intercept"])
            step = sas_compat.StepwiseStep(1, _cols[-1], None, 1, len(_cols), 0.0, None, 0.0, fit)
            return sas_compat.StepwiseResult([step], fit, io_fit)

        sas_compat.stepwise_logistic = one_step  # type: ignore[assignment]
        try:
            with contextlib.redirect_stdout(io.StringIO()):
                train.run(STAGED / name, out)
        except Exception as e:  # noqa: BLE001
            print(f"{name}: train.py stopped: {type(e).__name__}: {e}")
            bad += 1
            continue
        finally:
            sas_compat.stepwise_logistic = real  # type: ignore[assignment]
        sas_dir = ROOT / "judge" / "runs" / f"x22_{name}"
        for f, c in TABLES.items():
            want = _rows(sas_dir / f, c, False)
            got = _rows(out / f, c, f == "printed_fit_statistics.csv")
            ok = len(want) == len(got) and all(_same(a, b) for wr, gr in zip(want, got) for a, b in zip(wr, gr))
            bad += not ok
            print(f"{name}: {f}: {'as SAS' if ok else 'DIFFERS'}")
            if not ok:
                print(f"   SAS  {want}\n   port {got}")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
