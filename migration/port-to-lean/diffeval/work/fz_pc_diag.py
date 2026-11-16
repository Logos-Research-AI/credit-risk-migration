import json, sys
from pathlib import Path
sys.path.insert(0, "diffeval"); sys.path.insert(0, "diffeval/units")
import kit, compare as cmp
import fz_predict_check_gen as g
import polars as pl
s = json.load(open("diffeval/work/fz_predict_check.json"))
out = cmp.parse_lean(open("diffeval/work/fz_predict_check.out.txt").readline())
fails = [(c["id"], c.get("fz")) for c, o in zip(s["cases"][:600], out) if c["expected"] != o]
print(len(fails), "fail of 600;", sum(1 for _, f in fails if f == "kept"), "kept")
from collections import Counter
cv = Counter(); feats = Counter()
for cid, fz in fails:
    seed = int(cid.split("seed ")[1].split()[0]); v = kit.hsh(seed, 999) % 18
    cv[(v, fz)] += 1
    fr = g.mk(seed)
    if fr is not None:
        nanc = [c for c in fr.columns if fr.schema[c] == pl.Float64 and fr.get_column(c).is_nan().any()]
        infc = [c for c in fr.columns if fr.schema[c] == pl.Float64 and fr.get_column(c).is_infinite().any()]
        feats[("nan" if nanc else "") + ("inf" if infc else "") + f" rows{min(fr.height,2)}"] += 1
print(cv); print(feats)
# pass stats by same features
allf = Counter()
for c, o in zip(s["cases"][:600], out):
    seed = int(c["id"].split("seed ")[1].split()[0]); fr = g.mk(seed)
    if fr is not None and c["expected"] == o:
        nanc = any(fr.schema[x] == pl.Float64 and fr.get_column(x).is_nan().any() for x in fr.columns)
        infc = any(fr.schema[x] == pl.Float64 and fr.get_column(x).is_infinite().any() for x in fr.columns)
        allf[("nan" if nanc else "") + ("inf" if infc else "") + f" rows{min(fr.height,2)}"] += 1
print("passing:", allf)
