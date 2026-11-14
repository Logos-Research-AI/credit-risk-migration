"""Reproduce SAS ctable (Classification) from model features + pd; write candidate CSV."""
import sys, os, math
import numpy as np, polars as pl
J = "/Users/cristophersalvi/GitHub/sas-migration/judge"
MODEL_VARS = ["credit_utilization_capped", "debt_ratio_capped", "has_delinquency", "has_serious_delinquency",
              "log_monthly_income", "num_real_estate_loans", "num_dependents", "income_per_dependent",
              "credit_lines_per_person", "flag_high_utilization", "flag_very_high_utilization",
              "flag_very_high_debt_ratio", "flag_recent_late_payments", "flag_multiple_delinquencies",
              "flag_few_credit_lines", "credit_util_category", "financial_health", "age_income_interaction"]

def pct(num, den):
    return None if den == 0 else 100.0 * num / den

def fmt1(v):
    return "" if v is None else f"{v:.1f}"

def ctable(X, y, p, mode="loo", ge=True, grid=None):
    w = p * (1 - p)
    V = np.linalg.inv((X * w[:, None]).T @ X)
    q = np.einsum("ij,jk,ik->i", X, V, X)  # x'Vx
    h = w * q
    eta = np.log(p / (1 - p))
    if mode == "loo":
        ps = 1 / (1 + np.exp(-(eta - (y - p) * q / (1 - h))))
    else:
        ps = p
    if grid is None:
        lo = math.floor(p.min() / 0.02 + 1e-9) * 0.02  # round down to 0.02
        hi = math.ceil(p.max() / 0.02 - 1e-9) * 0.02   # round up to 0.02
        grid = np.round(np.arange(lo, hi + 1e-9, 0.02), 3)
    n1 = int(y.sum()); n0 = len(y) - n1; rows = []
    for z in grid:
        pe = ps >= z if ge else ps > z
        ce = int((pe & (y == 1)).sum()); ie = int((pe & (y == 0)).sum())
        cn = n0 - ie; inn = n1 - ce
        rows.append((z, ce, cn, ie, inn, pct(ce + cn, n1 + n0), pct(ce, n1), pct(cn, n0),
                     pct(ie, ce + ie), pct(inn, cn + inn), pct(ce, ce + ie), pct(cn, cn + inn)))
    return rows, ps, h

if __name__ == "__main__":
    scores, out = sys.argv[1], sys.argv[2]
    mode = sys.argv[3] if len(sys.argv) > 3 else "loo"
    ge = (sys.argv[4] if len(sys.argv) > 4 else "ge") == "ge"
    f = pl.read_csv(f"{J}/reference/model_features_train.csv", infer_schema_length=0).select(["row_id"] + MODEL_VARS)
    s = pl.read_csv(scores, infer_schema_length=0).select("row_id", "default_flag", "pd_logistic")
    d = s.join(f, on="row_id", how="inner")
    assert d.height == 105000
    X = np.column_stack([np.ones(d.height)] + [d[c].cast(pl.Float64).to_numpy() for c in MODEL_VARS])
    y = d["default_flag"].cast(pl.Int64).to_numpy(); p = d["pd_logistic"].cast(pl.Float64).to_numpy()
    rows, ps, h = ctable(X, y, p, mode, ge)
    print(f"pd min {p.min():.5f} max {p.max():.5f}; P* min {ps.min():.5f} max {ps.max():.5f}; max leverage {h.max():.4f}")
    os.makedirs(out, exist_ok=True)
    with open(f"{out}/printed_classification.csv", "w") as fh:
        fh.write("ProbLevel,CorrectEvents,CorrectNonevents,IncorrectEvents,IncorrectNonevents,Correct,Sensitivity,Specificity,FalsePositive,FalseNegative,PPV,NPV\n")
        for r in rows:
            fh.write(f"{r[0]:.3f},{r[1]},{r[2]},{r[3]},{r[4]}," + ",".join(fmt1(v) for v in r[5:]) + "\n")
