import sys, numpy as np, polars as pl
sys.path.insert(0, "/private/tmp/claude-501/-Users-cristophersalvi-GitHub-sas-migration/ecd11bde-e598-42bd-9cd4-9898388e98b1/scratchpad/review/metrics-A")
from pathlib import Path
exec(open(sys.path[0] + "/verify.py").read().split("bad = 0")[0])
d = read(SETS["real"][0] / "risk_scores_train.csv")
b = d.with_columns(score_bin=pl.Series(rank_groups(d["pd_logistic"].to_numpy(), 10, False)))
n = b.height
g = b.group_by("score_bin", maintain_order=True).agg(cnt=pl.len())
print("chunks", g.n_chunks(), g.schema)
print("select       :", g.select(pl.col("cnt") / n).to_series().to_list()[:3])
print("with_columns :", g.with_columns(p=pl.col("cnt") / n)["p"].to_list()[:3])
print("lazy         :", g.lazy().with_columns(p=pl.col("cnt") / n).collect()["p"].to_list()[:3])
print("cast f64 then:", g.with_columns(p=pl.col("cnt").cast(pl.Float64) / n)["p"].to_list()[:3])
print("sorted w_c   :", g.sort("score_bin").with_columns(p=pl.col("cnt") / n)["p"].to_list()[:3])
print("sas-style: agg then join tot:", g.with_columns(t=pl.lit(n)).with_columns(p=pl.col("cnt")/pl.col("t"))["p"].to_list()[:3])
