"""X17: the port's fit against SAS's iteration histories (x17_sas_iteration_histories.json).

(1) The ridge rule, replayed in three readings on every step of every run whose feature file is at
    hand, and compared with SAS line by line (ridge and -2 Log L of every iteration, the stop
    iteration, the last estimates):
      minus1  the rule of sas_compat._fit_as_sas: a step that lowers the log likelihood is retaken
              with the diagonal of the information matrix times 1 + 1e-4 * 4**j, j one up until the
              log likelihood is not lower; j is kept through the fit and goes one down after an
              iteration whose first ridge was accepted
      keep    j never goes down
      reset   j goes back to 0 after an iteration whose first ridge was accepted
(2) sas_compat._fit_as_sas itself on the same steps: stop iteration, estimates, -2 Log L.

Usage (from port/): uv run python ../migration/legacy-to-port/experiments/x17_port_check.py
Result 2026-11-17 (18 runs, 211 steps, 393 ridged iterations): minus1 and the port reproduce every
step; keep fails on 17 steps (among them real, step 8); reset fails on 7 (sub50000_2 steps 20 to
25, sub80000_2 step 8).
"""

from __future__ import annotations

import json
import math
import random
import sys
from pathlib import Path

import numpy as np
import polars as pl

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT / "port"))
from credit_risk import sas_compat  # noqa: E402

SAS = json.loads((HERE / "x17_sas_iteration_histories.json").read_text())
Arr = np.ndarray


def features(case: str) -> pl.DataFrame | None:
    ref = ROOT / "judge/reference/model_features_train.csv"
    if case == "real":
        return pl.read_csv(ref, infer_schema_length=None)
    if case.startswith("sub"):
        n, seed = (int(v) for v in case[3:].split("_"))
        df = pl.read_csv(ref, infer_schema_length=None)
        return df[sorted(random.Random(1000 * seed + n).sample(range(len(df)), n))]
    path = ROOT / "judge/runs" / f"gen_{case}" / "model_features_train.csv"
    return pl.read_csv(path, infer_schema_length=None) if path.exists() else None


def loglik(eta: Arr, y: Arr) -> float:
    return float(np.sum(y * eta - np.logaddexp(0.0, eta)))


def replay(x: Arr, y: Arr, variant: str) -> tuple[list[float], list[float], Arr, str]:
    b = np.zeros(x.shape[1])
    b[0] = math.log(y.sum() / (len(y) - y.sum()))
    ll = loglik(x @ b, y)
    j = 0
    ridges: list[float] = []
    m2 = [-2 * ll]
    for _ in range(25):
        p = 1.0 / (1.0 + np.exp(-(x @ b)))
        w = p * (1 - p)
        info = x.T @ (x * w[:, None])
        g = x.T @ (y - p)
        nb = b + np.linalg.solve(info, g)
        nll = loglik(x @ nb, y)
        ridge = 0.0
        if nll < ll:
            first = True
            while True:
                ridge = 1e-4 * 4.0**j
                nb = b + np.linalg.solve(info + np.diag(ridge * np.diag(info)), g)
                nll = loglik(x @ nb, y)
                if not nll < ll:
                    break
                j += 1
                first = False
                if j > 40:
                    return ridges, m2, b, "no ridge found"
            if first and variant == "minus1":
                j = max(j - 1, 0)
            if first and variant == "reset":
                j = 0
        b, ll = nb, nll
        ridges.append(ridge)
        m2.append(-2 * ll)
        p = 1.0 / (1.0 + np.exp(-(x @ b)))
        w = p * (1 - p)
        g = x.T @ (y - p)
        if float(g @ np.linalg.solve(x.T @ (x * w[:, None]), g)) / (abs(ll) + 1e-6) < 1e-8:
            return ridges, m2, b, "gconv"
    return ridges, m2, b, "25 iterations"


def main() -> None:
    fails: dict[str, list[str]] = {"minus1": [], "keep": [], "reset": [], "port": []}
    steps = ridged = 0
    worst = 0.0
    for case, hist in SAS.items():
        df = features(case)
        if df is None:
            print(f"{case}: feature file not at hand, skipped")
            continue
        y = df["default_flag"].to_numpy().astype(float)
        for st in hist:
            cols = [
                df[next(c for c in df.columns if c[:32] == v)].to_numpy().astype(float)
                for v in st["variables"]
            ]
            x = np.column_stack([np.ones(len(y)), *cols])
            sas_b = np.array(st["estimates"])
            steps += 1
            ridged += sum(r > 0 for r in st["ridge"])
            for variant in ("minus1", "keep", "reset"):
                ridges, m2, b, how = replay(x, y, variant)
                ok = (
                    how == "gconv"
                    and len(ridges) == len(st["ridge"])
                    and all(abs(a - r) < 1e-12 for a, r in zip(ridges, st["ridge"], strict=True))
                    and all(abs(a - r) <= 1e-9 * r for a, r in zip(m2, st["neg2loglike"], strict=True))
                    and np.allclose(b, sas_b, rtol=1e-9, atol=1e-11)
                )
                if not ok:
                    fails[variant].append(
                        f"{case} step {st['step']}: SAS ridges {st['ridge']}, {variant} {ridges} ({how})"
                    )
            fit = sas_compat._fit_as_sas(x, y, ["Intercept", *st["variables"]])
            if (
                fit is None
                or not fit.converged
                or fit.n_iter != len(st["ridge"])
                or not np.allclose(fit.beta, sas_b, rtol=1e-9, atol=1e-11)
                or abs(-2 * fit.loglik - st["neg2loglike"][-1]) > 1e-10 * st["neg2loglike"][-1]
            ):
                fails["port"].append(f"{case} step {st['step']}")
            else:
                worst = max(worst, float(np.abs(fit.beta - sas_b).max()))
        print(f"{case}: {len(hist)} steps", flush=True)
    print(f"\n{steps} steps, {ridged} ridged iterations in SAS")
    for name, bad in fails.items():
        print(f"{name}: {len(bad)} step(s) not reproduced")
        for line in bad:
            print("   ", line)
    print(f"port: largest difference of an estimate from SAS's, over the reproduced steps: {worst:.1e}")


if __name__ == "__main__":
    main()
