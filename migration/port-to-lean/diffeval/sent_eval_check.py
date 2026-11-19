"""Whether each given eval input file was sent, character for character, in an eval_decl call of the
session record (companion of sent_code_check.py, 2026-11-18).

usage: sent_eval_check.py <session.jsonl> <input file> [<input file> ...]
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


sent = []
with open(sys.argv[1], encoding="utf-8") as fh:
    for line in fh:
        try:
            rec = json.loads(line)
        except ValueError:
            continue
        for d in walk(rec):
            if isinstance(d.get("name"), str) and d["name"].endswith("eval_decl") and isinstance(d.get("input"), dict):
                sent += d["input"].get("inputs", [])
bad = 0
for p in sys.argv[2:]:
    ok = open(p, encoding="utf-8").read() in sent
    bad += not ok
    print(p, "SENT" if ok else "NOT SENT")
sys.exit(1 if bad else 0)
