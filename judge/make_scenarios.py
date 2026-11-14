"""Build edge-case INPUT scenarios (inputs only, never code) that drive the original SAS
through branches the real data never reaches (review B, finding 1). SAS's outputs on
these inputs become additional references the port is judged against.

  scenarios/edge_predict/     real cs-training.csv; cs-test.csv with MonthlyIncome = NA for
                              every applicant under 30. predict.sas imputes from TEST-set
                              medians, so age group 1 gets a missing median: monthly_income
                              stays missing and SAS missing-value semantics reach outputs
                              (flag_low_income = (. < 2500) = 1, log(.) missing, missing pd,
                              missing score -> grade F, Decline, 20%).
  scenarios/edge_metrics_a/   synthetic risk_scores_*.csv for metrics_calculation.sas:
                              weak signal (AUC ~0.6), pd rounded to 2 decimals (heavy ties
                              straddling decile/calibration boundaries -> PROC RANK tie
                              handling, unequal bins, non-zero PSI).
  scenarios/edge_metrics_b/   training pd heavily tied (1 decimal) vs validation pd at 3
                              decimals -> large PSI ("Significant change").
  scenarios/edge_metrics_c/   pd on 0.02 vs 0.01 grids -> PSI ~0.18 ("Some change"), AUC ~0.697
                              ("Requires Review").

Deterministic (fixed seeds). Usage (from judge/): uv run python make_scenarios.py
"""

from __future__ import annotations

import shutil
from pathlib import Path

import numpy as np
import polars as pl

JUDGE = Path(__file__).resolve().parent
DATA = JUDGE.parent / "legacy" / "data"
OUT = JUDGE / "scenarios"


def edge_predict() -> None:
    d = OUT / "edge_predict"
    d.mkdir(parents=True, exist_ok=True)
    shutil.copy(DATA / "cs-training.csv", d / "cs-training.csv")
    lines = (DATA / "cs-test.csv").read_text().splitlines(keepends=True)
    header, rows = lines[0], lines[1:]
    cols = header.rstrip("\n").split(",")
    i_age, i_inc = cols.index("age"), cols.index("MonthlyIncome")
    out, n = [header], 0
    for ln in rows:
        f = ln.rstrip("\n").split(",")
        if int(f[i_age]) < 30:
            f[i_inc] = "NA"
            n += 1
        out.append(",".join(f) + "\n")
    (d / "cs-test.csv").write_text("".join(out))
    print(f"edge_predict: MonthlyIncome set to NA for {n} applicants under 30")


def synthetic_scores(seed: int, n: int, signal: float, decimals: int, start_id: int,
                     step: float | None = None) -> pl.DataFrame:
    rng = np.random.default_rng(seed)
    latent = rng.normal(size=n)
    pd_ = 1 / (1 + np.exp(-(-2.6 + 0.9 * latent)))  # ~8% mean default rate
    y = (rng.random(n) < 1 / (1 + np.exp(-(-2.6 + signal * latent + rng.normal(scale=1.0, size=n))))).astype(int)
    if step is None:
        pd_ = np.clip(np.round(pd_, decimals), 10.0 ** -decimals, None)  # ties; keep pd > 0
    else:
        pd_ = np.clip(np.round(np.round(pd_ / step) * step, 6), step, None)  # grid ties
    # the score of the corrected train.sas (unrounded): metrics_calculation.sas bins it for PSI
    score = np.round(600 + 250 * (1 - pd_), 6)
    return pl.DataFrame({"row_id": np.arange(start_id, start_id + n), "default_flag": y, "pd_logistic": pd_,
                         "credit_risk_score": score})


def edge_metrics(name: str, seed: int, signal: float, dec_train: int, dec_valid: int,
                 step_train: float | None = None, step_valid: float | None = None) -> None:
    d = OUT / name
    d.mkdir(parents=True, exist_ok=True)
    tr = synthetic_scores(seed, 7000, signal, dec_train, 1, step_train)
    va = synthetic_scores(seed + 1, 3000, signal, dec_valid, 100001, step_valid)
    tr.write_csv(d / "risk_scores_train.csv")
    va.write_csv(d / "risk_scores_validation.csv")
    print(f"{name}: train distinct pd={tr['pd_logistic'].n_unique()}, valid distinct pd={va['pd_logistic'].n_unique()}, "
          f"default rate train={tr['default_flag'].mean():.3f} valid={va['default_flag'].mean():.3f}")


def real_metrics() -> None:
    """Stage inputs for metrics-only runs on the REAL data: the reference risk scores."""
    d = OUT / "real_metrics"
    d.mkdir(parents=True, exist_ok=True)
    for f in ("risk_scores_train.csv", "risk_scores_validation.csv"):
        shutil.copy(JUDGE / "reference" / f, d / f)
    print("real_metrics: copied reference risk_scores_*.csv")


if __name__ == "__main__":
    real_metrics()
    edge_predict()
    edge_metrics("edge_metrics_a", seed=11, signal=0.35, dec_train=2, dec_valid=2)
    edge_metrics("edge_metrics_b", seed=23, signal=0.6, dec_train=1, dec_valid=3)
    # tuned offline with an emulation of PROC RANK (reproduces SAS's PSI/AUC on edge_metrics_a
    # exactly): PSI ~0.18 ("Some change"), AUC ~0.697 ("Requires Review")
    edge_metrics("edge_metrics_c", seed=41, signal=0.9, dec_train=0, dec_valid=0, step_train=0.02, step_valid=0.01)
