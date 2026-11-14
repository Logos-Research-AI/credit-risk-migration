import polars as pl, numpy as np
n = 105000
binned = pl.DataFrame({"score_bin": list(range(10))*10500})
agg = binned.group_by("score_bin", maintain_order=True).agg(cnt=pl.len())
a = agg.with_columns(train_pct=pl.col("cnt")/n)                       # A7 as written: after aggregation, scalar n
print("A7 later with_columns, scalar n:", a["train_pct"].unique().to_list())
b = agg.with_columns(train_pct=pl.col("cnt")/pl.col("cnt").sum())     # divisor = expression sum
print("divisor pl.col.sum():", b["train_pct"].unique().to_list())
c = agg.with_columns(train_pct=pl.Series(np.divide(agg["cnt"].to_numpy().astype(float), float(n))))
print("numpy divide:", c["train_pct"].unique().to_list())
d = agg.with_columns(train_pct=pl.col("cnt").map_batches(lambda s: pl.Series(np.divide(s.to_numpy().astype(np.float64), n)), return_dtype=pl.Float64))
print("map_batches numpy:", d["train_pct"].unique().to_list())
nn = agg.with_columns(nn=pl.col("cnt").sum()).with_columns(train_pct=pl.col("cnt")/pl.col("nn"))
print("divisor materialised via sum() column:", nn["train_pct"].unique().to_list())
# component
x = a["train_pct"][0]; print("psi component with recip pct, valid pct 0.1:", (x-0.1)*np.log(x/0.1))
