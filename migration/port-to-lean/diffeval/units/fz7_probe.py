"""Per-unit digests of chosen seeds of fz7_metrics_gen: writes work/fz7_probe.in.txt (the eval_decl input) and prints the expected digests.
  PYTHONPATH=../../port uv run --project ../../port python diffeval/units/fz7_probe.py 41036 41055 ..."""
import sys, json
from pathlib import Path
HERE = Path(__file__).resolve().parent
args = sys.argv[1:]
sys.argv = [sys.argv[0]]
sys.path.insert(0, str(HERE))
import fz7_metrics_gen as g
import kit
seeds = [int(x) for x in args]
best = {}
exp = {}
for s in seeds:
    res, sz = g.python_seed(s, best, None)
    exp[s] = [(st, dg) for st, dg in res]
lets = g.lean_lets(best)
text = kit.KIT + kit.GEN + lets + "((" + str(seeds) + ").map (fun (s : Nat) => one s))"
text = "(" + text + ")"
# flat output: list of lists of digests: print as List (List Int) => use flatMap
text = text.replace(".map (fun (s : Nat) => one s))", ".flatMap (fun (s : Nat) => one s))")
Path(HERE.parent / "work" / "fz7_probe.in.txt").write_text(text)
json.dump({str(s): exp[s] for s in seeds}, open(HERE.parent / "work" / "fz7_probe.exp.json", "w"))
for s in seeds:
    print(s, [d for _, d in exp[s]])
print(len(text))
