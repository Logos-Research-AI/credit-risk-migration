import polars as pl, numpy as np
def div(a: pl.Expr, b) -> pl.Expr:  # element-wise IEEE division (sketch of sas_compat.div)
    b = b if isinstance(b, pl.Expr) else pl.lit(float(b))
    return pl.struct(a.cast(pl.Float64).alias("a"), b.cast(pl.Float64).alias("b")).map_batches(
        lambda s: pl.Series(np.divide(s.struct.field("a").to_numpy(), s.struct.field("b").to_numpy())), return_dtype=pl.Float64)
def rank_groups(x, k):
    r = x.rank("average"); return (r * k / (len(x) + 1)).floor()
out = {}
for nm in ("train", "validation"):
    d = pl.read_csv(f"reference/risk_scores_{nm}.csv", infer_schema_length=None).select("pd_logistic")
    d = d.with_columns(score_bin=rank_groups(d["pd_logistic"], 10))
    n = d.height
    g = d.group_by("score_bin", maintain_order=True).agg(cnt=pl.len()).sort("score_bin")
    out[nm] = (g.with_columns(pct_plain=pl.col("cnt") / n, pct_div=div(pl.col("cnt"), n)))
j = out["train"].join(out["validation"], on="score_bin", suffix="_v")
for c in ("plain", "div"):
    a, b = pl.col(f"pct_{c}"), pl.col(f"pct_{c}_v")
    psi = j.select(((a - b) * (a / b).log()).sum()).item()
    print(c, "PSI =", repr(psi))
