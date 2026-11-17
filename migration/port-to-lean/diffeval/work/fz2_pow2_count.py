"""Count of floats where Python's x ** 2 differs from x * x (this machine), for RULEBOOK section 6."""
import struct, sys, math
sys.path.insert(0, "diffeval")
import kit
n = bad = big = 0
for s in range(1000):
    for x in kit.gF(s + 9000000, 1000, 0, 40, [None]):
        n += 1
        a, b = x ** 2, x * x
        if a != b:
            bad += 1
            ua, ub = struct.unpack("<q", struct.pack("<d", a))[0], struct.unpack("<q", struct.pack("<d", b))[0]
            big += abs(ua - ub) > 1
print(n, bad, big)
