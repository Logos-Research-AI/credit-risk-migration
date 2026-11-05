import sys, numpy as np, polars as pl
sys.path.insert(0, "/private/tmp/claude-501/-Users-cristophersalvi-GitHub-sas-migration/ecd11bde-e598-42bd-9cd4-9898388e98b1/scratchpad/review/metrics-A")
from pathlib import Path
exec(open(sys.path[0] + "/verify.py").read().split("bad = 0")[0])
inp = SETS["real"][0]
fr = {}
for s, col in (("train", "train_pct"), ("validation", "valid_pct")):
    d = read(inp / f"risk_scores_{s}.csv")
    b = d.with_columns(score_bin=pl.Series(rank_groups(d["pd_logistic"].to_numpy(), 10, False)))
    n = b.height
    # A7-compliant: aggregate counts first, divide in a later with_columns (batch-1 row 19 / row 34)
    fr[s] = b.group_by("score_bin", maintain_order=True).agg(cnt=pl.len()).sort("score_bin").with_columns((pl.col("cnt") / n).alias(col)).drop("cnt")
j = fr["train"].join(fr["validation"], on="score_bin", how="inner", maintain_order="left").sort("score_bin").with_columns(
    psi_component=(pl.col("train_pct") - pl.col("valid_pct")) * (pl.col("train_pct") / pl.col("valid_pct")).log())
print(j)
print("psi_component[0] =", repr(j["psi_component"][0]), "-> SAS ref prints '0'")
