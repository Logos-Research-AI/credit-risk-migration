#!/usr/bin/env python3
"""Gap sweep (kit prompt 02): enumerate, by script, every site in the SAS programs where
SAS semantics differ from what Python/polars would do by default (RULEBOOK §5).
The output list is the definition of done for migration/inventory.tsv: the inventory is
complete when every site here has a row.

Categories (one site per occurrence; a statement can yield several sites):
  CMP       a comparison (<, <=, >, >=, =, ^=, ne, in) in IF / WHERE / CASE WHEN / flag
            assignment / PROC SQL: missing-value ordering, 0/1 result
  FUNC      a SAS function call (sum, min, max, log, exp, round, input, missing, ...)
  DIV       a division in an assignment or SQL expression: SAS gives missing on /0
  ARITH     an assignment whose expression does arithmetic on variables that may be missing
  PROC      every procedure invocation: defaults (type guessing, ties, ordering, tables)
  FORMAT    a format attached to a variable (printed output)
  DSTEP     DATA step machinery: retain, end=, merge, multiple output datasets, keep/drop
  SQL       PROC SQL machinery: joins, group by, aggregates, calculated, remerge, order by
  MACRO     macro definitions/calls, %let, INTO: macro variables
  ODS       ods output requests

Usage:  python3 sweep_gaps.py --root <repo> --out migration/gap-sweep.tsv [--stable]
Output: TSV site_id, file, line, category, symbol, snippet. Deterministic, sorted.
--stable keeps the site_id of every site already in --out (inventory rows cite them) and
numbers new sites after the highest existing id; sites no longer found are reported.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

PROGRAMS = ["feature_engineering.sas", "train.sas", "metrics_calculation.sas", "predict.sas"]
FUNCS = ["sum", "min", "max", "log", "exp", "round", "input", "missing", "abs", "mean", "median",
         "count", "today", "floor", "ceil", "int", "sqrt", "put", "substr", "scan", "compress", "coalesce"]
CMP_OP = r"(<=|>=|\^=|~=|<>|<|>|=|\bne\b|\beq\b|\blt\b|\bgt\b|\ble\b|\bge\b|\bin\s*\()"


OPERAND = r"(\((?:[^()]|\([^()]*\))*\)|[\w.&]+(?:\([^()]*\))?)"


def divisions(text: str) -> list[tuple[str, str]]:
    """Every a / b in text, including divisions nested inside parenthesized operands."""
    out = []
    for m in re.finditer(OPERAND + r"\s*/\s*" + OPERAND, text):
        out.append((m.group(1), m.group(2)))
        for g in (m.group(1), m.group(2)):
            if g.startswith("(") or "(" in g:
                out += divisions(g[g.index("(") + 1:-1])
    return out


def _blank(m: re.Match) -> str:
    return re.sub(r"[^\n]", " ", m.group(0))


def strip_comments(src: str) -> str:
    src = re.sub(r"/\*.*?\*/", _blank, src, flags=re.S)
    return re.sub(r"(?<=;)\s*%?\*[^;]*;|^\s*%?\*[^;]*;", _blank, src, flags=re.M)


def first_line_of(src: str, offset: int) -> int:
    return src.count("\n", 0, offset) + 1


def scan(path: Path, rel: str) -> list[tuple[str, int, str, str, str]]:
    src = strip_comments(path.read_text(errors="replace"))
    sites: list[tuple[str, int, str, str, str]] = []
    proc = None  # current procedure name, or "data"
    for m in re.finditer(r"[^;]*;", src, flags=re.S):
        raw = m.group(0)[:-1]
        if not raw.strip():
            continue
        lead = len(raw) - len(raw.lstrip())
        line = first_line_of(src, m.start() + lead)
        st = " ".join(raw.split())
        low = st.lower()
        snip = st[:160]
        head = low.split(" ", 1)[0]

        def add(cat: str, sym: str) -> None:
            sites.append((rel, line, cat, sym, snip))

        if head == "proc":
            proc = low.split()[1] if len(low.split()) > 1 else "?"
            add("PROC", f"proc {proc}")
        elif head == "data" and not low.startswith("data="):
            proc = "data"
            outs = re.findall(r"(?:work\.)?([\w&]+)", low[5:].split("/")[0])
            if len(outs) > 1:
                add("DSTEP", "multiple output datasets: " + " ".join(outs))
        elif head in ("run", "quit"):
            pass
        if head in ("%let",):
            add("MACRO", "%let " + low.split()[1].split("=")[0])
            continue
        if head.startswith("%macro"):
            add("MACRO", "%macro " + re.findall(r"%macro\s+(\w+)", low)[0])
            continue
        if re.match(r"%\w+\s*\(", low) and head not in ("%put", "%let"):
            add("MACRO", "macro call " + re.findall(r"%(\w+)", low)[0])
        if head.startswith("%"):
            continue
        if head == "ods" and "output" in low:
            add("ODS", "ods output " + " ".join(re.findall(r"(\w+)\s*=", low)))
        # formats
        if head == "format":
            for fm in re.findall(r"(\w+)\s+((?:best|percent|date|comma|dollar)?\d*\.\d*)", low):
                add("FORMAT", f"{fm[0]} {fm[1]}")
            if "_numeric_" in low:
                add("FORMAT", "_numeric_ " + low.split()[-1])
        for fm in re.findall(r"as\s+(\w+)\s+format\s*=\s*([\w.]+)", low):
            add("FORMAT", f"{fm[0]} {fm[1]}")
        # data step machinery
        if proc == "data":
            if head == "retain":
                add("DSTEP", "retain " + " ".join(low.split()[1:]))
            if head == "set" and "end=" in low:
                add("DSTEP", "set end=" + re.findall(r"end\s*=\s*(\w+)", low)[0])
            if head == "merge":
                add("DSTEP", "merge " + " ".join(re.findall(r"work\.(\w+)", low)))
            if head == "set" and len(re.findall(r"work\.\w+", low)) > 1:
                add("DSTEP", "set (concatenate) " + " ".join(re.findall(r"work\.(\w+)", low)))
            if head in ("keep", "drop", "rename"):
                add("DSTEP", f"{head} " + " ".join(low.split()[1:])[:80])
        # SQL machinery
        if proc == "sql":
            if " join " in low:
                add("SQL", re.findall(r"(left|right|inner|full)?\s*join", low)[0] + " join")
            if "group by" in low:
                for g in re.findall(r"group by ([\w ,]+?)(?= order by|\)|$)", low):
                    add("SQL", "group by " + g.strip())
            if "order by" in low:
                for o in re.findall(r"order by ([\w ,]+)", low):
                    add("SQL", "order by " + o.strip())
            if "calculated" in low:
                add("SQL", "calculated " + " ".join(re.findall(r"calculated\s+(\w+)", low)))
            if re.search(r"\(select ", low):
                add("SQL", "subquery / remerge")
            if " into " in low and ":" in low:
                add("MACRO", "into " + " ".join(re.findall(r":(\w+)", low)))
        # split IF/ELSE statements into condition and action
        cond, action = None, None
        if head == "if" or low.startswith("else if"):
            parts = re.split(r"\bthen\b", low, maxsplit=1)
            cond = re.sub(r"^(else\s+)?if\s+", "", parts[0]).strip()
            action = parts[1].strip() if len(parts) > 1 else ""
        elif head == "else":
            action = low[4:].strip()
        elif head == "where":
            cond = low[5:].strip()
        elif proc == "data" and re.match(r"^[a-z_]\w*\s*(=|\+)", low):
            action = low

        cmp_zones = []
        if cond is not None:
            cmp_zones.append(cond)
            if not re.search(CMP_OP, cond) and "missing" not in cond:
                add("CMP", "truthy " + cond)  # SAS: true iff not missing and not 0
        if proc == "sql":
            cmp_zones += re.findall(r"when (.*?) then", low)
            cmp_zones += re.findall(r"\bwhere (.*?)(?: group by| order by|;|$)", low)
            cmp_zones += re.findall(r"\bon (.*?)(?: where| group by|$)", low)
        if action and re.match(r"^[a-z_]\w*\s*=", action):
            rhs = action.split("=", 1)[1]
            cmp_zones += [z[0] for z in re.findall(r"\(([^()]*" + CMP_OP + r"[^()]*)\)", rhs)]
        for zone in cmp_zones:
            for cm in re.finditer(r"([\w.]+|\([^()]*\))\s*" + CMP_OP + r"\s*([\w.'\"&-]+)", zone):  # & = macro variable
                add("CMP", f"{cm.group(1)} {cm.group(2).strip()} {cm.group(3)}")
            if "is not missing" in zone:
                add("CMP", "is not missing")
        # functions
        for fm in re.finditer(r"\b(" + "|".join(FUNCS) + r")\s*\(", low):
            if proc == "sql" and fm.group(1) == "count" and "count(*)" in low:
                add("FUNC", "count(*)")
                continue
            add("FUNC", fm.group(1) + "()")
        # actions: assignments and sum statements (also inside THEN / ELSE)
        if action:
            if re.match(r"^[a-z_]\w*\s*\+\s*[\w.]+$", action):
                add("DSTEP", "sum statement " + action)
            elif re.match(r"^[a-z_]\w*\s*=", action):
                target, rhs = [x.strip() for x in action.split("=", 1)]
                rhs = re.sub(r"\"[^\"]*\"|'[^']*'", "", rhs)
                for a, b in divisions(rhs):
                    add("DIV", f"{target} = {a} / {b}")
                if re.search(r"[\w)]\s*[-+*]\s*[\w(]", rhs) and "/" not in rhs:
                    add("ARITH", target)
        # SQL select expressions
        if proc == "sql" and head in ("select", "create"):
            zone = re.sub(r"\"[^\"]*\"|'[^']*'|\"[^\"]*\"n", "", low)
            for a, b in divisions(zone):
                add("DIV", f"sql {a} / {b}")
            for am in re.finditer(r"([\w.]+\s*[-+*]\s*[\w.]+)\s+as\s+(\w+)", zone):
                add("ARITH", f"sql {am.group(2)}")
    return sites


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--stable", action="store_true")
    args = ap.parse_args()
    rows = []
    for prog in PROGRAMS:
        rows += scan(args.root / prog, prog)
    rows = sorted(set(rows), key=lambda r: (PROGRAMS.index(r[0]), r[1], r[2], r[3]))
    args.out.parent.mkdir(parents=True, exist_ok=True)
    ids = {r: f"S{i:03d}" for i, r in enumerate(rows, 1)}
    if args.stable and args.out.exists():
        old = {}
        for ln in args.out.read_text().splitlines()[1:]:
            sid, file, line, cat, sym, snip = ln.split("\t")
            old[(file, int(line), cat, sym, snip)] = sid
        gone = [sid for k, sid in old.items() if k not in ids]
        if gone:
            print(f"WARNING: sites no longer found: {','.join(gone)}")
        nxt = max(int(v[1:]) for v in old.values()) + 1
        for r in rows:
            if r in old:
                ids[r] = old[r]
            else:
                ids[r] = f"S{nxt:03d}"
                nxt += 1
                print(f"new site {ids[r]}: {r[0]}:{r[1]} {r[2]} {r[3]}")
    with open(args.out, "w") as f:
        f.write("site_id\tfile\tline\tcategory\tsymbol\tsnippet\n")
        for r in sorted(rows, key=lambda r: int(ids[r][1:])):
            file, line, cat, sym, snip = r
            f.write(f"{ids[r]}\t{file}\t{line}\t{cat}\t{sym}\t{snip}\n")
    counts: dict[str, int] = {}
    for r in rows:
        counts[r[2]] = counts.get(r[2], 0) + 1
    print(f"sites={len(rows)} " + " ".join(f"{k}={v}" for k, v in sorted(counts.items())))
    return 0


if __name__ == "__main__":
    sys.exit(main())
