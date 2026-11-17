import sys, json
from pathlib import Path
sys.path.insert(0, "diffeval/units"); sys.path.insert(0, "diffeval")
src = Path("diffeval/units/fz2_s567_gen.py").read_text()
g = {"__file__": str(Path("diffeval/units/fz2_s567_gen.py").resolve()), "__name__": "g"}
exec(compile(src.rstrip()[:-len("main()")], "fz2_s567_gen.py", "exec"), g)
cmp = g["cmp"]; sc = g["sc"]; np = g["np"]; NM = g["NM"]
out = {}
for s in [int(a) for a in sys.argv[1:]]:
    k, beta, cov, idxs, icpt = g["in06"](s)
    print(s, "k", k, "beta", [b.hex() for b in beta], "idxs", idxs, "icpt", icpt)
    for r in cov: print("   cov", r)
    fin = sc.LogisticFit(NM[:k], np.array(beta, dtype=np.float64), np.array(cov, dtype=np.float64).reshape(k, k), 0.0, 1, True)
    w, ns = g["run"](g["C06"], {"final": fin, "final_effects": [NM[i] for i in idxs], "final_index": idxs, "intercept": icpt})
    print(ns["model_coefficients"])
    for f in w: print(f)
    out[s] = cmp.tokens(cmp.canon_frame(ns["model_coefficients"])) + g["ftoks"](w)
Path("diffeval/work/fz2_dbg06b.tokens.json").write_text(json.dumps(out))
