"""Recompute the Python run's digest with pd_logistic of risk_scores_train.csv / final_model_output.csv taken from a
correctly rounded exp (mpmath) instead of polars' exp; compare with the Lean digest given on the command line."""
import sys
sys.path.insert(0, "/Users/cristophersalvi/GitHub/credit-risk-migration/migration/port-to-lean/diffeval/units")
sys.path.insert(0, "/Users/cristophersalvi/GitHub/credit-risk-migration/migration/port-to-lean/diffeval")
import mpmath
import polars as pl
import fz10c_train_run_gen as g

mpmath.mp.prec = 200


def cr(e):
    return None if e is None else 1 / (1 + float(mpmath.exp(-mpmath.mpf(e))))


for arg in sys.argv[1:]:
    s, lean = map(int, arg.split(":"))
    r = g.pyrun(s)
    mj = r["model_json"]
    W = dict(r["writes"])
    ft = W["risk_scores_train.csv"]
    etas = []
    for row in ft.iter_rows(named=True):
        e = mj["intercept"]
        for c, b in mj["coefficients"].items():
            e = None if (e is None or row[c] is None) else e + b * row[c]
        etas.append(e)
    new = [cr(e) for e in etas]
    old = ft.get_column("pd_logistic").to_list()
    changed = [(i, etas[i], old[i], new[i]) for i in range(len(old)) if old[i] != new[i]]
    writes = []
    for n, df in r["writes"]:
        if n in ("risk_scores_train.csv", "final_model_output.csv"):
            assert df.get_column("pd_logistic").to_list() == old
            df = df.with_columns(pd_logistic=pl.Series(new, dtype=pl.Float64))
        writes.append((n, df))
    r2 = dict(r, writes=writes)
    print(s, "python", g.expected(r), "python with correctly rounded exp", g.expected(r2), "lean", lean,
          "MATCH" if g.expected(r2) == lean else "NO", "rows changed", changed)

# whole run with every polars Expr.exp and math.exp correctly rounded
import math
_pe, _me = pl.Expr.exp, math.exp


def crx(x):
    if x is None:
        return None
    try:
        return float(mpmath.exp(mpmath.mpf(x)))
    except OverflowError:
        return math.inf


pl.Expr.exp = lambda self: self.map_elements(crx, return_dtype=pl.Float64, skip_nulls=True)
math.exp = crx
try:
    for arg in sys.argv[1:]:
        s, lean = map(int, arg.split(":"))
        r = g.pyrun(s)
        print(s, "whole run, correctly rounded exp:", g.expected(r), "lean", lean, "MATCH" if g.expected(r) == lean else "NO")
finally:
    pl.Expr.exp, math.exp = _pe, _me
