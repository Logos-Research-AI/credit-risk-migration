"""Per-seed term for the seeds of the chunks (1-based) given on the command line; expected digests to work/fz7_s06.detail.expect.json"""
import sys, json
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parent))
import fz5_s06_gen as g
kit, cmp = g.kit, g.cmp
chunks = [int(a) for a in sys.argv[1:]]
d = json.loads((HERE.parent / "work" / "fz5_s06.json").read_text())
kept = set(d["kept"]); K = d["K"]
seeds = [s for c in chunks for s in range((c - 1) * K, c * K) if s in kept]
exp = {s: d["digests"][str(s)] for s in seeds}
term = "(" + kit.KIT + g.LEAN + "([" + ", ".join(map(str, seeds)) + "]).map (fun (s : Nat) => dg (one s)) : List Int)"
(HERE.parent / "work" / "fz7_s06.detail.term.txt").write_text(term)
(HERE.parent / "work" / "fz7_s06.detail.expect.json").write_text(json.dumps({"seeds": seeds, "exp": exp}))
print(len(seeds), len(term))
