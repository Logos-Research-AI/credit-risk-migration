"""E12 (2026-11-16): R1 and R2, the port's own functions on the values a valid file can hold.

  PYTHONPATH=../../port uv run --project ../../port python experiments/e12_best32_best12.py > experiments/e12_best32_best12.out.txt

R1  sas_compat.input_best32 (on a String column) against Python float(text), which is the nearest
    double to the decimal written (correctly rounded, ties to even): bit for bit.
R2  x = float(text); y = input_best32(sas_best12(x)) as feature engineering step 01 / predict step 01
    do on a numeric column; is y == x bit for bit, for texts of at most 12 characters.
"""
from __future__ import annotations
import csv, random, struct
from pathlib import Path
import polars as pl
from credit_risk import sas_compat as sc

ROOT = Path(__file__).resolve().parents[3]
bits = lambda x: struct.unpack("<Q", struct.pack("<d", x))[0]  # noqa: E731
rng = random.Random(20261116)


def ib32(texts):
    return pl.DataFrame({"t": texts}, schema={"t": pl.String}).select(sc.input_best32(pl.col("t"))).to_series().to_list()


def check_r1(label, texts):
    texts = list(dict.fromkeys(texts))
    got = ib32(texts)
    bad = [(t, g) for t, g in zip(texts, got, strict=True) if g is None or bits(g) != bits(float(t))]
    print(f"R1 {label}: {len(texts)} distinct texts, not the nearest double (or read as missing): {len(bad)}" + (f"; e.g. {bad[:4]}" if bad else ""))
    return bad


def digits(n, first_nonzero=True):
    s = "".join(rng.choice("0123456789") for _ in range(n))
    return (rng.choice("123456789") + s[1:]) if first_nonzero and n else s


print("== R1: input_best32 against float(text)")
# every numeric field of the real files
real = set()
for fn in ("cs-training.csv", "cs-test.csv"):
    with (ROOT / "legacy/data" / fn).open() as fh:
        r = csv.reader(fh)
        next(r)
        for row in r:
            real.update(v for v in row if v not in ("", "NA"))
check_r1("every stated field of legacy/data (both files)", sorted(real))
check_r1("integers of 1 to 32 digits (2000 of each length)", [digits(n) for n in range(1, 33) for _ in range(2000)])
check_r1("decimals of 3 to 32 characters, point at every position (300 of each)",
         [(lambda s, p: s[:p] + "." + s[p:])(digits(n - 1), p) for n in range(3, 33) for p in range(1, n - 1) for _ in range(300)])
check_r1("0.ddd forms, 3 to 32 characters (2000 of each length)", ["0." + digits(n - 2, False) for n in range(3, 33) for _ in range(2000)])
check_r1("leading zeros in the integer part ('007', '00.5')", ["007", "00.5", "000", "0000000000000000000000000000001", "0.0", "00", "0"])
check_r1("at most 12 characters: integers, every length (20000 each)", [digits(n) for n in range(1, 13) for _ in range(20000)])
check_r1("at most 12 characters: decimals, every length and point position (5000 each)",
         [(lambda s, p: s[:p] + "." + s[p:])(digits(n - 1), p) for n in range(3, 13) for p in range(1, n - 1) for _ in range(5000)])
hard = ["9007199254740993", "9007199254740992.5", "0.1", "0.30000000000000004", "2.2250738585072014e-308", "4.9e-324", "1.7976931348623157e308",
        "8.41e21", "5e-324", "0.5000000000000001", "1.00000000000000011102230246251565", "9.5e-322", "123456789012345678901234567890.5",
        "0.00000000000000000000000000001", "99999999999999999999999999999999", "1.5e300", "4.5e1", "1E3", "1e+3", "1E-3", "+7", "-7", "-0", "+0.0",
        "5.", ".5", "-.5", "+.5", "1.e2", " 12", "12 ", "  12.5  "]
bad = check_r1("hard cases: ties, 17+ digits, exponents, signs, '5.', '.5', blanks around", hard)
print("   values:", [(t, v) for t, v in zip(hard[-12:], ib32(hard[-12:]), strict=True)])
print("-- texts read as missing (null) or not as their number")
odd = ["", " ", ".", "NA", "na", "N/A", "abc", "12abc", "1,000", "1 000", "1e", "e5", "+", "-", "--1", "1.2.3", "0x10", "1_000", "inf", "Infinity", "nan", "NaN",
       "1e400", "-1e400", "1e-400", "1d3", "$5", "5%", "\t5", "5\t", " 5", "１", "1" * 32, "1" * 33, "1" * 40, "9" * 33 + ".5", "0." + "1" * 31, " " + "1" * 32,
       "1" * 31 + "e5", "1" * 30 + "e55"]
for t, v in zip(odd, ib32(odd), strict=True):
    try:
        f = float(t)
    except ValueError:
        f = "not a number for Python"
    print(f"   {t!r:46} -> {v!r:28} (float(text): {f!r})")
print("   null input ->", ib32([None]))

print("\n== R2: input_best32(sas_best12(float(text))) == float(text), texts of at most 12 characters")


def check_r2(label, texts, show=6):
    texts = list(dict.fromkeys(texts))
    xs = [float(t) for t in texts]
    b12 = [sc.sas_best12(x) for x in xs]
    ys = ib32(b12)
    bad = [(t, b, y) for t, x, b, y in zip(texts, xs, b12, ys, strict=True) if y is None or bits(y) != bits(x)]
    print(f"R2 {label}: {len(texts)} texts, changed: {len(bad)}" + (f"; e.g. (text, BEST12 text, value read) {bad[:show]}" if bad else ""))
    return bad


inc = set()
with (ROOT / "legacy/data/cs-training.csv").open() as fh:
    r = csv.reader(fh); next(r)
    for row in r:
        inc.update(v for v in (row[6], row[11]) if v not in ("", "NA"))
check_r2("every MonthlyIncome / NumberOfDependents text of legacy/data training", sorted(inc))
check_r2("all integers 0..200000", [str(i) for i in range(200001)])
for n in range(6, 13):
    check_r2(f"integers of {n} digits (100000 random + ends)", [digits(n) for _ in range(100000)] + ["1" + "0" * (n - 1), "9" * n])
for n in range(3, 13):
    for p in range(1, n - 1):
        check_r2(f"{n} characters, {n - 1} digits, point after {p} digits, first digit not 0 (20000)",
                 [(lambda s: s[:p] + "." + s[p:])(digits(n - 1)) for _ in range(20000)], show=3)
for n in range(3, 13):
    check_r2(f"'0.' + {n - 2} digits ({n} characters) (30000)", ["0." + digits(n - 2, False) for _ in range(30000)], show=3)
for n in range(2, 13):
    check_r2(f"'.' + {n - 1} digits ({n} characters, no leading 0) (30000)", ["." + digits(n - 1, False) for _ in range(30000)], show=3)
check_r2("very small plain: '0.' + zeros + digits, 12 characters, every count of zeros",
         ["0." + "0" * z + digits(10 - z) for z in range(0, 10) for _ in range(5000)], show=3)
check_r2("smallest plain forms", ["0.0000000001", ".00000000001", "0.0000000009", "0.00001", "0.000009", "0.0000099999", "0.00001", "0.000010001"])
check_r2("zero forms", ["0", "0.0", "0.00000000", "000000000000", ".0", "0.", "00.0"])
check_r2("trailing zeros and leading zeros", ["5000.000000", "000000005000", "0005000.5000", "1.0", "10.00", "100.", "12345.67000"])
for n in (5, 8, 10, 12):
    check_r2(f"E-notation texts of {n} characters (20000)",
             [(lambda m, e: (m[0] + ("." + m[1:] if len(m) > 1 else "") + e))(digits(n - len(e) - (1 if n - len(e) > 1 else 0)), e)
              for _ in range(20000) for e in [rng.choice(["E-5", "E-9", "e-12", "E-30", "E5", "E9", "e11", "E20", "E-300", "E300"])] if n - len(e) - 1 >= 1], show=3)
check_r2("hard: 11 and 12 significant digits around powers of ten",
         ["99999999999", "999999999999", "100000000000", "99999999999.", "9999999999.9", "999999.99999", "9.9999999999", "0.9999999999", ".99999999999",
          "0.0999999999", "1.0000000001", "123456789012", "12345678901.", "1234567890.1", "0.1234567891", ".12345678901", ".01234567891"])
