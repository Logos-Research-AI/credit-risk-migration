import polars as pl, random
random.seed(2)
ints = [random.randint(1, 10**6) for _ in range(100000)]
divs = {"py int 105000": 105000, "py float 105000.0": 105000.0, "pl.lit(105000.0)": pl.lit(105000.0), "pl.lit(105000)": pl.lit(105000), "py float 3.7": 3.7, "py int 100": 100}
for dt in [pl.Int64, pl.UInt32, pl.Float64]:
    df = pl.DataFrame({"c": ints}).with_columns(pl.col("c").cast(dt))
    for name, dv in divs.items():
        out = df.select(pl.col("c") / dv).to_series().to_list()
        val = dv if not isinstance(dv, pl.Expr) else (105000.0 if "105000" in name else None)
        bad = sum(1 for a, o in zip(ints, out) if a / val != o)
        print(f"{str(dt):8s} / {name:20s}: non-IEEE {bad}")
    out = df.select(pl.col("c") / pl.col("c").sum()).to_series().to_list(); s = sum(ints)
    print(f"{str(dt):8s} / col.sum()            : non-IEEE {sum(1 for a,o in zip(ints,out) if a/s != o)}")
    df2 = df.with_columns(n=pl.col("c").sum())
    out = df2.select(pl.col("c") / pl.col("n")).to_series().to_list()
    print(f"{str(dt):8s} / materialised sum col : non-IEEE {sum(1 for a,o in zip(ints,out) if a/s != o)}")
