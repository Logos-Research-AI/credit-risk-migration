"""Compare the Lean outputs of def:_hl_groups after the 2026-11-18 correction with sas_compat._hl_groups,
on the inputs of the fz5 fuzz: random cases 0..599 of fz5_hl_groups.cases.json (the 600 evaluated by the
fuzzer; files fix.out0a 0-100, fix.out0b 101-249, fix.out1a 250-424 on revision c170d460; fix.out2a 425-514,
fix.out2b 515-599 + seed 700394 + the fuzzer's three named cases on revision af2ffda1), and the 150 targeted
cases (fix.tout, revision c170d460). Revisions differ only for a non-finite α value (an int beyond the float
range); among these inputs only seed 700394 has one, and it is evaluated on af2ffda1.

  cd migration/port-to-lean && PYTHONPATH=../../port uv run --project ../../port python diffeval/units/fz5_hl_fix_compare.py
"""
import json
from pathlib import Path
from credit_risk import sas_compat as sc
W = Path(__file__).resolve().parent.parent / "work"
rd = lambda f: (W / f"fz5_hl_groups.{f}.txt").read_text().splitlines()
A = json.loads((W / "fz5_hl_groups.cases.json").read_text())
T = json.loads((W / "fz5_hl_groups.tcases.json").read_text())
assert all(sc._hl_groups(list(c["blocks"]), c["n"], c["g"]) == c["py"] for c in A[:600] + T)
lean = rd("fix.out0a") + rd("fix.out0b") + rd("fix.out1a") + rd("fix.out2a")
b = rd("fix.out2b")
lean += b[:85]
assert len(lean) == 600
rows = [(c["seed"], c["py"], json.loads(l)) for c, l in zip(A[:600], lean)]
s394 = [c for c in A if c["seed"] == 700394][0]
rows = [r if r[0] != 700394 else (700394, s394["py"], json.loads(b[85])) for r in rows]
d = [r for r in rows if r[1] != r[2]]
print("random 600: Lean != Python", len(d), d[:3])
named = [([1, 18014398509481985], 9007199254740992, 1), ([7, 5, 7, 10**20], 10**20 + 19, 2),
         ([1, 18014398509481985, 7, 1], 9007199254740993, 1)]
print("named 3: Lean != Python", sum(sc._hl_groups(*e) != json.loads(l) for e, l in zip(named, b[86:89])))
t = rd("fix.tout")
print("targeted", len(t), ": Lean != Python", sum(json.loads(l) != c["py"] for c, l in zip(T, t)))
old = [json.loads(x) for x in rd("out0") + rd("out1") + rd("out2")]
print("old Lean (fuzzer's out0-2) != Python on the 600:", sum(o != c["py"] for o, c in zip(old, A[:600])))
