#!/usr/bin/env python3
"""Deterministic dependency mapper for SAS programs (stdlib only), adapted from the kit's
depmap_python.py (prompts/01-dependency-map.md contract).

SAS programs have no import statements. They depend on each other through:
  1. FILES      a program reads a file another program writes
                (PROC IMPORT datafile= / INFILE  <-  PROC EXPORT outfile= / FILE)
  2. SESSION    a program uses WORK-library state it never creates itself, created by
                another program run earlier in the same session
                (restore=work.X / set work.X / data=work.X / from work.X ...  <-
                 store work.X / out=work.X / data work.X / create table work.X ...)
  3. INCLUDES   %include "file"
  4. MACROS     a %macro or macro variable used but not defined in the program, defined
                in another program
Edge A -> B means A depends on B. In-repo .sas files only: reads of files no program
writes (raw data) are neither edges nor misses.

Parsing is regex-based (there is no SAS AST library); comments are stripped first
(/* */ blocks, and `* ... ;` / `%* ... ;` statement comments). Path macros (%let x = ...;)
are expanded per program before matching, so "&output_path/a.csv" written by one
program matches the same resolved path read by another.

Usage:  python3 depmap_sas.py --root <repo> --out <repo>/migration/depmap
Emits:  edges.tsv (from, to, kind, symbol, evidence), order.txt (topological, one SCC per
        line, dependencies first), cycles.txt (SCCs > 1 file). Deterministic: sorted walk,
        sorted output; two runs give byte-identical files.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

SKIP_DIRS = {"migration", "judge", "node_modules", "__pycache__"}

WRITE_FILE = [r'\boutfile\s*=\s*"([^"]+)"', r"\bfile\s+\"([^\"]+)\""]
READ_FILE = [r'\bdatafile\s*=\s*"([^"]+)"', r'\binfile\s+"([^"]+)"']
INCLUDE = r'%include\s+"([^"]+)"'
# WORK dataset/item-store use (creation patterns are in scan())
WORK = r"work\.(\w+)"
ODS_OUTPUT = r"\bods\s+output\s+([^;]+);"
MACRO_DEF = r"%macro\s+(\w+)"
MACRO_CALL = r"%(\w+)\s*\("
MVAR_DEF = [r"%let\s+(\w+)\s*=", r"\binto\s*:\s*(\w+)", r"\binto\s*:(\w+)\s*,\s*:(\w+)", r"call\s+symputx?\s*\(\s*'(\w+)'"]
MVAR_USE = r"&(\w+)"
MACRO_BUILTINS = {"include", "let", "put", "macro", "mend", "if", "then", "else", "do", "end", "sysfunc",
                  "eval", "str", "nrstr", "upcase", "scan", "substr", "global", "local"}


def _blank(m: re.Match) -> str:
    return re.sub(r"[^\n]", " ", m.group(0))  # keep newlines so line numbers survive


def strip_comments(src: str) -> str:
    src = re.sub(r"/\*.*?\*/", _blank, src, flags=re.S)
    # statement comments: '*' or '%*' at the start of a statement, up to ';'
    return re.sub(r"(?<=;)\s*%?\*[^;]*;|^\s*%?\*[^;]*;", _blank, src, flags=re.M)


def expand_lets(src: str) -> str:
    lets = dict(re.findall(r"%let\s+(\w+)\s*=\s*([^;]*);", src, flags=re.I))
    for _ in range(5):  # nested references
        src = re.sub(r"&(\w+)\.?", lambda m: lets.get(m.group(1), m.group(0)).strip(), src)
    return src


def line_of(src: str, pos: int) -> int:
    return src.count("\n", 0, pos) + 1


def scan(path: Path, root: Path) -> dict:
    raw = path.read_text(errors="replace")
    clean = strip_comments(raw)
    expanded = expand_lets(clean)
    low = expanded.lower()
    info = {"writes": {}, "reads": {}, "includes": {}, "work_created": {}, "work_used": {},
            "macros_def": set(), "macros_used": {}, "mvars_def": set(), "mvars_used": {}}

    def ev(m):  # evidence: file:line; comment stripping and %let expansion preserve newlines
        return f"{path.relative_to(root)}:{line_of(expanded, m.start())}"

    for pat in WRITE_FILE:
        for m in re.finditer(pat, expanded, flags=re.I):
            info["writes"].setdefault(m.group(1), ev(m))
    for pat in READ_FILE:
        for m in re.finditer(pat, expanded, flags=re.I):
            info["reads"].setdefault(m.group(1), ev(m))
    for m in re.finditer(INCLUDE, expanded, flags=re.I):
        info["includes"].setdefault(m.group(1), ev(m))
    for m in re.finditer(r"\bdata\s+([^;]+);", low):
        for name in re.findall(r"work\.(\w+)", m.group(1)):
            info["work_created"].setdefault(name, ev(m))
    for pat in (r"\bout\s*=\s*work\.(\w+)", r"\bstore\s+work\.(\w+)", r"\bcreate\s+table\s+work\.(\w+)"):
        for m in re.finditer(pat, low):
            info["work_created"].setdefault(m.group(1), ev(m))
    for m in re.finditer(ODS_OUTPUT, low):
        for name in re.findall(r"=\s*work\.(\w+)", m.group(1)):
            info["work_created"].setdefault(name, ev(m))
    for m in re.finditer(WORK, low):
        info["work_used"].setdefault(m.group(1), ev(m))
    info["macros_def"].update(x.lower() for x in re.findall(MACRO_DEF, clean, flags=re.I))
    for m in re.finditer(MACRO_CALL, clean, flags=re.I):
        name = m.group(1).lower()
        if name not in MACRO_BUILTINS:
            info["macros_used"].setdefault(name, ev(m))
    for pat in MVAR_DEF:
        for m in re.finditer(pat, clean, flags=re.I):
            info["mvars_def"].update(g.lower() for g in m.groups() if g)
    for m in re.finditer(MVAR_USE, clean):
        info["mvars_used"].setdefault(m.group(1).lower(), ev(m))
    # macro parameters are local definitions
    for m in re.finditer(r"%macro\s+\w+\s*\(([^)]*)\)", clean, flags=re.I):
        info["mvars_def"].update(p.strip().split("=")[0].lower() for p in m.group(1).split(",") if p.strip())
    return info


def extract_edges(files: list[Path], root: Path) -> list[tuple[str, str, str, str, str]]:
    rel = {p: str(p.relative_to(root)) for p in files}
    info = {p: scan(p, root) for p in files}
    edges = set()
    for a in files:
        ia = info[a]
        for b in files:
            if a == b:
                continue
            ib = info[b]
            for f, e in ia["reads"].items():
                if f in ib["writes"] and f not in ia["writes"]:
                    edges.add((rel[a], rel[b], "file", Path(f).name, f"{e} <- {ib['writes'][f]}"))
            for name, e in ia["work_used"].items():
                if name not in ia["work_created"] and name in ib["work_created"]:
                    edges.add((rel[a], rel[b], "session", f"work.{name}", f"{e} <- {ib['work_created'][name]}"))
            for name, e in ia["macros_used"].items():
                if name not in ia["macros_def"] and name in ib["macros_def"]:
                    edges.add((rel[a], rel[b], "macro", f"%{name}", e))
            for name, e in ia["mvars_used"].items():
                if name not in ia["mvars_def"] and name in ib["mvars_def"]:
                    edges.add((rel[a], rel[b], "macro-var", f"&{name}", e))
        for inc, e in ia["includes"].items():
            target = (a.parent / inc).resolve()
            for b in files:
                if b.resolve() == target:
                    edges.add((rel[a], rel[b], "include", inc, e))
    return sorted(edges)


def tarjan_scc(nodes: list[str], adj: dict[str, set[str]]) -> list[list[str]]:
    index, low, on, stack, out, counter = {}, {}, set(), [], [], [0]

    def visit(v):
        index[v] = low[v] = counter[0]
        counter[0] += 1
        stack.append(v)
        on.add(v)
        for w in sorted(adj.get(v, ())):
            if w not in index:
                visit(w)
                low[v] = min(low[v], low[w])
            elif w in on:
                low[v] = min(low[v], index[w])
        if low[v] == index[v]:
            comp = []
            while True:
                w = stack.pop()
                on.discard(w)
                comp.append(w)
                if w == v:
                    break
            out.append(sorted(comp))

    for v in sorted(nodes):
        if v not in index:
            visit(v)
    return out  # Tarjan emits SCCs in reverse topological order: dependencies first


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    args = ap.parse_args()
    root = args.root.resolve()
    files = sorted(p for p in root.rglob("*.sas")
                   if not any(part.startswith(".") or part in SKIP_DIRS for part in p.relative_to(root).parts))
    edges = extract_edges(files, root)
    nodes = [str(p.relative_to(root)) for p in files]
    adj: dict[str, set[str]] = {}
    for a, b, *_ in edges:
        adj.setdefault(a, set()).add(b)
    order = tarjan_scc(nodes, adj)
    cycles = [c for c in order if len(c) > 1]
    if len(files) > 1 and not edges:
        print("WARNING: 0 edges across multiple files - check --root (kit RUN-NOTES Run 1)", file=sys.stderr)
    args.out.mkdir(parents=True, exist_ok=True)
    with open(args.out / "edges.tsv", "w") as f:
        f.write("from\tto\tkind\tsymbol\tevidence\n")
        for e in edges:
            f.write("\t".join(e) + "\n")
    with open(args.out / "order.txt", "w") as f:
        f.write("# migration order: one batch per line, dependencies first\n")
        for scc in order:
            f.write("\t".join(scc) + "\n")
    with open(args.out / "cycles.txt", "w") as f:
        f.write(f"# strongly connected components > 1 file: {len(cycles)}\n")
        for scc in cycles:
            f.write("\t".join(scc) + "\n")
    print(f"files={len(files)} edges={len(edges)} batches={len(order)} cycles={len(cycles)}")
    print(f"wrote {args.out}/edges.tsv, order.txt, cycles.txt")
    return 0


if __name__ == "__main__":
    sys.exit(main())
