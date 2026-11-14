import math
def _gammaincc(a, x):
    if x <= 0: return 1.0
    if x < a + 1:
        s = t = 1.0 / a; ap = a
        for _ in range(10000):
            ap += 1; t *= x / ap; s += t
            if abs(t) < abs(s) * 1e-16: break
        return 1 - s * math.exp(-x + a * math.log(x) - math.lgamma(a))
    b = x + 1 - a; c = 1e300; dd = 1 / b; h = dd
    for i in range(1, 10000):
        an = -i * (i - a); b += 2
        dd = an * dd + b; dd = 1e-300 if abs(dd) < 1e-300 else dd
        c = b + an / c; c = 1e-300 if abs(c) < 1e-300 else c
        dd = 1 / dd; de = dd * c; h *= de
        if abs(de - 1) < 1e-16: break
    return math.exp(-x + a * math.log(x) - math.lgamma(a)) * h
class chi2:
    @staticmethod
    def sf(x, df): return _gammaincc(df / 2, x / 2)
class norm:
    @staticmethod
    def ppf(q):
        assert q == 0.975; return 1.959963984540054
