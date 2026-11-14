import polars as pl
S = "/private/tmp/claude-501/-Users-cristophersalvi-GitHub-sas-migration/ecd11bde-e598-42bd-9cd4-9898388e98b1/scratchpad/review/fe-predict-A/"
R = "/Users/cristophersalvi/GitHub/sas-migration/judge/reference/"
fe = pl.read_parquet(S + "fe.parquet")
def efmt(x):
    e = int(f"{x:e}".split("e")[1])
    exp = f"E{e}"
    w = 12 - len(exp)
    m = f"{x:.{w-2}e}".split("e")[0]
    if "." in m: m = m.rstrip("0").rstrip(".")
    return m + exp
ref = pl.concat([pl.read_csv(R + "model_features_train.csv", infer_schema=False), pl.read_csv(R + "model_features_validation.csv", infer_schema=False)])
e = ref.filter(pl.col("utilization_debt_interaction").str.contains("E")).select("row_id", "utilization_debt_interaction").with_columns(pl.col("row_id").cast(pl.Float64))
m = e.join(fe.select("row_id", pl.col("utilization_debt_interaction").alias("x")), on="row_id")
for r in m.rows(): print(r[1], efmt(r[2]), r[1] == efmt(r[2]))
print("max udi", fe["utilization_debt_interaction"].max(), "min nonzero", fe.filter(pl.col("utilization_debt_interaction") > 0)["utilization_debt_interaction"].min())
print(len(ref.columns))
