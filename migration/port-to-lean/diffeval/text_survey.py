"""Survey 2026-11-17 (asked by the lead): for every item of the port blueprint fetched with the
fields id, code, statement_text, does statement_text equal the stored source (`code`)?

  cd migration/port-to-lean && python3 diffeval/text_survey.py <since-ISO-date> <translator number> [<number> ...]

Reads the get_items results ONLY in the session records of the port translators whose numbers
are given (files agent-aport-translator-<number>-*.jsonl; default 8; no other agent's record is
opened), made on or after the given date; the last fetch of an item wins. A translator who
fetched items with the fields ["id", "code", "statement_text"] runs it with its own number. Nothing is fetched here and no Lean is read or written. Classes:
  SAME          statement_text == code
  NUMBERS       they differ only in digits inside comments (line numbers such as `name.sas:12-34`)
  COMMENTS      they differ only in comment text (code lines equal after removing `# ...`)
  SOURCE        code lines differ (the diff is listed)
  NO CODE       the item has no `code` (preconditions, items without a stored source)
"""
from __future__ import annotations

import difflib
import json
import re
import sys
from pathlib import Path

RECORDS = Path.home() / ".claude" / "projects" / "-Users-cristophersalvi-GitHub-credit-risk-migration"
since = sys.argv[1] if len(sys.argv) > 1 else "2026-11-17"
numbers = [a for a in sys.argv[2:] if re.fullmatch(r"[0-9]+", a)] or ["8"]
files = [f for n in numbers for f in sorted(RECORDS.glob(f"*/subagents/agent-aport-translator-{n}-*.jsonl"))]
items: dict[str, tuple[str, dict]] = {}
for f in files:
    with f.open() as fh:
        for line in fh:
            if "statement_text" not in line or "tool_result" not in line:
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
                for t in ([c] if isinstance(c, str) else [x.get("text", "") for x in c or [] if isinstance(x, dict)]):
                    try:
                        r = json.loads(t)
                    except (json.JSONDecodeError, TypeError):
                        continue
                    res = r.get("result") if isinstance(r, dict) else None
                    if not isinstance(res, list):
                        continue
                    for it in res:
                        if isinstance(it, dict) and "code" in it and "statement_text" in it and "id" in it and not it["id"].startswith("def:zz_"):
                            if it["id"] not in items or items[it["id"]][0] <= ts:
                                items[it["id"]] = (ts, it)


def nonum(s: str) -> str:
    out = []
    for ln in s.splitlines():
        if "#" in ln:
            i = ln.index("#")
            ln = ln[:i] + re.sub(r"\d+", "N", ln[i:])
        out.append(ln.rstrip())
    return "\n".join(out).strip("\n")


def nocomment(s: str) -> str:
    out = []
    for ln in s.splitlines():
        ln = re.sub(r"\s*#.*$", "", ln).rstrip()
        if ln.strip():
            out.append(ln)
    return "\n".join(out)


def stage(i: str) -> str:
    n = i.split(":", 1)[1]
    for p, s in (("fe_run", "feature engineering"), ("predict_run", "predict"), ("metrics_run", "metrics"), ("train_run", "train")):
        if n.startswith(p):
            return s
    return {"run": "feature engineering", "run_precond": "feature engineering", "run_py": "metrics", "run_py_precond": "metrics",
            "run_py_py": "predict", "run_py_py_precond": "predict", "run_py_py_py": "train", "run_py_py_py_precond": "train"}.get(n, "sas_compat and helpers")


rows: dict[str, list] = {}
for i, (_, it) in sorted(items.items()):
    code, text = it["code"], it["statement_text"] or ""
    if code is None:
        cls, diff = "NO CODE", []
    elif text.strip("\n") == code.strip("\n"):
        cls, diff = "SAME", []
    elif nonum(text) == nonum(code):
        cls, diff = "NUMBERS", []
    elif nocomment(text) == nocomment(code):
        cls, diff = "COMMENTS", []
    else:
        cls = "SOURCE"
        diff = [d for d in difflib.unified_diff(nocomment(text).splitlines(), nocomment(code).splitlines(), "statement_text", "code", lineterm="", n=0)
                if not d.startswith(("---", "+++", "@@"))]
    rows.setdefault(stage(i), []).append((i, cls, diff))
print(f"record files read: {len(files)}; items fetched with both fields since {since}: {len(items)}")
tot: dict[str, int] = {}
for s in ("sas_compat and helpers", "feature engineering", "train", "metrics", "predict"):
    print(f"\n== {s}")
    for i, cls, diff in rows.get(s, []):
        tot[cls] = tot.get(cls, 0) + 1
        if cls in ("SAME", "NO CODE"):
            continue
        print(f"  {cls:9s} {i}" + (f"  ({sum(d.startswith('-') for d in diff)} lines only in statement_text, {sum(d.startswith('+') for d in diff)} only in code)" if diff else ""))
        for d in diff[:12]:
            print(f"        {d[:150]}")
        if len(diff) > 12:
            print(f"        ... {len(diff) - 12} more")
    same = [i for i, c, _ in rows.get(s, []) if c == "SAME"]
    noc = [i for i, c, _ in rows.get(s, []) if c == "NO CODE"]
    print(f"  SAME: {len(same)}   NO CODE: {len(noc)}")
    print(f"  no code: {' '.join(x.split(':', 1)[1] for x in noc)}")
print("\ntotals:", tot)
