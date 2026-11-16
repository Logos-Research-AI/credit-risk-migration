"""E17 (2026-11-16): R7, a count that passes through 8-character text in metrics_calculation.

  PYTHONPATH=../../port uv run --project ../../port python experiments/e17_counts_best8.py > experiments/e17_counts_best8.out.txt

metrics_calculation._into_float(x) = float(sas_best(x, 8)) (None when the text is empty) is applied to
total_good_count, total_bad_count (:165-166), total_defaults and overall_default_rate (:294-295).
"""
import random
from credit_risk import metrics_calculation as mc, sas_compat as sc

print("== the four named counts and their neighbours: x, sas_best(x, 8), _into_float(x), equal to x?")
for x in [0, 1, 150000, 9999999, 10000000, 12345678, 99999994, 99999995, 99999998, 99999999, 100000000, 100000001, 100004999, 100005000, 100005001,
          100015000, 100050000, 123449999, 123450000, 123455000, 123456789, 199999999, 999949999, 999950000, 999999999, 1000000000, 1234567890,
          9999999999, 12345678901, 99999999999, 100000000000, 123456789012, 10**15, 10**20]:
    t = sc.sas_best(float(x), 8)
    v = mc._into_float(float(x))
    print(f"   {x:>22} -> text {t!r:12} ({len(t)} chars) -> {v!r:24} {'equal' if v == x else 'CHANGED by ' + repr(v - x)}")
print("   None ->", repr(sc.sas_best(None, 8)), "->", mc._into_float(None))

print("\n== integer counts below 10^8 (8 digits or fewer): every one from 0 to 2,000,000, and 2,000,000 random below 10^8")
bad = [x for x in range(2_000_001) if mc._into_float(float(x)) != x]
rng = random.Random(7)
bad += [x for x in (rng.randrange(10**8) for _ in range(2_000_000)) if mc._into_float(float(x)) != x]
print("   changed:", len(bad), bad[:5])

print("\n== counts from 10^8: which are unchanged (2,000,000 random in [10^8, 10^10))")
same = [x for x in (rng.randrange(10**8, 10**10) for _ in range(2_000_000)) if mc._into_float(float(x)) == x]
print("   unchanged:", len(same), "e.g.", same[:8])
print("   rule check: text is d.ddddEn (5 significant digits)")
for x in [100004999, 100005000, 100015000, 100025000, 100035000, 123445000, 123455000, 123465000, 999994999, 999995000, 1000050000, 1000150000, 99999500000, 99999499999]:
    print(f"   {x:>14} -> {sc.sas_best(float(x), 8)!r:12} -> {mc._into_float(float(x))!r}")
ok = 0
tot = 0
for _ in range(1_000_000):
    x = rng.randrange(10**8, 10**11)
    e = len(str(x)) - 1
    q = 10 ** (e - (6 - len(str(e))) + 1)   # 5 significant digits while the exponent has one digit, 4 from 10^10
    m = (x + q // 2) // q          # round half up (x is a positive integer)
    tot += 1
    ok += mc._into_float(float(x)) == float(m * q)
print(f"   _into_float(x) == x rounded half up to 5 significant digits (4 from 10^10): {ok} of {tot} random integers in [10^8, 10^11)")
print("\n== a rate (overall_default_rate) through the same text: x, text, value read")
for x in [0.06684, 0.066840000000001, 1 / 3, 2 / 3, 0.5, 0.05, 0.000123456, 1e-5, 9.9999e-6, 1.0, 0.99999999, 0.999999996, 6.684]:
    print(f"   {x!r:22} -> {sc.sas_best(x, 8)!r:12} -> {mc._into_float(x)!r}")
