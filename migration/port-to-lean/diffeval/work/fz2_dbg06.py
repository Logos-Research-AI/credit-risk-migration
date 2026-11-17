"""Triage of fz2_s06: per-seed digests of the failing blocks (debug only)."""
import sys
from pathlib import Path
sys.path.insert(0, "diffeval/units"); sys.path.insert(0, "diffeval")
src = Path("diffeval/units/fz2_s567_gen.py").read_text()
assert src.rstrip().endswith("main()")
g = {"__file__": str(Path("diffeval/units/fz2_s567_gen.py").resolve()), "__name__": "g"}
exec(compile(src.rstrip()[:-len("main()")], "fz2_s567_gen.py", "exec"), g)
g["suite_mod"].CARRIERS["identity"] = ("def:zz_carrier_t", "zz_carrier_t")
g["blocks"](g["d06"], 300000, 68)
BASES = [int(a) for a in sys.argv[1:]] or [300000, 301200, 301500, 303350, 300400]
st = g["Suite"]("fz2_dbg06")
cases = []
for b in BASES:
    for i in range(50):
        cls, d = g["d06"](b + i)
        cases.append((f"seed {b+i} {cls}", g["U6"], d if cls in ("kept", "rejected") else 0, {"fz": cls, "covers": 1}))
body = "(" + " ++ ".join(f"(List.range 50).map (fun (i : Nat) => dg (U6 ({b} + i)))" for b in BASES) + ")"
st.ints(g["FMT"] + g["lean_pow2"]() + g["L06"], body, cases, gen=True, table=True)
st.write()
import json
x = json.loads((g["suite_mod"].WORK / "fz2_dbg06.inputs.json").read_text())[0]["inputs"]
ref = json.loads((g["suite_mod"].WORK / "fz2_s06.inputs.json").read_text())[0]["inputs"][0]
k = ref.index("let ch :=")
assert x[0].startswith(ref[:k]), "prefix differs"
print(len(x), len(x[0])); print(x[0][k:])
