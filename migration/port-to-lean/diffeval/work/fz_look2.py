import json, sys
sys.path.insert(0, "diffeval/units"); sys.path.insert(0, "diffeval")
import io, contextlib
with contextlib.redirect_stdout(io.StringIO()):
    import fz_t8_gen as fz
import polars as pl
res = json.load(open("diffeval/work/fz_p04.result.json")); cs = json.load(open("diffeval/work/fz_p04.json"))["cases"]
def other(s):
    l, r = fz.gen04(s)
    l2 = l.with_columns(pl.col("age_group").cast(pl.Int64, strict=False))
    return fz.pre04((l2, r))
for c, r in zip(cs, res):
    if c.get("clause") == "left age_group not integer":
        o = [other(s) for s in c["seeds"]]
        pure = all(x is None for x in o)
        if r["status"] != "PASS" or not pure:
            print(r["status"], c["seeds"], [x for x in o if x])
for cl in ("MonthlyIncome_missing not integer",):
    print(cl, [ (r["status"]) for c, r in zip(cs, res) if c.get("clause") == cl].count("PASS"), "groups pass of", sum(1 for c in cs if c.get("clause") == cl))
