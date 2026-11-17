"""Text pass, port-translator-11: reads the get_items results of this translator's own session
record (last fetch of each field wins) and reports, per predict item: is statement_text == code,
and is code found verbatim in port/credit_risk/predict.py. Nothing is fetched or written."""
import json, re, sys
from pathlib import Path
REC = Path.home() / ".claude" / "projects" / "-Users-cristophersalvi-GitHub-credit-risk-migration"
since = sys.argv[1]
src = Path("../../port/credit_risk/predict.py").read_text()
vals = {}
for f in sorted(REC.glob("*/subagents/agent-aport-translator-11-*.jsonl")):
    for line in f.open():
        if "tool_result" not in line or '5365851c' in line and False:
            continue
        try: o = json.loads(line)
        except json.JSONDecodeError: continue
        ts = o.get("timestamp", "")
        if ts < since: continue
        content = (o.get("message") or {}).get("content")
        if not isinstance(content, list): continue
        for b in content:
            if not isinstance(b, dict) or b.get("type") != "tool_result": continue
            c = b.get("content")
            for t in ([c] if isinstance(c, str) else [x.get("text", "") for x in c or [] if isinstance(x, dict)]):
                try: r = json.loads(t)
                except (json.JSONDecodeError, TypeError): continue
                res = r.get("result") if isinstance(r, dict) else None
                if not isinstance(res, list): continue
                for it in res:
                    if not isinstance(it, dict) or "id" not in it: continue
                    for k in ("code", "statement_text", "state", "statement_lean"):
                        if k in it:
                            vals.setdefault(it["id"], {})[k] = (ts, it[k])
import hashlib
for i in sorted(vals):
    v = vals[i]
    if "code" not in v or v["code"][1] is None: continue
    code, text = v["code"][1], v.get("statement_text", (None, None))[1]
    lean = v.get("statement_lean", (None, None))[1]
    print(i, "SAME" if code == text else "DIFFERENT", "code-in-port" if code in src else "CODE-NOT-IN-PORT",
          "state=" + str(v.get("state", (None, None))[1]),
          "lean_sha=" + (hashlib.sha256(lean.encode()).hexdigest()[:16] if lean else "-"), len(code))
