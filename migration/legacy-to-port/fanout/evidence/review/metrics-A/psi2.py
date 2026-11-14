import sys, numpy as np, polars as pl
sys.path.insert(0, "/private/tmp/claude-501/-Users-cristophersalvi-GitHub-sas-migration/ecd11bde-e598-42bd-9cd4-9898388e98b1/scratchpad/review/metrics-A")
from pathlib import Path
exec(open(sys.path[0] + "/verify.py").read().split("bad = 0")[0])
inp = SETS["real"][0]
res = {}
for s in ("train", "validation"):
    d = read(inp / f"risk_scores_{s}.csv")
    b = d.with_columns(score_bin=pl.Series(rank_groups(d["pd_logistic"].to_numpy(), 10, False)))
    g = b.group_by("score_bin", maintain_order=True).agg(n=pl.len())
    n = b.height
    for lay, gg in (("as-is", g), ("rechunk", g.rechunk()), ("sorted", g.sort("score_bin")),
                    ("sql-style agg then join", None)):
        if gg is None: continue
        print(s, lay, "chunks", gg.n_chunks(), "n/N:", repr(gg.select(pl.col("n") / n)["n"][0]))
    # Exactly batch-1 row 19 'count / n AFTER the aggregation' on a frame built the SQL way
    sub = b.group_by("score_bin", maintain_order=True).agg(cnt=pl.len()).with_columns(tot=pl.lit(n))
    print(s, "count/tot col-col:", repr(sub.select(pl.col("cnt") / pl.col("tot"))["cnt"][0]))
