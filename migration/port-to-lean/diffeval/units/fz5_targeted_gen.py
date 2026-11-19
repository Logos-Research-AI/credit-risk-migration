"""validates the Float emulator (fz5_minimize.lean) against the transcribed Lean outputs of chunks 0-2, then builds a targeted set:
cases around the exactness boundary where Python (exact ints) and a Float evaluation can part: emulator-differs plus the
same shapes one unit either side. Writes work/fz5_hl_groups.tin.json (inputs) and work/fz5_hl_groups.tcases.json."""
import json, sys, itertools, random
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2] / "port")); sys.path.insert(0, str(HERE))
from credit_risk import sas_compat as sc
import fz5_minimize_lib as em
W = HERE.parent / "work"
cases = json.loads((W / "fz5_hl_groups.cases.json").read_text())
bad = 0
for k in range(3):
    lines = (W / f"fz5_hl_groups.out{k}.txt").read_text().splitlines()
    for c, l in zip(cases[k * 200:(k + 1) * 200], lines):
        if l.strip() == "SKIPPED": continue
        try: e = em.lean(c["blocks"], c["n"], c["g"])
        except OverflowError: continue
        if e != json.loads(l):
            bad += 1; print("emulator != Lean on seed", c["seed"])
print("emulator vs Lean on 600 transcribed:", bad, "mismatches")
random.seed(5)
P = [1, 2, 3, 7, 2**52, 2**52 + 1, 2**53 - 1, 2**53, 2**53 + 1, 2**53 + 2, 2**54, 2**54 + 1, 2**54 + 2, 2**54 + 3, 2**55 + 1, 2**56 + 7]
N = [0, 1, 2**52, 2**52 + 1, 2**53 - 1, 2**53, 2**53 + 1, 2**53 + 2, 2**54, 2**54 + 1, 2**54 + 3, 2**55 + 1, 2**56 + 7, 2**60 + 1]
out = []; seen = set()
tries = 0
while len(out) < 150 and tries < 200000:
    tries += 1
    L = random.choice([1, 2, 2, 3, 3, 4])
    bl = [random.choice(P) for _ in range(L)]
    n = random.choice(N + [sum(bl)] * 3); g = random.choice([1, 1, 2, 3, 10, 20])
    key = (tuple(bl), n, g)
    if key in seen: continue
    seen.add(key)
    try: py = sc._hl_groups(list(bl), n, g)
    except Exception: continue
    differs = em.lean(bl, n, g) != py
    # keep all emulator-differs (up to 60) and the rest as agreeing controls
    if differs and sum(1 for o in out if o["emu_differs"]) < 60 or (not differs and sum(1 for o in out if not o["emu_differs"]) < 90):
        out.append({"blocks": bl, "n": n, "g": g, "py": py, "emu_differs": differs,
                    "input": "(α := Float) [" + ",".join(str(b) for b in bl) + "] " + str(n) + " " + str(g)})
(W / "fz5_hl_groups.tcases.json").write_text(json.dumps(out))
(W / "fz5_hl_groups.tin.json").write_text(json.dumps([o["input"] for o in out], ensure_ascii=False))
print(len(out), sum(o["emu_differs"] for o in out), sum(len(o["input"]) for o in out))
