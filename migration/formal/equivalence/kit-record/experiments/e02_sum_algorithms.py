"""E02: bit-level identification of float summation order: polars sum/mean (select and group_by.agg), numpy sum/var/cumsum."""
import struct, random, math, sys
import numpy as np, polars as pl
sys.path.insert(0, ".")
from credit_risk import sas_compat
bits = lambda x: struct.unpack("<Q", struct.pack("<d", x))[0]
rng = random.Random(7)

def seq(xs, init=None):
    it = iter(xs)
    acc = next(it) if init is None else init
    for v in it: acc = acc + v
    return acc

# ---- numpy pairwise (loops_utils.h.src) ----
def np_pairwise(a):
    n = len(a)
    if n < 8:
        res = 0.0
        for v in a: res += v
        return res
    if n <= 128:
        r = list(a[:8]); i = 8
        while i < n - (n % 8):
            for j in range(8): r[j] += a[i + j]
            i += 8
        res = ((r[0] + r[1]) + (r[2] + r[3])) + ((r[4] + r[5]) + (r[6] + r[7]))
        while i < n:
            res += a[i]; i += 1
        return res
    n2 = n // 2; n2 -= n2 % 8
    return np_pairwise(a[:n2]) + np_pairwise(a[n2:])
def np_sum_a(a):  # reduce: first element, then pairwise of the rest
    return a[0] + np_pairwise(a[1:]) if len(a) else 0.0
def np_sum_b(a):
    return np_pairwise(a) if len(a) else 0.0
def np_sum_c(a):
    return 0.0 + np_pairwise(a)

# ---- polars float_sum candidates ----
def hsum16(v):
    v = list(v)
    for i in range(8): v[i] = v[i] + v[i + 8]
    for i in range(4): v[i] = v[i] + v[i + 4]
    for i in range(2): v[i] = v[i] + v[i + 2]
    return v[0] + v[1]
def block128(f):
    acc = [0.0] * 16
    for c in range(0, 128, 16):
        for j in range(16): acc[j] = acc[j] + f[c + j]
    return hsum16(acc)
def pl_pairwise(f):
    if len(f) == 128: return block128(f)
    blocks = len(f) // 128
    left = (blocks // 2) * 128
    return pl_pairwise(f[:left]) + pl_pairwise(f[left:])
def pl_sum(f, rest_init=0.0, rest_first=True, order="main+rest"):
    rem = len(f) % 128
    rest, main = (f[:rem], f[rem:]) if rest_first else (f[len(f) - rem:], f[:len(f) - rem])
    mainsum = pl_pairwise(main) if len(main) else 0.0
    restsum = rest_init
    for v in rest: restsum = restsum + v
    return mainsum + restsum if order == "main+rest" else restsum + mainsum

def check(name, got, cands, xs):
    return {k: bits(f(xs)) == bits(got) for k, f in cands.items()}

def tally(name, results):
    keys = results[0].keys()
    print(name, {k: f"{sum(r[k] for r in results)}/{len(results)}" for k in keys})

lens = list(range(0, 40)) + [63, 64, 65, 127, 128, 129, 130, 143, 144, 200, 255, 256, 257, 300, 383, 384, 385, 500, 640, 1000, 1024, 1500, 4097, 10000, 30011]
def rnd(n): return [rng.uniform(0, 1) * 10 ** rng.randint(-3, 3) for _ in range(n)]

res = []
for n in lens:
    for _ in range(3):
        xs = rnd(n); a = np.array(xs, dtype=np.float64)
        res.append(check("np", float(a.sum()), {"first+pairwise(rest)": np_sum_a, "pairwise": np_sum_b, "0+pairwise": np_sum_c, "seq": lambda v: seq(v, 0.0)}, xs))
tally("numpy a.sum():", res)

res = []; res_null = []
for n in lens:
    for _ in range(3):
        xs = rnd(n); s = pl.Series("x", xs, dtype=pl.Float64)
        c = {"pl_sum(rest first, 0.0)": lambda v: pl_sum(v), "pl_sum(rest first,-0.0)": lambda v: pl_sum(v, -0.0), "pl_sum(rest last)": lambda v: pl_sum(v, 0.0, False),
             "seq0": lambda v: seq(v, 0.0), "np": np_sum_b}
        res.append(check("pl", pl.DataFrame({"x": s}).select(pl.col("x").sum()).item(), c, xs))
        # with nulls: null -> treated how?
        ys = [None if rng.random() < 0.2 else v for v in xs]
        got = pl.DataFrame({"x": pl.Series("x", ys, dtype=pl.Float64)}).select(pl.col("x").sum()).item()
        c2 = {"masked: null as 0.0 in place": lambda v: pl_sum([0.0 if t is None else t for t in v]), "compacted non-null": lambda v: pl_sum([t for t in v if t is not None]),
              "seq compact": lambda v: seq([t for t in v if t is not None], 0.0)}
        res_null.append(check("pln", got, c2, ys))
tally("polars select sum, no nulls:", res)
tally("polars select sum, with nulls:", res_null)
print("empty sum:", pl.DataFrame({"x": pl.Series("x", [], dtype=pl.Float64)}).select(s=pl.col("x").sum(), m=pl.col("x").mean(), c=pl.col("x").count(), mn=pl.col("x").min()).to_dicts(),
      "all-null:", pl.DataFrame({"x": pl.Series("x", [None, None], dtype=pl.Float64)}).select(s=pl.col("x").sum(), m=pl.col("x").mean(), c=pl.col("x").count(), mn=pl.col("x").min(), l=pl.len()).to_dicts())
print("sum of [-0.0]:", math.copysign(1, pl.DataFrame({"x": [-0.0]}).select(pl.col("x").sum()).item()), "sum of [-0.0,-0.0]:", math.copysign(1, pl.DataFrame({"x": [-0.0, -0.0]}).select(pl.col("x").sum()).item()),
      " np:", math.copysign(1, np.array([-0.0]).sum()), math.copysign(1, np.array([-0.0, -0.0]).sum()))

# mean in select context
res = []; res_null = []
for n in lens[1:]:
    for _ in range(3):
        xs = rnd(n)
        got = pl.DataFrame({"x": xs}, schema={"x": pl.Float64}).select(pl.col("x").mean()).item()
        res.append(check("m", got, {"pl_sum/n": lambda v: pl_sum(v) / len(v), "seq/n": lambda v: seq(v, 0.0) / len(v), "sum*(1/n)": lambda v: pl_sum(v) * (1 / len(v))}, xs))
        ys = [None if rng.random() < 0.2 else v for v in xs]
        nn = [t for t in ys if t is not None]
        if nn:
            got = pl.DataFrame({"x": ys}, schema={"x": pl.Float64}).select(pl.col("x").mean()).item()
            res_null.append(check("m", got, {"masked sum / count": lambda v: pl_sum([0.0 if t is None else t for t in v]) / len(nn), "compact/count": lambda v: pl_sum(nn) / len(nn)}, ys))
tally("polars select mean, no nulls:", res)
tally("polars select mean, with nulls:", res_null)

# sql_sum / sql_mean wrappers in select context (when(count>0).then(sum))
res = []
for n in lens[1:]:
    xs = rnd(n); df = pl.DataFrame({"x": xs}, schema={"x": pl.Float64})
    got = df.select(sas_compat.sql_sum(pl.col("x"))).item(); gm = df.select(sas_compat.sql_mean(pl.col("x"))).item()
    res.append({"sql_sum==pl_sum": bits(got) == bits(pl_sum(xs)), "sql_mean==pl_sum/n": bits(gm) == bits(pl_sum(xs) / n)})
tally("sql_* in select:", res)

# group_by(maintain_order).agg context, as in metrics_calculation (key from proc_rank_groups, frame sorted)
res = []; resm = []
for trial in range(60):
    n = rng.choice([5, 37, 200, 1000, 3000, 20000])
    pdv = rnd(n); fl = [float(rng.random() < 0.3) for _ in range(n)]
    if trial % 3 == 0: pdv = [None if rng.random() < 0.1 else v for v in pdv]
    df = pl.DataFrame({"pd": pdv, "y": fl}, schema={"pd": pl.Float64, "y": pl.Float64}).sort("pd", maintain_order=True)
    df = df.with_columns(sas_compat.proc_rank_groups(df.get_column("pd"), 10, descending=True).alias("decile"))
    out = df.group_by("decile", maintain_order=True).agg(s=sas_compat.sql_sum(pl.col("pd")), m=sas_compat.sql_mean(pl.col("pd")), raw_s=pl.col("pd").sum(), raw_m=pl.col("pd").mean(), c=pl.col("pd").count(), n=pl.len())
    rows = df.to_dicts()
    for g in out.to_dicts():
        vals = [r["pd"] for r in rows if r["decile"] == g["decile"]]
        nn = [v for v in vals if v is not None]
        if not nn: continue
        c = {"seq from first": lambda v: seq(v), "seq from 0.0": lambda v: seq(v, 0.0), "seq from -0.0": lambda v: seq(v, -0.0), "pl_sum": pl_sum, "np": np_sum_b}
        res.append(check("g", g["s"], c, nn))
        resm.append({k: bits(f(nn) / len(nn)) == bits(g["m"]) for k, f in c.items()} | {"raw==sql": bits(g["raw_m"]) == bits(g["m"]) and bits(g["raw_s"]) == bits(g["s"])})
tally("group_by agg sum (group rows in frame order, non-null):", res)
tally("group_by agg mean = sum/count:", resm)

# cum_sum
xs = rnd(1000); cs = pl.DataFrame({"x": xs}).select(pl.col("x").cum_sum()).to_series().to_list()
acc = []; t = None
for v in xs:
    t = v if t is None else t + v; acc.append(t)
print("float cum_sum sequential from first:", all(bits(a) == bits(b) for a, b in zip(acc, cs)))
print("cum_sum with nulls:", pl.DataFrame({"x": [None, 1.0, None, 2.0, None], "i": [None, 1, None, 2, None]}).select(pl.col("x").cum_sum(), pl.col("i").cum_sum()).to_dict(as_series=False))
print("np.cumsum seq:", all(bits(a) == bits(b) for a, b in zip(acc, np.cumsum(np.array(xs)).tolist())))

# np.var(ddof=1)
res = []
for n in [2, 3, 7, 8, 9, 50, 128, 129, 130, 1000, 5000]:
    for _ in range(5):
        xs = rnd(n); a = np.array(xs)
        def var(v):
            m = np_sum_a(v) / len(v)
            d = [(t - m) * (t - m) for t in v]
            return np_sum_a(d) / (len(v) - 1)
        def var_b(v):
            m = np_sum_b(v) / len(v)
            d = [(t - m) * (t - m) for t in v]
            return np_sum_b(d) / (len(v) - 1)
        res.append({"first+pw": bits(var(xs)) == bits(float(np.var(a, ddof=1))), "pw": bits(var_b(xs)) == bits(float(np.var(a, ddof=1)))})
tally("np.var ddof=1:", res)
# sum of a slice / boolean-indexed array / int array / searchsorted-result sum
a = np.array(rnd(1000)); print("slice sum same alg:", bits(float(a[100:900].sum())) == bits(np_sum_b(a[100:900].tolist())), bits(float(a[100:900].sum())) == bits(np_sum_a(a[100:900].tolist())))
