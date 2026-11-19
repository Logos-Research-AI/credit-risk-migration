import json, sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2] / "port")); sys.path.insert(0, str(HERE))
import fz5_minimize_lib as em
W = HERE.parent / "work"
cs = json.loads((W / "fz5_hl_groups.tcases.json").read_text())
ls = (W / "fz5_hl_groups.tout.txt").read_text().splitlines()
print(len(cs), len(ls))
diff = emu_wrong = 0
for c, l in zip(cs, ls):
    lean = json.loads(l)
    if lean != c["py"]:
        diff += 1
    if em.lean(c["blocks"], c["n"], c["g"]) != lean:
        emu_wrong += 1; print("emulator != Lean", c["input"])
print("targeted compared", len(cs), "Lean != Python", diff, "emulator != Lean", emu_wrong)
if "-v" in sys.argv:
    for c, l in zip(cs, ls):
        if json.loads(l) != c["py"]: print(c["input"][12:], "py", c["py"], "lean", json.loads(l))
