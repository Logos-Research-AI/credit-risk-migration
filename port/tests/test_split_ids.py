"""The split file's row_id values are SAS numbers (doubles), matched by value (finding G1).

cd port && uv run python tests/test_split_ids.py        (or: uv run pytest tests)
"""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

import polars as pl

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from credit_risk import feature_engineering  # noqa: E402

HEADER = (
    ",SeriousDlqin2yrs,RevolvingUtilizationOfUnsecuredLines,age,NumberOfTime30-59DaysPastDueNotWorse,"
    "DebtRatio,MonthlyIncome,NumberOfOpenCreditLinesAndLoans,NumberOfTimes90DaysLate,"
    "NumberRealEstateLoansOrLines,NumberOfTime60-89DaysPastDueNotWorse,NumberOfDependents"
)


def _run(ids: list[str], split: list[str]) -> tuple[list[float], list[float]]:
    with tempfile.TemporaryDirectory() as tmp:
        d = Path(tmp)
        (d / "cs-training.csv").write_text(
            HEADER + "\n" + "".join(f"{i},0,0,0,0,0,0,0,0,0,0,0\n" for i in ids)
        )
        (d / "split_ids.csv").write_text("row_id\n" + "".join(f"{i}\n" for i in split))
        feature_engineering.run(d, d, split_ids=d / "split_ids.csv")
        train = pl.read_csv(d / "model_features_train.csv").get_column("row_id").cast(pl.Float64)
        valid = pl.read_csv(d / "model_features_validation.csv").get_column("row_id").cast(pl.Float64)
        return sorted(train.to_list()), sorted(valid.to_list())


def test_fractional_ids_g1_witness() -> None:
    # finding G1: VAR1 = 1/2, 1/4, 3/4, 1/5 is valid input; the split lists three of them
    train, valid = _run(["0.5", "0.25", "0.75", "0.2"], ["0.5", "0.25", "0.75"])
    assert train == [0.25, 0.5, 0.75]
    assert valid == [0.2]


def test_whole_ids_match_by_value() -> None:
    # whole ids as before; the text 3.0 names the id 3
    train, valid = _run(["1", "2", "3", "4"], ["1", "3.0", "4"])
    assert train == [1.0, 3.0, 4.0]
    assert valid == [2.0]


if __name__ == "__main__":
    test_fractional_ids_g1_witness()
    test_whole_ids_match_by_value()
    print("ok")
