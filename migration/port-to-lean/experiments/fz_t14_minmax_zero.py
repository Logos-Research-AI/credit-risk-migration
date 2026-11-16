"""Fuzz pass, T14 (step 04): min_pd / max_pd of a decile that holds zeros of both signs.
PYTHONPATH=../../port uv run --project ../../port python experiments/fz_t14_minmax_zero.py"""
import struct
import sys
from pathlib import Path

import polars as pl

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "diffeval" / "units"))
sys.argv = [sys.argv[0]]
import t14_gen as t14  # noqa: E402


def b(x):
    return None if x is None else struct.unpack("<Q", struct.pack("<d", x))[0]


for pd_ in ([-0.0, 0.0], [0.0, -0.0]):
    df = pl.DataFrame({"default_flag": [0.0, 1.0], "pd_logistic": pd_})
    da = t14.run_slice(t14.S04, {"logit_scored_valid": df})["decile_analysis"]
    print(pd_, "min_pd bits", [b(v) for v in da["min_pd"].to_list() if v is not None], "max_pd bits", [b(v) for v in da["max_pd"].to_list() if v is not None])
