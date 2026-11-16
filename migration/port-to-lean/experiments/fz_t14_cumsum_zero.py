"""Fuzz pass, T14 (step 05): polars cum_sum on a Float64 column whose first non-null values are -0.0.
PYTHONPATH=../../port uv run --project ../../port python experiments/fz_t14_cumsum_zero.py"""
import struct
import sys
from pathlib import Path

import polars as pl

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "diffeval" / "units"))
sys.argv = [sys.argv[0]]
import t14_gen as t14  # noqa: E402


def b(x):
    return None if x is None else struct.unpack("<Q", struct.pack("<d", x))[0]


s = pl.Series("x", [None, -0.0, -0.0, 1.0], dtype=pl.Float64)
print("polars", pl.__version__)
print("cum_sum of [null, -0.0, -0.0, 1.0] (bits):", [b(v) for v in pl.DataFrame({"x": s}).select(pl.col("x").cum_sum()).to_series().to_list()])
print("Series.cum_sum (bits):", [b(v) for v in s.cum_sum().to_list()])
dd = pl.DataFrame({"default_flag": [1.0]})
da = pl.DataFrame({"decile": pl.Series([1, 2], dtype=pl.Int64), "total_count": pl.Series([1, 1], dtype=pl.Int64),
                   "defaults": pl.Series([-0.0, -0.0], dtype=pl.Float64)})
out, best = t14.run05(dd, da)
for c in ("cum_defaults", "cum_capture_rate", "cum_lift"):
    print("step 05 lines 287-321,", c, "(bits):", [b(v) for v in out[c].to_list()])
