"""Compare the source text a translator SENT with write_code (taken from the translator's session
record) with the lines of the port file it stands for, character for character.

usage: sent_code_check.py <session.jsonl> <item id> <file> <first line> <last line>
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
            if isinstance(d.get("name"), str) and d["name"].endswith("write_code") and isinstance(d.get("input"), dict):
                if d["input"].get("item_id") == item:
                    sent = d["input"].get("content")
want = "".join(open(src, encoding="utf-8").readlines()[a - 1 : b]).rstrip("\n")
if sent is None:
    print(item, "no write_code call found")
    sys.exit(2)
sent = sent.rstrip("\n")
ok = sent == want
print(f"{item}\t{src}:{a}-{b}\tsent {len(sent)} chars\tfile {len(want)} chars\t"
      f"{hashlib.sha256(sent.encode()).hexdigest()[:16]}\t{hashlib.sha256(want.encode()).hexdigest()[:16]}\t"
      f"{'IDENTICAL' if ok else 'DIFFERENT'}")
if not ok:
    sl, wl = sent.split("\n"), want.split("\n")
    for i, (x, y) in enumerate(zip(sl, wl)):
        if x != y:
            print("first difference at file line", a + i)
            print("  sent:", x)
            print("  file:", y)
            break
    else:
        print("line counts differ:", len(sl), len(wl))
sys.exit(0 if ok else 1)
