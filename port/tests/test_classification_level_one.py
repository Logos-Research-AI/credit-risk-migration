"""The classification table at the level printed 1.000 on a fit with a variable.

    cd port && uv run python tests/test_classification_level_one.py        (or: uv run pytest tests)

Two separated fits whose leave-one-out probabilities reach exactly 1: the 280 training rows of
tests/data/age_features_280.csv with the outcome "age above 55" and "age above 62" (final model
age, kept at iteration 8). SAS's tables are judge/runs/sep_age_gt_55 and sep_age_gt_62
(printed_classification.csv, copied to tests/data/sas_classification_age_gt_*.csv): at the level
1.000 SAS counts no observation as a predicted event. The other 50 rows of each table are compared
too, and the table of the real data must not change.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import polars as pl

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))
from credit_risk import sas_compat  # noqa: E402
from test_entry_score import frame, stepwise  # noqa: E402

DATA = HERE / "data"
COUNTS = ["CorrectEvents", "CorrectNonevents", "IncorrectEvents", "IncorrectNonevents"]
PERCENT = ["Correct", "Sensitivity", "Specificity", "FalsePositive", "FalseNegative", "PPV", "NPV"]


def table(cut: int) -> tuple[pl.DataFrame, np.ndarray]:
    df = frame(cut)
    res = stepwise(df)
    assert res.final is not None and res.final.names == ["Intercept", "age"], res.final
    y = df["default_flag"].to_numpy().astype(np.float64)
    x = np.column_stack([np.ones(len(y)), df["age"].to_numpy().astype(np.float64)])
    pd_ = sas_compat._expit(x @ res.final.beta)
    return sas_compat.classification_table(y, x, pd=pd_), pd_


def test_level_one_counts_nobody_as_sas() -> None:
    for cut in (55, 62):
        got, pd_ = table(cut)
        sas = pl.read_csv(DATA / f"sas_classification_age_gt_{cut}.csv", infer_schema=False)
        assert got.height == sas.height == 51, (cut, got.height, sas.height)
        assert [f"{v:.3f}" for v in got["ProbLevel"].to_list()] == sas["ProbLevel"].to_list()
        for c in COUNTS:
            assert [str(v) for v in got[c].to_list()] == sas[c].to_list(), (cut, c)
        for c in PERCENT:  # SAS prints one decimal; a 0/0 is blank
            mine = ["" if v is None else f"{v:.1f}" for v in got[c].to_list()]
            assert mine == [v or "" for v in sas[c].to_list()], (cut, c)
        last = got.row(-1, named=True)
        assert (last["CorrectEvents"], last["IncorrectEvents"]) == (0, 0), last
        print(f"  age > {cut}: 51 levels as SAS; {int((pd_ == 1.0).sum())} fitted probabilities are exactly 1; "
              f"at 1.000: {[last[c] for c in COUNTS]} (SAS {sas.row(-1)[1:5]})")


def test_real_data_table_is_the_reference() -> None:
    """Nothing reaches 1 on the real data: the table is still SAS's reference table."""
    ref = HERE.parents[1] / "judge" / "reference"
    feats = pl.read_csv(ref / "model_features_train.csv", infer_schema_length=None)
    scores = pl.read_csv(ref / "risk_scores_train.csv", infer_schema_length=None).select("row_id", "pd_logistic")
    names = pl.read_csv(ref / "model_coefficients.csv", infer_schema=False)["Variable"].to_list()[1:]
    full = {c[:20]: c for c in feats.columns}
    df = feats.join(scores, on="row_id", how="inner", maintain_order="left")
    y = df["default_flag"].to_numpy().astype(np.float64)
    x = np.column_stack([np.ones(len(y))] + [df[full[n]].to_numpy().astype(np.float64) for n in names])
    got = sas_compat.classification_table(y, x, pd=df["pd_logistic"].to_numpy().astype(np.float64))
    sas = pl.read_csv(ref / "printed_classification.csv", infer_schema=False)
    assert [f"{v:.3f}" for v in got["ProbLevel"].to_list()] == sas["ProbLevel"].to_list()
    off = sum(abs(int(a) - int(b)) for c in COUNTS for a, b in zip(got[c].to_list(), sas[c].to_list(), strict=True))
    worst = max(abs(int(a) - int(b)) for c in COUNTS for a, b in zip(got[c].to_list(), sas[c].to_list(), strict=True))
    assert worst <= 1, worst  # the judge's rule for this table (SAS's pd are printed with 10 digits here)
    print(f"  real data: {got.height} levels, every count within 1 of the reference (sum of differences {off})")


if __name__ == "__main__":
    for t in (test_level_one_counts_nobody_as_sas, test_real_data_table_is_the_reference):
        print(t.__name__)
        t()
    print("ALL OK")
