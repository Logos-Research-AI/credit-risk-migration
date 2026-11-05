"""usage: python3 add.py rows.json -- appends rows (list of 7-field lists) to the shard file"""
import json, sys, pathlib
P = pathlib.Path("/Users/cristophersalvi/GitHub/sas-migration/migration/inventory.arith.tsv")
H = "file\tsymbol\tsource_construct\tclassification\ttarget_translation\tevidence\tstatus\n"
if not P.exists(): P.write_text(H)
rows = json.load(open(sys.argv[1]))
with P.open("a") as f:
    for r in rows:
        assert len(r) == 7, r
        for x in r: assert "\t" not in x and "\n" not in x, x
        f.write("\t".join(r) + "\n")
print("appended", len(rows))
