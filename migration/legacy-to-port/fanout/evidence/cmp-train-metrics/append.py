"""append rows: each arg is a JSON file holding a list of 7-field rows"""
import json, sys, pathlib
out = pathlib.Path("/Users/cristophersalvi/GitHub/sas-migration/migration/inventory.cmp-train-metrics.tsv")
HEADER = ["file","symbol","source_construct","classification","target_translation","evidence","status"]
if not out.exists():
    out.write_text("\t".join(HEADER) + "\n")
for p in sys.argv[1:]:
    for r in json.load(open(p)):
        assert len(r) == 7 and all("\t" not in f and "\n" not in f for f in r), r
        with out.open("a") as fh:
            fh.write("\t".join(r) + "\n")
