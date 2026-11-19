import math, struct, sys
import numpy as np
sys.path.insert(0, "diffeval/units")
import fz5_s10_gen as g
from fractions import Fraction
def bits(x): return struct.unpack("<Q", struct.pack("<d", x))[0]
def flt(b): return struct.unpack("<d", struct.pack("<Q", b))[0]
try:
    import mpmath
    mpmath.mp.prec = 200
except Exception: mpmath=None
cases = [(1997, 3, "pred_logistic", 4571571119672794081), (2018, 37, "c4", 4599861569886682854), (1313, 19, "pred_logistic", 4596284385332449513)]
for sd, row, cn, leanbits in cases:
    c = g.build(sd)
    x = [v for n, d, v in c["cols"] if n == cn][0][row]
    b = dict(c["coefs"])[cn]; ic = c["icpt"]
    eta = ic + b * x          # IEEE, as polars (scalar zero rule irrelevant: ic != 0 / -0.0)
    if ic == 0.0: eta = b * x
    neg = -eta
    e_math = math.exp(neg); e_np = float(np.exp(np.float64(neg)))
    e_mp = float(mpmath.exp(mpmath.mpf(neg))) if mpmath else None
    def pd(e): return 1.0 / (1.0 + e)
    print("seed", sd, "row", row, "eta", repr(eta), "-eta", repr(neg))
    print("  exp math", repr(e_math), hex(bits(e_math)), "np", hex(bits(e_np)), "mp", None if e_mp is None else hex(bits(e_mp)))
    for lab, e in [("math", e_math), ("-1ulp", flt(bits(e_math) - 1)), ("+1ulp", flt(bits(e_math) + 1))]:
        print("   pd with exp", lab, hex(bits(e)), "->", bits(pd(e)), "(lean pd bits", leanbits, ")", "MATCHES LEAN" if bits(pd(e)) == leanbits else "")
