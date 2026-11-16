"""E08 (T7, predict input check): library facts the unit def:predict_run_00_input_check relies on.

Run from migration/port-to-lean:
  PYTHONPATH=../../port uv run --project ../../port python experiments/e08_t7_input_check.py
"""
import polars as pl

from credit_risk import sas_compat

print("== with_columns of literals on a frame with no column")
f = pl.DataFrame({"a": [1.0, 2.0, 3.0], "b": ["x", "y", "z"]})
z = f.clear()
for label, fr in (("3 rows", f), ("0 rows", z)):
    e = fr.select([])
    w = e.with_columns([pl.lit(None, dtype=pl.Float64).alias(c) for c in ("p", "q")])
    print(label, "select([]) shape:", e.shape, "-> with_columns(2 null literals) shape:", w.shape, w.schema)
    one = fr.select([pl.col("a").alias("A")])
    w1 = one.with_columns([pl.lit(None, dtype=pl.Float64).alias(c) for c in ("p", "q")])
    print(label, "select(1 col) shape:", one.shape, "-> with_columns shape:", w1.shape)
    w0 = one.with_columns([])
    print(label, "with_columns([]) shape:", w0.shape)

print("== the check expressions on a frame with columns and no row")
raw = pl.DataFrame({"VAR1": pl.Series([], dtype=pl.Float64), "t": pl.Series([], dtype=pl.String)})
text = pl.col("t").str.strip_chars(" ")
chk = raw.select(
    pl.col("VAR1"),
    bad_row=sas_compat.flag(
        pl.col("VAR1").is_null()
        | ~pl.when(text.str.len_chars() <= 32).then(sas_compat.input_best32(text)).is_in([0.0, 1.0]).fill_null(False)
    ),
)
print(chk.shape, chk.schema, int(chk.get_column("bad_row").sum()), chk.height - chk.get_column("VAR1").drop_nulls().n_unique())

print("== the same on the one-row frame of null literals")
one = pl.DataFrame().with_columns([pl.lit(None, dtype=pl.Float64).alias(c) for c in ("VAR1", "x")])
x = pl.col("x")
cok = sas_compat.ge(x, 0) & sas_compat.eq(x, pl.when(x >= 0).then(x.floor()).otherwise(x.ceil()))
chk = one.select(pl.col("VAR1"), bad_row=sas_compat.flag(pl.col("VAR1").is_null() | ~cok))
print(one.shape, chk.shape, chk.rows(), chk.height - chk.get_column("VAR1").drop_nulls().n_unique())

print("== n_unique of a text id column; of floats")
print(pl.Series(["7", "07", "7 ", None, "7"]).drop_nulls().n_unique(),
      pl.Series([0.0, -0.0, float("nan"), float("nan"), None, 1.0]).drop_nulls().n_unique())

print("== count_ok and is_in on values")
v = pl.DataFrame({"x": [0.0, -0.0, 1.0, 1.5, -1.0, None, float("nan"), float("inf"), 2.0**53, -0.5, 1e300]})
print(v.select(ok=cok, isin=x.is_in([0.0, 1.0]), ge0=x >= 0).rows())

print("== strip / upper / is_in of the stated() chain")
s = pl.DataFrame({"t": [" na ", "Na", ".", " . ", "", None, "N A", "\tNA", "0", "na "]})
print(s.select(st=~pl.col("t").fill_null("").str.strip_chars(" ").str.to_uppercase().is_in(["", ".", "NA"])).to_series().to_list())

print("== Python upper on names; f-string")
print(["age".upper(), "Age".upper(), "VAR12".upper(), f"VAR{11 + 1}"])

print("== to_uppercase over every Unicode scalar value: which characters give a text with N, A or '.'")
cps = [c for c in range(0x110000) if not 0xD800 <= c <= 0xDFFF]
allc = pl.DataFrame({"c": [chr(c) for c in cps]}).with_columns(u=pl.col("c").str.to_uppercase())
hit = allc.filter(pl.col("u").str.contains("[NA.]") | (pl.col("u").str.len_chars() == 0))
print("characters whose upper form holds N, A or '.' or is empty:", sorted(hit.get_column("c").to_list()))
ascii_diff = allc.filter((pl.col("c").str.len_bytes() > 1) & pl.col("u").str.contains("^[\\x00-\\x7f]+$"))
print("non-ASCII characters whose upper form is ASCII:", [(hex(ord(c)), u) for c, u in ascii_diff.iter_rows()])
low = allc.filter(pl.col("c").str.len_bytes() == 1).with_columns(p=pl.col("c").map_elements(lambda s: s.upper() if "a" <= s <= "z" else s, return_dtype=pl.String))
print("ASCII characters where to_uppercase differs from a-z -> A-Z:", low.filter(pl.col("u") != pl.col("p")).height)
print("per character vs whole string:", pl.DataFrame({"t": ["naσς", "ǆna", "ŉa", "ṅa"]}).select(pl.col("t").str.to_uppercase()).to_series().to_list())
print("python upper, non-ASCII names with an ASCII upper form:", ["ſeriousDlqin2yrs".upper(), "MonthlyIncome".upper(), "ı".upper()])
print("strip_chars(' ') on other blanks:", pl.DataFrame({"t": [" NA ", "　NA", " NA ", "\tNA\n"]}).select(pl.col("t").str.strip_chars(" ")).to_series().to_list())
