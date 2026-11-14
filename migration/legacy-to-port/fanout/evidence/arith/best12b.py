from decimal import Decimal, ROUND_HALF_UP
def best12_15(x: float, sig=15) -> str:
    if x == 0: return "0"
    d = Decimal(f"{x:.{sig-1}e}")
    ilen = len(str(int(abs(x)))) + (1 if x < 0 else 0)
    dec = max(0, 12 - 1 - ilen)
    s = str(d.quantize(Decimal(1).scaleb(-dec), rounding=ROUND_HALF_UP))
    if "." in s: s = s.rstrip("0").rstrip(".")
    return "0" if s == "-0" else s
