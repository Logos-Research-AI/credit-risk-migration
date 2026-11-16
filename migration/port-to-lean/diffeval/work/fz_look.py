import json, sys, math
sys.path.insert(0, "diffeval/units"); sys.path.insert(0, "diffeval")
import io, contextlib
with contextlib.redirect_stdout(io.StringIO()):
    import fz_t8_gen as fz
import polars as pl
res = json.load(open("diffeval/work/fz_p04.result.json")); cs = json.load(open("diffeval/work/fz_p04.json"))["cases"]
for c, r in zip(cs, res):
    if c.get("clause") == "left age_group not integer":
        feats = []
        for s in c["seeds"]:
            l, rr = fz.gen04(s)
            k = l["age_group"].to_list(); rk = rr["age_group"].to_list()
            f = ("nanL" if any(x is not None and x != x for x in k) else "") + ("+nanR" if any(x is not None and x != x for x in rk) else "") + (" n=%d" % l.height)
            feats.append(f)
        print(r["status"], c["seeds"], feats)
# p02: emulate the ASCII-only rename and see which non-ASCII seeds it explains
def ascii_up(s): return "".join(ch.upper() if "a" <= ch <= "z" else ch for ch in s)
def ascii_lo(s): return "".join(ch.lower() if "A" <= ch <= "Z" else ch for ch in s)
def lean02(cols):
    up = [ascii_up(n) for n in cols]; out = []
    for i, n in enumerate(cols):
        if ascii_up(n) in ("AGE_GROUP", "MEDIAN_INCOME", "OVERALL_MEDIAN_INCOME") and ascii_up(n) not in up[:i] and (ascii_lo(n) == n or ascii_lo(n) not in cols):
            out.append(ascii_lo(n))
        else: out.append(n)
    return out
res = json.load(open("diffeval/work/fz_p02.result.json")); cs = json.load(open("diffeval/work/fz_p02.json"))["cases"]
ok = bad = 0; ex = None
for c, r in zip(cs, res):
    if c.get("clause") == "non-ASCII name":
        same = all(lean02(fz.gen02(s).columns) == fz.e8.step02(fz.gen02(s)).columns for s in c["seeds"])
        if same == (r["status"] == "PASS"): ok += 1
        else: bad += 1
        if not same and ex is None:
            s = next(s for s in c["seeds"] if lean02(fz.gen02(s).columns) != fz.e8.step02(fz.gen02(s)).columns)
            ex = (s, fz.gen02(s).columns, fz.e8.step02(fz.gen02(s)).columns, lean02(fz.gen02(s).columns))
print("p02 non-ASCII groups explained by the ASCII-only case mapping:", ok, "not explained:", bad, "example:", ex)
