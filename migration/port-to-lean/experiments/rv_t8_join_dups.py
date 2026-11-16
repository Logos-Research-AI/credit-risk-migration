"""Review of T8 (port-translator-9): left join with a key expression when the RIGHT frame repeats a
key. Does every left row get its matches in right order, at any size?"""
import random
import polars as pl

def model(lk, rk):
    out = []
    for i, a in enumerate(lk):
        ms = [j for j, b in enumerate(rk) if a is not None and b is not None and float(a) == b]
        out += [(i, None)] if not ms else [(i, j) for j in ms]
    return out

random.seed(7)
for nl, nr, kmax in [(4, 6, 3), (50, 40, 5), (5000, 300, 7), (200000, 2000, 9), (3, 100000, 4)]:
    lk = [random.choice([None] + list(range(kmax + 2))) for _ in range(nl)]
    rk = [random.choice([None, float("nan")] + [float(k) for k in range(kmax)]) for _ in range(nr)]
    l = pl.DataFrame({"i": list(range(nl)), "age_group": lk}, schema={"i": pl.Int64, "age_group": pl.Int32})
    r = pl.DataFrame({"age_group": rk, "j": list(range(nr))}, schema={"age_group": pl.Float64, "j": pl.Int64})
    got = l.join(r, left_on=pl.col("age_group").cast(pl.Float64), right_on="age_group", how="left",
                 maintain_order="left").select("i", "j").rows()
    exp = model(lk, rk)
    print(nl, nr, kmax, "rows", len(got), "equal to the model (right order within a left row):", got == exp)
    if got != exp:
        k = next(t for t in range(min(len(got), len(exp))) if got[t] != exp[t])
        print("  first difference at", k, got[k - 2:k + 4], exp[k - 2:k + 4])
