"""Fuzz pass 2026-11-16: take the Lean outputs of a suite from the tool results, by script.

  cd migration/port-to-lean && python3 diffeval/fuzz_collect.py <your number> <suite> [<suite> ...]

<your number>: 7 for port-translator-7. The script reads ONLY the session record of that translator
(files agent-aport-translator-<number>-*.jsonl; no other agent's record is opened). For each input of
work/<suite>.inputs.json it looks for an eval_decl call whose echoed input is that text, character
for character, and which returned a value; the outputs go to work/<suite>.out.txt, one line per
input, in order. An input with no such call is written as `ERROR not run` and listed. So a suite
that passes compare.py after this was evaluated on exactly the generated inputs, and nothing was
typed.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
RECORDS = Path.home() / ".claude" / "projects" / "-Users-cristophersalvi-GitHub-credit-risk-migration"


def eval_results(number: str) -> dict[str, str]:
    if not re.fullmatch(r"[0-9]+", number):
        raise SystemExit("first argument: your translator number")
    files = sorted(RECORDS.glob(f"*/subagents/agent-aport-translator-{number}-*.jsonl"))
    if not files:
        raise SystemExit(f"no session record of port-translator-{number}")
    out: dict[str, str] = {}
    for f in files:
        with f.open() as fh:
            for line in fh:
                if '\\"cases\\"' not in line or "elapsed_ms" not in line:
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
                        if not isinstance(r, dict) or not r.get("success"):
                            continue
                        for case in r.get("cases", []):
                            if case.get("kind") == "returned":
                                out[case["input"]] = " ".join(case["output"].split())
    return out


def main() -> int:
    got = eval_results(sys.argv[1])
    bad = 0
    for suite in sys.argv[2:]:
        groups = json.loads((HERE / "work" / f"{suite}.inputs.json").read_text())
        inputs = [t for g in groups for t in g["inputs"]]
        lines, missing = [], []
        for k, t in enumerate(inputs):
            if t in got:
                lines.append(got[t])
            else:
                lines.append("ERROR not run")
                missing.append(k)
        (HERE / "work" / f"{suite}.out.txt").write_text("\n".join(lines) + "\n")
        print(f"{suite}: {len(inputs) - len(missing)} of {len(inputs)} inputs found in the tool results; missing {missing}")
        bad += len(missing)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
