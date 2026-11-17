"""SAS names in DROP lists: case-insensitive, a name matching no column skipped (finding E4).

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


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print(f"{name}: ok")
