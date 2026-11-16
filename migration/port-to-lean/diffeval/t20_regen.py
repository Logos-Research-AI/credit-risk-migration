"""T20: are the suites of the update reproducible from the final port?

For each generator of the update (diffeval/units/t*_gen.py, rv_*_gen.py): keep the hashes of the suite files it wrote (work/<suite>.json: expected values and the
lookup tables of sas_best / sas_best12 / input_best32 baked into the Lean inputs;
work/<suite>.inputs.json: the Lean inputs), run it again on the port as it now stands, and compare
the hashes. Then compare.py on every suite that has a recorded Lean output.

  cd migration/port-to-lean && PYTHONPATH=../../port uv run --project ../../port python diffeval/t20_regen.py [gen ...]
"""

from __future__ import annotations

import hashlib
import os
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
WORK = HERE / "work"
SKIP: set[str] = set()


def hashes() -> dict[str, str]:
    out = {}
    for p in sorted(WORK.glob("*.json")):
        if p.name.endswith(".result.json") or ".prev." in p.name:
            continue
        out[p.name] = hashlib.sha256(p.read_bytes()).hexdigest()
    return out


def main() -> int:
    want = set(sys.argv[1:])
    gens = [
        p
        for p in sorted((HERE / "units").glob("*_gen.py"))
        if (p.name.startswith("t") or p.name.startswith("rv_")) and p.name not in SKIP
    ]
    if want:
        gens = [p for p in gens if p.name in want]
    port = max(os.path.getmtime(p) for p in (HERE.parent.parent.parent / "port" / "credit_risk").glob("*.py"))
    print("port last changed", time.strftime("%H:%M:%S", time.localtime(port)))
    bad = 0
    for g in gens:
        before = hashes()
        t0 = time.time()
        r = subprocess.run([sys.executable, str(g)], cwd=HERE.parent, capture_output=True, text=True)
        after = hashes()
        changed = sorted(k for k in after if before.get(k) != after[k])
        touched = sorted(
            p.name for p in WORK.glob("*.json") if p.stat().st_mtime >= t0 and not p.name.endswith(".result.json")
        )
        status = "SAME" if r.returncode == 0 and not changed else "DIFFERENT" if r.returncode == 0 else "FAILED"
        bad += status != "SAME"
        print(f"{g.name}\t{status}\t{time.time() - t0:.0f}s\twrote {touched}\tchanged {changed}")
        if r.returncode != 0:
            print("    " + "\n    ".join((r.stderr or r.stdout).strip().splitlines()[-6:]))
    print("--- compare.py on the recorded Lean outputs")
    for j in sorted(WORK.glob("*.json")):
        if ".inputs." in j.name or ".result." in j.name or ".prev." in j.name:
            continue
        o = j.with_suffix(".out.txt")
        if not o.exists():
            print(f"{j.stem}\tno recorded Lean output")
            continue
        r = subprocess.run(
            [sys.executable, str(HERE / "compare.py"), str(j), str(o)], cwd=HERE.parent, capture_output=True, text=True
        )
        last = (r.stdout.strip().splitlines() or [r.stderr.strip()[-200:]])[-1]
        print(f"{j.stem}\texit {r.returncode}\t{last}")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
