"""Update 2026-11-17: manifest.tsv after the port changes of 2026-11-16 and 2026-11-17.

Adds the column update_2026_11_17. The rows of the changed units get their new lines by hand
(CHANGED below, as the stored-source check finds them); every other row of the two changed files
gets its lines moved by the hunks of the two diffs (old line -> new line), checked by comparing
the first line of the unit's text is still a line of the file (def/class rows) where possible.

  python3 experiments/u17_manifest.py            (rewrites manifest.tsv; prints what moved)
"""
import csv
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
DIFFS = [HERE / "port-changes-2026-11-16.diff", HERE / "port-changes-2026-11-17-second.diff"]
CHANGED = {
    "def:LogisticFit": ("670-683", "CHANGE (field separation, D1)"),
    "def:classification_table": ("1236-1341", "CHANGE (b; level 1.000 on every fit)"),
    "def:run_py_py_py": ("20-851", "CHANGE (wiring; precondition without final_effects != [])"),
    "def:train_run_03_fit_global_rsquare": ("154-268", "CHANGE (d, e)"),
    "def:train_run_05_association": ("292-328", "CHANGE (d)"),
    "def:train_run_06_coefficients_odds": ("334-375", "CHANGE (d)"),
    "def:train_run_07_hl": ("380-414", "CHANGE (d)"),
    "def:train_run_13_roc": ("702-718", "CHANGE (a)"),
    "def:train_run_14_final_and_summary": ("725-819", "CHANGE (a; precondition G30)"),
    "def:train_run_15_printed_roc": ("823-842", "CHANGE (a)"),
}


def hunks(diff: Path) -> dict[str, list[tuple[int, int, int]]]:
    out: dict[str, list[tuple[int, int, int]]] = {}
    cur = None
    for line in diff.read_text().split("\n"):
        m = re.match(r"^\+\+\+ b/(.*)$", line)
        if m:
            cur = m.group(1)
            out[cur] = []
        m = re.match(r"^@@ -(\d+),(\d+) \+(\d+),(\d+) @@", line)
        if m and cur:
            a, n, b, k = (int(x) for x in m.groups())
            out[cur].append((a, n, k - n))  # old start, old length, net lines added
    return out


def move(line: int, hs: list[tuple[int, int, int]]) -> int:
    shift = 0
    for a, n, net in hs:
        if line >= a + n:
            shift += net
        elif line >= a:  # inside a hunk: keep the shift of the hunks before (context lines lead)
            break
    return line + shift


def main() -> int:
    rows = list(csv.DictReader((HERE / "manifest.tsv").open(), delimiter="\t"))
    fields = list(rows[0].keys())
    if "update_2026_11_17" not in fields:
        fields.append("update_2026_11_17")
    hs = [hunks(d) for d in DIFFS]
    for r in rows:
        item, f = r["item_id"], r["file"]
        if item in CHANGED:
            new, note = CHANGED[item]
            print(f"{item}\t{r['lines']} -> {new}\t{note}")
            r["lines"], r["update_2026_11_17"] = new, note
            continue
        if r.get("update_2026_11_17"):
            continue  # already done by an earlier run
        if "-" not in r["lines"] or not any(f in h for h in hs):
            r["update_2026_11_17"] = "unchanged"
            continue
        lo, hi = (int(x) for x in r["lines"].split("-"))
        for h in hs:
            if f in h:
                lo, hi = move(lo, h[f]), move(hi, h[f])
        new = f"{lo}-{hi}"
        if new != r["lines"]:
            print(f"{item}\t{r['lines']} -> {new}\tmoved")
            r["lines"], r["update_2026_11_17"] = new, "unchanged (source range updated)"
        else:
            r["update_2026_11_17"] = "unchanged"
    with (HERE / "manifest.tsv").open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fields, delimiter="\t", lineterminator="\n")
        w.writeheader()
        w.writerows(rows)
    return 0


if __name__ == "__main__":
    sys.exit(main())
