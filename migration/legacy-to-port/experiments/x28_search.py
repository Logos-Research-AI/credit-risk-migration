"""Linear algebra after the fit on the train path: does any call raise on a valid input?

For random outcome columns on known training parts (as search.py), runs the port's selection and then, per
step and on the final model, the calls train.py makes after the fit: np.linalg.solve(i0, u0) (the global
score test), sas_compat.global_wald, classification_is_made and classification_table (pd as train.py forms
it). Also measures, at every entry test, the alias ratio resid / zwz of every candidate that is an exact linear
combination of the model's columns (least squares residual below 1e-10 of its norm): an exactly collinear
column that passes the 1e-8 alias test would make X'X singular at the next step.

usage (from port/): uv run python ../migration/legacy-to-port/experiments/x28_search.py <n per set> <seed> <out.jsonl> [mode] [sets]
  sets: names under judge/runs, or refN (an N-row slice of the reference features). Runs of 2026-11-18, port at 41608e6:
  (4, 1), (150, 2) on the 15 parts; (40, 3) on ref300,ref1000,ref5000; (300, 4, sep) on ref200,ref1000,ref5000;
  (1500, 5, probe) on ref60,ref200,ref1000.
"""

from __future__ import annotations

import contextlib
import io
import json
import multiprocessing as mp
import sys
import warnings
from pathlib import Path

import numpy as np

sys.path.insert(0, "/Users/cristophersalvi/GitHub/credit-risk-migration/port")
RUNS = Path("/Users/cristophersalvi/GitHub/credit-risk-migration/judge/runs")
REF = Path("/Users/cristophersalvi/GitHub/credit-risk-migration/judge/reference/model_features_train.csv")
SETS = [
    "gen_s01", "gen_s03", "gen_s10", "gen_s25", "gen_s26", "gen_s27", "gen_s28", "gen_s29",
    "rawfit_Ca", "rawfit_Cb", "rawfit_Cc", "rawfit_Cd", "rawfit_Da", "rawfit_Dd", "rawfit_Dn6",
]
CANDS = [
    "credit_utilization_capped", "debt_ratio_capped", "num_late_30_59", "num_late_60_89", "num_late_90_plus",
    "total_late_payments", "has_delinquency", "has_serious_delinquency", "age", "monthly_income",
    "log_monthly_income", "num_credit_lines", "num_real_estate_loans", "log_num_credit_lines", "num_dependents",
    "income_per_dependent", "credit_lines_per_person", "flag_high_utilization", "flag_very_high_utilization",
    "flag_high_debt_ratio", "flag_very_high_debt_ratio", "flag_recent_late_payments", "flag_serious_delinquency",
    "flag_multiple_delinquencies", "flag_low_income", "flag_many_dependents", "flag_few_credit_lines",
    "total_risk_flags", "credit_util_category", "debt_category", "age_category", "financial_health",
    "age_income_interaction", "utilization_debt_interaction", "MonthlyIncome_missing", "Dependents_missing",
]
ALIAS: list[dict] = []


def _install() -> None:
    from credit_risk import sas_compat as sc

    real = sc._entry_score_chisq

    def wrapped(x, y, cur, others):  # noqa: ANN001, ANN202
        out = real(x, y, cur, others)
        scored = {c for c, _ in out}
        p = sc._expit(x @ cur.beta)
        w = p * (1.0 - p)
        info = x.T @ (x * w[:, None])
        for c, z in others.items():
            nz = float(np.linalg.norm(z))
            if nz == 0.0:
                continue
            coef, *_ = np.linalg.lstsq(x, z, rcond=None)
            if float(np.linalg.norm(z - x @ coef)) > 1e-10 * nz:
                continue
            zwz = float(z @ (z * w))
            try:
                ratio = (zwz - float((x.T @ (z * w)) @ np.linalg.solve(info, x.T @ (z * w)))) / zwz
            except Exception:  # noqa: BLE001
                ratio = float("nan")
            ALIAS.append({"cand": c, "model": cur.names[1:], "ratio": ratio, "scored": c in scored,
                          "cond": float(np.linalg.cond(info))})
        return out

    sc._entry_score_chisq = wrapped


def outcome(df, rng, mode):  # noqa: ANN001, ANN201
    n = df.height
    y = np.zeros(n)
    if mode == "sep":  # strong late-payment effects (near separation) and a large-scale column
        def col(c):
            v = df.get_column(c).to_numpy().astype(float)
            m = np.nanmean(v)
            return np.nan_to_num(v, nan=float(m) if np.isfinite(m) else 0.0)
        k = rng.uniform(0.5, 12.0, 3) * rng.choice([-1.0, 1.0], 3)
        eta = (rng.normal(-3.0, 2.0) + k[0] * col("num_late_30_59") + k[1] * col("num_late_60_89")
               + k[2] * col("num_late_90_plus"))
        for c in rng.choice(len(CANDS), size=int(rng.integers(0, 3)), replace=False):
            v = col(CANDS[c])
            eta = eta + rng.normal(0, 2.0) * (v - v.mean()) / (float(v.std()) or 1.0)
        y = (rng.random(n) < 1.0 / (1.0 + np.exp(-np.clip(eta, -700, 700)))).astype(float)
    elif mode == "probe":  # as x28_alias_probe.py: a late-payment group, large-scale and random columns, strong effects
        groups = [["has_serious_delinquency"], ["num_late_30_59", "num_late_60_89", "num_late_90_plus"],
                  ["num_late_30_59", "num_late_60_89", "total_late_payments"]]
        big = ["monthly_income", "age_income_interaction", "income_per_dependent", "utilization_debt_interaction",
               "debt_ratio_capped", "credit_utilization_capped"]
        model = list(groups[int(rng.integers(len(groups)))])
        model += list(rng.choice(big, size=int(rng.integers(0, 4)), replace=False))
        model += list(rng.choice(CANDS, size=int(rng.integers(0, 6)), replace=False))
        eta = np.full(n, rng.normal(-2.0, 1.0) * (1 if rng.random() < 0.5 else 3))
        for c in set(model):
            v = df.get_column(c).to_numpy().astype(float)
            m = np.nanmean(v)
            v = np.nan_to_num(v, nan=float(m) if np.isfinite(m) else 0.0)
            eta = eta + rng.normal(0, 0.8 if rng.random() < 0.5 else 4.0) * (v - v.mean()) / (float(v.std()) or 1.0)
        y = (rng.random(n) < 1.0 / (1.0 + np.exp(-np.clip(eta, -700, 700)))).astype(float)
    elif mode == "rare" or rng.random() < 0.3:
        k = int(rng.integers(1, 5)) if rng.random() < 0.5 else int(rng.integers(1, max(2, n // 2)))
        y[rng.choice(n, size=min(k, n - 1), replace=False)] = 1.0
    else:
        eta = np.full(n, rng.normal(-1.5, 1.5))
        for c in rng.choice(len(CANDS), size=int(rng.integers(1, 5)), replace=False):
            col = df.get_column(CANDS[c]).to_numpy().astype(float)
            m = np.nanmean(col)
            col = np.nan_to_num(col, nan=float(m) if np.isfinite(m) else 0.0)
            sd = float(col.std()) or 1.0
            eta = eta + rng.normal(0, 2.0) * (col - col.mean()) / sd
        y = (rng.random(n) < 1.0 / (1.0 + np.exp(-eta))).astype(float)
    if rng.random() < 0.5:
        y = 1.0 - y
    return y


def one(task):  # noqa: ANN001, ANN201
    import polars as pl

    from credit_risk import sas_compat as sc

    name, seed, idx, mode = task
    rng = np.random.default_rng([seed, idx, sum(map(ord, name))])
    if name.startswith("ref"):
        full = sc.proc_import_csv(REF, guessingrows=None)
        size = int(name[3:])
        df = full.slice(int(rng.integers(0, full.height - size)), size)
    else:
        df = sc.proc_import_csv(RUNS / name / "model_features_train.csv", guessingrows=None)
    df = df.with_columns(default_flag=pl.Series(outcome(df, rng, mode)))
    mask = df.select(pl.all_horizontal(pl.col(*CANDS, "default_flag").is_not_null())).to_series().to_numpy()
    ff = df.filter(pl.Series(mask))
    yy = ff.get_column("default_flag").to_numpy().astype(float)
    if ff.height < 2 or yy.min() == yy.max():
        return None
    rec: dict = {"set": name, "seed": seed, "idx": idx, "n": ff.height, "events": int(yy.sum())}
    ALIAS.clear()
    buf = io.StringIO()
    try:
        with contextlib.redirect_stdout(buf), warnings.catch_warnings():
            warnings.simplefilter("ignore")
            res, _ = sc._stepwise_logistic_with_note(ff, "default_flag", CANDS, 0.05, 0.05)
    except Exception as e:  # noqa: BLE001
        rec["error"] = f"{type(e).__name__}: {e}"[:200]
    else:
        rec["steps"] = [(s.entered, s.removed) for s in res.steps]
        errs: list[str] = []
        ybar = float(yy.mean())
        for st in res.steps:
            if len(st.fit.names) == 1:
                continue
            x = np.column_stack([np.ones(ff.height), *[ff.get_column(c).to_numpy().astype(float) for c in st.fit.names[1:]]])
            u0 = x.T @ (yy - ybar)
            i0 = ybar * (1.0 - ybar) * (x.T @ x)
            if len(sc._kept(x.T @ x)) < x.shape[1]:
                errs.append(f"step {st.step}: X'X has a dependent column {st.fit.names}")
            try:
                float(u0 @ np.linalg.solve(i0, u0))
            except np.linalg.LinAlgError as e:
                errs.append(f"step {st.step}: score solve {e}")
            try:
                sc.global_wald(st.fit, CANDS)
            except np.linalg.LinAlgError as e:
                errs.append(f"step {st.step}: global_wald {e}")
        fin = res.final
        if fin is not None and len(fin.names) > 1:
            x = np.column_stack([np.ones(ff.height), *[ff.get_column(c).to_numpy().astype(float) for c in fin.names[1:]]])
            lo = [i for i in range(len(fin.names)) if float(fin.cov[i, i]) == 0.0]
            b = np.where(np.isin(np.arange(len(fin.names)), lo), 0.0, fin.beta)
            pd = np.asarray(pl.Series(x @ b).map_batches(lambda s: 1 / (1 + (-s).exp())).to_numpy(), dtype=float) if False else 1 / (1 + np.exp(-(x @ b)))
            try:
                if sc.classification_is_made(fin, x):
                    with warnings.catch_warnings():
                        warnings.simplefilter("ignore")
                        sc.classification_table(yy, x, pd=pd)
            except np.linalg.LinAlgError as e:
                errs.append(f"classification {e}")
        rec["la_errors"] = errs
    dep = [a for a in ALIAS if np.isfinite(a["ratio"])]
    rec["n_dep_tests"] = len(dep)
    if dep:
        top = max(dep, key=lambda a: abs(a["ratio"]))
        rec["max_dep_ratio"] = top["ratio"]
        rec["max_dep"] = top
        rec["dep_scored"] = [a for a in dep if a["scored"]]
    return rec


if __name__ == "__main__":
    per, seed, out = int(sys.argv[1]), int(sys.argv[2]), sys.argv[3]
    mode = sys.argv[4] if len(sys.argv) > 4 else ""
    sets = sys.argv[5].split(",") if len(sys.argv) > 5 else SETS
    tasks = [(s, seed, i, mode) for s in sets for i in range(per)]
    with mp.Pool(11, initializer=_install) as pool, open(out, "w") as fh:
        for r in pool.imap_unordered(one, tasks, chunksize=2):
            if r is not None:
                fh.write(json.dumps(r) + "\n")
                fh.flush()
