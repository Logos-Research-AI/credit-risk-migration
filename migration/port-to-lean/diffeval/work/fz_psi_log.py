"""Seed 20912, bin 7: train share 7/37, validation share 0.5. Which operation carries the 1-ulp difference?"""
import math
import struct

import polars as pl


def bits(x):
    return struct.unpack("<Q", struct.pack("<d", x))[0]


a, b = 7 / 37, 0.5
r = a / b
lp = pl.DataFrame({"x": [r]}).select(pl.col("x").log()).item()
print("a", bits(a), "b", bits(b), "ratio", bits(r), repr(r))
print("polars log", bits(lp), repr(lp), "math.log", bits(math.log(r)), "difference", bits(lp) - bits(math.log(r)))
print("component with polars log", bits((a - b) * lp), "with math.log", bits((a - b) * math.log(r)))
print(f"Lean: [((Float.log (Float.ofBits {bits(r)})).toBits.toNat : Int), (((Float.ofBits {bits(a)} - Float.ofBits {bits(b)}) * Float.log (Float.ofBits {bits(r)})).toBits.toNat : Int)]")
