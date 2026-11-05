"""Reproduce SAS ROCAssociation (PROC LOGISTIC nofit + roc) and compare with the reference."""
import sys
import numpy as np
import polars as pl
from statistics import NormalDist

J = "/Users/cristophersalvi/GitHub/sas-migration/judge"


def roc_assoc(y, s, eps=0.0):
    y = np.asarray(y); s = np.asarray(s, dtype=float)
    ev, ne = s[y == 1], s[y == 0]
    n1, n0 = len(ev), len(ne)
    ne_sorted = np.sort(ne); ev_sorted = np.sort(ev)
    # per event: nonevents strictly lower (beyond eps) and tied (within eps)
    lo_ne = np.searchsorted(ne_sorted, ev - eps, side="left")    # ne < ev-eps
    le_ne = np.searchsorted(ne_sorted, ev + eps, side="right")   # ne <= ev+eps
    conc_e = lo_ne; tie_e = le_ne - lo_ne
    lo_ev = np.searchsorted(ev_sorted, ne - eps, side="left")
    le_ev = np.searchsorted(ev_sorted, ne + eps, side="right")
    conc_n = n1 - le_ev; tie_n = le_ev - lo_ev
    C = conc_e.sum(); T = tie_e.sum(); P = n1 * n0; D = P - C - T
    area = (C + 0.5 * T) / P
    v10 = (conc_e + 0.5 * tie_e) / n0
    v01 = (conc_n + 0.5 * tie_n) / n1
    var = v10.var(ddof=1) / n1 + v01.var(ddof=1) / n0
    se = np.sqrt(var)
    z = NormalDist().inv_cdf(0.975)
    n = n1 + n0
    return dict(Area=area, StdErr=se, LowerArea=area - z * se, UpperArea=area + z * se,
                SomersD=(C - D) / P, Gamma=(C - D) / (C + D), TauA=(C - D) / (n * (n - 1) / 2),
                C=int(C), D=int(D), T=int(T), n1=n1, n0=n0)


cases = [
    ("real train", f"{J}/reference/risk_scores_train.csv", f"{J}/reference/printed_roc_train.csv"),
    ("real valid", f"{J}/reference/risk_scores_validation.csv", f"{J}/reference/printed_roc_validation.csv"),
    ("real metrics", f"{J}/reference/risk_scores_validation.csv", f"{J}/reference/printed_roc_metrics.csv"),
] + [(f"edge {x}", f"{J}/scenarios/edge_metrics_{x}/risk_scores_validation.csv",
      f"{J}/reference/scenarios/edge_metrics_{x}/printed_roc_metrics.csv") for x in "abc"]

cols = ["Area", "StdErr", "LowerArea", "UpperArea", "SomersD", "Gamma", "TauA"]
eps = float(sys.argv[1]) if len(sys.argv) > 1 else 0.0
worst = {}
for name, data, ref in cases:
    d = pl.read_csv(data, infer_schema_length=0).select(
        pl.col("default_flag").cast(pl.Int64), pl.col("pd_logistic").cast(pl.Float64))
    r = roc_assoc(d["default_flag"].to_numpy(), d["pd_logistic"].to_numpy(), eps)
    refrow = pl.read_csv(ref, infer_schema_length=0).row(0, named=True)
    print(f"== {name}: n1={r['n1']} n0={r['n0']} C={r['C']} D={r['D']} T={r['T']}")
    for c in cols:
        rv = refrow[c]; dec = len(rv.split(".")[1])
        diff = abs(float(rv) - r[c])
        unit = 10 ** -dec
        worst[c] = max(worst.get(c, 0), diff / unit)
        print(f"  {c:10s} ref={rv:8s} ours={r[c]:.8f} printed={r[c]:.{dec}f} diff={diff:.2e} ({diff/unit:.3f} du) {'OK' if f'{r[c]:.{dec}f}'==rv else 'PRINT-DIFF'}")
print("worst diff in display units:", worst)
