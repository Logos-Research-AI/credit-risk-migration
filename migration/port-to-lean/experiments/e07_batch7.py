"""E07: library calls new to the port after 2026-11-16 (rulebook batch 7). Run from port/:
    uv run python ../migration/port-to-lean/experiments/e07_batch7.py
"""
import math, struct, random
import numpy as np, polars as pl
from credit_risk import sas_compat as sc

nan, inf = float("nan"), float("inf")
bits = lambda x: None if x is None else struct.unpack("<Q", struct.pack("<d", x))[0]
def show(tag, f):
    try:
        print(f"{tag}: {f()!r}")
    except Exception as e:  # noqa: BLE001
        print(f"{tag}: RAISES {type(e).__name__}: {str(e)[:120]}")

print("== strings")
s = pl.DataFrame({"t": ["  12 ", "\t12", " NA ", "", None, "na", ". ", " é ", "ß", "x" * 33, " " + "1" * 32 + " ", " 12"]})
show("strip_chars(' ')", lambda: s.select(pl.col("t").str.strip_chars(" ")).to_series().to_list())
show("strip_chars()   ", lambda: s.select(pl.col("t").str.strip_chars()).to_series().to_list())
show("len_chars", lambda: s.select(pl.col("t").str.len_chars()).to_series().to_list())
show("len_chars dtype", lambda: s.select(pl.col("t").str.len_chars()).schema)
show("len_chars <= 32", lambda: s.select(pl.col("t").str.strip_chars(" ").str.len_chars() <= 32).to_series().to_list())
show("to_uppercase", lambda: s.select(pl.col("t").str.to_uppercase()).to_series().to_list())
show("python upper", lambda: ["ß".upper(), "é".upper(), "ı".upper(), "age".upper()])
show("fill_null('')", lambda: s.select(pl.col("t").fill_null("")).to_series().to_list())
show("stated", lambda: s.select(~pl.col("t").fill_null("").str.strip_chars(" ").str.to_uppercase().is_in(["", ".", "NA"])).to_series().to_list())
show("is_in strings null", lambda: pl.DataFrame({"t": ["A", None, "C"]}).select(pl.col("t").is_in(["A", "B"])).to_series().to_list())
show("when(len<=32).then(x) name", lambda: s.select(pl.when(pl.col("t").str.len_chars() <= 32).then(sc.input_best32(pl.col("t").str.strip_chars(" ")))).schema)
show("input_best32 on stripped", lambda: s.select(sc.input_best32(pl.col("t").str.strip_chars(" "))).to_series().to_list())

print("== is_in floats, floor/ceil, count_ok")
f = pl.DataFrame({"x": [0.0, -0.0, 1.0, 2.0, None, nan, 0.5, -0.5, -1.5, 3.0, inf, -inf, 1e300]})
show("is_in([0.0,1.0])", lambda: f.select(pl.col("x").is_in([0.0, 1.0])).to_series().to_list())
show("~is_in.fill_null(False)", lambda: f.select(~pl.col("x").is_in([0.0, 1.0]).fill_null(False)).to_series().to_list())
show("is_in on Int64 col", lambda: pl.DataFrame({"x": [0, 1, 2, None]}).select(pl.col("x").is_in([0.0, 1.0])).to_series().to_list())
show("ceil bits", lambda: [bits(v) for v in f.select(pl.col("x").ceil()).to_series().to_list()])
show("-floor(-x) bits", lambda: [bits(v) for v in f.select(-((-pl.col("x")).floor())).to_series().to_list()])
show("floor bits", lambda: [bits(v) for v in f.select(pl.col("x").floor()).to_series().to_list()])
x = pl.col("x")
show("count_ok", lambda: f.select(sc.ge(x, 0) & sc.eq(x, pl.when(x >= 0).then(x.floor()).otherwise(x.ceil()))).to_series().to_list())
show("ceil of Int64 col dtype", lambda: pl.DataFrame({"x": [1, None]}).select(pl.col("x").ceil(), f=pl.col("x").floor()).schema)

print("== n_unique / drop_nulls")
show("n_unique float", lambda: pl.Series([1.0, 1.0, None, nan, nan, 0.0, -0.0, None]).drop_nulls().n_unique())
show("n_unique float with nulls kept", lambda: pl.Series([1.0, None, None]).n_unique())
show("n_unique str", lambda: pl.Series(["a", "A", "a ", None, "a"]).drop_nulls().n_unique())
show("n_unique empty", lambda: pl.Series([], dtype=pl.Float64).drop_nulls().n_unique())
show("sum of Int64 flag col", lambda: (pl.DataFrame({"b": [1, 0, 1]}).get_column("b").sum(), pl.DataFrame({"b": []}, schema={"b": pl.Int64}).get_column("b").sum()))

print("== coalesce vs fill_null")
c = pl.DataFrame({"a": [1.0, None, nan, None, -0.0], "b": [9.0, 8.0, 7.0, None, 5.0]})
show("coalesce", lambda: [bits(v) for v in c.select(pl.coalesce(pl.col("a"), pl.col("b"))).to_series().to_list()])
show("fill_null", lambda: [bits(v) for v in c.select(pl.col("a").fill_null(pl.col("b"))).to_series().to_list()])
show("coalesce name", lambda: c.select(pl.coalesce(pl.col("a"), pl.col("b"))).columns)
show("coalesce f64,null-f64 all null col", lambda: pl.DataFrame({"a": [None, None], "b": [1.0, None]}, schema={"a": pl.Float64, "b": pl.Float64}).select(pl.coalesce("a", "b")).to_series().to_list())

print("== shift / ne_missing / int_range")
k = pl.DataFrame({"p": [None, None, 0.1, 0.1, 0.2, nan, nan, 0.0, -0.0, 0.3]})
show("shift(-1)", lambda: k.select(pl.col("p").shift(-1)).to_series().to_list())
show("ne_missing(shift(-1))", lambda: k.select(pl.col("p").ne_missing(pl.col("p").shift(-1))).to_series().to_list())
last = (pl.int_range(pl.len()) == pl.len() - 1) | pl.col("p").ne_missing(pl.col("p").shift(-1))
show("last flag", lambda: k.select(last).to_series().to_list())
show("last flag empty frame", lambda: k.clear().select(last).to_series().to_list())
show("last flag 1 row", lambda: k.head(1).select(last).to_series().to_list())
show("when(last).then(abs) on empty", lambda: k.clear().with_columns(v=pl.when(last).then(pl.col("p").abs())).schema)
show("int_range dtype", lambda: k.select(pl.int_range(pl.len())).schema)

print("== head / clear / item negative")
show("head(0) cols", lambda: (k.head(0).shape, k.head(0).schema))
show("head(min(h,1))", lambda: k.head(min(k.height, 1)).shape)
show("clear", lambda: (k.clear().shape, k.clear().schema))
show("clear.with_columns(lit+flag)", lambda: k.clear().with_columns(score_bin=pl.lit(0, pl.Int64) + sc.flag(sc.gt(pl.col("p"), pl.lit(0.1, pl.Float64)))).schema)
show("lit(0,Int64)+flag on rows", lambda: k.with_columns(sb=pl.lit(0, pl.Int64) + sc.flag(sc.gt(pl.col("p"), pl.lit(0.1, pl.Float64))) + sc.flag(sc.gt(pl.col("p"), pl.lit(None, pl.Float64)))).get_column("sb").to_list())
show("with_columns(score_bin=lit(0,Int64)) no cuts", lambda: k.clear().with_columns(score_bin=pl.lit(0, pl.Int64)).schema)
srt = pl.DataFrame({"s": [3.0, None, 1.0, 2.0, nan]}).select("s").sort("s", maintain_order=True)
show("sorted", lambda: srt.to_series().to_list())
show("item(-1,0), item(0,0), item(-5,0)", lambda: (srt.item(-1, 0), srt.item(0, 0), srt.item(-5, 0)))
show("nearest-rank idx n=5", lambda: [-(-kk * 5 // 10) - 1 for kk in range(1, 10)])
show("nearest-rank idx n=1", lambda: [-(-kk * 1 // 10) - 1 for kk in range(1, 10)])
show("floor div negatives", lambda: [(-7) // 10, (-10) // 10, (-11) // 10, 7 // 10])

print("== join with left_on expression")
l = pl.DataFrame({"VAR1": [1.0, 2.0, 3.0, 4.0], "age_group": pl.Series([1, 2, 5, 3], dtype=pl.Int32)})
r = pl.DataFrame({"age_group": [1.0, 2.0, 3.0, 4.0, 5.0], "median_income": [10.0, None, 30.0, 40.0, 50.0], "overall_median_income": [33.0] * 5})
j = l.join(r, left_on=pl.col("age_group").cast(pl.Float64), right_on="age_group", how="left", maintain_order="left")
show("join cols/schema", lambda: j.schema)
show("join rows", lambda: j.rows())
r2 = pl.DataFrame({"age_group": [1.0, 1.0, None, 2.5], "median_income": [10.0, 11.0, 12.0, 13.0], "overall_median_income": [33.0] * 4})
show("join dup/missing keys", lambda: l.join(r2, left_on=pl.col("age_group").cast(pl.Float64), right_on="age_group", how="left", maintain_order="left").rows())
r3 = pl.DataFrame({"age_group": ["1", "2"], "median_income": [10.0, 11.0], "overall_median_income": [1.0, 1.0]})
show("join string key", lambda: l.join(r3, left_on=pl.col("age_group").cast(pl.Float64), right_on="age_group", how="left", maintain_order="left").rows())
r4 = pl.DataFrame({"age_group": [1.0], "median_income": [10.0], "overall_median_income": [1.0], "VAR1": [7.0]})
show("join clash", lambda: l.join(r4, left_on=pl.col("age_group").cast(pl.Float64), right_on="age_group", how="left", maintain_order="left").columns)
show("left join Int32 on Int32, keep right cols", lambda: pl.DataFrame({"age_group": [1, 2, 3, 4, 5]}, schema={"age_group": pl.Int32}).join(
    pl.DataFrame({"age_group": pl.Series([3, 1], dtype=pl.Int32), "median_income": [5.0, 6.0]}), on="age_group", how="left", maintain_order="left").rows())
show("lit(median, Float64) broadcast", lambda: pl.DataFrame({"a": [1, 2]}).with_columns(o=pl.lit(pl.Series([1.0, None, 4.0]).drop_nulls().median(), dtype=pl.Float64)).rows())
show("Series.median none", lambda: pl.Series([None, None], dtype=pl.Float64).drop_nulls().median())

print("== fill_null on joined columns")
dl = pl.DataFrame({"decile": list(range(1, 4))}, schema={"decile": pl.Int64})
dg = pl.DataFrame({"decile": pl.Series([2], dtype=pl.Int64), "total_count": pl.Series([7], dtype=pl.Int64), "defaults": [3.0], "capture_rate": [0.5]})
dj = dl.join(dg, on="decile", how="left", maintain_order="left").with_columns(
    total_count=pl.col("total_count").fill_null(0), defaults=pl.col("defaults").fill_null(0), capture_rate=pl.col("capture_rate").fill_null(0.0))
show("fill_null schema", lambda: dj.schema)
show("fill_null rows", lambda: dj.rows())
show("fill_null(0) keeps NaN", lambda: pl.DataFrame({"a": [nan, None]}).select(pl.col("a").fill_null(0)).to_series().to_list())
show("cum_sum of filled Int64 / Float64", lambda: dj.select(pl.col("total_count").cum_sum(), pl.col("defaults").cum_sum().forward_fill()).rows())

print("== group agg of flag sums, cum_sum arithmetic, frame cast")
g = pl.DataFrame({"pd": [0.2, 0.1, 0.2, None, 0.1, nan], "d": [1.0, 0.0, 0.0, 1.0, None, 1.0]})
ap = (g.filter(pl.col("pd").is_not_null()).group_by("pd", maintain_order=True)
      .agg(n_bad=sc.flag(pl.col("d") == 1).sum(), n_good=sc.flag(pl.col("d") == 0).sum()).sort("pd", maintain_order=True))
show("auc_pairs", lambda: (ap.schema, ap.rows()))
at = ap.select(concordant=(pl.col("n_bad") * (pl.col("n_good").cum_sum() - pl.col("n_good"))).sum(), tied=(pl.col("n_bad") * pl.col("n_good")).sum(),
               cum_good=pl.col("n_good").sum(), cum_bad=pl.col("n_bad").sum()).cast(pl.Float64)
show("auc_totals", lambda: (at.schema, at.rows()))
ae = ap.clear().select(concordant=(pl.col("n_bad") * (pl.col("n_good").cum_sum() - pl.col("n_good"))).sum(), cum_bad=pl.col("n_bad").sum()).cast(pl.Float64)
show("auc_totals on empty pairs", lambda: (ae.shape, ae.rows()))
show("when(prod>0).then(..) / with_columns(lit str) / select / head(0)", lambda: at.with_columns(ROCModel=pl.lit("M"), AUC=pl.when(pl.col("cum_bad") * pl.col("cum_good") > 0).then(
    (pl.col("concordant") + pl.col("tied") / 2) / (pl.col("cum_bad") * pl.col("cum_good")))).with_columns(Gini=2 * pl.col("AUC") - 1).select("ROCModel", "AUC", "Gini").head(0).schema)

print("== map_elements(sas_best12)")
m = pl.DataFrame({"v": [1234567890123.0, None, 5.0, nan, 0.1 + 0.2, -0.0, 1e20]})
calls = []
def spy(v):
    calls.append(v)
    return sc.sas_best12(v)
show("map_elements", lambda: m.select(pl.col("v").map_elements(spy, return_dtype=pl.String)).to_series().to_list())
show("values passed", lambda: calls)
show("name kept", lambda: m.select(pl.col("v").map_elements(sc.sas_best12, return_dtype=pl.String)).columns)
show("on Int64 column: python type passed", lambda: (pl.DataFrame({"v": [3, None]}).select(pl.col("v").map_elements(lambda z: type(z).__name__, return_dtype=pl.String)).to_series().to_list()))
show("empty frame", lambda: m.clear().select(sc.input_best32(pl.col("v").map_elements(sc.sas_best12, return_dtype=pl.String))).schema)

print("== numpy ** 2, math.fsum, builtin max/min")
rng = random.Random(7)
arr = np.array([rng.uniform(-1, 1) * 10 ** rng.randint(-8, 8) for _ in range(400000)])
show("np array ** 2 == x * x (bits) mismatches", lambda: int(np.count_nonzero((arr ** 2).view(np.uint64) != (arr * arr).view(np.uint64))))
show("(arr - c) ** 2 .tolist() == python (x-c)*(x-c) mismatches", lambda: sum(1 for a, b in zip(((arr - 0.3) ** 2).tolist(), [(v - 0.3) * (v - 0.3) for v in arr.tolist()]) if bits(a) != bits(b)))
vals = [rng.uniform(0, 1) for _ in range(1000)]
acc = 0.0
for v in vals: acc += v
show("fsum vs left fold vs np.sum (bits)", lambda: (bits(math.fsum(vals)), bits(acc), bits(float(np.sum(np.array(vals))))))
show("fsum [] / [nan] / [inf,-inf]", lambda: (math.fsum([]), math.fsum([nan]),))
show("fsum inf,-inf", lambda: math.fsum([inf, -inf]))
show("max(a,0.0): -0.0, nan, 0.3, -1", lambda: [max(-0.0, 0.0), max(nan, 0.0), max(0.3, 0.0), max(-1.0, 0.0)])
show("min(a,1.0): nan, 1.5, 0.3", lambda: [min(nan, 1.0), min(1.5, 1.0), min(0.3, 1.0)])
show("_SE_EPS, _SQRTBIG, _TIE_EPS hex", lambda: (sc._SE_EPS.hex(), sc._SQRTBIG.hex(), sc._TIE_EPS.hex(), repr(sc._SE_EPS), repr(sc._SQRTBIG)))
show("0.5/int, int/int", lambda: (0.5 / 3, 7 / 2))

print("== lit(None, Float64).alias; rename identity; select alias")
z = pl.DataFrame({"AGE": [1.0], "x": ["a"]})
show("with_columns(lit None f64)", lambda: z.with_columns([pl.lit(None, dtype=pl.Float64).alias(cn) for cn in ["q", "x2"]]).schema)
show("rename identity+case", lambda: z.rename({"AGE": "age", "x": "x"}).columns)
show("rename to duplicate", lambda: pl.DataFrame({"AGE": [1.0], "age": [2.0]}).rename({"AGE": "age", "age": "age"}).columns)
show("select alias list", lambda: z.select([pl.col("AGE").alias("age")]).columns)
show("select([]) on frame", lambda: z.select([]).shape)
show("schema test", lambda: (z.schema["x"] != pl.String, z.schema["AGE"] != pl.String))
