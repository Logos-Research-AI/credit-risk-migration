"""Render Python values as Lean 4 terms for `(α := Float)`.

Floats are rendered by their bits, `(Float.ofBits N)`, so the Lean value is exactly the Python
value (NaN, infinities, -0.0, subnormals included). Nothing here prints a decimal literal.
"""
from __future__ import annotations

import math
import struct

import polars as pl

INT_DTYPES = (pl.Int8, pl.Int16, pl.Int32, pl.Int64, pl.UInt8, pl.UInt16, pl.UInt32, pl.UInt64)
FLOAT_DTYPES = (pl.Float32, pl.Float64)


def bits(x: float) -> int:
    return struct.unpack("<Q", struct.pack("<d", float(x)))[0]


def from_bits(b: int) -> float:
    return struct.unpack("<d", struct.pack("<Q", b))[0]


def lean_float(x: float) -> str:
    return f"(Float.ofBits {bits(x)})"


def lean_int(n: int, typed: bool = False) -> str:
    """An integer literal; negative ones are parenthesised; typed=True gives `(n : Int)`."""
    if typed:
        return f"({n} : Int)"
    return f"({n})" if n < 0 else str(n)


def lean_bool(b: bool) -> str:
    return "true" if b else "false"


def lean_str(s: str) -> str:
    out = ['"']
    for ch in s:
        o = ord(ch)
        if ch == "\\":
            out.append("\\\\")
        elif ch == '"':
            out.append('\\"')
        elif ch == "\n":
            out.append("\\n")
        elif ch == "\t":
            out.append("\\t")
        elif ch == "\r":
            out.append("\\r")
        elif o < 32 or o == 127:
            out.append("\\x%02x" % o)
        else:
            out.append(ch)
    out.append('"')
    return "".join(out)


def lean_opt(v, f) -> str:
    return "none" if v is None else f"some {f(v)}"


def lean_opt_float(x: float | None) -> str:
    return lean_opt(x, lean_float)


def lean_list(items: list[str], typ: str | None = None) -> str:
    """A list literal from already rendered items; `typ` annotates it (needed for empty lists)."""
    body = "[" + ", ".join(items) + "]"
    return f"({body} : {typ})" if typ else body


def lean_floats(xs) -> str:
    """List Float"""
    return lean_list([lean_float(x) for x in xs], "List Float")


def lean_opt_floats(xs) -> str:
    """List (Option Float)"""
    return lean_list([lean_opt_float(x) for x in xs], "List (Option Float)")


def lean_ints(xs) -> str:
    return lean_list([lean_int(int(x)) for x in xs], "List Int")


def lean_opt_ints(xs) -> str:
    return lean_list([lean_opt(x, lean_int) for x in xs], "List (Option Int)")


def lean_value(v) -> str:
    """Generic scalar / list / tuple renderer (bool before int: bool is an int in Python)."""
    if v is None:
        return "none"
    if isinstance(v, bool):
        return lean_bool(v)
    if isinstance(v, int):
        return lean_int(v)
    if isinstance(v, float):
        return lean_float(v)
    if isinstance(v, str):
        return lean_str(v)
    if isinstance(v, tuple):
        return "(" + ", ".join(lean_value(x) for x in v) + ")"
    if isinstance(v, list):
        return "[" + ", ".join(lean_value(x) for x in v) + "]"
    if isinstance(v, pl.Series):
        return lean_col(v)
    if isinstance(v, pl.DataFrame):
        return lean_frame(v)
    raise TypeError(f"no Lean rendering for {type(v)}")


def col_kind(dtype) -> str:
    if dtype in FLOAT_DTYPES:
        return "f64"
    if dtype in INT_DTYPES:
        return "int"
    if dtype == pl.Boolean:
        return "bool"
    if dtype == pl.String:
        return "str"
    if dtype == pl.Null:
        return "null"
    return f"other:{dtype}"


def lean_col(s: pl.Series) -> str:
    """A polars Series as a `Pl.Col Float` term, by dtype (.f64 / .int / .bool / .str; a Null-dtype
    Series of n nulls is `(Pl.Col.null n)`)."""
    k = col_kind(s.dtype)
    vals = s.to_list()
    if k == "f64":
        return "(Pl.Col.f64 " + lean_list([lean_opt_float(x) for x in vals]) + ")"
    if k == "int":
        return "(Pl.Col.int " + lean_list([lean_opt(x, lean_int) for x in vals]) + ")"
    if k == "bool":
        return "(Pl.Col.bool " + lean_list([lean_opt(x, lean_bool) for x in vals]) + ")"
    if k == "str":
        return "(Pl.Col.str " + lean_list([lean_opt(x, lean_str) for x in vals]) + ")"
    if k == "null":
        return f"(Pl.Col.null {len(vals)})"
    raise TypeError(f"no Pl.Col for dtype {s.dtype}")


def lean_frame_items(df: pl.DataFrame) -> str:
    """The bare list literal `[(name, column), ...]` of a DataFrame (no type: use it as the value of
    a `let f : Pl.Frame Float := ...`)."""
    return lean_list([f"({lean_str(n)}, {lean_col(df.get_column(n))})" for n in df.columns])


def lean_frame(df: pl.DataFrame) -> str:
    """A polars DataFrame as a `Pl.Frame Float` term: the list of (name, column) pairs in order.

    The term is `(let f_ : Pl.Frame Float := [...]; f_)`, whose type IS `Pl.Frame Float`, so dot
    notation works on it (`{lean_frame(df)}.select [...]`). The ascription `([...] : Pl.Frame Float)`
    does not: it elaborates to a `List` and `.select` is looked up in `List`."""
    return f"(let f_ : Pl.Frame Float := {lean_frame_items(df)}; f_)"


def lean_frame_let(name: str, df: pl.DataFrame) -> str:
    """`let NAME : Pl.Frame Float := [...]; ` -- the recommended way to give a frame to a unit:
    put it in the suite's `lets` and write `NAME.select [...]` / `unit NAME` in the case terms."""
    return f"let {name} : Pl.Frame Float := {lean_frame_items(df)}; "


def lean_table(df: pl.DataFrame) -> str:
    """A DataFrame as a `Tabular.Table Float` term: rows of (name, cell). Float/int/bool columns
    are `Tabular.Cell.num (some (Float.ofBits ..))` (ints and bools cast, true = 1), String
    columns `Tabular.Cell.str (some "..")`; a null is `none`; a Null-dtype column is
    `Tabular.Cell.num none`."""
    return "(let t_ : Tabular.Table Float := " + lean_list(lean_rows(df)) + "; t_)"


def lean_rows(df: pl.DataFrame) -> list[str]:
    """The rows of lean_table, one `Tabular.Row Float` term each."""
    kinds = [col_kind(df.schema[n]) for n in df.columns]
    rows = []
    for r in df.iter_rows():
        cells = []
        for n, k, v in zip(df.columns, kinds, r, strict=True):
            if k == "str":
                cells.append(f"({lean_str(n)}, Tabular.Cell.str ({lean_opt(v, lean_str)}))")
            elif k in ("f64", "int", "bool", "null"):  # a Null-dtype value is a numeric missing cell
                cells.append(f"({lean_str(n)}, Tabular.Cell.num ({lean_opt(v, lambda x: lean_float(float(x)))}))")
            else:
                raise TypeError(f"no Tabular.Cell for dtype {df.schema[n]}")
        rows.append(lean_list(cells))
    return rows


if __name__ == "__main__":
    assert lean_float(-0.0) == "(Float.ofBits 9223372036854775808)"
    assert math.isnan(from_bits(bits(float("nan"))))
    df = pl.DataFrame({"a": [1.5, None, float("nan")], "i": [1, -2, None], "b": [True, None, False], "s": ["x\"y", None, "é\n"]})
    print(lean_frame(df))
    print(lean_table(df))
    assert lean_col(pl.Series("n", [None, None], dtype=pl.Null)) == "(Pl.Col.null 2)"
    assert lean_frame_let("f", df.select("i").head(1)) == 'let f : Pl.Frame Float := [("i", (Pl.Col.int [some 1]))]; '
