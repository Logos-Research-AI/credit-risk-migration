import polars as pl, numpy as np
from decimal import Decimal, ROUND_HALF_UP, ROUND_HALF_EVEN
raw = pl.read_csv("../data/cs-training.csv", infer_schema=False).rename({"": "row_id"})
ref = pl.concat([pl.read_csv(f"reference/model_features_{s}.csv", infer_schema=False) for s in ("train","validation")])
d = ref.select("row_id","utilization_debt_interaction").join(raw.select("row_id","RevolvingUtilizationOfUnsecuredLines","DebtRatio"), on="row_id")
vals=[]
for _, refs, r, dd in d.iter_rows():
    if "E" in refs: continue
    u=float(r)*100; v=float(dd)*100; vals.append(((u*v)/100, refs))
def mk(src, mode):
    def f(x):
        if x == 0: return "0"
        ilen = len(str(int(abs(x)))) + (x < 0); dec = max(0, 11 - ilen)
        s = str(Decimal(src(x)).quantize(Decimal(1).scaleb(-dec), rounding=mode))
        if "." in s: s = s.rstrip("0").rstrip(".")
        return "0" if s in ("-0", "") else s
    return f
srcs = {"exact binary": lambda x: x, "repr (shortest)": repr, "15 sig": lambda x: f"{x:.15g}",
        "16 sig": lambda x: f"{x:.16g}", "17 sig": lambda x: f"{x:.17g}"}
for sn, src in srcs.items():
    for mn, mode in [("half-up", ROUND_HALF_UP), ("half-even", ROUND_HALF_EVEN)]:
        f = mk(src, mode); bad = sum(f(x) != t for x, t in vals)
        print(f"{sn:16s} {mn:9s} mismatches {bad} / {len(vals)}")
import math
def scaled(kind):
    def f(x):
        ilen = len(str(int(abs(x)))) + (x < 0); dec = max(0, 11 - ilen)
        if kind == "mul": y = x * 10.0**dec
        elif kind == "ld": y = float(np.longdouble(x) * np.longdouble(10)**dec)
        n = math.floor(abs(y) + 0.5) if kind != "ldr" else None
        s = str(n).rjust(dec + 1, "0"); s = (s[:-dec] + "." + s[-dec:]) if dec else s
        s = ("-" if x < 0 else "") + s
        if "." in s: s = s.rstrip("0").rstrip(".")
        return s
    return f
def ld_round(x):
    ilen = len(str(int(abs(x)))) + (x < 0); dec = max(0, 11 - ilen)
    y = np.longdouble(abs(x)) * np.longdouble(10)**dec
    n = int(np.floor(y + np.longdouble(0.5)))
    s = str(n).rjust(dec + 1, "0"); s = (s[:-dec] + "." + s[-dec:]) if dec else s
    s = ("-" if x < 0 else "") + s
    return s.rstrip("0").rstrip(".") if "." in s else s
print("longdouble", np.finfo(np.longdouble).nmant)
for name, f in [("double x*10^d, floor+0.5", scaled("mul")), ("longdouble x*10^d, floor+0.5", ld_round)]:
    bad = [(x, t, f(x)) for x, t in vals if f(x) != t]
    print(f"{name:30s} mismatches {len(bad)}", bad[:3])
f15 = mk(lambda x: f"{x:.15g}", ROUND_HALF_UP)
bad = [(repr(x), f"{x:.17g}", t, f15(x)) for x, t in vals if f15(x) != t]
for b in bad[:12]: print(b)
print("---- fuzz fit")
ups, downs = [], []
for x, t in vals:
    ilen = len(str(int(abs(x)))) + (x < 0); dec = max(0, 11 - ilen)
    y = Decimal(x) * (Decimal(10) ** dec); fl = int(y); frac = y - fl
    if not (Decimal("0.49") < frac < Decimal("0.51")): continue
    n_up = str(fl + 1); s = n_up.rjust(dec + 1, "0"); s = (s[:-dec] + "." + s[-dec:]) if dec else s
    s = s.rstrip("0").rstrip(".") if "." in s else s
    (ups if s == t else downs).append(float(Decimal("0.5") - frac))  # distance below half (negative = above)
print("rounded UP: max distance below half", max(ups), " | rounded DOWN: min distance below half", min(d for d in downs))
print("n up", len(ups), "n down", len(downs))
print("---- relative fuzz fit")
U, Dn = [], []
for x, t in vals:
    ilen = len(str(int(abs(x)))) + (x < 0); dec = max(0, 11 - ilen)
    y = Decimal(x) * (Decimal(10) ** dec); fl = int(y); frac = y - fl
    if not (Decimal("0.4") < frac < Decimal("0.6")): continue
    n_up = str(fl + 1); s = n_up.rjust(dec + 1, "0"); s = (s[:-dec] + "." + s[-dec:]) if dec else s
    s = s.rstrip("0").rstrip(".") if "." in s else s
    rel = float((Decimal("0.5") - frac) / y)   # distance below half, relative to the scaled value
    (U if s == t else Dn).append(rel)
print("UP max rel", max(U), "DOWN min rel (below half)", min(r for r in Dn if r > 0), "DOWN with r<=0:", sum(r <= 0 for r in Dn))
