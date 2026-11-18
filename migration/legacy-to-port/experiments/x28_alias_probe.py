"""How close does the port's alias test (relative residual information < 1e-8, _entry_score_chisq) come to
admitting a candidate that is an exact linear combination of the model's columns? Random models on row
subsets of the reference feature file, large-scale columns favoured, the model fitted with _fit_as_sas on a
random outcome; for every candidate exactly dependent on the model (least squares residual < 1e-10 of its
norm) the ratio the port computes. usage (from port/):
uv run python ../migration/legacy-to-port/experiments/x28_alias_probe.py <tasks> <seed> <out.jsonl>
Runs of 2026-11-18: (2000, 1) with outcome effects N(0, 0.8); (30000, 2) as the file is now (stronger effects)."""

from __future__ import annotations

import json
import multiprocessing as mp
import sys
import warnings
from pathlib import Path

import numpy as np

sys.path.insert(0, "/Users/cristophersalvi/GitHub/credit-risk-migration/port")
sys.path.insert(0, str(Path(__file__).parent))
from x28_search import CANDS, REF  # noqa: E402

BIG = ["monthly_income", "age_income_interaction", "income_per_dependent", "utilization_debt_interaction",
       "debt_ratio_capped", "credit_utilization_capped"]
GROUPS = [["has_serious_delinquency"], ["flag_serious_delinquency"],
          ["num_late_30_59", "num_late_60_89", "num_late_90_plus"],
          ["num_late_30_59", "num_late_60_89", "total_late_payments"]]
FULL = None


def one(task):  # noqa: ANN001, ANN201
    global FULL
    from credit_risk import sas_compat as sc
    import polars as pl

    seed, idx = task
    rng = np.random.default_rng([seed, idx])
    if FULL is None:
        FULL = sc.proc_import_csv(REF, guessingrows=None)
        FULL = FULL.filter(pl.all_horizontal(pl.col(*CANDS).is_not_null()))
    size = int(rng.choice([60, 200, 1000, 5000, 20000]))
    df = FULL.slice(int(rng.integers(0, FULL.height - size)), size)
    model = list(GROUPS[int(rng.integers(len(GROUPS)))])
    model += [c for c in rng.choice(BIG, size=int(rng.integers(0, 4)), replace=False) if c not in model]
    model += [c for c in rng.choice(CANDS, size=int(rng.integers(0, 6)), replace=False) if c not in model]
    model = sorted(set(model), key=CANDS.index)
    x = np.column_stack([np.ones(df.height), *[df.get_column(c).to_numpy().astype(float) for c in model]])
    if len(sc._kept(x.T @ x)) < x.shape[1]:
        return None  # the model itself is dependent: not reachable
    eta = rng.normal(-2.0, 1.0) * (1 if rng.random() < 0.5 else 3) + sum(rng.normal(0, 0.8 if rng.random() < 0.5 else 4.0) * (x[:, i] - x[:, i].mean()) / (x[:, i].std() or 1.0)
                                     for i in range(1, x.shape[1]))
    y = (rng.random(df.height) < 1 / (1 + np.exp(-eta))).astype(float)
    if y.min() == y.max():
        return None
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        try:
            fit = sc._fit_as_sas(x, y, ["Intercept", *model])
        except Exception:  # noqa: BLE001
            return None
    if fit is None or sc._left_out(fit):
        return None  # a left-out parameter is removed before any entry test
    p = sc._expit(x @ fit.beta)
    w = p * (1.0 - p)
    info = x.T @ (x * w[:, None])
    out = []
    for c in CANDS:
        if c in model:
            continue
        z = df.get_column(c).to_numpy().astype(float)
        nz = float(np.linalg.norm(z))
        if nz == 0.0:
            continue
        coef, *_ = np.linalg.lstsq(x, z, rcond=None)
        if float(np.linalg.norm(z - x @ coef)) > 1e-10 * nz:
            continue
        zwz = float(z @ (z * w))
        if zwz <= 0:
            continue
        v = x.T @ (z * w)
        ratio = (zwz - float(v @ np.linalg.solve(info, v))) / zwz
        out.append({"cand": c, "ratio": ratio})
    if not out:
        return None
    return {"idx": idx, "n": df.height, "model": model, "cond": float(np.linalg.cond(info)), "dep": out}


if __name__ == "__main__":
    n, seed, path = int(sys.argv[1]), int(sys.argv[2]), sys.argv[3]
    with mp.Pool(11) as pool, open(path, "w") as fh:
        for r in pool.imap_unordered(one, [(seed, i) for i in range(n)], chunksize=8):
            if r is not None:
                fh.write(json.dumps(r) + "\n")
