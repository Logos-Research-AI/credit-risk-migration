"""E03: float sum/mean order inside group_by(maintain_order=True).agg, by group size and null presence."""
import struct, random, sys, collections
import numpy as np, polars as pl
sys.path.insert(0, "."); sys.path.insert(0, "migration/experiments")
from credit_risk import sas_compat
from e02_algos import pl_sum, np_pairwise, seq
bits = lambda x: struct.unpack("<Q", struct.pack("<d", x))[0]
rng = random.Random(11)
def rnd(n): return [rng.uniform(0, 1) * 10 ** rng.randint(-3, 3) for _ in range(n)]
stats = collections.defaultdict(lambda: collections.Counter())
for trial in range(80):
    n = rng.choice([5, 37, 200, 1000, 3000, 20000])
    nulls = trial % 2 == 0
    mode = ["rank_sorted", "random_key", "rank_unsorted"][trial % 3]
    pdv = rnd(n)
    if nulls: pdv = [None if rng.random() < 0.1 else v for v in pdv]
    df = pl.DataFrame({"pd": pdv}, schema={"pd": pl.Float64})
    if mode == "rank_sorted": df = df.sort("pd", maintain_order=True)
    if mode == "random_key":
        df = df.with_columns(pl.Series("decile", [rng.randint(0, 9) for _ in range(n)], dtype=pl.Int64))
    else:
        df = df.with_columns(sas_compat.proc_rank_groups(df.get_column("pd"), 10, descending=True).alias("decile"))
    out = df.group_by("decile", maintain_order=True).agg(s=pl.col("pd").sum(), m=pl.col("pd").mean(), c=pl.col("pd").count(), n=pl.len())
    rows = df.to_dicts()
    for g in out.to_dicts():
        vals = [r["pd"] for r in rows if r["decile"] == g["decile"]]
        nn = [v for v in vals if v is not None]
        if not nn: continue
        z = [0.0 if v is None else v for v in vals]
        c = {"seq nn": seq(nn), "seq nn 0": seq(nn, 0.0), "pl_sum nn": pl_sum(nn), "pl_sum masked": pl_sum(z), "np nn": np_pairwise(nn), "np masked": np_pairwise(z)}
        key = (mode, "nulls" if len(nn) != len(vals) else "nonull", "small<128" if len(vals) < 128 else "big")
        stats[key]["total"] += 1
        for k, v in c.items():
            stats[key][k] += bits(v) == bits(g["s"])
        stats[key]["mean=s/c"] += bits(g["s"] / g["c"]) == bits(g["m"])
for k in sorted(stats): print(k, dict(stats[k]))
