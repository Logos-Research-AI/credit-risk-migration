"""Positive control for the judge: a "correct port" of the train stage.

Refits the SAS-selected logistic model on the reference features with Newton-Raphson to
full convergence (SAS stops earlier, at GCONV=1E-8), then rewrites the train-stage
row-level outputs exactly as SAS's rules would from the refit pd: score with
round-half-away-from-zero, grade/recommendation/rate, the 0.5 prediction, pd printed
with BEST12. A correct port behaves like this, so the judge must PASS it.
(Idea and first version: adversarial review C.)

Usage (from judge/): uv run python make_converged_candidate.py  -> fixtures/converged/
"""

from __future__ import annotations

import math
from pathlib import Path

import numpy as np
import polars as pl

import compare as C

JUDGE = Path(__file__).resolve().parent
REF = JUDGE / "reference"
OUT = JUDGE / "fixtures" / "converged"


def fit(X: np.ndarray, y: np.ndarray) -> np.ndarray:
    b = np.zeros(X.shape[1])
    for _ in range(100):
        p = 1 / (1 + np.exp(-X @ b))
        step = np.linalg.solve((X * (p * (1 - p))[:, None]).T @ X, X.T @ (y - p))
        b += step
        if np.abs(step).max() < 1e-14:
            return b
    raise RuntimeError("no convergence")


def sas_tuple(score: int) -> tuple[str, str, str]:
    grade = next((g for cut, g in ((750, "A"), (700, "B"), (650, "C"), (600, "D"), (550, "E")) if score >= cut), "F")
    rec = "Approve" if grade in ("A", "B") else "Review" if grade == "C" else "Decline"
    rate = {"A": 0.05, "B": 0.07, "C": 0.09, "D": 0.12, "E": 0.15}.get(grade, 0.20)
    return grade, rec, f"{rate * 100:.2f}%"


def main() -> None:
    variables = [v for v in C.read_text_csv(REF / "model_coefficients.csv")["Variable"].to_list() if v != "Intercept"]
    feats = {s: pl.read_csv(REF / f"model_features_{s}.csv") for s in ("train", "validation")}
    full = {c[:20]: c for c in feats["train"].columns}  # ODS truncates names to 20 chars
    cols = [full[v] for v in variables]
    X = lambda df: np.column_stack([np.ones(df.height)] + [df[c].to_numpy().astype(float) for c in cols])
    beta = fit(X(feats["train"]), feats["train"]["default_flag"].to_numpy().astype(float))
    OUT.mkdir(parents=True, exist_ok=True)
    pds = {}
    for s, df in feats.items():
        pd_ = 1 / (1 + np.exp(-X(df) @ beta))
        pds[s] = dict(zip(df["row_id"].to_list(), pd_))
    for f, s in (("risk_scores_train.csv", "train"), ("risk_scores_validation.csv", "validation"),
                 ("final_model_output.csv", "train")):
        ref = C.read_text_csv(REF / f)
        pd_ = [pds[s][int(r)] for r in ref["row_id"].to_list()]
        score = [math.floor(600 + 250 * (1 - p) + 0.5) for p in pd_]  # SAS round(): half away from 0
        tup = [sas_tuple(sc) for sc in score]
        upd = {"pd_logistic": [C.sas_best12(p) for p in pd_], "credit_risk_score": [str(x) for x in score],
               "risk_grade": [t[0] for t in tup], "recommendation": [t[1] for t in tup],
               "interest_rate": [t[2] for t in tup]}
        if "pred_logistic" in ref.columns:
            upd["pred_logistic"] = ["1" if p >= 0.5 else "0" for p in pd_]
        ref.with_columns([pl.Series(k, v, dtype=pl.Utf8) for k, v in upd.items()]).write_csv(OUT / f)
        d = np.abs(np.array(pd_) - ref["pd_logistic"].cast(pl.Float64).to_numpy())
        print(f"{f}: max|dpd|={d.max():.2e} mean|dpd|={d.mean():.2e} median={np.median(d):.2e}")


if __name__ == "__main__":
    main()
