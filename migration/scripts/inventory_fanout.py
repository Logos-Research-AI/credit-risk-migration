#!/usr/bin/env python3
"""Gap inventory fan-out tooling (kit prompt 02, after the first-20-rows gate).

  assign            write migration/fanout/<shard>.sites.tsv: every gap-sweep site not yet
                    cited by migration/inventory.batch1.tsv, split into disjoint shards
  check SHARD [--final]
                    validate migration/inventory.<SHARD>.tsv against its assignment
                    (format, vocabulary, cited sites real and in the right file, coverage;
                    --final makes missing coverage an error)
  merge             merge batch1 + every shard into migration/inventory.tsv: dedupe on
                    (file, symbol, source_construct) (last write wins inside a shard; the
                    same key from two sources with different content is a CONFLICT),
                    deterministic sort, coverage of all sweep sites, then `wc -l`

Row contract (same 7 columns as batch 1): the evidence column cites file.sas:line and
ends with '; sites S###,S###,...' (the sweep sites the row decides).
"""

from __future__ import annotations

import csv
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MIG = ROOT / "migration"
SWEEP = MIG / "gap-sweep.tsv"
BATCH1 = MIG / "inventory.batch1.tsv"
FANOUT = MIG / "fanout"
MERGED = MIG / "inventory.tsv"
PROGRAMS = ["feature_engineering.sas", "train.sas", "metrics_calculation.sas", "predict.sas"]
HEADER = ["file", "symbol", "source_construct", "classification", "target_translation", "evidence", "status"]
VOCAB = {"TYPE_GUESS", "MISSING_SOURCE", "MISSING_NULLABLE", "MISSING_NEVER", "ROUNDING", "FORMAT",
         "ORDER", "PROC_SEMANTICS", "MODEL_STAT", "SESSION_STATE", "BUG", "UNKNOWN", "NO_GAP",
         "LISTING_ONLY"}
SHARD_STATUS = {"proposed", "unknown"}

# shards owning explicit sites (claimed first), then category shards take the rest
EXPLICIT: dict[str, set[str]] = {
    "modelstat-fit": set(),  # rows required below; the PROC LOGISTIC site S093 is batch 1's
    "modelstat-classify": {"S191", "S192", "S193", "S194", "S215", "S216"},  # ROC nofit + ods output
}
# shard -> judged output files that must each be the symbol of at least one row
REQUIRED: dict[str, list[str]] = {
    "modelstat-fit": ["model_coefficients.csv", "stepwise_summary.csv", "printed_fit_statistics.csv",
                      "printed_global_tests.csv", "printed_rsquare.csv", "printed_odds_ratios.csv"],
    "modelstat-classify": ["printed_hl_partition.csv", "printed_hosmer_lemeshow.csv",
                           "printed_classification.csv", "printed_roc_train.csv",
                           "printed_roc_validation.csv", "printed_roc_metrics.csv"],
}
# shard name -> (categories, files or None for all)
SHARDS: dict[str, tuple[set[str], set[str] | None]] = {
    "cmp-fe-predict": ({"CMP"}, {"feature_engineering.sas", "predict.sas"}),
    "cmp-train-metrics": ({"CMP"}, {"train.sas", "metrics_calculation.sas"}),
    "arith": ({"FUNC", "ARITH", "DIV"}, None),
    "proc": ({"PROC", "ODS", "FORMAT"}, None),
    "dstep": ({"DSTEP", "SQL", "MACRO"}, None),
}
ALL_SHARDS = list(EXPLICIT) + list(SHARDS)


def sweep() -> list[dict[str, str]]:
    return list(csv.DictReader(open(SWEEP), delimiter="\t"))


def read_rows(path: Path) -> list[list[str]]:
    lines = [ln for ln in path.read_text().split("\n") if ln.strip()]
    if not lines or lines[0].split("\t") != HEADER:
        raise SystemExit(f"{path.name}: header must be exactly {HEADER}")
    return [ln.split("\t") for ln in lines[1:]]


def cited(row: list[str]) -> list[str]:
    m = re.search(r"sites (S\d{3}(?:,S\d{3})*)\s*$", row[5])
    return m.group(1).split(",") if m else []


def covered_by_batch1() -> set[str]:
    return {s for r in read_rows(BATCH1) for s in cited(r)}


def assign() -> int:
    FANOUT.mkdir(exist_ok=True)
    done = covered_by_batch1()
    todo = [s for s in sweep() if s["site_id"] not in done]
    seen: set[str] = set()
    for name in ALL_SHARDS:
        if name in EXPLICIT:
            mine = [s for s in todo if s["site_id"] in EXPLICIT[name]]
        else:
            cats, files = SHARDS[name]
            mine = [s for s in todo if s["site_id"] not in seen and s["category"] in cats
                    and (files is None or s["file"] in files)]
        seen |= {s["site_id"] for s in mine}
        with open(FANOUT / f"{name}.sites.tsv", "w") as f:
            f.write("site_id\tfile\tline\tcategory\tsymbol\tsnippet\n")
            for s in mine:
                f.write("\t".join(s[k] for k in ("site_id", "file", "line", "category", "symbol", "snippet")) + "\n")
        print(f"{name}: {len(mine)} sites")
    left = [s["site_id"] for s in todo if s["site_id"] not in seen]
    assert not left, f"unassigned sites: {left}"
    print(f"assigned {len(seen)} of {len(todo)} uncovered sites ({len(done)} covered by batch 1)")
    return 0


def check(name: str, final: bool) -> int:
    sites = {s["site_id"]: s for s in sweep()}
    assigned = [ln.split("\t")[0] for ln in (FANOUT / f"{name}.sites.tsv").read_text().split("\n")[1:] if ln]
    path = MIG / f"inventory.{name}.tsv"
    if not path.exists():
        print(f"{path.name}: missing")
        return 1
    errors, warns, cov = [], [], set()
    keys: dict[tuple[str, str, str], int] = {}
    for i, r in enumerate(read_rows(path), 2):
        tag = f"line {i}"
        if len(r) != 7:
            errors.append(f"{tag}: {len(r)} fields (need 7; tabs inside a field?)")
            continue
        if any(not x.strip() for x in r):
            errors.append(f"{tag}: empty field")
        if r[0] not in PROGRAMS:
            errors.append(f"{tag}: file {r[0]!r} is not one of {PROGRAMS}")
        bad = [c for c in r[3].split(";") if c not in VOCAB]
        if bad:
            errors.append(f"{tag}: classification {bad} not in {sorted(VOCAB)}")
        if r[6] not in SHARD_STATUS:
            errors.append(f"{tag}: status {r[6]!r} not in {sorted(SHARD_STATUS)}")
        if (r[6] == "unknown" or "UNKNOWN" in r[3]) and "TODO(port):" not in r[4]:
            errors.append(f"{tag}: UNKNOWN row needs a conservative translation with 'TODO(port): ... q: ...'")
        if not re.search(r"\b\w+\.sas:\d+", r[5]):
            errors.append(f"{tag}: evidence cites no file.sas:line")
        ids = cited(r)
        if not ids:
            errors.append(f"{tag}: evidence must end with '; sites S###,...'")
        for s in ids:
            if s not in sites:
                errors.append(f"{tag}: {s} is not a sweep site")
            elif sites[s]["file"] != r[0]:
                errors.append(f"{tag}: {s} is in {sites[s]['file']}, row is for {r[0]}")
            elif s not in assigned:
                warns.append(f"{tag}: {s} is not assigned to shard {name} (fine if it really belongs here)")
        cov |= set(ids)
        k = (r[0], r[1], r[2])
        if k in keys:
            warns.append(f"{tag}: duplicate key of line {keys[k]} (last write wins at merge)")
        keys[k] = i
    missing = [s for s in assigned if s not in cov]
    symbols = " ".join(k[1] for k in keys)
    need = [f for f in REQUIRED.get(name, []) if f not in symbols]
    (errors if final else warns).extend([f"required table rows missing: {need}"] if need else [])
    (errors if final else warns).extend([f"uncovered assigned sites ({len(missing)}): {','.join(missing)}"] if missing else [])
    for w in warns:
        print("WARN ", w)
    for e in errors:
        print("ERROR", e)
    print(f"{path.name}: {len(keys)} rows, covers {len(set(assigned) & cov)}/{len(assigned)} assigned sites, "
          f"{len(errors)} errors")
    return 1 if errors else 0


def merge() -> int:
    sources = [BATCH1] + [MIG / f"inventory.{n}.tsv" for n in ALL_SHARDS]
    merged: dict[tuple[str, str, str], tuple[list[str], str]] = {}
    conflicts = []
    for src in sources:
        rows = read_rows(src)
        local: dict[tuple[str, str, str], list[str]] = {}
        for r in rows:
            local[(r[0], r[1], r[2])] = r  # retry duplicates inside one source: last wins
        for k, r in local.items():
            if k in merged and merged[k][0] != r:
                conflicts.append(f"{k} differs between {merged[k][1]} and {src.name}")
            merged[k] = (r, src.name)
    if conflicts:
        for c in conflicts:
            print("CONFLICT", c)
        return 1

    def order(r: list[str]) -> tuple[int, int, str, str]:
        first = min((int(s[1:]) for s in cited(r)), default=10**6)
        return (PROGRAMS.index(r[0]), first, r[1], r[2])

    rows = sorted((r for r, _ in merged.values()), key=order)
    with open(MERGED, "w") as f:
        f.write("\t".join(HEADER) + "\n")
        for r in rows:
            f.write("\t".join(r) + "\n")
    all_sites = {s["site_id"] for s in sweep()}
    cov = {s for r in rows for s in cited(r)}
    missing = sorted(all_sites - cov)
    print(f"rows={len(rows)} sites covered={len(cov & all_sites)}/{len(all_sites)}"
          + (f" UNCOVERED={','.join(missing)}" if missing else ""))
    print(subprocess.run(["wc", "-l", str(MERGED.relative_to(ROOT))], cwd=ROOT, capture_output=True,
                         text=True).stdout.strip())
    return 1 if missing else 0


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd == "assign":
        sys.exit(assign())
    if cmd == "check" and len(sys.argv) >= 3:
        sys.exit(check(sys.argv[2], "--final" in sys.argv))
    if cmd == "merge":
        sys.exit(merge())
    sys.exit(__doc__)
