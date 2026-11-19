"""Record the arguments of math.exp that step 06 passes for the given seeds; write work/fz7_s06.expargs.json and the Lean term."""
import sys, json, math, types
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parent))
import fz5_s06_gen as g
seeds = [int(a) for a in sys.argv[1:]]
args = {}
rec = []
class M:
    def __getattr__(self, k): return getattr(math, k)
    @staticmethod
    def exp(x):
        rec.append(x); return math.exp(x)
g_math = g.math
res = {}
for s in seeds:
    rec.clear()
    c = g.case(s)
    # run with the recording math
    import numpy as np
    from credit_risk import sas_compat as sc
    if c["rankbad"] and not c["rb2"]:
        cov = np.array([r[i] if i < len(r) else 0.0 for i, r in enumerate(c["rows"])], dtype=np.float64)
    else:
        cov = np.array(c["rows"], dtype=np.float64).reshape(len(c["rows"]), c["mn"])
    beta = np.array([c["betaL"]], dtype=np.float64) if c["rankbad"] and c["rb2"] else np.array(c["betaL"], dtype=np.float64)
    fit = sc.LogisticFit(names=[], beta=beta, cov=cov, loglik=0.0, n_iter=0, converged=True)
    g.WROTE.clear()
    g.NS["_blk"](fit if c["hasfit"] else None, list(c["effects"]), list(c["fidx"]), c["icpt"], list(c["lo"]), g.FAKE, M(), g.pl, Path("out"))
    res[s] = [g.fb(x) for x in rec]
allbits = sorted({b for v in res.values() for b in v})
Path(HERE.parent / "work" / "fz7_s06.expargs.json").write_text(json.dumps({"per_seed": {str(k): v for k, v in res.items()}, "bits": allbits, "pyexp": {str(b): g.fb(math.exp(g.bf(b))) for b in allbits}}))
print(len(allbits))
print("[" + ", ".join(hex(b) for b in allbits) + "]")
