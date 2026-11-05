import polars as pl
df = pl.DataFrame({"c": [10500], "n": [105000]})
print("with_columns c/105000 (int lit):", repr(df.with_columns(r=pl.col("c")/105000)["r"][0]))
print("with_columns c/105000.0:", repr(df.with_columns(r=pl.col("c")/105000.0)["r"][0]))
print("with_columns c.cast(f64)/lit:", repr(df.with_columns(r=pl.col("c").cast(pl.Float64)/pl.lit(105000.0))["r"][0]))
print("with_columns c/col n:", repr(df.with_columns(r=pl.col("c")/pl.col("n"))["r"][0]))
print("c.truediv(n col):", repr(df.with_columns(r=pl.col("c").truediv(pl.col("n")))["r"][0]))
print("python:", repr(10500/105000))
d2 = pl.DataFrame({"c":[10500.0]*3})
print("multi-row lit:", d2.with_columns(r=pl.col("c")/105000.0)["r"].to_list())
print("lit broadcast col:", d2.with_columns(n=pl.lit(105000.0)).with_columns(r=pl.col("c")/pl.col("n"))["r"].to_list())
s = pl.Series([10500.0]); print("series / scalar:", repr((s/105000.0)[0]))
print("1/x via lit numerator:", d2.with_columns(r=pl.lit(1.0)/pl.col("c"))["r"][0] == 1/10500.0)
# 1 + exp: 
