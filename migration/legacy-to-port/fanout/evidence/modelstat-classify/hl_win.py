import numpy as np, polars as pl
J = "/Users/cristophersalvi/GitHub/sas-migration/judge"
d = pl.read_csv(f"{J}/reference/risk_scores_train.csv", infer_schema_length=0).with_row_index("csvrow").select(
    "csvrow", "row_id", pl.col("default_flag").cast(pl.Int64), pl.col("pd_logistic").alias("txt"), pl.col("pd_logistic").cast(pl.Float64).alias("pd")).sort("pd", maintain_order=True).with_row_index("pos", offset=1)
for b in [10498, 21000, 31501, 42003, 52502]:
    print(d.filter((pl.col("pos") >= b - 6) & (pl.col("pos") <= b + 6)).with_columns(logit=(pl.col("pd")/(1-pl.col("pd"))).log()))
