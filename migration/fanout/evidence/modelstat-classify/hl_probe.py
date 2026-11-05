import numpy as np, polars as pl
J = "/Users/cristophersalvi/GitHub/sas-migration/judge"
d = pl.read_csv(f"{J}/reference/risk_scores_train.csv", infer_schema_length=0).select(
    pl.col("default_flag").cast(pl.Int64), pl.col("pd_logistic").cast(pl.Float64).alias("pd")).sort("pd", maintain_order=True)
p = d["pd"].to_numpy(); y = d["default_flag"].to_numpy()
cp = np.r_[0, np.cumsum(p)]; cy = np.r_[0, np.cumsum(y)]
ref = pl.read_csv(f"{J}/reference/printed_hl_partition.csv")
cum_ref = np.cumsum(ref["Total"].to_numpy())
prev = 0
for g, (tot, eo, ee) in enumerate(zip(ref["Total"], ref["EventsObserved"], ref["EventsExpected"])):
    end = prev + tot
    print(f"group {g+1}: SAS rows ({prev},{end}] obs={eo} exp={ee}; ours obs={cy[end]-cy[prev]} exp={cp[end]-cp[prev]:.4f}")
    prev = end
# exactly-10500 groups
print("equal 10500 groups:")
for g in range(10):
    a, b = g*10500, (g+1)*10500
    print(g+1, cy[b]-cy[a], round(cp[b]-cp[a], 4))
