import polars as pl, random
print(pl.__version__)
random.seed(1)
xs = [random.uniform(0, 1e6) for _ in range(200000)]
df = pl.DataFrame({"x": xs, "y": [100.0]*len(xs)})
out = df.select(a=pl.col("x")/100, b=pl.col("x")/pl.lit(100.0), c=pl.col("x")/pl.col("y"), m=pl.col("x")*100, n=pl.col("x")*pl.col("y"))
for k in "abc":
    v = out[k].to_list()
    print(k, "diff vs python x/100:", sum(1 for x,a in zip(xs,v) if x/100 != a), "equal to x*(1/100):", sum(1 for x,a in zip(xs,v) if x*(1/100) == a and x/100 != a))
for k in "mn":
    v = out[k].to_list(); print(k, "diff vs python x*100", sum(1 for x,a in zip(xs,v) if x*100 != a))
# division by non-literal column with varied values
ys = [random.uniform(1, 50) for _ in xs]
df2 = pl.DataFrame({"x": xs, "y": ys})
v = df2.select(pl.col("x")/pl.col("y")).to_series().to_list()
print("col/col diffs", sum(1 for x,y,a in zip(xs,ys,v) if x/y != a))
v = df2.select(pl.col("x")/(pl.col("y")+1)).to_series().to_list()
print("col/(col+1) diffs", sum(1 for x,y,a in zip(xs,ys,v) if x/(y+1) != a))
v = pl.select(pl.lit(1.0) / (1 + pl.Series(ys).exp())).to_series().to_list()
import math
print("1/(1+exp) diffs", sum(1 for y,a in zip(ys,v) if 1/(1+math.exp(y)) != a))
v = pl.Series(ys).log().to_list(); print("log diffs", sum(1 for y,a in zip(ys,v) if math.log(y)!=a))
