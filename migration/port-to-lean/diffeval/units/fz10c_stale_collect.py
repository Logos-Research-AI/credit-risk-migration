"""Fidelity pass 2026-11-20, third attempt (label stale-compositions): take the Lean outputs of a suite by
script, from the eval_decl tool results of this agent's session.

  cd migration/port-to-lean && python3 diffeval/units/fz10c_stale_collect.py <session record .jsonl> <tool-results dir> <suite>

As fz10_collect.py (an output is taken only for an input whose echoed text equals the generated input
character for character, and which returned), plus: a result too large for the session record is saved by
the client as a JSON file in <tool-results dir> (mcp-*eval_decl-*.txt); those files are read too.
Writes work/<suite>.out.txt, one line per input (`ERROR not run` when none).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import fz10_collect as base  # noqa: E402


def saved(d: Path) -> dict[str, str]:
    out: dict[str, str] = {}
    for f in sorted(d.glob("mcp-*eval_decl-*.txt")):
        try:
            r = json.loads(f.read_text())
        except json.JSONDecodeError:
            continue
        if isinstance(r, dict) and r.get("success"):
            for case in r.get("cases", []):
                if case.get("kind") == "returned":
                    out[case["input"]] = " ".join(case["output"].split())
    return out


def main() -> None:
    rec, tr, suite = Path(sys.argv[1]), Path(sys.argv[2]), sys.argv[3]
    got = base.results(rec)
    got.update(saved(tr))
    calls = json.loads((HERE.parent / "work" / f"{suite}.inputs.json").read_text())
    lines, miss = [], 0
    for c in calls:
        for t in c["inputs"]:
            if t in got:
                lines.append(got[t])
            else:
                lines.append("ERROR not run")
                miss += 1
    (HERE.parent / "work" / f"{suite}.out.txt").write_text("\n".join(lines) + "\n")
    print(f"{suite} inputs {len(lines)} not run {miss}")


if __name__ == "__main__":
    main()
