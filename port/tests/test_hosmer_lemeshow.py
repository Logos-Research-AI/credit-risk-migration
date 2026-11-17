"""The Hosmer-Lemeshow tables on extreme fits: SAS's limits on a group's probability, and no table
below 3 groups.

    cd port && uv run python tests/test_hosmer_lemeshow.py        (or: uv run pytest tests)

tests/data/sas_hosmer_lemeshow.json: for 11 SAS runs (judge/runs/<run>), the outcome and the
probability of every training row as SAS wrote them (risk_scores_train.csv, 10 digits), SAS's two
tables (printed_hosmer_lemeshow.csv, printed_hl_partition.csv; null when SAS created none), and
whether its listing has the note "In calculating the Expected values, predicted probabilities less
than 1E-6 and greater than 0.999999 were changed to 1E-6 and 0.999999 respectively."
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import polars as pl

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from credit_risk import sas_compat  # noqa: E402

CASES: list[dict[str, Any]] = json.loads((HERE / "data" / "sas_hosmer_lemeshow.json").read_text())


def tables(case: dict[str, Any]) -> tuple[pl.DataFrame, dict[str, str]]:
    y = pl.Series(case["y"], dtype=pl.Int64)
    pd = pl.Series([float(v) for v in case["pd"]], dtype=pl.Float64)
    table, chisq, dof, p = sas_compat.hosmer_lemeshow(y, pd)
    test = {
        "ChiSq": sas_compat.fmt_wd(chisq, 10, 4).strip(),
        "DF": str(dof),
        "ProbChiSq": sas_compat.sas_pvalue(p).strip(),
        "NGroups": str(table.height),
    }
    return table, test


def group_means(table: pl.DataFrame) -> list[float]:
    return [r["EventsExpected"] / r["Total"] for r in table.to_dicts()]


def test_tables_are_sas() -> None:
    """Where SAS created the tables: the test's four cells and the partition, as SAS printed them."""
    n = 0
    for case in CASES:
        if case["test"] is None:
            continue
        table, test = tables(case)
        assert test == {k: v.strip() for k, v in case["test"].items()}, (case["run"], test, case["test"])
        mine = [
            [
                str(r["Group"]),
                str(r["Total"]),
                str(r["EventsObserved"]),
                f"{r['EventsExpected']:.2f}",
                str(r["NoneventsObserved"]),
                f"{r['NoneventsExpected']:.2f}",
            ]
            for r in table.to_dicts()
        ]
        assert mine == [[v.strip() for v in row] for row in case["partition"]], case["run"]
        n += 1
    print(f"  {n} runs: test and partition as SAS")


def test_the_limit_is_on_the_group_not_on_the_observation() -> None:
    """SAS's note goes with a GROUP whose average probability is outside [1e-6, 0.999999]. floorC has
    62 observations above 0.999999 and no group outside (its last group is at 1 - 1.31e-6): SAS has
    no note and the chi-square of the unlimited probabilities, 95.1047 (95.1048 if each observation
    were limited). floorB has groups outside on both sides: 0.3656 with the limits, 0.3644 without."""
    by = {c["run"]: c for c in CASES}
    for case in CASES:
        if case["test"] is None:
            continue
        table, _ = tables(case)
        means = group_means(table)
        # the port's groups are already limited: one AT a limit is one SAS changed
        at_limit = any(m <= 1e-6 * (1 + 1e-12) or m >= 0.999999 * (1 - 1e-12) for m in means)
        assert at_limit == case["note"], (case["run"], min(means), max(means))
    c = by["rawfit_floorC"]
    assert (
        not c["note"]
        and sum(float(v) > 0.999999 for v in c["pd"]) == 62
        and c["test"]["ChiSq"].strip() == "95.1047"
    )
    b = by["rawfit_floorB"]
    assert b["note"] and b["test"]["ChiSq"].strip() == "0.3656"
    assert sum(float(v) < 1e-6 for v in b["pd"]) > 1000 and sum(float(v) > 0.999999 for v in b["pd"]) > 600
    print("  SAS's note exactly on the runs with a group at a limit;")
    print("  floorC (observations beyond the limit, no group) is not limited")


def test_no_table_below_three_groups() -> None:
    """SAS creates the two tables with 3 groups or more and neither with 2."""
    seen: dict[int, set[bool]] = {}
    for case in CASES:
        table, _ = tables(case)
        printed = sas_compat.hosmer_lemeshow_is_printed(table.height)
        assert printed == (case["test"] is not None), (case["run"], table.height)
        seen.setdefault(table.height, set()).add(printed)
    assert seen[2] == {False} and seen[3] == {True} and seen[4] == {True}, seen
    print(f"  groups -> tables created: { ({k: next(iter(v)) for k, v in sorted(seen.items())}) }")


if __name__ == "__main__":
    for t in (
        test_tables_are_sas,
        test_the_limit_is_on_the_group_not_on_the_observation,
        test_no_table_below_three_groups,
    ):
        print(t.__name__)
        t()
    print("ALL OK")
