"""E04: group_by(maintain_order=True).agg float sum/mean = Kahan fold in row order (Idx groups); median formula.
Source: polars py-2.1.0 crates/polars-core/src/frame/group_by/aggregations/mod.rs (agg_sum, agg_mean),
crates/polars-utils/src/kahan_sum.rs, crates/polars-core/src/chunked_array/ops/aggregate/quantile.rs (linear_interpol)."""
import struct, random, sys, math, collections
import polars as pl
sys.path.insert(0, "."); sys.path.insert(0, "migration/experiments")
from credit_risk import sas_compat
from e02_algos import pl_sum
bits = lambda x: struct.unpack("<Q", struct.pack("<d", x))[0]
rng = random.Random(21)
def rnd(n): return [rng.uniform(0, 1) * 10 ** rng.randint(-3, 3) for _ in range(n)]
def kahan(xs):
    s = 0.0; e = 0.0
    for x in xs:
        y = x - e; t = s + y; ne = (t - s) - y; s = t
        if math.isfinite(ne): e = ne
    return s
st = collections.defaultdict(collections.Counter)
for trial in range(120):
    n = rng.choice([5, 37, 200, 1000, 3000, 20000]); nulls = trial % 2 == 0
    mode = ["rank_sorted", "random_key", "rank_unsorted", "sorted_then_rank20"][trial % 4]
    pdv = rnd(n)
    if nulls: pdv = [None if rng.random() < 0.1 else v for v in pdv]
    df = pl.DataFrame({"pd": pdv, "y": [float(rng.random() < 0.3) for _ in range(n)]}, schema={"pd": pl.Float64, "y": pl.Float64})
    if mode in ("rank_sorted", "sorted_then_rank20"): df = df.sort("pd", maintain_order=True)
    if mode == "random_key": df = df.with_columns(pl.Series("g", [rng.randint(0, 9) for _ in range(n)], dtype=pl.Int64))
    elif mode == "sorted_then_rank20": df = df.with_columns(sas_compat.proc_rank_groups(df.get_column("pd"), 20).alias("g"))
    else: df = df.with_columns(sas_compat.proc_rank_groups(df.get_column("pd"), 10, descending=True).alias("g"))
    out = df.group_by("g", maintain_order=True).agg(s=sas_compat.sql_sum(pl.col("pd")), m=sas_compat.sql_mean(pl.col("pd")), c=pl.col("pd").count(), n=pl.len(),
                                                   rs=pl.col("pd").sum(), rm=pl.col("pd").mean(), ys=sas_compat.sql_sum(pl.col("y")), ym=sas_compat.sql_mean(pl.col("y")),
                                                   mn=sas_compat.sql_min(pl.col("pd")), mx=sas_compat.sql_max(pl.col("pd")))
    rows = df.to_dicts()
    seen = []
    for r in rows:
        if r["g"] not in seen: seen.append(r["g"])
    key = (mode, "nulls" if nulls else "nonull")
    st[key]["group order = first appearance"] += seen == out.get_column("g").to_list(); st[key]["frames"] += 1
    for g in out.to_dicts():
        vals = [r["pd"] for r in rows if r["g"] == g["g"]]; nn = [v for v in vals if v is not None]
        ys = [r["y"] for r in rows if r["g"] == g["g"]]
        st[key]["groups"] += 1
        st[key]["n=len"] += g["n"] == len(vals); st[key]["c=nonnull"] += g["c"] == len(nn)
        if nn:
            st[key]["sum=kahan(nonnull,row order)"] += bits(g["s"]) == bits(kahan(nn)) and bits(g["rs"]) == bits(g["s"])
            st[key]["mean=kahan/count"] += bits(g["m"]) == bits(kahan(nn) / len(nn)) and bits(g["rm"]) == bits(g["m"])
            st[key]["min/max"] += g["mn"] == min(nn) and g["mx"] == max(nn)
        else:
            st[key]["allnull group: sql_sum,sql_mean,min None; raw sum"] += (g["s"] is None and g["m"] is None and g["mn"] is None)
            st[key]["allnull raw sum==0.0, raw mean None"] += (g["rs"] == 0.0 and g["rm"] is None)
        st[key]["ysum kahan"] += bits(g["ys"]) == bits(kahan(ys)); st[key]["ymean"] += bits(g["ym"]) == bits(kahan(ys) / len(ys))
for k in sorted(st): print(k, dict(st[k]))
# single-row group and all-null group edge
e = pl.DataFrame({"g": [1, 2, 2, 3, None, None], "x": [-0.0, None, None, None, 5.0, 7.0]}, schema={"g": pl.Int64, "x": pl.Float64})
o = e.group_by("g", maintain_order=True).agg(s=pl.col("x").sum(), m=pl.col("x").mean(), ss=sas_compat.sql_sum(pl.col("x")), c=pl.col("x").count(), med=pl.col("x").median())
print(o.to_dicts(), "single -0.0 group sum sign:", math.copysign(1, o.item(0, "s")))
# median: group context and formula
cnt = collections.Counter()
for trial in range(400):
    n = rng.choice([1, 2, 3, 4, 7, 10, 51, 200]); xs = rnd(n); ks = [rng.randint(0, 2) for _ in range(n)]
    ys = [None if rng.random() < 0.15 else v for v in xs]
    out = pl.DataFrame({"k": ks, "x": ys}, schema={"k": pl.Int32, "x": pl.Float64}).filter(pl.col("x").is_not_null()).group_by("k", maintain_order=True).agg(m=pl.col("x").median())
    for g in out.to_dicts():
        v = sorted(y for k, y in zip(ks, ys) if k == g["k"] and y is not None); m = len(v)
        cnt["groups"] += 1
        if m % 2: cnt["odd: middle"] += bits(v[m // 2]) == bits(g["m"])
        else:
            a, b = v[m // 2 - 1], v[m // 2]
            cnt["even"] += 1
            cnt["even: 0.5*(b-a)+a"] += bits(0.5 * (b - a) + a) == bits(g["m"]); cnt["even: (a+b)/2"] += bits((a + b) / 2) == bits(g["m"])
print("median:", dict(cnt))
print("median with NaN/inf:", pl.DataFrame({"k": [1, 1, 1, 2, 2, 3, 3], "x": [1.0, float("nan"), 3.0, float("nan"), 2.0, float("inf"), 1.0]}).group_by("k", maintain_order=True).agg(pl.col("x").median()).to_dicts())
