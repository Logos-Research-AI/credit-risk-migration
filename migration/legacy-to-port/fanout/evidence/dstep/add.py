import sys, json
from pathlib import Path
OUT=Path('/Users/cristophersalvi/GitHub/sas-migration/migration/inventory.dstep.tsv')
HDR="file\tsymbol\tsource_construct\tclassification\ttarget_translation\tevidence\tstatus"
rows=json.load(open(sys.argv[1]))
if not OUT.exists(): OUT.write_text(HDR+"\n")
with OUT.open('a') as f:
    for r in rows:
        assert len(r)==7 and all('\t' not in x and '\n' not in x for x in r), r[:2]
        f.write("\t".join(r)+"\n")
print(len(OUT.read_text().strip().split("\n"))-1, "rows")
