"""Token term for given seeds (flat, 999 after each seed), expected tokens to work/fz7_s06.tok.expect.json"""
import sys, json
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parent))
import fz5_s06_gen as g
seeds = [int(a) for a in sys.argv[1:]]
term = "(" + g.kit.KIT + g.LEAN + "tk ((([" + ", ".join(map(str, seeds)) + "]).flatMap (fun (s : Nat) => one s ++ [999])) : List UInt64) : List Int)"
exp = {s: g.toks(g.py_run(g.case(s))[0]) for s in seeds}
W = HERE.parent / "work"
(W / "fz7_s06.tok.term.txt").write_text(term)
(W / "fz7_s06.tok.expect.json").write_text(json.dumps({"seeds": seeds, "exp": {str(k): v for k, v in exp.items()}}))
print({s: len(v) for s, v in exp.items()})
