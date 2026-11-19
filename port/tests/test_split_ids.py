"""The split file's row_id values are SAS numbers (doubles), matched by value (finding G1).
The split selects exactly (7n+9)/10 distinct ids among the input's (T0, owner 2026-11-19).

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


ROOT = HERE.parent.parent


def _outputs(d: Path) -> tuple[list[float], list[float]]:
    train = pl.read_csv(d / "model_features_train.csv").get_column("row_id").cast(pl.Float64)
    valid = pl.read_csv(d / "model_features_validation.csv").get_column("row_id").cast(pl.Float64)
    return sorted(train.to_list()), sorted(valid.to_list())


def _run(ids: list[str], split: list[str]) -> tuple[list[float], list[float]]:
    with tempfile.TemporaryDirectory() as tmp:
        d = Path(tmp)
        (d / "cs-training.csv").write_text(
            HEADER + "\n" + "".join(f"{i},0,0,0,0,0,0,0,0,0,0,0\n" for i in ids)
        )
        (d / "split_ids.csv").write_text("row_id\n" + "".join(f"{i}\n" for i in split))
        feature_engineering.run(d, d, split_ids=d / "split_ids.csv")
        return _outputs(d)


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


def _check_exact(n: int, split: list[str]) -> tuple[list[float], list[float]]:
    ids = [str(i) for i in range(1, n + 1)]
    train, valid = _run(ids, split)
    assert len(train) == (7 * n + 9) // 10, (n, train)
    assert len(set(train)) == len(train)
    assert set(train) <= {float(i) for i in ids}
    assert sorted(train + valid) == [float(i) for i in ids]
    return train, valid


def test_file_that_does_not_fit_is_replaced() -> None:
    # T0 witnesses: an empty file, ids not in the input, too many, too few, repeated ids
    for split in ([], ["101", "102", "103"], ["1", "2", "3", "4", "5", "6"], ["1"], ["1", "1", "2"]):
        _check_exact(6, split)


def test_counts_n_4_5_10() -> None:
    assert len(_check_exact(4, [])[0]) == 3
    assert len(_check_exact(5, [])[0]) == 4
    assert len(_check_exact(10, [])[0]) == 7
    # a fitting file is kept as given
    assert _check_exact(10, ["1", "2", "3", "4", "5", "6", "7"])[0] == [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0]


def test_draw_is_seeded() -> None:
    assert _check_exact(10, []) == _check_exact(10, [])


def test_real_data_keeps_sas_split() -> None:
    reference = ROOT / "judge" / "reference"
    ref_train = pl.read_csv(reference / "model_features_train.csv").get_column("row_id").cast(pl.Float64)
    ref_valid = pl.read_csv(reference / "model_features_validation.csv").get_column("row_id").cast(pl.Float64)
    with tempfile.TemporaryDirectory() as tmp:
        d = Path(tmp)
        (d / "split_ids.csv").write_text("row_id\n" + "".join(f"{i}\n" for i in ref_train.to_list()))
        feature_engineering.run(ROOT / "legacy" / "data", d, split_ids=d / "split_ids.csv")
        train, valid = _outputs(d)
    assert train == sorted(ref_train.to_list())
    assert valid == sorted(ref_valid.to_list())


if __name__ == "__main__":
    test_fractional_ids_g1_witness()
    test_whole_ids_match_by_value()
    test_file_that_does_not_fit_is_replaced()
    test_counts_n_4_5_10()
    test_draw_is_seeded()
    test_real_data_keeps_sas_split()
    print("ok")
