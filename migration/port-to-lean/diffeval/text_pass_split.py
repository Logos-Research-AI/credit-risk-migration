"""Text pass 2026-11-17, helper for an item fetched in separate calls (a composition over the cap).

  cd migration/port-to-lean && python3 diffeval/text_pass_split.py <since-ISO-date> <translator number> <item id> [<item id> ...]

Reads the get_items results ONLY in the session record of the port translator whose number is
given (as diffeval/text_survey.py does; no other agent's record is opened). For each item id it
prints, in the order of the fetches, the length and SHA-256 of every `code`, `statement_text`
and `statement_lean` value seen, and the state. The last `code` and the last `statement_text`
are compared (SAME / DIFFERENT); all `statement_lean` values are compared with each other
(before and after an edit_text). Nothing is fetched here; nothing is written.
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

RECORDS = Path.home() / ".claude" / "projects" / "-Users-cristophersalvi-GitHub-credit-risk-migration"
since, number, wanted = sys.argv[1], sys.argv[2], sys.argv[3:]
assert re.fullmatch(r"[0-9]+", number)
seen: dict[str, list[tuple[str, dict]]] = {w: [] for w in wanted}
for f in sorted(RECORDS.glob(f"*/subagents/agent-aport-translator-{number}-*.jsonl")):
    with f.open() as fh:
        for line in fh:
            if "tool_result" not in line:
                continue
            try:
                o = json.loads(line)
            except json.JSONDecodeError:
                continue
            ts = o.get("timestamp", "")
            if ts < since:
                continue
            content = (o.get("message") or {}).get("content")
            if not isinstance(content, list):
                continue
            for b in content:
                if not isinstance(b, dict) or b.get("type") != "tool_result":
                    continue
                c = b.get("content")
                for t in [c] if isinstance(c, str) else [x.get("text", "") for x in c or [] if isinstance(x, dict)]:
                    try:
                        r = json.loads(t)
                    except (json.JSONDecodeError, TypeError):
                        continue
                    res = r.get("result") if isinstance(r, dict) else None
                    if not isinstance(res, list):
                        continue
                    for it in res:
                        if isinstance(it, dict) and it.get("id") in seen:
                            seen[it["id"]].append((ts, it))


def sig(s: str) -> str:
    return f"len={len(s)} sha256={hashlib.sha256(s.encode()).hexdigest()}"


for item, fetches in seen.items():
    print(f"== {item}: {len(fetches)} fetches")
    last: dict[str, str] = {}
    leans: list[str] = []
    states: list[str] = []
    for ts, it in sorted(fetches, key=lambda p: p[0]):
        for k in ("code", "statement_text", "statement_lean"):
            if isinstance(it.get(k), str):
                print(f"  {ts} {k:15s} {sig(it[k])}")
                last[k] = it[k]
                if k == "statement_lean":
                    leans.append(it[k])
        if "state" in it:
            states.append(it["state"])
    if "code" in last and "statement_text" in last:
        print("  last statement_text vs last code:", "SAME" if last["code"] == last["statement_text"] else "DIFFERENT")
    if leans:
        print(f"  statement_lean values: {len(leans)}, all equal: {len(set(leans)) == 1}")
    print("  states seen:", sorted(set(states)))
