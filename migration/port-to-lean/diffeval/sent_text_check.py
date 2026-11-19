"""Compare the statement_text a translator SENT with edit_text (from the session record) with the
lines of the port file, character for character (companion of sent_code_check.py, 2026-11-18).

usage: sent_text_check.py <session.jsonl> <item id> <file> <first line> <last line>
"""
import hashlib
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


path, item, src, a, b = sys.argv[1], sys.argv[2], sys.argv[3], int(sys.argv[4]), int(sys.argv[5])
sent = None
with open(path, encoding="utf-8") as fh:
    for line in fh:
        try:
            rec = json.loads(line)
        except ValueError:
            continue
        for d in walk(rec):
            if isinstance(d.get("name"), str) and d["name"].endswith("edit_text") and isinstance(d.get("input"), dict):
                if d["input"].get("item_id") == item and d["input"].get("statement_text") is not None:
                    sent = d["input"]["statement_text"]
want = "".join(open(src, encoding="utf-8").readlines()[a - 1 : b]).rstrip("\n")
if sent is None:
    print(item, "no edit_text call found")
    sys.exit(2)
sent = sent.rstrip("\n")
ok = sent == want
print(f"{item}\t{src}:{a}-{b}\tsent {len(sent)} chars\tfile {len(want)} chars\t"
      f"{hashlib.sha256(sent.encode()).hexdigest()[:16]}\t{hashlib.sha256(want.encode()).hexdigest()[:16]}\t"
      f"{'IDENTICAL' if ok else 'DIFFERENT'}")
sys.exit(0 if ok else 1)
