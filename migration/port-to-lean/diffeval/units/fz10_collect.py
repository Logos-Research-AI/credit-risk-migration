"""Take the Lean outputs of a fz10 suite from the eval_decl tool results of a session record, by script
(fuzz_collect.py, for a record whose file name is not agent-aport-translator-<n>-*).

  cd migration/port-to-lean && python3 diffeval/units/fz10_collect.py <session record .jsonl> <suite>

For each input of work/<suite>.inputs.json (a list of {"inputs": [text]}) it looks for an eval_decl case whose
echoed input is that text character for character and which returned; writes work/<suite>.out.txt, one line per
input (`ERROR not run` when none).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))


def results(record: Path) -> dict[str, str]:
    out: dict[str, str] = {}
    with record.open() as fh:
        for line in fh:
            if "elapsed_ms" not in line:
                continue
            try:
                o = json.loads(line)
            except json.JSONDecodeError:
                continue
            content = (o.get("message") or {}).get("content")
            if not isinstance(content, list):
                continue
            for b in content:
                if not isinstance(b, dict) or b.get("type") != "tool_result":
                    continue
                c = b.get("content")
                texts = [c] if isinstance(c, str) else [x.get("text", "") for x in c or [] if isinstance(x, dict)]
                for t in texts:
                    try:
                        r = json.loads(t)
                    except (json.JSONDecodeError, TypeError):
                        continue
                    if isinstance(r, dict) and r.get("success"):
                        for case in r.get("cases", []):
                            if case.get("kind") == "returned":
                                out[case["input"]] = " ".join(case["output"].split())
    return out


def main() -> None:
    rec, suite = Path(sys.argv[1]), sys.argv[2]
    got = results(rec)
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
