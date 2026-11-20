"""Take the Lean outputs of a suite from this agent's own eval_decl results, by script (fidelity pass 2026-11-20c).

  cd migration/port-to-lean && python3 diffeval/units/fz10c_collect.py <suite> <session record .jsonl> [<tool-result .txt> ...]

As fz10_collect.py, plus: a result too long for the transcript is saved by the client as a JSON file under
<session>/tool-results/ (the session record then holds only a notice); those files are read too. For each input of
work/<suite>.inputs.json the output is that of an eval_decl case whose echoed input is the text, character for
character, and which returned; written to work/<suite>.out.txt, one line per input (`ERROR not run` when none).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import fz10_collect as base  # noqa: E402


def from_files(paths: list[Path]) -> dict[str, str]:
    out: dict[str, str] = {}
    for p in paths:
        r = json.loads(p.read_text())
        if isinstance(r, dict) and r.get("success"):
            for case in r.get("cases", []):
                if case.get("kind") == "returned":
                    out[case["input"]] = " ".join(case["output"].split())
    return out


def main() -> None:
    suite, rec = sys.argv[1], Path(sys.argv[2])
    got = base.results(rec)
    got.update(from_files([Path(x) for x in sys.argv[3:]]))
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
    print(suite, "inputs", len(lines), "not run", miss)


if __name__ == "__main__":
    main()
