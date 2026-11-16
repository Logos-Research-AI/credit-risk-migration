"""E12b (2026-11-16): R2, which texts of at most 12 characters the BEST12 round trip changes.

  PYTHONPATH=../../port uv run --project ../../port python experiments/e12b_best12_changed.py > experiments/e12b_best12_changed.out.txt

y = input_best32(sas_best12(float(text))); changed means y is not float(text) bit for bit.
"""
from __future__ import annotations
import random, struct
from collections import Counter
import polars as pl
from credit_risk import sas_compat as sc

bits = lambda x: struct.unpack("<Q", struct.pack("<d", x))[0]  # noqa: E731
rng = random.Random(11)
dg = lambda n: "".join(rng.choice("0123456789") for _ in range(n))  # noqa: E731


def trip(texts):
    xs = [float(t) for t in texts]
    b = [sc.sas_best12(x) for x in xs]
    ys = pl.DataFrame({"t": b}, schema={"t": pl.String}).select(sc.input_best32(pl.col("t"))).to_series().to_list()
    return [(t, bb, y, y is not None and bits(y) == bits(x)) for t, x, bb, y in zip(texts, xs, b, ys, strict=True)]


print("== '.' + 11 digits (12 characters): changed exactly when the 11th digit is not 0?")
r = trip(["." + dg(11) for _ in range(200000)])
c = Counter((t[-1] != "0", ok) for t, _, _, ok in r)
print("   (11th digit not 0, unchanged) counts:", dict(c))
print("   value read is the text rounded to 10 decimals:", sum(1 for t, b, y, ok in r if y == float(f"{float(t):.10f}")), "of", len(r))
print("   examples of rounding at a 5:", [(t, b) for t, b, y, ok in trip([".12345678905", ".12345678915", ".12345678925", ".99999999995", ".00000000005", ".00000000004", ".00000000001"])])

print("\n== plain texts (digits and at most one point, no sign, no exponent): every shape of at most 12 characters")
tot = Counter(); bad = Counter(); ex = {}
for n in range(1, 13):
    shapes = [("int", None)] + [("point", p) for p in range(0, n)]   # p digits before the point; p = n-1 is 'ddd.'
    for kind, p in shapes:
        if kind == "point" and n == 1:
            continue
        texts = []
        for _ in range(4000):
            s = dg(n) if kind == "int" else dg(n - 1)
            texts.append(s if kind == "int" else s[:p] + "." + s[p:])
        for t, b, y, ok in trip(texts):
            key = "integer" if kind == "int" else ("'.' first, 11 digits after" if (p == 0 and n == 12) else "point elsewhere or shorter")
            tot[key] += 1
            if not ok:
                bad[key] += 1
                ex.setdefault(key, (t, b, y))
print("   tried:", dict(tot)); print("   changed:", dict(bad)); print("   first changed:", ex)

print("\n== E-notation texts of at most 12 characters (if a valid file may hold them): changed by number of significant digits and exponent")
res = Counter(); allc = Counter(); ex = {}
for _ in range(400000):
    e = rng.choice(["E-12", "E-9", "E-7", "E-6", "E-5", "E-4", "E-3", "E-1", "E0", "E1", "E3", "E5", "E7", "E9", "E10", "E11", "E12", "E20", "E-20", "E300", "E-300"])
    k = rng.randint(1, 12 - len(e) - 1)                     # significant digits, written d.ddd
    m = rng.choice("123456789") + dg(k - 1)
    if k > 1 and m[-1] == "0":
        m = m[:-1] + "5"
    t = (m[0] + "." + m[1:] if k > 1 else m) + e
    if len(t) > 12:
        continue
    (_, b, y, ok), = trip([t])
    allc[(e, k)] += 1
    if not ok:
        res[(e, k)] += 1
        ex.setdefault((e, k), (t, b, y))
for key in sorted(res, key=lambda z: (float("1" + z[0]), z[1])):
    print(f"   exponent {key[0]:5} {key[1]} significant digits: changed {res[key]} of {allc[key]}; e.g. {ex[key]}")
print("   exponents with no change at any number of digits:", sorted({e for e, _ in allc} - {e for e, _ in res}, key=lambda z: float("1" + z)))
