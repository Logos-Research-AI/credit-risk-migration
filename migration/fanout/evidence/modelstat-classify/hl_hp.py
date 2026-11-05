import numpy as np, polars as pl
J = "/Users/cristophersalvi/GitHub/sas-migration/judge"
import sys
r = sys.argv[1]; lo, hi = int(sys.argv[2]), int(sys.argv[3])
d = pl.read_csv(f"{J}/runs/{r}/risk_scores_train.csv", infer_schema_length=0).select("row_id", "default_flag", pl.col("pd_logistic").alias("txt"), pl.col("pd_logistic").cast(pl.Float64).alias("pd")).sort("pd", maintain_order=True).with_row_index("pos", offset=1)
with pl.Config(tbl_rows=100):
    print(d.filter((pl.col("pos") >= lo) & (pl.col("pos") <= hi)))
