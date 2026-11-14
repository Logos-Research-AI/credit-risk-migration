"""E01: polars 2.1.0 element-wise semantics on nulls, NaN, inf, signed zero, dtypes."""
import math, json
import polars as pl
nan, inf = float("nan"), float("inf")
vals = [None, nan, -inf, -1.5, -0.0, 0.0, 2.0, inf]
df = pl.DataFrame({"x": [a for a in vals for b in vals], "y": [b for a in vals for b in vals]}, schema={"x": pl.Float64, "y": pl.Float64})
def show(name, e):
    out = df.select(e.alias("r")).get_column("r")
    print(name, out.dtype)
    n = len(vals)
    for i, a in enumerate(vals):
        print("   ", repr(a).rjust(5), [out[i * n + j] for j in range(n)])
print("columns (y):", vals)
for nm, e in [("lt", pl.col("x") < pl.col("y")), ("le", pl.col("x") <= pl.col("y")), ("gt", pl.col("x") > pl.col("y")),
              ("ge", pl.col("x") >= pl.col("y")), ("eq", pl.col("x") == pl.col("y")), ("ne", pl.col("x") != pl.col("y")),
              ("min_h", pl.min_horizontal(pl.col("x"), pl.col("y"))), ("max_h", pl.max_horizontal(pl.col("x"), pl.col("y"))),
              ("sum_h", pl.sum_horizontal(pl.col("x"), pl.col("y"))),
              ("add", pl.col("x") + pl.col("y")), ("div", pl.col("x") / pl.col("y"))]:
    show(nm, e)
u = pl.DataFrame({"x": vals + [1e-320, -3.7, 3.5, 709.0, 710.0]}, schema={"x": pl.Float64})
print(u.select(x=pl.col("x"), isnull=pl.col("x").is_null(), isfin=pl.col("x").is_finite(), log=pl.col("x").log(), exp=pl.col("x").exp(),
               abs=pl.col("x").abs(), floor=pl.col("x").floor(), sign=pl.col("x").sign(), p0=pl.col("x") + 0.0, neg=-pl.col("x"),
               gt0=pl.col("x") > 0, ).with_columns(pl.all().cast(pl.String) if False else pl.all()).to_dicts().__repr__().replace("}, {", "}\n {"))
print("sign(-0.0) bits:", math.copysign(1, u.select(pl.col("x").sign()).item(4, 0)), " abs(-0.0):", math.copysign(1, u.select(pl.col("x").abs()).item(4, 0)),
      " -0.0+0.0:", math.copysign(1, u.select(pl.col("x") + 0.0).item(4, 0)), "floor(-0.0)", math.copysign(1, u.select(pl.col("x").floor()).item(4, 0)))
# min/max horizontal signed zeros
z = pl.DataFrame({"a": [0.0, -0.0], "b": [-0.0, 0.0]})
print("min_h zeros", [math.copysign(1, v) for v in z.select(pl.min_horizontal("a", "b")).to_series()], "max_h zeros", [math.copysign(1, v) for v in z.select(pl.max_horizontal("a", "b")).to_series()])
# boolean logic with nulls
b = [None, False, True]
bd = pl.DataFrame({"p": [a for a in b for c in b], "q": [c for a in b for c in b]}, schema={"p": pl.Boolean, "q": pl.Boolean})
print(bd.with_columns(and_=pl.col("p") & pl.col("q"), or_=pl.col("p") | pl.col("q"), not_=~pl.col("p"), fill=pl.col("p").fill_null(False),
                      castint=pl.col("p").cast(pl.Int64), allh=pl.all_horizontal("p", "q"),
                      when=pl.when(pl.col("p")).then(1).otherwise(2), when_no_else=pl.when(pl.col("p")).then(pl.col("q")),
                      chain=pl.when(pl.col("p")).then(pl.lit("A")).when(pl.col("q")).then(pl.lit("B")).otherwise(pl.lit("C"))))
# dtypes
t = pl.DataFrame({"f": [1.5, None], "i": [3, None]}, schema={"f": pl.Float64, "i": pl.Int64})
print(t.select(a=pl.when(pl.col("f") < 2).then(1).otherwise(5), b=pl.col("i") + 1, c=pl.col("i") / pl.col("i"), d=pl.col("i") * 100, e=1 - pl.col("i"),
               f=pl.col("f") * 100, g=pl.col("i") == 3, h=pl.col("f") == 1, i=pl.col("i") > 0.5, j=pl.lit(1.0), k=pl.lit(5), l=pl.lit(None),
               m=pl.when(pl.col("f") < 2).then(None).otherwise(pl.col("f")), n=2 * pl.col("f") - 1, o=1 / (1 + pl.col("f")), p=pl.col("i").cast(pl.Float64),
               q=pl.max_horizontal(pl.lit(1.0), pl.col("i")), r=pl.max_horizontal(pl.col("f"), 1e-4), s=pl.sum_horizontal(pl.col("f"), pl.col("i").cast(pl.Float64)),
               u=pl.col("f").is_in([1.5]), v=pl.col("i") != 0, w=pl.when(pl.col("f") < 2).then(pl.lit(100.0) - 15).otherwise(pl.lit(100.0))).schema)
print(t.select(c=pl.col("i") / pl.col("i"), z=pl.col("i") / 0, zz=pl.col("f") / 0, m=pl.when(pl.col("f") < 2).then(None).otherwise(pl.col("f")), sh=pl.sum_horizontal(pl.col("f"), pl.col("i").cast(pl.Float64)),
               shn=pl.sum_horizontal(pl.lit(None, pl.Float64), pl.lit(None, pl.Float64)), mh=pl.min_horizontal(pl.lit(None, pl.Float64), pl.lit(None, pl.Float64))))
print("names:", [e.meta.output_name(raise_if_undetermined=False) for e in [pl.lit(1.0), pl.col("a") + pl.col("b"), pl.lit(1) - pl.col("z"), pl.col("a").alias("q") * 2, pl.sum_horizontal(pl.col("u"), pl.col("v")), pl.when(pl.col("a").is_null()).then(pl.col("b")).otherwise(pl.col("c")), pl.struct(pl.col("m").alias("a"), pl.col("n").alias("b")), -pl.col("pl"), pl.lit(3).alias("k"), pl.len(), pl.col("c").filter(pl.col("d") > 1).sum(), 100 * pl.col("COUNT")]])
for e in [pl.col("a"), pl.lit(2.5), pl.col("a") * pl.col("b"), pl.col("a").sum(), pl.col("a").count(), pl.len(), pl.col("a").cum_sum(), 100 * pl.col("a"), pl.col("a").cast(pl.Float64), pl.lit(None, pl.Float64), pl.col("a") / pl.col("b").max(), pl.col("a").mean(), pl.col("a").median(), pl.col("a").first()]:
    print(json.dumps(json.loads(e.meta.serialize(format="json")))[:230])
