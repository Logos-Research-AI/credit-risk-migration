"""Run of the six pow2-suspect seeds with a pow2 table (arguments where Python's x ** 2 != x * x) on the Lean side."""
import sys, json, math
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parent))
import fz5_s06_gen as g
seeds = [int(a) for a in sys.argv[1:]]
rec = []
allrec = []
src = g.CODE.replace("(b / se) ** 2", "(lambda t: (rec.append(t), t ** 2)[1])(b / se)")
NS = {"rec": rec}; exec(src, NS)
import numpy as np
from credit_risk import sas_compat as sc
exp = {}
for s in seeds:
    c = g.case(s)
    r, e = g.py_run(c)  # real; just for digest
    exp[s] = g.cmp.digest(g.toks(r))
    # collect arguments with the table version
    if c["rankbad"] and not c["rb2"]:
        cov = np.array([rr[i] if i < len(rr) else 0.0 for i, rr in enumerate(c["rows"])], dtype=np.float64)
    else:
        cov = np.array(c["rows"], dtype=np.float64).reshape(len(c["rows"]), c["mn"])
    beta = np.array([c["betaL"]], dtype=np.float64) if c["rankbad"] and c["rb2"] else np.array(c["betaL"], dtype=np.float64)
    fit = sc.LogisticFit(names=[], beta=beta, cov=cov, loglik=0.0, n_iter=0, converged=True)
    with np.errstate(all="ignore"):
        rec.clear(); NS["_blk"](fit if c["hasfit"] else None, list(c["effects"]), list(c["fidx"]), c["icpt"], list(c["lo"]), g.FAKE, math, g.pl, Path("out")); allrec.extend(rec)
tab = {}
for t in allrec:
    if g.fb(t ** 2) != g.fb(t * t):
        tab[g.fb(t)] = g.fb(t ** 2)
print("table", tab)
p2 = "let p2 := fun (x : Float) => " + "".join(f"if x.toBits == {k} then Float.ofBits {v} else " for k, v in tab.items()) + "x * x; "
assert "let p2 := fun (x : Float) => x * x; " in g.LEAN
lean = g.LEAN.replace("let p2 := fun (x : Float) => x * x; ", p2)
term = "(" + g.kit.KIT + lean + "([" + ", ".join(map(str, seeds)) + "]).map (fun (s : Nat) => dg (one s)) : List Int)"
W = HERE.parent / "work"
(W / "fz7_s06.pow2.term.txt").write_text(term)
(W / "fz7_s06.pow2.expect.json").write_text(json.dumps(exp))
print(exp)
i = term.index("let p2"); print(term[i:i+400]); print(term[term.index("([" + str(seeds[0])):])
