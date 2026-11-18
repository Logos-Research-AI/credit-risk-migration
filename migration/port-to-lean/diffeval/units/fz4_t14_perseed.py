"""Per-seed view of fz4_t14: Lean returns the digest of each seed (window), Python's expected digest per seed."""
import sys, json
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import fz4_t14_gen as g
fz, td = g.fz, g.td
a, n = int(sys.argv[1]), int(sys.argv[2])
base = g.LETS
t0 = (HERE.parent / "work" / "fz4_t14.in0.txt").read_text()
i = t0.index("(let X : List Nat")
lean = t0[:i] + f"(List.range' {a} {n}).map (fun (s : Nat) => (ONE s).2))"
exp = []
for s in range(a, a + n):
    e = g.env14(s)
    try:
        _, w, _ = td.run_slice("s14", e)
        exp.append(fz.out_digest(w))
    except Exception as ex:
        exp.append(f"RAISES {type(ex).__name__}")
W = HERE.parent / "work"
(W / "fz4_t14_ps.in.txt").write_text(lean)
(W / "fz4_t14_ps.exp.json").write_text(json.dumps({"a": a, "n": n, "exp": exp, "cls": [int(g.rp.pre(g.env14(s))) for s in range(a, a + n)]}))
print(len(lean))
