"""The entry score chi-square after a separated step that stays (separation-rule.md, part 3).

    cd port && uv run python tests/test_entry_score.py        (or: uv run pytest tests)

Data, all under tests/data:
  age_features_280.csv   the 280 training rows of generator seed 1's 400-row file (the feature file
                         of its SAS run). The outcome is replaced here by "age above the cut".
  sas_age_cuts.json      what SAS printed for the cuts 55, 59, 60, 62, 64, 66, 71 on those rows
                         (out/separation/sas/P10, P11, P20 to P24, 32-character numbers): the steps
                         with their chi-squares, the final estimates, and for 55, 59, 60, 62 and 64
                         the score chi-square of all 35 candidates after step 1 (age, separated).
  real_data_steps_before.txt  the port's 19 steps on judge/reference/model_features_train.csv as
                         hex floats, written by the port BEFORE this change (commit 237b5cc),
                         with the fully converged estimates the port then had on a converged step.
"""

from __future__ import annotations

import contextlib
import io
import json
import re
import sys
from pathlib import Path

import numpy as np
import polars as pl

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from credit_risk import sas_compat  # noqa: E402

DATA = HERE / "data"
SAS = json.loads((DATA / "sas_age_cuts.json").read_text())
_train = (HERE.parent / "credit_risk" / "train.py").read_text()
_start = _train.index("candidates = [")
CANDIDATES = re.findall(r'"([A-Za-z_0-9]+)"', _train[_start : _train.index("]", _start)])
assert len(CANDIDATES) == 36, CANDIDATES
REL = 1e-9  # SAS's numbers are printed with 15 digits; the two sides solve the same systems differently


def frame(cut: int) -> pl.DataFrame:
    df = pl.read_csv(DATA / "age_features_280.csv", infer_schema_length=None)
    return df.with_columns((pl.col("age") > cut).cast(pl.Int64).alias("default_flag"))


def stepwise(df: pl.DataFrame) -> sas_compat.StepwiseResult:
    with contextlib.redirect_stdout(io.StringIO()):  # the separation warnings
        return sas_compat.stepwise_logistic(df, "default_flag", CANDIDATES, 0.05, 0.05)


def close(a: float, b: float) -> bool:
    return abs(a - b) <= REL * abs(b)


def test_steps_and_final_model_are_sas() -> None:
    """Every cut: the port's steps, their chi-squares and the final estimates are SAS's. Cut 59 is
    the one whose final model was different before (the port ended with age and age_category)."""
    for cut, sas in SAS.items():
        res = stepwise(frame(int(cut)))
        mine = [(s.entered or "", s.removed or "", s.score_chisq if s.entered else s.wald_chisq) for s in res.steps]
        assert [(e[:20], r[:20]) for e, r, _ in mine] == [(s["entered"], s["removed"]) for s in sas["steps"]], (cut, mine)
        for (_, _, v), s in zip(mine, sas["steps"], strict=True):
            assert v is not None and close(v, s["chisq"]), (cut, v, s["chisq"])
        assert res.final is not None
        assert [n[:20] for n in res.final.names] == list(sas["final"]), (cut, res.final.names)
        for b, (name, est) in zip(res.final.beta, sas["final"].items(), strict=True):
            assert close(float(b), est), (cut, name, float(b), est)
        print(f"  age > {cut}: steps {[(e or '-' + r)[:20] for e, r, _ in mine]}, final {res.final.names[1:]}: as SAS")
    assert [n for n in stepwise(frame(59)).final.names] == ["Intercept", "age"]


def test_entry_chisq_after_the_separated_step_is_sas() -> None:
    """After step 1 (age, complete separation, kept at iteration 8) the score chi-square of each of
    the 35 other candidates is the number SAS printed (DETAILS), 175 numbers over five cuts."""
    worst = 0.0
    for cut, sas in SAS.items():
        printed = sas["entry_after_step_1"]
        if not printed:
            continue
        df = frame(int(cut))
        y = df["default_flag"].to_numpy().astype(np.float64)
        x = np.column_stack([np.ones(len(y)), df["age"].to_numpy().astype(np.float64)])
        fit = sas_compat._fit_as_sas(x, y, ["Intercept", "age"])
        assert fit is not None and fit.separation == "complete" and fit.n_iter == 8, cut
        others = {c: df[c].to_numpy().astype(np.float64) for c in CANDIDATES if c != "age"}
        got = dict(sas_compat._entry_score_chisq(x, y, fit, others))
        assert {c[:20] for c in got} == set(printed), (cut, set(printed) ^ {c[:20] for c in got})
        for c, v in got.items():
            worst = max(worst, abs(v - printed[c[:20]]) / printed[c[:20]])
            assert close(v, printed[c[:20]]), (cut, c, v, printed[c[:20]])
        best = max(got, key=lambda c: got[c])
        print(f"  age > {cut}: 35 score chi-squares as SAS; largest {best} = {got[best]:.4f}")
    print(f"  largest relative difference from SAS over the 175 numbers: {worst:.1e}")


def test_real_data_keeps_its_steps() -> None:
    """The real data (no separated step): the same 19 steps and the same final variables as before
    the entry score change (commit 237b5cc). Since SAS's estimates replaced the fully converged
    ones on a converged step (`_fit_as_sas`, 2026-11-17) the numbers are no longer the same bits:
    they are within 1e-3 relative of the earlier ones (test_fit_as_sas.py compares them with SAS)."""
    df = pl.read_csv(HERE.parents[1] / "judge" / "reference" / "model_features_train.csv", infer_schema_length=None)
    res = stepwise(df)
    assert res.final is not None
    text = (DATA / "real_data_steps_before.txt").read_text().splitlines()
    before = [line.split(" ") for line in text[:-1]]
    assert len(res.steps) == len(before)
    worst = 0.0
    for s, b in zip(res.steps, before):
        assert [str(s.step), s.entered or "-", s.removed or "-", str(s.fit.separation)] == [b[0], b[1], b[2], b[5]], b
        v = s.score_chisq if s.entered else s.wald_chisq
        assert v is not None
        worst = max(worst, abs(float(v) - float.fromhex(b[3])) / float.fromhex(b[3]))
    assert text[-1].startswith(f"final {res.final.names} "), text[-1][:80]
    old_beta = [float.fromhex(h) for h in re.findall(r"'(-?0x[^']+)'", text[-1])]
    assert len(old_beta) == len(res.final.beta)
    worst_beta = max(abs(float(n) - o) for n, o in zip(res.final.beta, old_beta))
    assert worst < 1e-3 and worst_beta < 1e-3, (worst, worst_beta)
    print(f"  real data: the same {len(res.steps)} steps and final variables; chi-squares within {worst:.1e} relative,")
    print(f"  final estimates within {worst_beta:.1e} of the fully converged ones")


if __name__ == "__main__":
    for t in (test_steps_and_final_model_are_sas, test_entry_chisq_after_the_separated_step_is_sas,
              test_real_data_keeps_its_steps):
        print(t.__name__)
        t()
    print("ALL OK")
