"""The stepwise selection ends rather than have a model twice (migration/legacy-to-port/recycling-rule.md).

    cd port && uv run python tests/test_recycling.py        (or: uv run pytest tests)

tests/data/sas_recycling_cases.json: the training features of 19 small raw inputs as SAS wrote them
(judge/runs/rawfit_<case>/model_features_train.csv, the 36 MODEL variables and the outcome), with
SAS's steps (stepwise_summary.csv), the variables of its final model, and its note on why the
selection ended (train.sas.lst). The 13 inputs Da to Dn6 are those of experiment x18.
"""

from __future__ import annotations

import contextlib
import io
import json
import sys
from pathlib import Path
from typing import Any

import polars as pl

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from credit_risk import sas_compat  # noqa: E402

CASES: list[dict[str, Any]] = json.loads((HERE / "data" / "sas_recycling_cases.json").read_text())
RECYCLING = "Model building terminates because of recycling of previous steps."
NEXT_ENTRY = "Model building terminates because the next effect to be added recycles previous steps."
LAST_ENTERED = (
    "Model building terminates because the last effect entered is removed by the Wald statistic criterion."
)


def select(case: dict[str, Any]) -> tuple[sas_compat.StepwiseResult, str]:
    df = pl.DataFrame({"default_flag": case["y"], **case["columns"]})
    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
        return sas_compat._stepwise_logistic_with_note(df, "default_flag", list(case["columns"]), 0.05, 0.05)


def steps(res: sas_compat.StepwiseResult) -> list[list[str]]:
    return [[(s.entered or "")[:20], (s.removed or "")[:20]] for s in res.steps]  # SAS prints 20 characters


def test_steps_final_model_and_note_are_sas() -> None:
    """Every case: SAS's steps in SAS's order, SAS's final variables, and SAS's note for the way the
    selection ended. The note tells the three ends apart where the steps alone do not: a removal
    onto the empty model is the last step because the empty model of step 0 is one the selection
    has had (note "recycling of previous steps"), not because the next entry would recycle."""
    for case in CASES:
        res, note = select(case)
        assert steps(res) == case["steps"], (case["case"], steps(res), case["steps"])
        assert res.final is not None
        assert sorted(n[:20] for n in res.final.names[1:]) == sorted(case["final"]), (
            case["case"],
            res.final.names,
        )
        assert note == case["note"], (case["case"], note, case["note"])
    by_note: dict[str, int] = {}
    for case in CASES:
        by_note[case["note"]] = by_note.get(case["note"], 0) + 1
    assert by_note[RECYCLING] >= 7 and by_note[NEXT_ENTRY] >= 6 and by_note[LAST_ENTERED] >= 4, by_note
    assert len(by_note) == 4, by_note  # and one that ends with no candidate to enter
    print(f"  {len(CASES)} selections: steps, final model and closing note as SAS")
    for note, n in sorted(by_note.items()):
        print(f"    {n:2d}  {note}")


def test_the_cases_hold_each_shape_of_the_rule() -> None:
    """What the cases must contain for each part of the rule to be pinned."""
    by = {c["case"]: c for c in CASES}
    # a removal onto the empty model (rule 1 with the empty model of step 0 in the list)
    empty = [c for c in CASES if c["note"] == RECYCLING and not c["final"]]
    assert len(empty) >= 5
    # a removal onto an earlier model that is not the empty one
    assert [c["case"] for c in CASES if c["note"] == RECYCLING and c["final"]] == ["Dd", "De"]
    # the next entry would give an earlier model, and it is NOT the variable just removed (the port's
    # old special case): the last step removed another variable, or was an entry
    for name in ("Dn1", "Dn2", "Dn3", "Dn4", "Dn5", "Dn6"):
        assert by[name]["note"] == NEXT_ENTRY
    assert by["Dn1"]["steps"][-1][0] != ""  # ends after an entry
    # the second-best candidate is not tried: with it Dn1 to Dn4 would make further steps (checked by
    # mutation: candidates whose entry gives a model already had left out of the choice)
    print(
        f"  {len(empty)} removals onto the empty model, 2 onto another earlier model, 6 next entries that recycle"
    )


if __name__ == "__main__":
    for t in (test_steps_final_model_and_note_are_sas, test_the_cases_hold_each_shape_of_the_rule):
        print(t.__name__)
        t()
    print("ALL OK")
