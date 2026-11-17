"""Update 2026-11-17: for every manifest row whose lines were moved, print the first and last line
of the cited range in the port file, to check the range by eye."""
import csv
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
PORT = HERE.parent.parent / "port" / "credit_risk"
rows = list(csv.DictReader((HERE / "manifest.tsv").open(), delimiter="\t"))
for r in rows:
    if r["update_2026_11_17"].startswith("unchanged (source") and "-" in r["lines"]:
        lo, hi = map(int, r["lines"].split("-"))
        lines = (PORT / Path(r["file"]).name).read_text().split("\n")
        print(r["item_id"], r["lines"], "|", lines[lo - 1][:60], "||", lines[hi - 1][:50])
