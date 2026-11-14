"""E06: bracketing of pl.sum_horizontal for N = 2..6 Float64 columns (brute force over all binary trees preserving left-to-right order, and with commuted operands irrelevant)."""
import struct, random, itertools, collections, sys
import polars as pl
sys.path.insert(0, ".")
from credit_risk import sas_compat as sc
bits = lambda x: struct.unpack("<Q", struct.pack("<d", x))[0]
rng = random.Random(1)
def trees(lo, hi):
    if hi - lo == 1: yield lo; return
    for m in range(lo + 1, hi):
        for l in trees(lo, m):
            for r in trees(m, hi): yield (l, r)
def ev(t, v): return v[t] if isinstance(t, int) else ev(t[0], v) + ev(t[1], v)
for N in range(2, 7):
    names = [f"c{i}" for i in range(N)]
    rows = [[rng.uniform(-1, 1) * 10 ** rng.randint(-8, 8) for _ in range(N)] for _ in range(4000)]
    df = pl.DataFrame(rows, schema=names, orient="row")
    got = df.select(pl.sum_horizontal(*names)).to_series().to_list()
    got2 = df.select(sc.sas_sum(*[pl.col(n) for n in names])).to_series().to_list()
    ok = [t for t in trees(0, N) if all(bits(ev(t, r)) == bits(g) for r, g in zip(rows, got))]
    print(N, "order-preserving trees matching all 4000 rows:", ok, " sas_sum identical:", all(bits(a) == bits(b) for a, b in zip(got, got2)))
# nulls: which fold when some are null
df = pl.DataFrame({"a": [1e16, None, 1e16, 1e16], "b": [1.0, 1e16, None, 1.0], "c": [1.0, 1.0, 1.0, None], "d": [1.0, 1.0, 1.0, 1.0]})
print("with nulls:", df.select(pl.sum_horizontal("a", "b", "c", "d")).to_series().to_list())
