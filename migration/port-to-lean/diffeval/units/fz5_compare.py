"""compare transcribed Lean outputs (work/fz5_hl_groups.out<k>.txt, one list per line, in order of in<k>.json) with Python"""
import json, sys
from pathlib import Path
W = Path(__file__).resolve().parent.parent / "work"
cases = json.loads((W / "fz5_hl_groups.cases.json").read_text())
per = 200
bad = 0; tot = 0
for k in map(int, sys.argv[1:]):
    lines = (W / f"fz5_hl_groups.out{k}.txt").read_text().splitlines()
    ch = cases[k * per:(k + 1) * per]
    if len(lines) != len(ch): print("chunk", k, "lines", len(lines), "cases", len(ch))
    for c, l in zip(ch, lines):
        tot += 1
        if l.strip() == 'SKIPPED':
            print('skipped seed', c['seed']); continue
        lean = json.loads(l)
        if lean != c["py"]:
            bad += 1
            print("DIFF seed", c["seed"], c["input"][12:], "py", c["py"], "lean", lean)
print("compared", tot, "differences", bad)
