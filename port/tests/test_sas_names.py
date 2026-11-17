"""SAS names in DROP and KEEP lists: case-insensitive, a name matching no column skipped (finding E4).

cd port && uv run python tests/test_sas_names.py        (or: uv run pytest tests)
"""

from __future__ import annotations

import sys
from pathlib import Path

import polars as pl

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from credit_risk import sas_compat  # noqa: E402

PREFIXES = ("IP_", "XP_")
NAMES = ("_FROM_", "_INTO_", "_LEVEL_")


def test_drop_e4_witness() -> None:
    # finding E4: one row, one numeric column IP_X; SAS's clean export has no IP_X
    frame = pl.DataFrame({"IP_X": [0.0]})
    out = sas_compat.drop_sas_names(frame, PREFIXES, NAMES)
    assert out.columns == []


def test_drop_any_case_keeps_order_and_rows() -> None:
    frame = pl.DataFrame(
        {
            "row_id": [1, 2, 3],
            "ip_a": [0.1, 0.2, 0.3],
            "pd_logistic": [0.5, 0.6, 0.7],
            "Xp_1": [1.0, 2.0, 3.0],
            "_level_": [1, 1, 1],
            "_From_": ["0", "1", "0"],
            "_INTO_": ["1", "0", "1"],
            "IPX": [9, 9, 9],  # no underscore: not in IP_:
            "a_IP_": [8, 8, 8],  # IP_ inside the name, not at its start
            "risk_grade": ["A", "B", "C"],
        }
    )
    out = sas_compat.drop_sas_names(frame, PREFIXES, NAMES)
    assert out.columns == ["row_id", "pd_logistic", "IPX", "a_IP_", "risk_grade"]
    assert out.height == 3
    assert out.equals(frame.select(out.columns))


def test_drop_nothing_matches() -> None:
    # SAS only warns for a name in the list that no column has (train.sas.log:636-639)
    frame = pl.DataFrame({"row_id": [1, 2], "pd_logistic": [0.1, None], "interest_rate": [0.05, 0.2]})
    out = sas_compat.drop_sas_names(frame, PREFIXES, NAMES)
    assert out.equals(frame)


def test_keep_any_case_pdv_order_stored_spelling() -> None:
    # predict.sas:426 keeps `age` from a test file headed AGE and SAS writes AGE in its PDV place
    # (judge/runs/ev11_round5_before/14_test_header_age_upper/test_predictions.csv)
    frame = pl.DataFrame(
        {
            "row_id": [1, 2],
            "AGE": [30.0, 41.0],
            "Monthly_Income": [None, 2500.0],
            "flag_low_income": [1, 0],
            "PD_Logistic": [0.1, 0.2],
        }
    )
    out = sas_compat.keep_sas_names(frame, {"pd_logistic", "age", "row_id", "monthly_income", "absent"})
    assert out.columns == ["row_id", "AGE", "Monthly_Income", "PD_Logistic"]
    assert out.equals(frame.select(out.columns))


def test_keep_exact_names_unchanged() -> None:
    frame = pl.DataFrame({"row_id": [1, 2, 3], "x": [1, 2, 3], "pd_logistic": [0.5, None, 0.25]})
    out = sas_compat.keep_sas_names(frame, {"row_id", "pd_logistic"})
    assert out.equals(frame.select([c for c in frame.columns if c in {"row_id", "pd_logistic"}]))


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print(f"{name}: ok")
