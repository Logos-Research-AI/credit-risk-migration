import sys, os, glob, math
sys.path.insert(0, "/private/tmp/claude-501/-Users-cristophersalvi-GitHub-sas-migration/ecd11bde-e598-42bd-9cd4-9898388e98b1/scratchpad/fan/modelstat-classify")
from hl_lib import anchored_blocks, doc
import numpy as np, polars as pl
J = "/Users/cristophersalvi/GitHub/sas-migration/judge"
dirs = sorted({os.path.dirname(f) for f in glob.glob(f"{J}/runs/*/printed_hl_partition.csv")} | {f"{J}/reference"})
def tables(y, p, rep):
    o = np.argsort(p, kind="stable"); p = p[o]; y = y[o]
    bs = anchored_blocks(p, 1e-6); starts = np.r_[0, np.cumsum(bs)[:-1]]
    # representative pd per observation
    if rep == "own": q = p
    else:
        q = np.empty_like(p)
        for s, n in zip(starts, bs):
            blk = p[s:s+n]
            q[s:s+n] = {"min": blk[0], "max": blk[-1], "mean": blk.mean(), "mid": (blk[0]+blk[-1])/2}[rep]
    sizes = doc(bs, len(p)); st = 0; x2 = 0; E = []
    for n in sizes:
        o1 = y[st:st+n].sum(); e1 = q[st:st+n].sum(); st += n
        x2 += (o1-e1)**2/e1 + ((n-o1)-(n-e1))**2/(n-e1); E.append(e1)
    return x2, E
for rep in ("own", "min", "max", "mid"):
    worst_x2 = 0; worst_e = 0; okx = 0; oke = 0
    for dd in dirs:
        d = pl.read_csv(f"{dd}/risk_scores_train.csv", infer_schema_length=0)
        y = d["default_flag"].cast(pl.Int64).to_numpy(); p = d["pd_logistic"].cast(pl.Float64).to_numpy()
        x2, E = tables(y, p, rep)
        rx2 = float(pl.read_csv(f"{dd}/printed_hosmer_lemeshow.csv", infer_schema_length=0)["ChiSq"][0])
        rE = pl.read_csv(f"{dd}/printed_hl_partition.csv")["EventsExpected"].to_numpy()
        worst_x2 = max(worst_x2, abs(x2 - rx2)); okx += f"{x2:.4f}" == f"{rx2:.4f}"
        de = np.abs(np.array(E) - rE).max(); worst_e = max(worst_e, de); oke += all(f"{a:.2f}" == f"{b:.2f}" for a, b in zip(E, rE))
    print(f"rep={rep:5s} chisq printed-equal {okx}/{len(dirs)} max|dX2|={worst_x2:.5f}; EventsExpected all-printed-equal {oke}/{len(dirs)} max|dE|={worst_e:.4f}")
