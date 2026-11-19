import json, struct, sys
sys.path.insert(0, "diffeval/units")
import fz5_s10_gen as g
lean = json.load(open("diffeval/work/fz5_s10.pout.json"))
seeds = [1997, 2018, 1313]
def fl(b): return struct.unpack("<d", struct.pack("<Q", b))[0]
for sd, L in zip(seeds, lean):
    c = g.build(sd); res, df = g.run_py(c)
    P = [None if v is None else g.bits(v) for v in res.get_column("pd_logistic").to_list()]
    print("seed", sd, "rows", len(P), "lean rows", len(L), "icpt", c["icpt"], "coefs", c["coefs"])
    for i, (p, l) in enumerate(zip(P, L)):
        lb = None if l == -1 else l
        if p != lb:
            row = {n: v[i] for n, d, v in c["cols"] if n in dict(c["coefs"])}
            print("  row", i, "py", p, fl(p) if p is not None else None, "lean", lb, fl(lb) if lb is not None else None, "ulp", None if p is None or lb is None else lb - p, "x", row)
