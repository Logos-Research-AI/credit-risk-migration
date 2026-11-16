"""E09 (check of G27 a): no non-ASCII character has an upper form made only of the characters of "", ".", "NA"."""
import sys
import polars as pl
bad_py = [hex(c) for c in range(128, sys.maxunicode + 1) if not (0xD800 <= c <= 0xDFFF) and set(chr(c).upper()) <= set("NA.")]
print("python upper, non-ASCII characters whose upper form is within 'NA.':", bad_py)
chars = [chr(c) for c in range(128, sys.maxunicode + 1) if not (0xD800 <= c <= 0xDFFF)]
up = pl.Series(chars).str.to_uppercase().to_list()
print("polars to_uppercase, same question:", [hex(ord(c)) for c, u in zip(chars, up) if set(u) <= set("NA.")])
print("empty upper forms (polars):", sum(1 for u in up if u == ""))
t = pl.Series(["n" + "ŉ", "ŉa", "na", "Na", ".", " nA "])
print(t.str.strip_chars(" ").str.to_uppercase().is_in(["", ".", "NA"]).to_list(), [s.strip(" ").upper() in ("", ".", "NA") for s in t.to_list()])
