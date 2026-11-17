"""Text pass of 2026-11-17 (update-2026-11-17.md section 6): check from a translator's own session record.

usage: python3 diffeval/text_pass_check.py <session.jsonl> <since ISO time> [<item id>=<file>:<first>-<last> ...]

Reads, in order, every edit_text call (the statement_text SENT) and every get_items result of the
record since the given time. For each item reports:
  sent = code      the text sent with edit_text equals the `code` field as last fetched
  stored = code    the statement_text of the LAST fetch equals the code of the last fetch
For an item given as id=file:a-b (code over the fetch cap) the sent text is compared with the
lines of the port file. Trailing newlines are ignored (the tool drops them).
"""
import json
import sys


def walk(o):
    if isinstance(o, dict):
        yield o
        for v in o.values():
            yield from walk(v)
    elif isinstance(o, list):
        for v in o:
            yield from walk(v)


def texts(o):
    if isinstance(o, str):
        yield o
    elif isinstance(o, list):
        for v in o:
            yield from texts(v)
    elif isinstance(o, dict):
        for k in ("text", "content"):
            if k in o:
                yield from texts(o[k])


path, since = sys.argv[1], sys.argv[2]
files = dict(a.split("=", 1) for a in sys.argv[3:])
sent, code, stored, state = {}, {}, {}, {}
for line in open(path, encoding="utf-8"):
    try:
        rec = json.loads(line)
    except ValueError:
        continue
    if str(rec.get("timestamp", "")) < since:
        continue
    for d in walk(rec):
        if d.get("type") == "tool_use" and str(d.get("name", "")).endswith("edit_text"):
            i = d.get("input", {})
            if i.get("statement_text") is not None:
                sent[i["item_id"]] = i["statement_text"]
        if d.get("type") == "tool_result":
            for t in texts(d.get("content")):
                if not t.startswith('{"result":[{"id"'):
                    continue
                try:
                    items = json.loads(t)["result"]
                except ValueError:
                    continue
                for it in items:
                    if "id" not in it:
                        continue
                    if it.get("code") is not None:
                        code[it["id"]] = it["code"]
                    if it.get("statement_text") is not None:
                        stored[it["id"]] = it["statement_text"]
                    if "state" in it:
                        state[it["id"]] = it["state"]
n = lambda s: s.rstrip("\n")
bad = 0
for i in sorted(set(sent) | set(code)):
    if i.startswith("def:zz_"):
        continue
    row = [i, "edited" if i in sent else "not edited"]
    if i in files:
        f, r = files[i].rsplit(":", 1)
        a, b = map(int, r.split("-"))
        want = "".join(open(f, encoding="utf-8").readlines()[a - 1:b])
        ok = i in sent and n(sent[i]) == n(want)
        row.append(f"sent = {files[i]}: {ok} ({len(n(sent.get(i, '')))} / {len(n(want))} chars)")
        bad += not ok
    else:
        if i in sent:
            ok = i in code and n(sent[i]) == n(code[i])
            row.append(f"sent = code: {ok}")
            bad += not ok
        if i in stored and i in code:
            ok = n(stored[i]) == n(code[i])
            row.append(f"stored (last fetch) = code: {ok}")
            if i not in sent:
                bad += not ok
    row.append(state.get(i, ""))
    print("\t".join(row))
print("items:", len([i for i in set(sent) | set(code) if not i.startswith('def:zz_')]), "edited:", len(sent), "failures:", bad)
