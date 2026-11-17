"""Show that items resubmitted "unchanged" are unchanged: for each item id given, the accepted
Lean fetched (get_items, field statement_lean) BEFORE a dividing write and the accepted Lean
fetched AFTER it are compared character for character. Both texts are taken from the
translator's own session record; no Lean is written anywhere, only lengths, SHA-256 and the
verdict.

usage: unchanged_check.py <session.jsonl> <divider item id of the write_code call> <item id>...
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
    elif isinstance(o, str) and o.startswith('{"result"') and "statement_lean" in o:
        try:
            yield from walk(json.loads(o))
        except ValueError:
            pass


def main() -> int:
    path, divider, ids = sys.argv[1], sys.argv[2], sys.argv[3:]
    div_line = None
    seen: dict[str, list[tuple[int, str]]] = {i: [] for i in ids}
    with open(path, encoding="utf-8") as fh:
        for n, line in enumerate(fh):
            try:
                rec = json.loads(line)
            except ValueError:
                continue
            for d in walk(rec):
                if isinstance(d.get("name"), str) and d["name"].endswith("write_code") and isinstance(d.get("input"), dict):
                    if d["input"].get("item_id") == divider:
                        div_line = n
                if isinstance(d.get("id"), str) and d["id"] in seen and isinstance(d.get("statement_lean"), str):
                    seen[d["id"]].append((n, d["statement_lean"]))
    if div_line is None:
        print("no write_code call on", divider)
        return 2
    print(f"divider: write_code on {divider} at record {div_line}")
    print("item\tbefore_record\tafter_record\tchars\tsha256_before\tsha256_after\tverdict")
    bad = 0
    for i in ids:
        before = [x for x in seen[i] if x[0] < div_line]
        after = [x for x in seen[i] if x[0] > div_line]
        if not before or not after:
            print(f"{i}\t-\t-\t-\t-\t-\tMISSING (before {len(before)}, after {len(after)})")
            bad += 1
            continue
        (nb, b), (na, a) = before[-1], after[-1]
        hb = hashlib.sha256(b.encode()).hexdigest()[:16]
        ha = hashlib.sha256(a.encode()).hexdigest()[:16]
        ok = a == b
        bad += not ok
        print(f"{i}\t{nb}\t{na}\t{len(a)}\t{hb}\t{ha}\t{'IDENTICAL' if ok else 'DIFFERENT'}")
    print("all identical" if bad == 0 else f"{bad} not shown identical")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
