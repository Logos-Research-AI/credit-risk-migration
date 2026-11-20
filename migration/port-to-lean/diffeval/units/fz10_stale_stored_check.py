"""Fidelity pass 2026-11-20 (label stale-compositions): is the Python source STORED in def:run and
def:run_py_py (field `code`, as get_items returned it in this agent's own session record) out of date
against port/credit_risk at HEAD?

  cd migration/port-to-lean && python3 diffeval/units/fz10_stale_stored_check.py <session record .jsonl>

The stored text is taken by script from the get_items tool results (never typed), written to
diffeval/work/stored_fz10/<item>.py, and compared line by line with the function in the file at HEAD
(the `def run(` block of the file, to the end of the function). Prints a unified diff (stored -> HEAD)
and the verdict IDENTICAL / DIFFERS, plus where the stored text's first and last lines sit in HEAD.
"""
from __future__ import annotations

import difflib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
OUT = HERE.parent / "work" / "stored_fz10"
ITEMS = {"def:run": "port/credit_risk/feature_engineering.py", "def:run_py_py": "port/credit_risk/predict.py"}


def stored(record: Path) -> dict[str, str]:
    found: dict[str, str] = {}

    def walk(o):
        if isinstance(o, dict):
            if o.get("id") in ITEMS and isinstance(o.get("code"), str):
                found[o["id"]] = o["code"]
            for v in o.values():
                walk(v)
        elif isinstance(o, list):
            for v in o:
                walk(v)
        elif isinstance(o, str) and '"code"' in o and o.lstrip().startswith("{"):
            try:
                walk(json.loads(o))
            except json.JSONDecodeError:
                pass

    for line in record.open():
        if '\\"code\\"' in line:
            try:
                walk(json.loads(line))
            except json.JSONDecodeError:
                pass
    return found


def function_block(lines: list[str]) -> tuple[int, int]:
    """1-based first and last line of the top-level `def run(` in the file."""
    a = next(i for i, x in enumerate(lines) if x.startswith("def run("))
    b = a + 1
    while b < len(lines) and (lines[b] == "" or lines[b].startswith((" ", "\t", ")"))):
        b += 1
    while lines[b - 1].strip() == "":
        b -= 1
    return a + 1, b


def main() -> int:
    got = stored(Path(sys.argv[1]))
    OUT.mkdir(parents=True, exist_ok=True)
    rc = 0
    for item, f in ITEMS.items():
        if item not in got:
            print(f"{item}\tNOT-FETCHED")
            rc = 1
            continue
        text = got[item]
        (OUT / (item.replace("def:", "") + ".py")).write_text(text + "\n")
        flines = [x.rstrip() for x in (ROOT / f).read_text().split("\n")]
        a, b = function_block(flines)
        head = flines[a - 1 : b]
        st = [x.rstrip() for x in text.split("\n")]
        while st and st[-1] == "":
            st.pop()
        verdict = "IDENTICAL" if st == head else "DIFFERS"
        print(f"{item}\t{verdict}\tHEAD {f}:{a}-{b} ({b - a + 1} lines)\tstored {len(st)} lines")
        if verdict == "DIFFERS":
            rc = 1
            for d in difflib.unified_diff(st, head, "stored", f"HEAD {f}", lineterm="", n=1):
                # report hunk headers with absolute HEAD line numbers
                if d.startswith("@@"):
                    p = d.split()
                    o0 = int(p[1].split(",")[0][1:])
                    n0 = int(p[2].split(",")[0][1:])
                    d = f"{d}   (stored line {o0} ~ HEAD line {n0 + a - 1})"
                print("    " + d)
    return rc


if __name__ == "__main__":
    sys.exit(main())
