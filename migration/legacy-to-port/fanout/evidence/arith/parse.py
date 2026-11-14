import polars as pl
R = "/Users/cristophersalvi/GitHub/sas-migration"
raw = pl.read_csv(f"{R}/data/cs-training.csv", infer_schema=False)
for c in ["RevolvingUtilizationOfUnsecuredLines","DebtRatio"]:
    s = raw[c]; pv = s.cast(pl.Float64).to_list(); n = sum(1 for a,b in zip(s.to_list(), pv) if float(a)!=b)
    print(c, "polars-vs-python parse diffs", n)
df = raw.select(r=pl.col("RevolvingUtilizationOfUnsecuredLines").cast(pl.Float64), d=pl.col("DebtRatio").cast(pl.Float64))
df = df.with_columns(u=(pl.col("r")*100)*(pl.col("d")*100)/100, u2=pl.col("r")*100*pl.col("d")*100/100)
n = sum(1 for r,d,u in df.select("r","d","u").iter_rows() if (r*100)*(d*100)/100 != u)
n2 = sum(1 for r,d,u in df.select("r","d","u2").iter_rows() if r*100*d*100/100 != u)
print("polars vs python arithmetic diffs", n, n2)
