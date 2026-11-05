"""Full HL tables (partition + chi-square) from a risk_scores_train.csv; writes candidate CSVs."""
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from hl_lib import anchored_blocks, doc
import numpy as np, polars as pl

def chi2_sf_even(x, k):
    assert k % 2 == 0
    return math.exp(-x / 2) * sum((x / 2) ** i / math.factorial(i) for i in range(k // 2))

def pvalue64(p):
    return "<.0001" if p < 0.0001 else f"{p:.4f}"

def hl(y, p, G=10, eps=1e-6):
    o = np.argsort(p, kind="stable"); p = p[o]; y = y[o]
    bs = anchored_blocks(p, eps)
    sizes = doc(bs, len(p), G)
    # every member of a block gets the block's SMALLEST pd (anchored 1e-6 block)
    p = np.repeat(p[np.r_[0, np.cumsum(bs)[:-1]]], bs)
    rows = []; start = 0; chisq = 0.0
    for g, n in enumerate(sizes, 1):
        yy, pp = y[start:start + n], p[start:start + n]; start += n
        o1, e1 = int(yy.sum()), float(pp.sum()); o0, e0 = n - o1, n - e1
        chisq += (o1 - e1) ** 2 / e1 + (o0 - e0) ** 2 / e0
        rows.append((g, n, o1, e1, o0, e0))
    df = len(sizes) - 2
    return rows, chisq, df, chi2_sf_even(chisq, df)

if __name__ == "__main__":
    src, out = sys.argv[1], sys.argv[2]
    d = pl.read_csv(src, infer_schema_length=0)
    y = d["default_flag"].cast(pl.Int64).to_numpy(); p = d["pd_logistic"].cast(pl.Float64).to_numpy()
    rows, x2, df, pv = hl(y, p)
    os.makedirs(out, exist_ok=True)
    with open(f"{out}/printed_hl_partition.csv", "w") as f:
        f.write("Group,Total,EventsObserved,EventsExpected,NoneventsObserved,NoneventsExpected\n")
        for g, n, o1, e1, o0, e0 in rows:
            f.write(f"{g},{n},{o1},{e1:.2f},{o0},{e0:.2f}\n")
    with open(f"{out}/printed_hosmer_lemeshow.csv", "w") as f:
        f.write("ChiSq,DF,ProbChiSq,NGroups\n")
        f.write(f"{x2:.4f},{df},{pvalue64(pv)},{len(rows)}\n")
    print(open(f"{out}/printed_hl_partition.csv").read(), open(f"{out}/printed_hosmer_lemeshow.csv").read(), f"chisq full={x2!r} p={pv:.3e}")
