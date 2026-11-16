"""Compare the outputs saved so far (work/t6_out/<input>.txt) with the suite; print differences."""
import json, sys
from pathlib import Path
W = Path(__file__).parent
s = json.load(open(W / "t6_run.json"))
bad = n = 0
for k in range(len(s["inputs"])):
    p = W / "t6_out" / f"{k}.txt"
    if not p.exists():
        print("input", k, "not run"); continue
    got = json.loads(p.read_text())
    cs = [c for c in s["cases"] if c["input"] == k]
    assert len(got) == len(cs), (k, len(got), len(cs))
    for c in cs:
        n += 1
        if got[c["pos"]] != c["expected"]:
            bad += 1; print("DIFF", c["id"], "expected", c["expected"], "got", got[c["pos"]], c.get("note", ""))
print(n, "cases compared,", bad, "differences")
