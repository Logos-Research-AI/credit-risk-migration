"""T20: the Python source stored in each changed or added code item, against port/credit_risk.

The stored text reaches the translator only as the output of get_items (field `code`). This script
takes those outputs from the session record of the translator (argument 1: the .jsonl file), keeps
the last one seen for each item, writes it under diffeval/work/stored/<item>.py, and compares it with
the file and lines the manifest cites.

Verdicts
  IDENTICAL       the stored text is a run of whole lines of the file (trailing blanks ignored)
  COMMENTS-ONLY   not a run of lines, but the code tokens (comments, blank lines and line breaks
                  left out) are a run of the file's code tokens
  CODE-DIFFERS    neither
For the first two the lines where the text was found are printed beside the lines the manifest cites.
"""

from __future__ import annotations

import csv
import difflib
import io
import json
import sys
import textwrap
import tokenize
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent.parent
OUT = HERE / "work" / "stored"
SKIP = {tokenize.COMMENT, tokenize.NL, tokenize.NEWLINE, tokenize.INDENT, tokenize.DEDENT, tokenize.ENDMARKER}


def stored_items(record: Path) -> dict[str, str]:
    found: dict[str, str] = {}

    def walk(o: object) -> None:
        if isinstance(o, dict):
            if isinstance(o.get("id"), str) and isinstance(o.get("code"), str) and "state" in o:
                found[o["id"]] = o["code"]
            for v in o.values():
                walk(v)
        elif isinstance(o, list):
            for v in o:
                walk(v)
        elif isinstance(o, str) and o.startswith('{"result":[{"id":"def:') and '"code":' in o:
            try:
                walk(json.loads(o))
            except json.JSONDecodeError:
                pass

    with record.open() as fh:
        for line in fh:
            if '\\"code\\":' not in line:
                continue
            try:
                walk(json.loads(line))
            except json.JSONDecodeError:
                continue
    return found


def code_tokens(text: str) -> list[tuple[str, int]]:
    toks = []
    for t in tokenize.generate_tokens(io.StringIO(text).readline):
        if t.type not in SKIP:
            toks.append((t.string, t.start[0]))
    return toks


def find_run(hay: list[str], needle: list[str]) -> int:
    n = len(needle)
    for i in range(len(hay) - n + 1):
        if hay[i] == needle[0] and hay[i : i + n] == needle:
            return i
    return -1


def main() -> int:
    record = Path(sys.argv[1])
    only = set(sys.argv[2:])
    stored = stored_items(record)
    OUT.mkdir(parents=True, exist_ok=True)
    rows = list(csv.DictReader((HERE.parent / "manifest.tsv").open(), delimiter="\t"))
    bad = 0
    for r in rows:
        upd = r["update_2026_11_16"]
        if upd.startswith("unchanged") or upd.startswith("REMOVE"):
            continue
        item = r["item_id"]
        if only and item not in only:
            continue
        if item not in stored:
            print(f"{item}\tNOT-FETCHED\tcited {r['lines']}")
            bad += 1
            continue
        text = stored[item]
        (OUT / (item.replace("def:", "") + ".py")).write_text(text + "\n")
        file_lines = (ROOT / r["file"]).read_text().split("\n")
        hay = [x.rstrip() for x in file_lines]
        needle = [x.rstrip() for x in text.split("\n")]
        while needle and needle[-1] == "":
            needle.pop()
        i = find_run(hay, needle)
        if i >= 0:
            print(f"{item}\tIDENTICAL\tfound {i + 1}-{i + len(needle)}\tcited {r['lines']}")
            continue
        ftoks = code_tokens("\n".join(file_lines))
        stoks = code_tokens(textwrap.dedent(text) + "\n")
        j = find_run([t for t, _ in ftoks], [t for t, _ in stoks])
        lo, hi = (int(x) for x in r["lines"].split("-"))
        diff = [
            d
            for d in difflib.unified_diff(
                [x.rstrip() for x in file_lines[lo - 1 : hi]], needle, "file", "stored", lineterm="", n=0
            )
        ]
        if j >= 0:
            a, b = ftoks[j][1], ftoks[j + len(stoks) - 1][1]
            print(f"{item}\tCOMMENTS-ONLY\tcode found {a}-{b}\tcited {r['lines']}")
        else:
            print(f"{item}\tCODE-DIFFERS\tcited {r['lines']}")
            bad += 1
        for d in diff[:80]:
            print("    " + d)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
