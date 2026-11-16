"""Generate x13_best32_edges.sas: BEST32. in the three regions X11 did not measure.
  a  non-whole values next to and below 1e-5 (X11 holds none within a few ulps of 1e-5, none below 1e-8)
  b  non-whole values from 1e15 up to 2**52 (X11: one point)
  c  whole numbers of more than 21 digits
Every value is the hex of a binary64 number; the log gives hex and BEST32. text side by side.
Usage: python3 x13_make.py > x13_best32_edges.sas"""

import math
import random
import struct


def hx(x: float) -> str:
    return struct.pack(">d", x).hex().upper()


vals: list[float] = [float.fromhex(h) if False else struct.unpack(">d", bytes.fromhex(h))[0] for h in ("3EE4F8B588E368F0", "430C6BF526340006", "4520AF1D78B58C40")]
rnd = random.Random(20261116)
# a: the neighbours of every power of ten from 1e-4 down to 1e-12, then random values below 1e-5
for e in range(-4, -13, -1):
    p = 10.0**e
    for k in (-3, -2, -1, 0, 1, 2, 3):
        v = p
        for _ in range(abs(k)):
            v = math.nextafter(v, math.inf if k > 0 else 0.0)
        vals.append(v)
for e in list(range(-5, -21, -1)) + [-30, -50, -100, -200, -300, -310]:
    for _ in range(4):
        vals.append(rnd.uniform(1, 10) * 10.0**e)
vals += [9.9999999999999e-6, 9.99999999999999e-6, 9.99999999999995e-6, 9.999999999999949e-6, 1.00000000000001e-5, 9.5e-6, 9.99e-6, 5e-6, 2.5e-6, 1.5e-9, 1.25e-7, 2.0**-20, 2.0**-30, 2.0**-40, 1e-300, 5e-324]
vals += [1.2345678901234e-6, 1.23456789012345e-6, 1.234567890123449e-6, 1.2345678901234499e-6, 1.23456789012346e-6, 9.9999999999999e-7, 9.99999999999999e-7, 1.99999999999999e-7, 1.999999999999995e-7]
# b: non-whole values from 1e15 to 2**52 (the spacing is 0.125, 0.25 or 0.5 there)
for b in (1e15, 1000000000000001.0, 1234567890123456.0, 2e15, 2251799813685248.0, 3999999999999999.0, 4e15, 4503599627370494.0, 999999999999999.0, 562949953421312.0, 123456789012345.0):
    for f in (0.125, 0.25, 0.5, 0.75, 0.875):
        if b + f != math.floor(b + f):
            vals.append(b + f)
vals += [2.0**52 - 0.5, 2.0**52, 2.0**52 + 1, 2.0**53 - 1, 2.0**53, 2.0**53 + 2]
# c: whole numbers of 16 to 40 digits
for e in range(15, 41):
    vals.append(10.0**e)
    vals.append(float(rnd.randint(10**e, 10 ** (e + 1) - 1)))
vals += [2.0**64, 2.0**70, 2.0**80, 2.0**100, 2.0**103, 2.0**106, 2.0**107, 99999999999999991611392.0, 1e100, 1e300, 1.7976931348623157e308]
vals += [-v for v in vals[:3]] + [-1e-7, -9.999999999999999e-06, -1000000000000001.5, -1e22, -1e25, -1e31, -1e32, -1.2345678901234e-6]

print("/* X13: BEST32. next to and below 1e-5, of non-whole values from 1e15, of whole numbers over 21 digits. */")
print('data _null_; input x :hex16.; put "X13 " x hex16. " [" x best32. "]"; datalines;')
for v in vals:
    print(hx(v))
print(";")
