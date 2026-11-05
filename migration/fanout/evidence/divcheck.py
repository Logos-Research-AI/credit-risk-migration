import polars as pl, numpy as np
print("polars", pl.__version__, "| IEEE 10500/105000 =", repr(10500/105000), "| 10500*(1/105000) =", repr(10500*(1/105000)))
one = pl.DataFrame({"c": [10500]*10})
print("one chunk, col / 105000     :", one.select(pl.col("c") / 105000)["c"][0])
print("one chunk, col / pl.lit     :", one.select(pl.col("c") / pl.lit(105000.0))["c"][0])
print("one chunk, col / col.sum()*10:", one.select(pl.col("c") / (pl.col("c").sum() * 10))["c"][0])
multi = pl.concat([pl.DataFrame({"c": [10500]}) for _ in range(10)], rechunk=False)
print("n chunks", multi.n_chunks(), " col / 105000:", multi.select(pl.col("c") / 105000)["c"][0])
g = pl.DataFrame({"k": list(range(10))*10500}).group_by("k", maintain_order=True).len()
print("group_by out chunks", g.n_chunks(), " len / 105000:", g.select(pl.col("len") / 105000)["len"][0],
      " after rechunk:", g.rechunk().select(pl.col("len") / 105000)["len"][0])
two = pl.DataFrame({"a": [10500]*10, "b": [105000]*10})
print("col / col                   :", two.select(pl.col("a") / pl.col("b"))["a"][0])
print("numpy                       :", np.divide(np.array([10500.]), 105000.)[0])
