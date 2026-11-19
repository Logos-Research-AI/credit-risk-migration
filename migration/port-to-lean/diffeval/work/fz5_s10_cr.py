import struct, math
from decimal import Decimal, getcontext
getcontext().prec = 60
def bits(x): return struct.unpack("<Q", struct.pack("<d", x))[0]
for neg, lean_e_guess in [(5.452245352868285, "-1ulp"), (0.6472422941797361, "-1ulp"), (1.4018746075979729, "+1ulp")]:
    e = Decimal(neg).exp()   # Decimal(float) is exact
    m = math.exp(neg)
    # neighbours as exact decimals
    cands = {k: struct.unpack("<d", struct.pack("<Q", bits(m) + k))[0] for k in (-1, 0, 1)}
    errs = {k: abs(Decimal(v) - e) for k, v in cands.items()}
    best = min(errs, key=errs.get)
    print(neg, "correctly rounded = math.exp %+d ulp" % best, "| lean's (inferred) =", lean_e_guess, "| errors in units of ulp:",
          {k: float(errs[k] / (Decimal(cands[1]) - Decimal(cands[0]))) for k in errs})
