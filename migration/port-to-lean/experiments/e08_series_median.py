"""E08 (T4, 2026-11-16): `Series.drop_nulls().median()` against the select-context expression median
(prelude `Pl.median`, evidence E04), and `pl.lit(x, dtype=pl.Float64)` of the Python float it returns.

  PYTHONPATH=../../port uv run --project ../../port python experiments/e08_series_median.py
"""
import random
import struct

import polars as pl


def bits(x):
    return None if x is None else struct.unpack("<Q", struct.pack("<d", x))[0]


def model(vals):
    """prelude Pl.median: non-null values in the total order (NaN greatest); odd: the middle one;
    even: a if a == b else 0.5 * (b - a) + a"""
    s = sorted((v for v in vals if v is not None), key=lambda v: (v != v, 0.0 if v != v else v))
    n = len(s)
    if n == 0:
        return None
    if n % 2 == 1:
        return s[n // 2]
    a, b = s[n // 2 - 1], s[n // 2]
    return a if (a == b or (a != a and b != b)) else 0.5 * (b - a) + a


random.seed(8)
nan, inf = float("nan"), float("inf")
n_cases = diff_expr = diff_model = diff_lit = 0
kinds = {"even": 0, "odd": 0, "empty": 0, "with_nan": 0, "with_null": 0}
for case in range(4000):
    n = random.choice([0, 1, 2, 3, 4, 5, 6, 7, 10, 11, 50, 51, 257, 1000])
    mode = case % 4
    vals = []
    for _ in range(n):
        r = random.random()
        if r < 0.15:
            vals.append(None)
        elif r < 0.20 and mode == 1:
            vals.append(nan)
        elif r < 0.22 and mode == 2:
            vals.append(random.choice([inf, -inf]))
        elif mode == 3:
            vals.append(float(random.randint(0, 20)) * 250.0)  # many ties, like incomes
        else:
            vals.append(random.uniform(-1e6, 1e6) * 10 ** random.randint(-3, 3))
    s = pl.Series("MonthlyIncome", vals, dtype=pl.Float64)
    m = s.drop_nulls().median()
    assert m is None or type(m) is float
    e = pl.DataFrame({"x": s}).select(pl.col("x").median()).item()
    lit = pl.DataFrame({"k": [1, 2, 3]}).with_columns(o=pl.lit(m, dtype=pl.Float64))
    assert lit.schema["o"] == pl.Float64
    nn = [v for v in vals if v is not None]
    kinds["empty" if not nn else ("even" if len(nn) % 2 == 0 else "odd")] += 1
    kinds["with_nan"] += any(v != v for v in nn)
    kinds["with_null"] += len(nn) < len(vals)
    n_cases += 1
    diff_expr += bits(m) != bits(e)
    diff_model += bits(m) != bits(model(vals))
    diff_lit += [bits(v) for v in lit["o"].to_list()] != [bits(m)] * 3
print("cases", n_cases, kinds)
print("Series.drop_nulls().median() != select-context pl.col.median():", diff_expr)
print("Series.drop_nulls().median() != model of Pl.median:", diff_model)
print("pl.lit(m, dtype=Float64) broadcast != m on every row (null for None):", diff_lit)
# small table
for vals in ([], [None, None], [5000.0], [1.0, 2.0], [1.0, nan], [nan, nan], [1.0, 2.0, nan, nan], [1.0, inf],
             [-inf, inf], [3.0, 1.0, None, 2.0], [1016.85, 7098.24]):
    s = pl.Series("x", vals, dtype=pl.Float64)
    m = s.drop_nulls().median()
    print(vals, "->", m, bits(m), "model", bits(model(vals)))
# an Int32 key joined with an Int64 key
a = pl.DataFrame({"age_group": [1, 2, 3, 4, 5]}, schema={"age_group": pl.Int32})
for dt in (pl.Int32, pl.Int64, pl.Float64, pl.String):
    try:
        b = pl.DataFrame({"age_group": pl.Series([2, 1], dtype=pl.Int64).cast(dt), "median_income": [5.0, 6.0]})
        r = a.join(b, on="age_group", how="left", maintain_order="left")
        print("join Int32 with", dt, "->", r.schema, r.rows())
    except Exception as ex:  # noqa: BLE001
        print("join Int32 with", dt, "raises", type(ex).__name__, str(ex)[:80])
# a right frame without the key, with a column that clashes, with overall_median_income already there
for b in (pl.DataFrame({"k": [1]}),
          pl.DataFrame({"age_group": pl.Series([1], dtype=pl.Int32), "overall_median_income": ["x"]}),
          pl.DataFrame({"age_group": pl.Series([1, 1], dtype=pl.Int32), "median_income": [1.0, 2.0]}),
          pl.DataFrame({"age_group": pl.Series([None, 3], dtype=pl.Int32), "median_income": [1.0, 2.0]}),
          pl.DataFrame({"age_group": pl.Series([], dtype=pl.Int32), "median_income": pl.Series([], dtype=pl.Float64)})):
    try:
        r = a.join(b, on="age_group", how="left", maintain_order="left").with_columns(
            overall_median_income=pl.lit(2.5, dtype=pl.Float64))
        print("02b on", b.schema, b.rows(), "->", r.schema, r.rows())
    except Exception as ex:  # noqa: BLE001
        print("02b on", b.schema, "raises", type(ex).__name__, str(ex)[:80])
# median of a column that is not Float64
for dt in (pl.Int64, pl.String, pl.Boolean):
    try:
        m = pl.Series([1, 2], dtype=pl.Int64).cast(dt).drop_nulls().median()
        print("median of", dt, "->", repr(m))
        print("   lit:", pl.DataFrame({"k": [1]}).with_columns(o=pl.lit(m, dtype=pl.Float64)).rows())
    except Exception as ex:  # noqa: BLE001
        print("median of", dt, "raises", type(ex).__name__, str(ex)[:80])
# coalesce with other dtypes (step 04)
f = pl.DataFrame({"m": [1.0, None], "o": [2.0, 2.0], "s": ["a", "b"], "i": [7, 8], "n": [None, None], "c": [1, 1],
                  "v": [9.0, 9.0]})
for x, y in (("m", "o"), ("m", "i"), ("i", "o"), ("m", "s"), ("s", "o"), ("m", "n"), ("n", "o")):
    try:
        r = f.select(pl.when(pl.col("c") == 1).then(pl.coalesce(pl.col(x), pl.col(y))).otherwise(pl.col("v")).alias("z"))
        print("when.then(coalesce(", x, ",", y, ")).otherwise(f64) ->", r.schema, r.rows())
    except Exception as ex:  # noqa: BLE001
        print("coalesce(", x, ",", y, ") raises", type(ex).__name__, str(ex)[:80])
