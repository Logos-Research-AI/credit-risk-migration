"""Text pass 2026-11-17, feature engineering (port-translator-4): checks the survey cannot make.
(1) def:run is over the size cap with both fields, so its `code` and `statement_text` were fetched in
    separate calls: compare the last of each, read from this translator's own session record.
(2) For each item, does the stored `code` equal the lines of port/credit_risk/feature_engineering.py that
    the manifest gives (step 9: report only, nothing fixed)?
"""
import csv, json, re
from pathlib import Path

HERE = Path(__file__).resolve().parents[2]
REC = Path.home() / ".claude" / "projects" / "-Users-cristophersalvi-GitHub-credit-risk-migration"
last = {}
for f in sorted(REC.glob("*/subagents/agent-aport-translator-4-*.jsonl")):
    for line in f.open():
        if "tool_result" not in line or '"def:' not in line:
            continue
        try:
            o = json.loads(line)
        except json.JSONDecodeError:
            continue
        ts = o.get("timestamp", "")
        if ts < "2026-11-17":
            continue
        c = (o.get("message") or {}).get("content")
        for b in c if isinstance(c, list) else []:
            if not isinstance(b, dict) or b.get("type") != "tool_result":
                continue
            cc = b.get("content")
            for t in ([cc] if isinstance(cc, str) else [x.get("text", "") for x in cc or [] if isinstance(x, dict)]):
                try:
                    r = json.loads(t)
                except (json.JSONDecodeError, TypeError):
                    continue
                for it in (r.get("result") if isinstance(r, dict) and isinstance(r.get("result"), list) else []):
                    if isinstance(it, dict) and "id" in it:
                        for k in ("code", "statement_text", "state"):
                            if k in it and (it["id"], k) not in last or (k in it and last[(it["id"], k)][0] <= ts):
                                last[(it["id"], k)] = (ts, it[k])
src = (HERE.parents[1] / "port" / "credit_risk" / "feature_engineering.py").read_text().splitlines()
for row in csv.DictReader((HERE / "manifest.tsv").open(), delimiter="\t"):
    if row["file"] != "port/credit_risk/feature_engineering.py":
        continue
    i = row["item_id"]
    code, text, state = (last.get((i, k), (None, None))[1] for k in ("code", "statement_text", "state"))
    a, b = (int(x) for x in row["lines"].split("-"))
    port = "\n".join(src[a - 1:b])
    nonum = lambda s: "\n".join(re.sub(r"\d+", "N", ln) if ln.lstrip().startswith("#") or "  # " in ln else ln for ln in s.splitlines())  # noqa: E731
    strip = lambda s: "\n".join(ln for ln in (re.sub(r"\s*#.*$", "", x).rstrip() for x in s.splitlines()) if ln.strip())  # noqa: E731
    vs = "equal" if code.strip("\n") == port.strip("\n") else "numbers in comments only" if nonum(code).strip("\n") == nonum(port).strip("\n") else \
        "comments only" if strip(code) == strip(port) else "CODE LINES DIFFER"
    print(f"{i:32} state {state}; statement_text == code: {text == code}; code vs port lines {row['lines']}: {vs}")
