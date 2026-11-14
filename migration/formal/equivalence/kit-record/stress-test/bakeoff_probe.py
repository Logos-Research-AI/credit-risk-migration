"""Diff-inspector probes: real Python (polars) on inputs that separate translation A from B."""
import math
import struct

import polars as pl

from credit_risk import sas_compat as sc
from credit_risk.metrics_calculation import confusion_metrics

nan = float("nan")
inf = float("inf")


def bits(v):
    if v is None:
        return "null"
    if isinstance(v, bool):
        return str(v)
    if isinstance(v, int):
        return f"int {v}"
    return f"{v!r} [{struct.unpack('<Q', struct.pack('<d', v))[0]:016x}]"


def show(title, f):
    try:
        r = f()
    except BaseException as e:  # noqa: BLE001
        r = f"RAISES {type(e).__name__}: {str(e).splitlines()[0][:140]}"
    print(f"{title}: {r}")


print("polars", pl.__version__)
print("\n== P1 names (_named / alias) ==")
df = pl.DataFrame({"a": [1.0, None], "b": [2.0, 3.0]})
show("select(lt(col a, col b)).columns", lambda: df.select(sc.lt(pl.col("a"), pl.col("b"))).columns)
show("select(lt(1.0, col b)).columns", lambda: df.select(sc.lt(1.0, pl.col("b"))).columns)
show("select(gt(col a, 0)).columns", lambda: df.select(sc.gt(pl.col("a"), 0)).columns)
show("select(flag(col a > 1)).columns", lambda: df.select(sc.flag(pl.col("a") > 1)).columns)
show("select(sas_round(col a)).columns", lambda: df.select(sc.sas_round(pl.col("a"))).columns)
show("select(sas_round(2.5)).columns", lambda: df.select(sc.sas_round(2.5)).columns)
show("with_columns(sas_round(col a)) replaces a", lambda: df.with_columns(sc.sas_round(pl.col("a") + 0.6)).to_dict(as_series=False))
show("raw when-chain name without _named", lambda: df.select(
    pl.when(pl.col("a").is_null()).then(pl.col("b").is_not_null()).otherwise(pl.col("a") < pl.col("b"))).columns)

print("\n== P2 lt/gt truth table (null, NaN, numbers) ==")
vals = [None, nan, -inf, -1.0, -0.0, 0.0, 1.0, inf]
g = pl.DataFrame({"x": [x for x in vals for _ in vals], "c": [c for _ in vals for c in vals]},
                 schema={"x": pl.Float64, "c": pl.Float64})
o = g.with_columns(lt=sc.lt(pl.col("x"), pl.col("c")), gt=sc.gt(pl.col("x"), pl.col("c")))
print("dtypes", o.schema, "null_count", o.null_count().row(0))
for r in o.iter_rows():
    if r[0] is None or r[1] is None or (isinstance(r[0], float) and math.isnan(r[0])) or (
            isinstance(r[1], float) and math.isnan(r[1])) or (r[0] == 0 and r[1] == 0):
        print("  x=%s c=%s lt=%s gt=%s" % r)

print("\n== P3 lt on ints beyond 2^53, int vs float ==")
big = 2**53
di = pl.DataFrame({"i": [big + 1, big], "f": [float(big), float(big)]})
show("Int64 col (2^53+1, 2^53) lt Float64 col 2^53", lambda: di.select(sc.lt(pl.col("f"), pl.col("i"))).to_series().to_list())
show("Int64 col == Float64 col", lambda: di.select(pl.col("i") == pl.col("f")).to_series().to_list())
show("lt(Int64 col, Int64 lit 2^53+1)", lambda: di.select(sc.lt(pl.col("i"), big + 1)).to_series().to_list())
show("lt(col i, 2^53+2) with i=2^53+1", lambda: di.select(sc.lt(pl.col("i"), big + 2)).to_series().to_list())

print("\n== P4 flag ==")
fb = pl.DataFrame({"p": [True, False, None]})
show("flag(col p)", lambda: (fb.select(sc.flag(pl.col("p"))).schema, fb.select(sc.flag(pl.col("p"))).to_series().to_list()))
show("flag(Float64 col)", lambda: pl.DataFrame({"p": [1.0, 0.0, None]}).select(sc.flag(pl.col("p"))).to_series().to_list())
show("flag(Int64 col)", lambda: pl.DataFrame({"p": [2, 0, None]}).select(sc.flag(pl.col("p"))).to_series().to_list())

print("\n== P5 sas_round: + 0.0 and the sign of zero ==")
xs = [-0.3, -0.0, 0.0, 0.3, -0.5, 0.5, 2.5, -2.5, None, nan, inf, -inf, 2.0**52, -(2.0**52) - 2, 0.5 - 1e-14, 0.5 - 1e-10]
col = pl.DataFrame({"x": xs}, schema={"x": pl.Float64})
print("multi-row column:", [bits(v) for v in col.select(sc.sas_round(pl.col("x"))).to_series().to_list()])
print("with_columns    :", [bits(v) for v in col.with_columns(sc.sas_round(pl.col("x"))).to_series().to_list()])
print("lazy collect    :", [bits(v) for v in col.lazy().select(sc.sas_round(pl.col("x"))).collect().to_series().to_list()])
for x in [-0.3, -0.0, 0.0, None, nan]:
    one = pl.DataFrame({"x": [x]}, schema={"x": pl.Float64})
    print(f"  x={x!r}: 1-row column -> {bits(one.select(sc.sas_round(pl.col('x'))).item())};"
          f" literal on 1-row frame -> {bits(one.select(sc.sas_round(x) if x is not None else sc.sas_round(pl.lit(None, pl.Float64))).item())};"
          f" literal broadcast in 3-row with_columns -> "
          f"{[bits(v) for v in pl.DataFrame({'k': [1, 2, 3]}).with_columns(r=sc.sas_round(x) if x is not None else sc.sas_round(pl.lit(None, pl.Float64)))['r'].to_list()]}")
show("2-row column [-0.3,-0.3]", lambda: [bits(v) for v in pl.DataFrame({"x": [-0.3, -0.3]}).select(sc.sas_round(pl.col("x"))).to_series().to_list()])
show("empty column", lambda: pl.DataFrame({"x": []}, schema={"x": pl.Float64}).select(sc.sas_round(pl.col("x"))).to_series().to_list())
show("int literal sas_round(3)", lambda: (pl.select(sc.sas_round(3)).schema, bits(pl.select(sc.sas_round(3)).item())))
show("Int64 column", lambda: [bits(v) for v in pl.DataFrame({"x": [3, -4, None]}).select(sc.sas_round(pl.col("x"))).to_series().to_list()])
show("String column", lambda: pl.DataFrame({"x": ["a"]}).select(sc.sas_round(pl.col("x"))).to_series().to_list())
show("explain", lambda: pl.DataFrame({"x": [-0.3, 1.0]}).lazy().select(sc.sas_round(pl.col("x"))).explain())

print("\n== P6 pieces: sign, max_horizontal, abs ==")
pc = pl.DataFrame({"x": [nan, -0.0, 0.0, -3.0, 3.0, None, inf, -inf]}, schema={"x": pl.Float64})
print("sign          :", [bits(v) for v in pc.select(pl.col("x").sign()).to_series().to_list()])
print("abs           :", [bits(v) for v in pc.select(pl.col("x").abs()).to_series().to_list()])
print("max_h(1.0, x) :", [bits(v) for v in pc.select(pl.max_horizontal(pl.lit(1.0), pl.col("x"))).to_series().to_list()])
print("max_h(1.0,|x|):", [bits(v) for v in pc.select(pl.max_horizontal(pl.lit(1.0), pl.col("x").abs())).to_series().to_list()])
print("up for NaN    :", pc.select((pl.col("x").abs() - pl.col("x").abs().floor()) >= (0.5 - pl.max_horizontal(pl.lit(1.0), pl.col("x").abs()) * 1e-12)).to_series().to_list())

print("\n== P7 confusion_metrics ==")


def cm(df, thr=0.5):
    c, m, k = confusion_metrics(thr, "s", df)
    return {"confusion": (dict(c.schema), c.rows()), "conf_matrix": (dict(m.schema), m.rows()),
            "metrics": (dict(k.schema), [tuple(bits(v) for v in r) for r in k.rows()])}


def showcm(title, df, thr=0.5):
    print(f"-- {title}")
    try:
        r = cm(df, thr)
        for k2, v in r.items():
            print(f"   {k2}: {v}")
    except BaseException as e:  # noqa: BLE001
        print(f"   RAISES {type(e).__name__}: {str(e).splitlines()[0][:160]}")


base = pl.DataFrame({"pd_logistic": [0.9, 0.1, 0.7, 0.2, None, nan, 0.5],
                     "default_flag": [1.0, 0.0, 0.0, 1.0, 1.0, 0.0, None]})
showcm("float default_flag, null/NaN pd, null default_flag", base)
showcm("Int64 default_flag", base.with_columns(pl.col("default_flag").cast(pl.Int64)))
showcm("existing predicted column in the middle", pl.DataFrame({"pd_logistic": [0.9], "predicted": ["old"], "default_flag": [1.0]}))
showcm("zero rows, schema present", pl.DataFrame(schema={"pd_logistic": pl.Float64, "default_flag": pl.Float64}))
showcm("zero rows, zero columns", pl.DataFrame())
showcm("pd_logistic missing", pl.DataFrame({"default_flag": [1.0]}))
showcm("default_flag missing", pl.DataFrame({"pd_logistic": [0.9]}))
showcm("pd_logistic String", pl.DataFrame({"pd_logistic": ["0.9"], "default_flag": [1.0]}))
showcm("default_flag String", pl.DataFrame({"pd_logistic": [0.9, 0.1], "default_flag": ["1", "0"]}))
showcm("default_flag Boolean", pl.DataFrame({"pd_logistic": [0.9, 0.1], "default_flag": [True, False]}))
showcm("default_flag String, zero rows", pl.DataFrame(schema={"pd_logistic": pl.Float64, "default_flag": pl.String}))
showcm("pd_logistic Int64", pl.DataFrame({"pd_logistic": [1, 0], "default_flag": [1.0, 0.0]}))
showcm("keys -0.0 then 0.0, NaN, 2.0", pl.DataFrame({"pd_logistic": [0.1, 0.1, 0.1, 0.1, 0.1, 0.9],
                                                     "default_flag": [-0.0, 0.0, nan, 2.0, nan, 1.0]}))
showcm("keys 0.0 then -0.0", pl.DataFrame({"pd_logistic": [0.1, 0.1], "default_flag": [0.0, -0.0]}))
showcm("f1 guard: TP=0, FP>0, FN>0 (p=r=0)", pl.DataFrame({"pd_logistic": [0.9, 0.1], "default_flag": [0.0, 1.0]}))
showcm("only negatives predicted (precision null)", pl.DataFrame({"pd_logistic": [0.1, 0.1], "default_flag": [1.0, 0.0]}))
showcm("threshold NaN", base, nan)
showcm("threshold as Python int 1", pl.DataFrame({"pd_logistic": [1.0, 0.5], "default_flag": [1.0, 0.0]}), 1)
showcm("f1 arithmetic 3 TP 1 FP 2 FN", pl.DataFrame({"pd_logistic": [0.9] * 4 + [0.1] * 3, "default_flag": [1.0, 1.0, 1.0, 0.0, 1.0, 1.0, 0.0]}))
tp, fp, fn = 3, 1, 2
p, r = tp / (tp + fp), tp / (tp + fn)
print("   python (2*(p*r))/(p+r) =", bits((2 * (p * r)) / (p + r)), "| 2*p*r/(p+r) =", bits(2 * p * r / (p + r)), "| 2*((p*r)/(p+r)) =", bits(2 * ((p * r) / (p + r))))
