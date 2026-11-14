import polars as pl
R="/Users/cristophersalvi/GitHub/sas-migration/judge/reference/"
for f in ["risk_scores_train.csv","risk_scores_validation.csv","final_model_output.csv"]:
    df = pl.read_csv(R+f, infer_schema=False)
    print(f, df.group_by(["risk_grade","recommendation","interest_rate"]).len().sort("risk_grade").rows())
    rec = pl.when(pl.col("risk_grade").is_in(["A","B"])).then(pl.lit("Approve")).when(pl.col("risk_grade")=="C").then(pl.lit("Review")).otherwise(pl.lit("Decline"))
    rate = (pl.when(pl.col("risk_grade")=="A").then(0.05).when(pl.col("risk_grade")=="B").then(0.05+0.02)
            .when(pl.col("risk_grade")=="C").then(0.05+0.04).when(pl.col("risk_grade")=="D").then(0.05+0.07)
            .when(pl.col("risk_grade")=="E").then(0.05+0.10).otherwise(0.05+0.15))
    out = df.with_columns(rec.alias("rec2"), (rate*100).map_elements(lambda v: f"{v:.2f}%", return_dtype=pl.Utf8).alias("rate2"))
    print(" mismatches:", out.filter((pl.col("rec2")!=pl.col("recommendation"))|(pl.col("rate2")!=pl.col("interest_rate"))).height, "trailing-blank recs:", df.filter(pl.col("recommendation").str.ends_with(" ")).height)
